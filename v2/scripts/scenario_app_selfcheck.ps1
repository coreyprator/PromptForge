[CmdletBinding()]
param([string]$ProjectRoot)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Set location
if ($ProjectRoot) { Set-Location -LiteralPath $ProjectRoot }

$timestamp = Get-Date -Format 'HH:mm:ss'
$results = @()

Write-Host "=== PromptForge Project Health Check & Standards Validation ===" -ForegroundColor Magenta
Write-Host "Target Project: $((Get-Location).Path)" -ForegroundColor White
Write-Host "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor White
Write-Host ""

# Function to add validation result
function Add-ValidationResult {
    param(
        [string]$Component,
        [string]$Status,
        [string]$Details,
        [string]$Action = ""
    )
    
    $result = [PSCustomObject]@{
        Component = $Component
        Status = $Status
        Details = $Details
        Action = $Action
        Timestamp = $timestamp
    }
    
    $script:results += $result
    
    $color = switch ($Status) {
        'PASS' { 'Green' }
        'WARN' { 'Yellow' }
        'FAIL' { 'Red' }
        default { 'White' }
    }
    
    Write-Host "[$Status] $Component" -ForegroundColor $color
    Write-Host "    $Details" -ForegroundColor White
    if ($Action) {
        Write-Host "    Action: $Action" -ForegroundColor Yellow
    }
    
    # Log details without color codes
    Write-Host "Component : $Component"
    Write-Host "Status    : $Status"
    Write-Host "Details   : $Details"
    Write-Host "Action    : $Action"
    Write-Host "Timestamp : $timestamp"
}

Write-Host "=== Core PromptForge Structure Validation ===" -ForegroundColor Cyan

# Check .pf directory
$pfDir = Join-Path (Get-Location) '.pf'
if (Test-Path $pfDir) {
    Add-ValidationResult -Component ".pf Directory" -Status "PASS" -Details "Core configuration directory exists"
} else {
    Add-ValidationResult -Component ".pf Directory" -Status "FAIL" -Details "Missing .pf configuration directory" -Action "Create .pf directory"
}

# Check project.json
$projectJson = Join-Path $pfDir 'project.json'
if (Test-Path $projectJson) {
    try {
        $content = Get-Content $projectJson -Raw | ConvertFrom-Json
        $properties = @($content | Get-Member -MemberType NoteProperty | Select-Object -ExpandProperty Name)
        
        if ($properties.Count -eq 1 -and $properties[0] -eq 'theme_color') {
            Add-ValidationResult -Component "Project Configuration" -Status "WARN" -Details "Incomplete project.json (only theme_color)" -Action "Repair with full configuration"
        } else {
            Add-ValidationResult -Component "Project Configuration" -Status "PASS" -Details "Complete project configuration present"
        }
    } catch {
        Add-ValidationResult -Component "Project Configuration" -Status "FAIL" -Details "Invalid project.json format" -Action "Repair configuration file"
    }
} else {
    Add-ValidationResult -Component "Project Configuration" -Status "FAIL" -Details "Missing project.json" -Action "Create project configuration"
}

# Check scenario registry
$registryFile = Join-Path $pfDir 'scenario_registry.json'
if (Test-Path $registryFile) {
    try {
        $registry = Get-Content $registryFile -Raw | ConvertFrom-Json
        $coreScenarios = 0
        $untestedScenarios = 0
        $deprecatedScenarios = 0
        
        if ($registry.scenarios.core) { $coreScenarios = $registry.scenarios.core.Count }
        if ($registry.scenarios.untested) { $untestedScenarios = $registry.scenarios.untested.Count }
        if ($registry.scenarios.deprecated) { $deprecatedScenarios = $registry.scenarios.deprecated.Count }
        
        $totalScenarios = $coreScenarios + $untestedScenarios + $deprecatedScenarios
        Add-ValidationResult -Component "Scenario Registry" -Status "PASS" -Details "Registry found with $totalScenarios scenarios ($coreScenarios core, $untestedScenarios untested, $deprecatedScenarios deprecated)"
    } catch {
        Add-ValidationResult -Component "Scenario Registry" -Status "WARN" -Details "Registry file exists but has parsing errors" -Action "Validate registry JSON format"
    }
} else {
    Add-ValidationResult -Component "Scenario Registry" -Status "FAIL" -Details "Missing scenario_registry.json" -Action "Create scenario registry"
}

# Check Python environment
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Add-ValidationResult -Component "Python Environment" -Status "PASS" -Details "Python available: $pythonVersion"
    } else {
        Add-ValidationResult -Component "Python Environment" -Status "WARN" -Details "Python not available or not in PATH" -Action "Install Python 3.12+ and add to PATH"
    }
} catch {
    Add-ValidationResult -Component "Python Environment" -Status "WARN" -Details "Could not check Python version" -Action "Verify Python installation"
}

# Summary
Write-Host ""
Write-Host "=== File Operations Summary ===" -ForegroundColor Cyan

$passCount = @($results | Where-Object { $_.Status -eq 'PASS' }).Count
$warnCount = @($results | Where-Object { $_.Status -eq 'WARN' }).Count
$failCount = @($results | Where-Object { $_.Status -eq 'FAIL' }).Count

if ($failCount -eq 0 -and $warnCount -eq 0) {
    Write-Host "No file repairs needed - project configuration is complete" -ForegroundColor Green
} else {
    Write-Host "Issues found requiring attention:" -ForegroundColor Yellow
    Write-Host "  PASS: $passCount components" -ForegroundColor Green
    Write-Host "  WARN: $warnCount components" -ForegroundColor Yellow
    Write-Host "  FAIL: $failCount components" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Health Check Summary ===" -ForegroundColor Cyan
Write-Host "Validation Results:" -ForegroundColor White
Write-Host "  PASS: $passCount components" -ForegroundColor Green
Write-Host "  WARN: $warnCount components" -ForegroundColor Yellow
Write-Host "  FAIL: $failCount components" -ForegroundColor Red
Write-Host ""

if ($failCount -eq 0) {
    if ($warnCount -eq 0) {
        Write-Host "HEALTH CHECK: EXCELLENT" -ForegroundColor Green
        Write-Host "PromptForge project is fully operational." -ForegroundColor Green
    } else {
        Write-Host "HEALTH CHECK: GOOD" -ForegroundColor Yellow
        Write-Host "PromptForge project is operational with minor issues." -ForegroundColor Yellow
    }
} else {
    Write-Host "HEALTH CHECK: NEEDS ATTENTION" -ForegroundColor Red
    Write-Host "PromptForge project has critical issues requiring resolution." -ForegroundColor Red
}

Write-Host "Enhanced app_selfcheck scenario - addresses project configuration validation" -ForegroundColor Gray

exit 0
