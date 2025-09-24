[CmdletBinding()]
param([string]$ProjectRoot)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Set location and validate git
if ($ProjectRoot) { Set-Location -LiteralPath $ProjectRoot }
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { 
    Write-Host 'ERROR: git not found in PATH' -ForegroundColor Red
    exit 1 
}

# Function to execute git command and capture output
function Invoke-GitCommand {
    param([string]$Command, [string]$Description)
    Write-Host "=== $Description ===" -ForegroundColor Cyan
    Write-Host "Executing: git $Command" -ForegroundColor Yellow
    
    try {
        $output = Invoke-Expression "git $Command" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host $output -ForegroundColor Green
            return $output
        } else {
            Write-Host "ERROR: $output" -ForegroundColor Red
            throw "Git command failed: git $Command"
        }
    } catch {
        Write-Host "EXCEPTION: $($_.Exception.Message)" -ForegroundColor Red
        throw
    }
}

# Show current project and timestamp
Write-Host "=== PromptForge Git Publish ===" -ForegroundColor Magenta
Write-Host "Project: $((Get-Location).Path)" -ForegroundColor White
Write-Host "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor White
Write-Host ""

# Show current status
Write-Host "=== Current Git Status ===" -ForegroundColor Cyan
$status = git status --porcelain=v1 -b 2>&1
Write-Host $status -ForegroundColor White

# Check if there are changes to commit
$changes = git status --porcelain=v1 2>&1
if (-not $changes) {
    Write-Host "No changes to commit. Repository is clean." -ForegroundColor Yellow
    
    # Still show current branch and remote info
    Write-Host ""
    Invoke-GitCommand "branch -vv" "Current Branch Information"
    Invoke-GitCommand "remote -v" "Remote Repository Information"
    exit 0
}

# Show what will be committed
Write-Host ""
$stagedOutput = Invoke-GitCommand "diff --name-status --cached" "Staged Changes"
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($stagedOutput)) {
    Write-Host "No staged changes. Staging all changes..." -ForegroundColor Yellow
}

# Stage all changes
Write-Host ""
$addResult = Invoke-GitCommand "add -A" "Staging All Changes"

# Show what was staged
Write-Host ""
Invoke-GitCommand "diff --name-status --cached" "Files to be Committed"

# Commit with automatic message
$commitMessage = "pf: apply changes - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""
$commitResult = Invoke-GitCommand "commit -m `"$commitMessage`"" "Committing Changes"

# Extract commit hash from commit output - FIXED VERSION
$commitHash = ""
if ($commitResult) {
    $commitResultString = $commitResult -join "`n"
    # Look for patterns like [branch 1a151c5] or [branch abcd123]
    if ($commitResultString -match '\[(.*?)\s+([a-f0-9]{7,})\]') {
        $commitHash = $matches[2]
        Write-Host "Commit Hash: $commitHash" -ForegroundColor Green
    } else {
        # Fallback: try to get latest commit hash
        try {
            $commitHash = git rev-parse --short HEAD 2>$null
            if ($commitHash) {
                Write-Host "Commit Hash (fallback): $commitHash" -ForegroundColor Green
            }
        } catch {
            Write-Host "Warning: Could not extract commit hash" -ForegroundColor Yellow
        }
    }
}

# Show branch information before push
Write-Host ""
Invoke-GitCommand "branch -vv" "Branch Information Before Push"

# Get current branch name
$currentBranch = git branch --show-current 2>&1
Write-Host "Current Branch: $currentBranch" -ForegroundColor White

# Push to remote
Write-Host ""
$pushResult = Invoke-GitCommand "push" "Pushing to Remote Repository"

# Show final status and references
Write-Host ""
Write-Host "=== Publish Complete - Handoff Information ===" -ForegroundColor Magenta
Write-Host "Project: $((Get-Location).Path)" -ForegroundColor White
Write-Host "Branch: $currentBranch" -ForegroundColor White
Write-Host "Commit Hash: $commitHash" -ForegroundColor Green
Write-Host "Commit Message: $commitMessage" -ForegroundColor White
Write-Host "Push Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor White

# Show remote repository URLs
Write-Host ""
Invoke-GitCommand "remote -v" "Remote Repository URLs"

# Show recent commit log for verification
Write-Host ""
Invoke-GitCommand "log --oneline -5" "Recent Commits"

Write-Host ""
Write-Host "SUCCESS: Git publish completed successfully!" -ForegroundColor Green
Write-Host "Repository is now synchronized with remote." -ForegroundColor Green

exit 0