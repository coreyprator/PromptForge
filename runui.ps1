# PowerShell version of runui launcher
# Usage: .\runui.ps1 or just 'runui' if in PATH

$ErrorActionPreference = "Stop"

# Find app entry point
$testRig = Join-Path $PWD "pf\ui_app.py"
$mainApp = Join-Path $PWD "app.py"

if (Test-Path $testRig) {
    Write-Host "Launching PromptForge V2.2 Test Rig..." -ForegroundColor Green
    python -c "from pf.ui_app import App; import tkinter as tk; app = App(); app.mainloop()"
}
elseif (Test-Path $mainApp) {
    Write-Host "Launching PromptForge Main App..." -ForegroundColor Green
    python app.py
}
else {
    Write-Host "Error: No PromptForge app found in current directory." -ForegroundColor Red
    Write-Host "Expected: pf\ui_app.py or app.py"
    exit 1
}
