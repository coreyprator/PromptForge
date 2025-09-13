<# 
  Publish Milestone Script — PowerShell 7 / Python 3.12

  Steps:
   1) (Optional) create/switch to a milestone branch
   2) Ruff format + fix  (aka “RIFF” step)
   3) pytest -q
   4) git add/commit
   5) (Optional) annotated tag
   6) push branch and tag

  Examples:
    pwsh .\scripts\publish_milestone.ps1 -Milestone "SQL log smoke test green"
    pwsh .\scripts\publish_milestone.ps1 -Milestone "SQL log smoke test green" -NewBranch -BranchPrefix "milestone/sql-log" -AutoTag
#>

[CmdletBinding()]
param(
  [string] $Milestone,

  # Branch options
  [switch] $NewBranch,
  [string] $BranchPrefix = "milestone/sql-log",
  [string] $BranchName,

  # Tag options
  [switch] $AutoTag,
  [string] $TagName,
  [switch] $NoTag,

  # CI behavior toggles
  [switch] $SkipRuff,
  [switch] $SkipPyTest,
  [switch] $AllowEmptyCommit,

  # Git remote
  [string] $Remote = "origin",
  [switch] $NoPush
)

$ErrorActionPreference = 'Stop'

function Write-Header([string]$Text) {
  Write-Host ""
  Write-Host $Text -ForegroundColor Cyan
  Write-Host ("-" * $Text.Length) -ForegroundColor DarkCyan
}

# ---- IMPORTANT: do NOT name this parameter $Args (conflicts with $args) ----
function Invoke-CLI {
  param(
    [Parameter(Mandatory)][string] $Exe,
    [string[]] $CliArgs
  )
  $disp = if ($CliArgs -and $CliArgs.Count) { $CliArgs -join ' ' } else { '' }
  Write-Host "» $Exe $disp" -ForegroundColor DarkGray
  $out = & $Exe @CliArgs 2>&1
  $code = $LASTEXITCODE
  if ($code -ne 0) {
    if ($out) { $out | ForEach-Object { Write-Host $_ -ForegroundColor Yellow } }
  }
  return @{ Code = $code; Output = $out }
}

function Ensure-Tool([string]$Name) {
  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "Required tool not found on PATH: $Name"
  }
}

function Git-CurrentBranch {
  $r = Invoke-CLI -Exe "git" -CliArgs @("rev-parse","--abbrev-ref","HEAD")
  if ($r.Code -ne 0) { throw "Not a git repository (or HEAD is detached)." }
  return ($r.Output | Select-Object -First 1).Trim()
}

function Git-EnsureRemote([string]$RemoteName) {
  $r = Invoke-CLI -Exe "git" -CliArgs @("remote")
  if ($r.Code -ne 0) { throw "This directory is not a git repository." }
  $names = ($r.Output | ForEach-Object { $_.Trim() }) | Where-Object { $_ -ne "" }
  if (-not ($names -contains $RemoteName)) {
    throw "Git remote '$RemoteName' not found. Add it: git remote add $RemoteName <url>"
  }
}

function Safe-Name([string]$s) {
  return ($s -replace '[^\w\.\-\/]', '-')
}

# --- Pre-flight ---
Ensure-Tool "git"
Git-EnsureRemote $Remote

# cd to repo root (script lives in /scripts)
$ScriptPath = $MyInvocation.MyCommand.Path
$ScriptRoot = Split-Path -Parent $ScriptPath
$RepoRoot   = Split-Path -Parent $ScriptRoot
Set-Location $RepoRoot

$ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"
if (-not $Milestone -or $Milestone.Trim() -eq "") {
  $Milestone = "milestone: SQL log smoke test green ($ts)"
}
$autoTagName = "milestone-sql-log-smoke-" + (Get-Date -Format "yyyyMMdd-HHmmss")

# --- Branch handling ---
$currentBranch = Git-CurrentBranch
if ($NewBranch) {
  $name = if ($BranchName) { $BranchName } else { "$BranchPrefix/$(Get-Date -Format 'yyyyMMdd-HHmmss')" }
  $branch = Safe-Name $name
  Write-Header "Create/Switch Branch: $branch"
  $r = Invoke-CLI -Exe "git" -CliArgs @("checkout","-b",$branch)
  if ($r.Code -ne 0) { throw "Failed to create/switch to branch $branch" }
  $currentBranch = $branch
} elseif ($BranchName) {
  $branch = Safe-Name $BranchName
  Write-Header "Switch Branch: $branch"
  $r = Invoke-CLI -Exe "git" -CliArgs @("checkout",$branch)
  if ($r.Code -ne 0) { throw "Failed to switch to branch $branch" }
  $currentBranch = $branch
} else {
  Write-Header "Using Current Branch: $currentBranch"
}

# --- Ruff (“RIFF”) ---
if (-not $SkipRuff) {
  Write-Header "Ruff (format + fix)"
  $ran = $false
  $r = Invoke-CLI -Exe "python" -CliArgs @("-m","ruff","format",".")
  if ($r.Code -eq 0) { $ran = $true }
  $r = Invoke-CLI -Exe "python" -CliArgs @("-m","ruff","check","--fix",".")
  if ($r.Code -eq 0) { $ran = $true }
  if (-not $ran) {
    if (Get-Command "ruff" -ErrorAction SilentlyContinue) {
      Invoke-CLI -Exe "ruff" -CliArgs @("format",".") | Out-Null
      Invoke-CLI -Exe "ruff" -CliArgs @("check","--fix",".") | Out-Null
    } elseif (Get-Command "riff" -ErrorAction SilentlyContinue) {
      Invoke-CLI -Exe "riff" -CliArgs @("format",".") | Out-Null
      Invoke-CLI -Exe "riff" -CliArgs @("check","--fix",".") | Out-Null
    } else {
      Write-Host "Ruff not available — skipping (use -SkipRuff to hide this message)." -ForegroundColor Yellow
    }
  }
} else {
  Write-Header "Ruff step skipped"
}

# --- PyTest ---
if (-not $SkipPyTest) {
  Write-Header "PyTest"
  $r = Invoke-CLI -Exe "python" -CliArgs @("-m","pytest","-q")
  if ($r.Code -ne 0) { throw "PyTest failed (exit $($r.Code)). Aborting publish." }
} else {
  Write-Header "PyTest step skipped"
}

# --- Stage / Commit ---
Write-Header "Git Add/Commit"
Invoke-CLI -Exe "git" -CliArgs @("add","-A") | Out-Null

# anything to commit?
$r = Invoke-CLI -Exe "git" -CliArgs @("diff","--cached","--name-only")
$hasChanges = $false
if ($r.Code -eq 0) {
  $names = ($r.Output | ForEach-Object { $_.Trim() }) | Where-Object { $_ -ne "" }
  $hasChanges = ($names.Count -gt 0)
}

if (-not $hasChanges -and -not $AllowEmptyCommit) {
  Write-Host "No staged changes to commit. Use -AllowEmptyCommit to force an empty commit." -ForegroundColor Yellow
} else {
  $args = @("commit","-m",$Milestone)
  if ($AllowEmptyCommit -and -not $hasChanges) { $args += "--allow-empty" }
  $r = Invoke-CLI -Exe "git" -CliArgs $args
  if ($r.Code -ne 0) { throw "git commit failed (exit $($r.Code))." }
}

# --- Tag (optional) ---
$tagCreated = $false
if (-not $NoTag -and ($AutoTag -or $TagName)) {
  Write-Header "Git Tag"
  $tag = if ($TagName) { Safe-Name $TagName } else { Safe-Name $autoTagName }
  $r = Invoke-CLI -Exe "git" -CliArgs @("tag","-a",$tag,"-m",$Milestone)
  if ($r.Code -ne 0) { throw "git tag failed (exit $($r.Code))." }
  $tagCreated = $true
  Write-Host "Created tag: $tag"
}

# --- Push (optional) ---
if (-not $NoPush) {
  Write-Header "Git Push"
  $r = Invoke-CLI -Exe "git" -CliArgs @("push","-u",$Remote,$currentBranch)
  if ($r.Code -ne 0) { throw "git push branch failed (exit $($r.Code))." }
  if ($tagCreated) {
    $r = Invoke-CLI -Exe "git" -CliArgs @("push",$Remote,"--tags")
    if ($r.Code -ne 0) { throw "git push tags failed (exit $($r.Code))." }
  }
} else {
  Write-Header "Push skipped (local only)"
}

Write-Host ""
Write-Host "✅ Milestone published successfully." -ForegroundColor Green
Write-Host "   Branch: $currentBranch"
if ($tagCreated) { Write-Host "   Tag: (see 'git tag' output above')" }
