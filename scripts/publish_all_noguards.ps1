
<#
  publish_all_noguards.ps1 — PromptForge
  Fully explicit Git/Python calls (no helper wrappers), PS7-safe.
  Runs: export seeds -> ruff format/fix -> pytest -> archive -> commit/tag/push

  Usage:
    pwsh .\scripts\publish_all_noguards.ps1 -RepoRoot "G:\My Drive\Code\Python\PromptForge" -Milestone "Baseline" -NewBranch -AutoTag
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

# Preflight
if (-not (Test-Path -LiteralPath $RepoRoot)) { throw "RepoRoot not found: $RepoRoot" }
$gitPath = (Get-Command git -ErrorAction SilentlyContinue)?.Source
$pyPath  = (Get-Command python -ErrorAction SilentlyContinue)?.Source
if (-not $gitPath) { throw "git not found on PATH" }
if (-not $pyPath)  { throw "python not found on PATH" }
Write-Host "git: $gitPath"
Write-Host "python: $pyPath"

Push-Location $RepoRoot
try {
  Step "Ensure Git repo"
  if (-not (Test-Path ".git")) {
    Write-Host "> git init" -ForegroundColor DarkCyan
    & git init
  }

  Step "Configure 'origin' remote"
  $remoteList = (& git remote) 2>$null
  $hasOrigin = $false
  if ($remoteList) { $hasOrigin = ($remoteList -split "\r?\n") -contains "origin" }
  if (-not $hasOrigin) {
    Write-Host ("> git remote add origin {0}" -f $Remote) -ForegroundColor DarkCyan
    & git remote add origin $Remote
  } else {
    Write-Host ("> git remote set-url origin {0}" -f $Remote) -ForegroundColor DarkCyan
    & git remote set-url origin $Remote
  }

  Step "Select branch"
  if ($NewBranch -or $BranchName) {
    if (-not $BranchName) { $BranchName = "{0}-{1}" -f $BranchPrefix, (Get-Date).ToString("yyyyMMdd-HHmm") }
    Write-Host ("> git checkout -B {0}" -f $BranchName) -ForegroundColor DarkCyan
    & git checkout -B $BranchName
  } else {
    Write-Host "> git checkout -B main" -ForegroundColor DarkCyan
    & git checkout -B main
  }

  Step "Ensure ruff/pytest"
  try { & python -m ruff --version | Out-Null } catch { & python -m pip install ruff }
  try { & python -m pytest --version | Out-Null } catch { & python -m pip install pytest }

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
  Write-Host "> python -m ruff format ." -ForegroundColor DarkCyan
  & python -m ruff format .
  Write-Host "> python -m ruff check --fix ." -ForegroundColor DarkCyan
  & python -m ruff check --fix .

  if (Test-Path -LiteralPath ".\tests") {
    Step "Run pytest"
    Write-Host "> python -m pytest -q" -ForegroundColor DarkCyan
    & python -m pytest -q
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
  Write-Host "> git add -A" -ForegroundColor DarkCyan
  & git add -A
  Write-Host ("> git commit -m `"{0}`" --allow-empty" -f $Milestone) -ForegroundColor DarkCyan
  & git commit -m $Milestone --allow-empty

  $doTag = $AutoTag -or $TagName
  if ($doTag) {
    if (-not $TagName) { $TagName = "milestone-" + (Get-Date).ToString("yyyyMMdd-HHmm") }
    Write-Host ("> git tag -a {0} -m `"{1}`"" -f $TagName, $Milestone) -ForegroundColor DarkCyan
    & git tag -a $TagName -m $Milestone
  }

  $currentBranch = (& git rev-parse --abbrev-ref HEAD).Trim()
  if (-not $currentBranch) { throw "Could not determine current branch." }
  Write-Host ("> git push -u origin {0}" -f $currentBranch) -ForegroundColor DarkCyan
  & git push -u origin $currentBranch
  if ($doTag) {
    Write-Host "> git push origin --tags" -ForegroundColor DarkCyan
    & git push origin --tags
  }

  Write-Host "`n✅ Published: $Milestone" -ForegroundColor Green
  Write-Host ("   Branch: {0}" -f $currentBranch)
  if ($doTag) { Write-Host ("   Tag:    {0}" -f $TagName) }
}
finally { Pop-Location }
