param([string]$Venv = "C:\venvs\promptforge-v2")
$py = Join-Path $Venv "Scripts\python.exe"
& $py -m pip install --upgrade pip
& $py -m pip install openai
Write-Host "Installed 'openai' into $Venv" -ForegroundColor Green
