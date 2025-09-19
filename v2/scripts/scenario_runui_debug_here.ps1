[CmdletBinding()]
param([string]$ProjectRoot)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if ($PSBoundParameters.ContainsKey('ProjectRoot') -and $ProjectRoot){ Set-Location -LiteralPath $ProjectRoot }

$py = (Get-Command py -EA SilentlyContinue)?.Source ?? (Get-Command python -EA SilentlyContinue)?.Source ?? 'python'
Write-Host "[debug] using: $py"
& $py -X dev -X faulthandler -X utf8 .\app.py
$rc = $LASTEXITCODE
Write-Host "[debug] app.py exited rc=$rc"
exit $rc
