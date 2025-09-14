param(
  [string]$RepoRoot = (Get-Location).Path,
  [string]$Venv = "C:\venvs\promptforge-v2"
)
$ErrorActionPreference = "Stop"
if (-not (Test-Path $Venv)) { python -m venv $Venv }
& "$Venv\Scripts\Activate.ps1"
python -m pip install --upgrade pip
pip install -e .
pf init
pf gui
