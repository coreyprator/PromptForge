# Install runui command globally
# Run this once to enable 'runui' from any PromptForge project

$scriptDir = $PSScriptRoot
$runuiScript = Join-Path $scriptDir "runui.ps1"

if (-not (Test-Path $runuiScript)) {
    Write-Host "Error: runui.ps1 not found in $scriptDir" -ForegroundColor Red
    exit 1
}

# Add to PowerShell profile for persistent availability
$profilePath = $PROFILE
$profileDir = Split-Path $profilePath -Parent

if (-not (Test-Path $profileDir)) {
    New-Item -ItemType Directory -Path $profileDir -Force
}

$aliasLine = "function runui { & '$runuiScript' }"

# Check if alias already exists
$currentProfile = ""
if (Test-Path $profilePath) {
    $currentProfile = Get-Content $profilePath -Raw
}

if ($currentProfile -notmatch "function runui") {
    Add-Content $profilePath "`n$aliasLine"
    Write-Host "Added 'runui' function to PowerShell profile." -ForegroundColor Green
    Write-Host "Restart PowerShell or run: . `$PROFILE" -ForegroundColor Yellow
} else {
    Write-Host "'runui' function already exists in profile." -ForegroundColor Yellow
}

Write-Host "Test with: runui" -ForegroundColor Cyan
