
<#
  publish_all_simple.ps1 — PromptForge
  Ultra-robust, chatty version. Avoids wrapper abstractions;
  we never call git/python with empty arg lists.

  Usage:
    pwsh .\scripts\publish_all_simple.ps1 -RepoRoot "G:\My Drive\Code\Python\PromptForge" -Milestone "Baseline" -NewBranch -AutoTag
#>

[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$RepoRoot,
  [string]$Remote = "https://github.com/coreyprator/PromptForge.git",
  [string]$Milestone = "Milestone " + (Get-Date).ToString("yyyy-MM-dd HH:mm"),
  [switch]$NewBranch,
  [string]$BranchPrefix = "milestone/promptforge",
  [string]$BranchName,
  [switch]$AutoTag,
  [string]$TagName,
  [switch]$SkipArchive,
  [string]$ArchiveOutDir = ".\handoff",
  [string]$ArchiveBaseName = "promptforge_handoff",
  [switch]$SkipSeedExport
)

$ErrorActionPreference = "Stop"

function Step($msg){ Write-Host ("`n== {0}" -f $msg) -ForegroundColor Cyan }
function Run($exe, $args) {
  if (!$args -or $args.Count -eq 0) { throw "Internal guard: refusing to run '$exe' with no arguments." }
  Write-Host ("`n> {0} {1}" -f $exe, ($args -join ' ')) -ForegroundColor DarkCyan
  & $exe @args
  $code = $LASTEXITCODE
  if ($code -ne 0) { throw ("{0} failed with exit code {1}" -f $exe, $code) }
}

# Validate inputs
if (-not (Test-Path -LiteralPath $RepoRoot)) { throw "RepoRoot not found: $RepoRoot" }
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "git not found on PATH" }
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { throw "python not found on PATH" }

Push-Location $RepoRoot
try {
  Step "Ensure Git repo"
  if (-not (Test-Path ".git")) {
    Run "git" @("init")
  }

  Step "Configure 'origin' remote"
  $hasOrigin = $false
  $remoteList = (& git remote) 2>$null
  if ($remoteList) {
    $hasOrigin = ($remoteList -split "\r?\n") -contains "origin"
  }
  if (-not $hasOrigin) {
    Run "git" @("remote","add","origin",$Remote)
  } else {
    Run "git" @("remote","set-url","origin",$Remote)
  }

  Step "Select branch"
  if ($NewBranch -or $BranchName) {
    if (-not $BranchName) { $BranchName = "{0}-{1}" -f $BranchPrefix, (Get-Date).ToString("yyyyMMdd-HHmm") }
    Run "git" @("checkout","-B",$BranchName)
  } else {
    Run "git" @("checkout","-B","main")
  }

  Step "Ensure ruff/pytest"
  try { Run "python" @("-m","ruff","--version") } catch { Run "python" @("-m","pip","install","ruff") }
  try { Run "python" @("-m","pytest","--version") } catch { Run "python" @("-m","pip","install","pytest") }

  if (-not $SkipSeedExport) {
    Step "Export seeds from DB"
    $exportScript = Join-Path $PSScriptRoot "pf_export_db.ps1"
    if (Test-Path -LiteralPath $exportScript) {
      & $exportScript -RepoRoot $RepoRoot | Write-Host
      if (-not (Test-Path -LiteralPath "seeds")) { New-Item -ItemType Directory -Force -Path "seeds" | Out-Null }
    } else {
      Write-Host "Seed export script not found at $exportScript (skipping)" -ForegroundColor Yellow
    }
  }

  Step "Ruff format + fix"
  Run "python" @("-m","ruff","format",".")
  Run "python" @("-m","ruff","check","--fix",".")

  if (Test-Path -LiteralPath ".\tests") {
    Step "Run pytest"
    Run "python" @("-m","pytest","-q")
  } else {
    Write-Host "No tests folder; skipping pytest." -ForegroundColor Yellow
  }

  if (-not $SkipArchive) {
    Step "Archive source"
    $archiveScript = Join-Path $PSScriptRoot "archive_source.ps1"
    if (-not (Test-Path -LiteralPath $archiveScript)) { $archiveScript = "scripts\archive_source.ps1" }
    if (Test-Path -LiteralPath $archiveScript) {
      & $archiveScript -RepoRoot $RepoRoot -OutDir $ArchiveOutDir -BaseName $ArchiveBaseName
    } else {
      Write-Host "archive_source.ps1 not found; skipping archive." -ForegroundColor Yellow
    }
  }

  Step "Commit + (optional) tag + push"
  Run "git" @("add","-A")
  Run "git" @("commit","-m",$Milestone,"--allow-empty")

  $doTag = $AutoTag -or $TagName
  if ($doTag) {
    if (-not $TagName) { $TagName = "milestone-" + (Get-Date).ToString("yyyyMMdd-HHmm") }
    Run "git" @("tag","-a",$TagName,"-m",$Milestone)
  }

  $currentBranch = (& git rev-parse --abbrev-ref HEAD).Trim()
  if (-not $currentBranch) { throw "Could not determine current branch." }
  Run "git" @("push","-u","origin",$currentBranch)
  if ($doTag) { Run "git" @("push","origin","--tags") }

  Write-Host "`n✅ Published: $Milestone" -ForegroundColor Green
  Write-Host ("   Branch: {0}" -f $currentBranch)
  if ($doTag) { Write-Host ("   Tag:    {0}" -f $TagName) }
}
finally { Pop-Location }
