[CmdletBinding()]
param([string]$ProjectRoot)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($ProjectRoot) { Set-Location -LiteralPath $ProjectRoot }
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { Write-Host 'git not found'; exit 1 }
Write-Host 'Git status:'
git status --porcelain=v1 -b
Write-Host ''
Write-Host 'Dry-run. To publish:'
Write-Host '  git add -A'
Write-Host '  git commit -m "pf: apply changes"'
Write-Host '  git push'
exit 0
