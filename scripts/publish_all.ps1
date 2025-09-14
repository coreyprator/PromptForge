
<# 
  publish_all.ps1 — PromptForge (auto seed export + robust git wrapper)
  One command to export seeds (from DB), format (Ruff), test (pytest), archive, commit, tag, and push.

  Usage examples:
    pwsh .\scripts\publish_all.ps1 -RepoRoot "G:\My Drive\Code\Python\PromptForge" -Milestone "Baseline" -NewBranch -AutoTag
    pwsh .\scripts\publish_all.ps1 -RepoRoot "G:\...\PromptForge" -Milestone "update" -SkipArchive
#>

[CmdletBinding()]
param(
  [string]$RepoRoot = "G:\My Drive\Code\Python\PromptForge",
  [string]$Remote = "https://github.com/coreyprator/PromptForge.git",
  [string]$Milestone = "Milestone " + (Get-Date).ToString("yyyy-MM-dd HH:mm"),
  [switch]$NewBranch,
  [string]$BranchPrefix = "milestone/promptforge",
  [string]$BranchName,
  [switch]$AutoTag,
  [string]$TagName,           # if provided, overrides AutoTag naming
  [switch]$SkipArchive,
  [string]$ArchiveOutDir = ".\handoff",
  [string]$ArchiveBaseName = "promptforge_handoff",
  [switch]$SkipSeedExport     # allows bypassing seeds export step
)

$ErrorActionPreference = "Stop"

function Run-Cmd([string]$Exe, [string[]]$Args) {
  if (-not $Args) { throw "Internal error: attempted to run '$Exe' with no arguments." }
  Write-Host ("`n> {0} {1}" -f $Exe, ($Args -join ' ')) -ForegroundColor DarkCyan
  & $Exe @Args
  $code = $LASTEXITCODE
  if ($code -ne 0) { throw "'$Exe' failed with exit code $code" }
}

function Run-Git([string[]]$Args) { Run-Cmd "git" $Args }
function Run-Python([string[]]$Args) { Run-Cmd "python" $Args }

Push-Location $RepoRoot
try {
  # Ensure repo exists
  if (-not (Test-Path ".git")) {
    Run-Git @("init")
  }

  # Ensure remote
  $remotes = (& git remote) 2>$null
  $hasOrigin = $false
  if ($remotes) { $hasOrigin = ($remotes -split "\r?\n") -contains "origin" }
  if (-not $hasOrigin) {
    Run-Git @("remote","add","origin",$Remote)
  } else {
    Run-Git @("remote","set-url","origin",$Remote)
  }

  # Branch
  if ($NewBranch -or $BranchName) {
    if (-not $BranchName) {
      $BranchName = "{0}-{1}" -f $BranchPrefix, (Get-Date).ToString("yyyyMMdd-HHmm")
    }
    Run-Git @("checkout","-B",$BranchName)
  } else {
    # Ensure on main
    Run-Git @("checkout","-B","main")
  }

  # Ensure ruff + pytest
  try { Run-Python @("-m","ruff","--version") } catch { Run-Python @("-m","pip","install","ruff") }
  try { Run-Python @("-m","pytest","--version") } catch { Run-Python @("-m","pip","install","pytest") }

  # Export seeds before formatting/testing
  if (-not $SkipSeedExport) {
    $exportScript = Join-Path $PSScriptRoot "pf_export_db.ps1"
    if (Test-Path -LiteralPath $exportScript) {
      Write-Host "`n== Exporting seeds from DB ==" -ForegroundColor Cyan
      & $exportScript -RepoRoot $RepoRoot | Write-Host
      if (-not (Test-Path -LiteralPath "seeds")) { New-Item -ItemType Directory -Force -Path "seeds" | Out-Null }
    } else {
      Write-Host "Seed export script not found at $exportScript (skipping)" -ForegroundColor Yellow
    }
  }

  # RIFF (Ruff format + fix)
  Run-Python @("-m","ruff","format",".")
  Run-Python @("-m","ruff","check","--fix",".")

  # Tests
  if (Test-Path -LiteralPath ".\tests") {
    Run-Python @("-m","pytest","-q")
  } else {
    Write-Host "No tests folder; skipping pytest." -ForegroundColor Yellow
  }

  # Archive (optional)
  if (-not $SkipArchive) {
    $archiveScript = Join-Path $PSScriptRoot "archive_source.ps1"
    if (-not (Test-Path -LiteralPath $archiveScript)) { $archiveScript = "scripts\archive_source.ps1" }
    if (Test-Path -LiteralPath $archiveScript) {
      & $archiveScript -RepoRoot $RepoRoot -OutDir $ArchiveOutDir -BaseName $ArchiveBaseName
    } else {
      Write-Host "archive_source.ps1 not found; skipping archive." -ForegroundColor Yellow
    }
  }

  # Commit + tag + push
  Run-Git @("add","-A")
  Run-Git @("commit","-m",$Milestone,"--allow-empty")

  $doTag = $AutoTag -or $TagName
  if ($doTag) {
    if (-not $TagName) { $TagName = "milestone-" + (Get-Date).ToString("yyyyMMdd-HHmm") }
    Run-Git @("tag","-a",$TagName,"-m",$Milestone)
  }

  $currentBranch = (& git rev-parse --abbrev-ref HEAD).Trim()
  Run-Git @("push","-u","origin",$currentBranch)
  if ($doTag) { Run-Git @("push","origin","--tags") }

  Write-Host "`n✅ Published: $Milestone" -ForegroundColor Green
  Write-Host ("   Branch: {0}" -f $currentBranch)
  if ($doTag) { Write-Host ("   Tag:    {0}" -f $TagName) }
}
finally { Pop-Location }
