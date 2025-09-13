<# 
  publish_all.ps1 — PromptForge
  One command to format (RIFF), test, archive, commit, tag, and push.

  Requires:
    - PowerShell 7
    - Python 3.12 on PATH
    - git on PATH
    - ruff + pytest (will be installed if missing)

  Examples:
    pwsh .\scripts\publish_all.ps1 -RepoRoot "G:\My Drive\Code\Python\PromptForge" -Milestone "V1 milestone snapshot" -AutoTag
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
  [string]$ArchiveBaseName = "promptforge_handoff"
)

$ErrorActionPreference = "Stop"

function Invoke-CLI([string]$Exe, [string[]]$Args) {
  Write-Host ("`n> {0} {1}" -f $Exe, ($Args -join ' ')) -ForegroundColor DarkCyan
  $p = Start-Process -FilePath $Exe -ArgumentList $Args -NoNewWindow -PassThru -Wait
  if ($p.ExitCode -ne 0) { throw "`"$Exe`" failed with exit code $($p.ExitCode)" }
}

Push-Location $RepoRoot
try {
  # Ensure remote
  $hasOrigin = (git remote) -contains "origin"
  if (-not $hasOrigin) {
    Invoke-CLI git @("remote","add","origin",$Remote)
  } else {
    Invoke-CLI git @("remote","set-url","origin",$Remote)
  }

  # Branch
  if ($NewBranch -or $BranchName) {
    if (-not $BranchName) {
      $BranchName = "{0}-{1}" -f $BranchPrefix, (Get-Date).ToString("yyyyMMdd-HHmm")
    }
    Invoke-CLI git @("checkout","-B",$BranchName)
  } else {
    # Ensure on main
    Invoke-CLI git @("checkout","-B","main")
  }

  # Ensure ruff + pytest
  try { python -m ruff --version | Out-Null } catch { python -m pip install ruff }
  try { python -m pytest --version | Out-Null } catch { python -m pip install pytest }

  # RIFF (Ruff format + fix)
  Invoke-CLI python @("-m","ruff","format",".")
  Invoke-CLI python @("-m","ruff","check","--fix",".")

  # Tests
  $hasTests = Test-Path -LiteralPath ".\tests"
  if ($hasTests) {
    Invoke-CLI python @("-m","pytest","-q")
  } else {
    Write-Host "No tests folder; skipping pytest." -ForegroundColor Yellow
  }

  # Archive (optional)
  if (-not $SkipArchive) {
    $archiveScript = Join-Path (Join-Path $PSScriptRoot ".") "archive_source.ps1"
    if (-not (Test-Path -LiteralPath $archiveScript)) {
      # fallback if script placed alongside
      $archiveScript = "archive_source.ps1"
    }
    if (-not (Test-Path -LiteralPath $archiveScript)) {
      throw "archive_source.ps1 not found near publish_all.ps1"
    }
    & $archiveScript -RepoRoot $RepoRoot -OutDir $ArchiveOutDir -BaseName $ArchiveBaseName
  }

  # Commit + tag + push
  Invoke-CLI git @("add","-A")
  Invoke-CLI git @("commit","-m",$Milestone,"--allow-empty")

  $doTag = $AutoTag -or $TagName
  if ($doTag) {
    if (-not $TagName) { $TagName = "milestone-" + (Get-Date).ToString("yyyyMMdd-HHmm") }
    Invoke-CLI git @("tag","-a",$TagName,"-m",$Milestone)
  }

  # Push
  # Determine current branch
  $currentBranch = (& git rev-parse --abbrev-ref HEAD).Trim()
  Invoke-CLI git @("push","-u","origin",$currentBranch)
  if ($doTag) { Invoke-CLI git @("push","origin","--tags") }

  Write-Host "`n✅ Published: $Milestone" -ForegroundColor Green
  Write-Host ("   Branch: {0}" -f $currentBranch)
  if ($doTag) { Write-Host ("   Tag:    {0}" -f $TagName) }
}
finally { Pop-Location }
