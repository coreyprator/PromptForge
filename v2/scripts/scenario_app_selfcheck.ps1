[CmdletBinding()]
param([string]$ProjectRoot)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if ($ProjectRoot) { Set-Location -LiteralPath $ProjectRoot }
$ok = $true
$needPaths = @('.\app.py', '.\pf\ui_app.py', '.\pf\utils.py', '.\pf\registry.py')
foreach($p in $needPaths){ if(-not (Test-Path -LiteralPath $p)){ Write-Host "Missing $p"; $ok=$false } }
if($ok){
  $ui = Get-Content .\pf\ui_app.py -Raw
  $need = @('Run Scenario','Validate Schema','Run Compliance','Quick Fix','Ruff Fix','Fix & Validate','Apply','Undo','Open Latest Journal','Retry','Project:','New…','PF_SENTINEL_END')
  foreach($n in $need){ if($ui -notmatch [regex]::Escape($n)){ Write-Host "Missing UI string: $n"; $ok=$false } }
}
if($ok){ Write-Host 'Self-check: PASS'; exit 0 } else { Write-Host 'Self-check: FAIL'; exit 1 }
