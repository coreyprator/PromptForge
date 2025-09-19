[CmdletBinding()]
param([string]$ProjectRoot)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($ProjectRoot) { Set-Location -LiteralPath $ProjectRoot }
$errors = @()

# Python
$pyver = & py -3.12 -c "import sys;print(sys.version.split()[0])" 2>$null
if (-not $pyver) { $errors += 'Python 3.12 not found (py -3.12).'; } else { Write-Host "Python: $pyver" }

# ruff
$ruff = Get-Command ruff -ErrorAction SilentlyContinue
if (-not $ruff) { $errors += 'ruff not on PATH. Try: py -3.12 -m pip install -U ruff' } else { Write-Host (ruff --version 2>$null) }

# PSScriptAnalyzer
$isa = Get-Command Invoke-ScriptAnalyzer -ErrorAction SilentlyContinue
if (-not $isa) { $errors += 'PSScriptAnalyzer missing. Install: Install-Module PSScriptAnalyzer -Scope CurrentUser -Force' } else { Write-Host 'PSScriptAnalyzer: OK' }

# pytest (optional)
$pytest = & py -3.12 -m pytest --version 2>$null
if (-not $pytest) { Write-Host 'pytest not found (optional).' } else { Write-Host $pytest }

if ($errors.Count) {
  Write-Host 'Validation: FAIL' -ForegroundColor Red
  $errors | ForEach-Object { Write-Host " - $_" -ForegroundColor Red }
  exit 1
}
Write-Host 'Validation: PASS' -ForegroundColor Green
exit 0
