[CmdletBinding()]
param([string]$ProjectRoot)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($ProjectRoot) { Set-Location -LiteralPath $ProjectRoot }
$py = $env:PF_PY
if (-not $py) { $py = (Get-Command py -ErrorAction SilentlyContinue)?.Source }
if (-not $py) { $py = (Get-Command python -ErrorAction SilentlyContinue)?.Source }
if (-not $py) { throw 'Python not found. Set PF_PY or install Python 3.12+' }
Write-Host "Launching: $py app.py"
& $py -3.12 .\app.py 2>$null
if ($LASTEXITCODE -ne 0) { & $py .\app.py }
Write-Host "GUI exit code: $LASTEXITCODE"
exit 0
