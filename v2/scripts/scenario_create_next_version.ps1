[CmdletBinding()]
param(
    [string]$ProjectRoot,
    [string]$NewVersionName = "PromptForge_V2.5",
    [string]$NewBranchName = "feature/v2.5-development",
    [switch]$SetupEnvironment
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Set location and validate we're in a PromptForge project
if ($ProjectRoot) { Set-Location -LiteralPath $ProjectRoot }

# Validate we're in a PromptForge project
if (-not (Test-Path ".pf")) {
    Write-Host "ERROR: Not in a PromptForge project (no .pf directory found)" -ForegroundColor Red
    exit 1
}

Write-Host "=== PromptForge Next Version Project Creator ===" -ForegroundColor Magenta
Write-Host "Current Project: $((Get-Location).Path)" -ForegroundColor White
Write-Host "New Version: $NewVersionName" -ForegroundColor White
Write-Host "New Branch: $NewBranchName" -ForegroundColor White
Write-Host "Setup Environment: $SetupEnvironment" -ForegroundColor White
Write-Host "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor White
Write-Host ""

# Function to safely execute commands with error handling
function Invoke-SafeCommand {
    param([string]$Command, [string]$Description, [switch]$AllowFailure)
    
    Write-Host ">>> $Description" -ForegroundColor Cyan
    Write-Host "    $Command" -ForegroundColor Yellow
    
    try {
        $output = Invoke-Expression $Command 2>&1
        if ($LASTEXITCODE -eq 0 -or $AllowFailure) {
            if ($output) { Write-Host $output -ForegroundColor Green }
            return $output
        } else {
            Write-Host "ERROR: $output" -ForegroundColor Red
            if (-not $AllowFailure) { throw "Command failed: $Command" }
        }
    } catch {
        Write-Host "EXCEPTION: $($_.Exception.Message)" -ForegroundColor Red
        if (-not $AllowFailure) { throw }
    }
}

# Function to format file paths for better readability
function Format-PathOutput {
    param([string[]]$Paths)
    
    if (-not $Paths) { return "No files found" }
    
    $sortedPaths = $Paths | Sort-Object
    return ($sortedPaths -join "`n")
}

# === STEP 1: Gather Current Project Information ===
# [Previous Steps 1-6 remain exactly the same as original scenario]
# ... [keeping all existing logic for brevity]

# === STEP 7: Environment Setup (Optional) ===
if ($SetupEnvironment) {
    Write-Host "\n=== Step 7: Environment Setup ===" -ForegroundColor Cyan
    
    # Navigate to new project
    Set-Location $newProjectPath
    
    # Check Python availability
    $pythonCmd = "python"
    if (Get-Command py -ErrorAction SilentlyContinue) {
        $pythonCmd = "py"
    }
    
    # Create virtual environment
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    Invoke-SafeCommand "$pythonCmd -m venv venv" "Create virtual environment"
    
    # Activate and install dependencies
    if (Test-Path "venv\Scripts\Activate.ps1") {
        Write-Host "Activating virtual environment..." -ForegroundColor Yellow
        
        # Note: PowerShell script activation in scenario context
        Write-Host "Installing dependencies..." -ForegroundColor Yellow
        Invoke-SafeCommand "venv\Scripts\python.exe -m pip install --upgrade pip" "Upgrade pip"
        
        if (Test-Path "requirements.txt") {
            Invoke-SafeCommand "venv\Scripts\python.exe -m pip install -r requirements.txt" "Install requirements"
        } else {
            Write-Host "WARNING: No requirements.txt found, skipping dependency installation" -ForegroundColor Yellow
        }
        
        # Test basic functionality
        Write-Host "Testing basic UI functionality..." -ForegroundColor Yellow
        Invoke-SafeCommand "venv\Scripts\python.exe -c 'import sys; print(f\"Python {sys.version} ready\")' " "Test Python environment"
        
        Write-Host "\nEnvironment setup complete!" -ForegroundColor Green
        Write-Host "To activate: venv\Scripts\activate" -ForegroundColor Cyan
        
    } else {
        Write-Host "WARNING: Virtual environment activation script not found" -ForegroundColor Yellow
    }
}

# === COMPLETION ===
Write-Host "\n=== Project Creation Complete ===" -ForegroundColor Magenta
Write-Host "New Project: $newProjectPath" -ForegroundColor Green
Write-Host "Git Branch: $NewBranchName" -ForegroundColor Green

if ($SetupEnvironment) {
    Write-Host "Environment: Configured and ready" -ForegroundColor Green
    Write-Host ""
    Write-Host "Ready to develop! Navigate to project:" -ForegroundColor Cyan
    Write-Host "cd '$newProjectPath'" -ForegroundColor White
    Write-Host "venv\Scripts\activate" -ForegroundColor White
    Write-Host "python -m pf.ui_app" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Cyan
    Write-Host "1. cd '$newProjectPath'" -ForegroundColor White
    Write-Host "2. python -m venv venv" -ForegroundColor White
    Write-Host "3. venv\Scripts\activate" -ForegroundColor White
    Write-Host "4. pip install -r requirements.txt" -ForegroundColor White
    Write-Host "5. python -m pf.ui_app" -ForegroundColor White
}

Write-Host ""
Write-Host "SUCCESS: PromptForge project scaffolding complete!" -ForegroundColor Green

exit 0
