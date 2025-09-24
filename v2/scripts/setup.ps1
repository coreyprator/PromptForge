param(
  [string]$Venv = "C:\venvs\promptforge-v2"
)
$ErrorActionPreference = "Stop"

# Derive paths relative to this script
$v2Dir   = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$repoDir = (Resolve-Path (Join-Path $v2Dir "..")).Path

Write-Host "Repo: $repoDir"
Write-Host "V2:   $v2Dir"
Write-Host "Venv: $Venv"

# Create / activate venv
if (!(Test-Path -LiteralPath $Venv)) {
  Write-Host "Creating venv..." -ForegroundColor Cyan
  python -m venv $Venv
}
& "$Venv\Scripts\Activate.ps1"

# Upgrade pip and install our package from v2 explicitly
python -m pip install --upgrade pip
pip install -e "$v2Dir"

# Ensure dev tools in this venv
try { python -m ruff --version | Out-Null } catch { pip install ruff }
try { python -m pytest --version | Out-Null } catch { pip install pytest }

# Smoke test the CLI
pf --version 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
  Write-Host "pf entrypoint not found; trying 'python -m promptforge_cli' instead." -ForegroundColor Yellow
  python -m promptforge_cli --help | Out-Null
}

# Initialize config and launch GUI
pf init 2>$null | Out-Null
pf gui 2>$null | Out-Null
