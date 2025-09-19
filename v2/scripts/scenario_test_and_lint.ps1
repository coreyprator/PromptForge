[CmdletBinding()]
param([string]$ProjectRoot)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($ProjectRoot) { Set-Location -LiteralPath $ProjectRoot }
$failed = $false

if (Get-Command ruff -ErrorAction SilentlyContinue) {
  Write-Host 'Running ruff check ...'
  ruff check . | Write-Output
  if ($LASTEXITCODE -ne 0) { $failed = $true }
} else { Write-Host 'ruff not found; skipping' }

$hasTests = Test-Path -LiteralPath '.\tests'
if ($hasTests) {
  Write-Host 'Running pytest -q ...'
  py -3.12 -m pytest -q
  if ($LASTEXITCODE -ne 0) { $failed = $true }
} else { Write-Host 'No tests/ folder; skipping pytest' }

if ($failed) { exit 1 } else { exit 0 }
