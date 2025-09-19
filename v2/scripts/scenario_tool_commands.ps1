[CmdletBinding()]
param([string]$ProjectRoot)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($ProjectRoot) { Set-Location -LiteralPath $ProjectRoot }
$py = (Get-Command py -ErrorAction SilentlyContinue)?.Source
if (-not $py) { $py = (Get-Command python -ErrorAction SilentlyContinue)?.Source }
Write-Host 'fix_channel_a.py --help'
& $py -3.12 v2/tools/fix_channel_a.py -h 2>&1 | Write-Output
exit $LASTEXITCODE
