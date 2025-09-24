[CmdletBinding()]
param([string]$ProjectRoot)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Set location
if ($ProjectRoot) { Set-Location -LiteralPath $ProjectRoot }

# Ensure .pf directory exists
$pfDir = Join-Path (Get-Location) '.pf'
if (-not (Test-Path $pfDir)) {
    New-Item -ItemType Directory -Path $pfDir -Force | Out-Null
}

$statusFile = Join-Path $pfDir 'PROJECT_STATUS.md'
$timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$projectName = Split-Path (Get-Location) -Leaf

# Get git information - NO REGEX ANYWHERE
$gitBranch = "unknown"
$gitCommit = "unknown"  
$gitStatus = "unknown"

try {
    $branchCmd = git branch --show-current 2>&1
    if ($LASTEXITCODE -eq 0 -and $branchCmd) {
        $gitBranch = [string]$branchCmd
        $gitBranch = $gitBranch.Trim()
    }
} catch {
    $gitBranch = "error-branch"
}

try {
    $commitCmd = git rev-parse --short HEAD 2>&1
    if ($LASTEXITCODE -eq 0 -and $commitCmd) {
        $gitCommit = [string]$commitCmd
        $gitCommit = $gitCommit.Trim()
    }
} catch {
    $gitCommit = "error-commit"
}

try {
    $statusCmd = @(git status --porcelain=v1 2>&1)
    if ($LASTEXITCODE -eq 0) {
        if ($statusCmd.Length -gt 0) {
            $gitStatus = "$($statusCmd.Length) changes"
        } else {
            $gitStatus = "clean"
        }
    }
} catch {
    $gitStatus = "error-status"
}

# Get scenario files
$scriptsDir = Join-Path (Get-Location) 'v2/scripts'
$scenarioFiles = @()
if (Test-Path $scriptsDir) {
    $scriptFiles = Get-ChildItem -Path $scriptsDir -Filter 'scenario_*.ps1'
    foreach ($file in $scriptFiles) {
        $baseName = $file.BaseName
        if ($baseName.StartsWith('scenario_')) {
            $scenarioName = $baseName.Substring(9)  # Remove 'scenario_' prefix
            $scenarioFiles += $scenarioName
        }
    }
    $scenarioFiles = $scenarioFiles | Sort-Object
}

# Try to read registry
$registryFile = Join-Path $pfDir 'scenario_registry.json'
$registryScenarios = @()
if (Test-Path $registryFile) {
    try {
        $registryContent = Get-Content $registryFile -Raw | ConvertFrom-Json
        if ($registryContent.scenarios) {
            # Count scenarios in registry
            $coreCount = 0
            $untestedCount = 0
            $deprecatedCount = 0
            
            if ($registryContent.scenarios.core) {
                $coreCount = $registryContent.scenarios.core.Count
            }
            if ($registryContent.scenarios.untested) {
                $untestedCount = $registryContent.scenarios.untested.Count
            }
            if ($registryContent.scenarios.deprecated) {
                $deprecatedCount = $registryContent.scenarios.deprecated.Count
            }
            
            $registryScenarios = @("Core: $coreCount", "Untested: $untestedCount", "Deprecated: $deprecatedCount")
        }
    } catch {
        $registryScenarios = @("Registry read error")
    }
} else {
    $registryScenarios = @("Registry file not found")
}

Write-Host "=== Comprehensive Project Status Update ===" -ForegroundColor Cyan
Write-Host "Project: $projectName" -ForegroundColor White
Write-Host "Timestamp: $timestamp" -ForegroundColor White
Write-Host "Git Branch: $gitBranch" -ForegroundColor White
Write-Host "Git Commit: $gitCommit" -ForegroundColor White
Write-Host "Git Status: $gitStatus" -ForegroundColor White
Write-Host "Scenario Files: $($scenarioFiles.Count)" -ForegroundColor White
Write-Host "Registry Status: $($registryScenarios -join ', ')" -ForegroundColor White
Write-Host ""

# Create status content
$statusLines = @()
$statusLines += "# $projectName - Comprehensive Project Status"
$statusLines += ""
$statusLines += "**Last Updated:** $timestamp"
$statusLines += "**Git Branch:** $gitBranch"
$statusLines += "**Git Commit:** $gitCommit"
$statusLines += "**Git Status:** $gitStatus"
$statusLines += "**Sprint:** V2.4"
$statusLines += "**Status:** Active - Registry System Deployed"
$statusLines += ""
$statusLines += "## Registry System Status"
$statusLines += ""
foreach ($regStatus in $registryScenarios) {
    $statusLines += "- $regStatus"
}
$statusLines += ""
$statusLines += "## Current Sprint Objectives - V2.4"
$statusLines += ""
$statusLines += "### Completed Tasks"
$statusLines += "- [x] Scenario Registry System - Centralized configuration deployed (2025-09-22)"
$statusLines += "- [x] Registry Python Module - ScenarioRegistry class created (2025-09-22)"
$statusLines += "- [x] Enhanced Git Publish - Working with commit hash extraction (2025-09-22)"
$statusLines += "- [x] Scenario Consolidation - Removed redundant shims (2025-09-22)"
$statusLines += ""
$statusLines += "### In Progress"
$statusLines += "- [ ] PowerShell Error Elimination - Fixing `$matches and object property errors"
$statusLines += "- [ ] UI Registry Integration - Update dropdown to use registry"
$statusLines += "- [ ] Comprehensive Scenario Testing - Validate all scenarios"
$statusLines += ""
$statusLines += "### Remaining Tasks"
$statusLines += "- [ ] Scenario CRUD Interface - AI-assisted scenario management"
$statusLines += "- [ ] Enhanced Error Diagnostics - Verbose error analysis"
$statusLines += "- [ ] Documentation Updates - Complete scenario docs"
$statusLines += "- [ ] V2.4 Release Preparation - Final testing and validation"
$statusLines += ""
$statusLines += "## Discovered Scenario Files ($($scenarioFiles.Count) total)"
$statusLines += ""
foreach ($scenario in $scenarioFiles) {
    $testStatus = switch ($scenario) {
        'app_selfcheck' { 'FIXING - PowerShell object property errors' }
        'git_publish' { 'TESTED - Working with enhanced output' }
        'apply_freeform_paste' { 'TESTED - Working with verbose logging' }
        'project_status_comprehensive' { 'FIXING - Eliminating all regex usage' }
        'project_status_update' { 'DEPRECATED - Has $matches bugs' }
        default { 'UNTESTED - Needs validation' }
    }
    $statusLines += "- **$scenario** - Status: $testStatus"
}
$statusLines += ""
$statusLines += "## V2.4 Success Criteria"
$statusLines += ""
$statusLines += "- [ ] All PowerShell scenarios execute without variable or object errors"
$statusLines += "- [ ] Registry system integrated with UI dropdown"
$statusLines += "- [ ] All scenarios tested and status documented"
$statusLines += "- [ ] Scenario CRUD system operational"
$statusLines += "- [ ] Enhanced error diagnostics deployed"
$statusLines += "- [ ] Complete documentation with delivery protocols"
$statusLines += ""
$statusLines += "---"
$statusLines += "*Updated by scenario_project_status_comprehensive (NO REGEX VERSION)*"
$statusLines += "*Status: $timestamp | Branch: $gitBranch | Commit: $gitCommit*"

# Write status file
try {
    $statusContent = $statusLines -join "`n"
    $statusContent | Out-File -FilePath $statusFile -Encoding UTF8 -Force
    Write-Host "SUCCESS: PROJECT_STATUS.md created" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to write status file: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "Location: $statusFile" -ForegroundColor White
Write-Host "Size: $((Get-Item $statusFile).Length) bytes" -ForegroundColor White
Write-Host "Git: $gitBranch | $gitCommit | $gitStatus" -ForegroundColor Yellow
Write-Host "Files: $($scenarioFiles.Count) | Registry: $($registryScenarios -join ', ')" -ForegroundColor Yellow
Write-Host ""
Write-Host "Project status updated successfully - no regex usage." -ForegroundColor Green

exit 0
