param([Parameter(Mandatory=$true)][string]$ProjectRoot)
Push-Location $ProjectRoot
try { pwsh -NoProfile -ExecutionPolicy Bypass -Command "run_ui" }
finally { Pop-Location }
