<# 
  archive_source.ps1 (PromptForge edition)
  - Creates a structure-preserving ZIP of the repo for handoffs.
  - Uses ROBOCOPY to stage a clean tree, then zips it with a single top-level folder.
  - Defaults tuned for PromptForge.
#>

[CmdletBinding()]
param(
  [string]$RepoRoot = (Get-Location).Path,
  [string]$OutDir = ".\handoff",
  [string]$OutFile,
  [string]$BaseName = "promptforge_handoff",
  [switch]$IncludeLogs = $true
)

$ErrorActionPreference = "Stop"

function Quote([string]$p){ if($p -match '\s'){ return ('"'+$p+'"') } else { return $p } }

# Resolve paths
$rootFull = [IO.Path]::GetFullPath($RepoRoot)
if (!(Test-Path -LiteralPath $rootFull)) { throw "RepoRoot not found: $RepoRoot" }

# Stamp + output file
$stamp = (Get-Date).ToString("yyyyMMdd-HHmmss")
if (-not $OutFile) {
  $OutFile = Join-Path $OutDir ("{0}-{1}.zip" -f $BaseName, $stamp)
}
$finalDir = Split-Path -Path $OutFile -Parent
if ($finalDir) { New-Item -ItemType Directory -Force -Path $finalDir | Out-Null }

# Exclusions
$excludeDirNames = @(
  ".git", ".vscode", ".idea", ".vs", "node_modules",
  ".venv", "venv", ".tox", "dist", "build",
  "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
  "handoff", "db_backups"
)
# PromptForge-specific: keep config; exclude generated output folder
$excludeDirNames += @(".promptforge\out")

$filePatterns = @("*.pyc","*.pyo","*.pyd","*.tmp","*.lock","*.DS_Store","Thumbs.db")
if (-not $IncludeLogs) { $filePatterns += "*.log" }

# Stage dir
$stageRoot = Join-Path $env:TEMP ("stage_{0}_{1}" -f $BaseName, $stamp)
$stageBase = Join-Path $stageRoot $BaseName
New-Item -ItemType Directory -Force -Path $stageBase | Out-Null

# ROBOCOPY mirror with exclusions
$robArgs = @()
$robArgs += @((Quote $rootFull), (Quote $stageBase), "*", "/MIR", "/XJ", "/NFL", "/NDL", "/NJH", "/NJS", "/NP")

foreach($d in $excludeDirNames){
  $robArgs += "/XD"
  $robArgs += (Quote (Join-Path $rootFull $d))
}
foreach($p in $filePatterns){
  $robArgs += "/XF"
  $robArgs += $p
}

Write-Host "Staging with ROBOCOPY..." -ForegroundColor Cyan
$proc = Start-Process -FilePath "robocopy.exe" -ArgumentList $robArgs -NoNewWindow -PassThru -Wait
$code = $proc.ExitCode
if ($code -gt 7) { throw "ROBOCOPY failed with exit code $code." }

# Zip creation
Add-Type -AssemblyName System.IO.Compression.FileSystem
$tmpZip = Join-Path ([IO.Path]::GetTempPath()) ([IO.Path]::GetRandomFileName() + ".zip")
if (Test-Path -LiteralPath $tmpZip) { Remove-Item -LiteralPath $tmpZip -Force -ErrorAction SilentlyContinue }
[IO.Compression.ZipFile]::CreateFromDirectory($stageBase, $tmpZip, [IO.Compression.CompressionLevel]::Optimal, $true)

# Move + cleanup
Move-Item -Force -LiteralPath $tmpZip -Destination $OutFile
Remove-Item -LiteralPath $stageRoot -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "Created: $OutFile" -ForegroundColor Green
