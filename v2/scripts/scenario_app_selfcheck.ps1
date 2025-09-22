[CmdletBinding()]
param([string]$ProjectRoot)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Set location to project root
if ($ProjectRoot) { Set-Location -LiteralPath $ProjectRoot }

Write-Host "=== PromptForge Project Health Check & Standards Validation ==="
Write-Host "Target Project: $((Get-Location).Path)"
Write-Host "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""

# Initialize arrays at script level with proper PowerShell syntax
$script:fileOperations = @()
$script:validationResults = @()
$script:repairActions = @()

# Function to track validation results
function Add-ValidationResult {
    param(
        [string]$Component,
        [string]$Status,
        [string]$Details = "",
        [string]$Action = ""
    )
    
    # Create object with explicit property names
    $result = New-Object PSObject -Property @{
        Component = $Component
        Status = $Status
        Details = $Details
        Action = $Action
        Timestamp = Get-Date -Format 'HH:mm:ss'
    }
    
    # Use array addition operator for reliable array building
    $script:validationResults = $script:validationResults + $result
    
    Write-Host "[$Status] $Component"
    if ($Details) { Write-Host "    $Details" }
    if ($Action) { Write-Host "    Action: $Action" }
    
    return $result
}

# Function to track file operations
function Add-FileOperation {
    param(
        [string]$FilePath,
        [string]$Operation,
        [string]$Status = "PENDING"
    )
    
    $relativePath = if ($FilePath.StartsWith((Get-Location).Path)) {
        $FilePath.Substring((Get-Location).Path.Length + 1)
    } else {
        $FilePath
    }
    
    $operation = New-Object PSObject -Property @{
        Filename = Split-Path $FilePath -Leaf
        RelativePath = $relativePath.Replace('\', '/')
        Operation = $Operation
        Status = $Status
        SizeBytes = 0
        Modified = ""
        SHA256 = ""
        Timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    }
    
    $script:fileOperations = $script:fileOperations + $operation
    return $operation
}

# Function to update file operation metadata
function Update-FileOperation {
    param(
        [PSObject]$Operation,
        [string]$Status = "SUCCESS"
    )
    
    try {
        $fullPath = Join-Path (Get-Location) $Operation.RelativePath
        if (Test-Path $fullPath) {
            $fileInfo = Get-Item $fullPath
            $Operation.SizeBytes = $fileInfo.Length
            $Operation.Modified = $fileInfo.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss')
            
            # Calculate SHA-256 hash
            $hash = Get-FileHash -Path $fullPath -Algorithm SHA256
            $Operation.SHA256 = $hash.Hash.Substring(0, 14) + ".."
            
            $Operation.Status = $Status
        } else {
            $Operation.Status = "FAILED: File not found"
        }
    } catch {
        $Operation.Status = "ERROR: $($_.Exception.Message)"
    }
}

Write-Host "=== Core PromptForge Structure Validation ==="

# 1. Validate .pf directory structure
if (Test-Path ".pf") {
    Add-ValidationResult -Component ".pf Directory" -Status "PASS" -Details "Core configuration directory exists"
} else {
    try {
        New-Item -ItemType Directory -Path ".pf" -Force | Out-Null
        Add-ValidationResult -Component ".pf Directory" -Status "FIXED" -Details "Created missing .pf directory" -Action "Directory structure repaired"
        $script:repairActions = $script:repairActions + "Created .pf directory"
    } catch {
        Add-ValidationResult -Component ".pf Directory" -Status "FAIL" -Details "Cannot create .pf directory: $($_.Exception.Message)"
    }
}

# 2. Validate project.json and repair if incomplete
$projectJsonPath = ".pf/project.json"
$minimalProjectConfig = @{
    "project_name" = (Split-Path (Get-Location) -Leaf)
    "version" = "1.0.0"
    "description" = "PromptForge V2.3 managed project"
    "standards" = @{
        "version" = "1.0"
        "updated" = (Get-Date -Format 'yyyy-MM-dd')
        "documentation" = ".pf/STANDARDS.md"
        "validation_config" = ".pf/validation_config.json"
        "promptforge_version" = "V2.3"
    }
    "retry_policy" = @{
        "auto_retries" = 1
    }
    "scenarios" = @{
        "system" = @()
        "project" = @()
    }
}

$needsProjectJsonRepair = $false
$existingConfig = @{}

if (Test-Path $projectJsonPath) {
    try {
        $jsonContent = Get-Content $projectJsonPath -Raw
        $existingConfigObj = $jsonContent | ConvertFrom-Json
        
        # Convert PSCustomObject to hashtable for easier manipulation
        $existingConfig = @{}
        $existingConfigObj.PSObject.Properties | ForEach-Object {
            $existingConfig[$_.Name] = $_.Value
        }
        
        # Check if it's just the theme color (indicating incomplete configuration)
        if ($existingConfig.Keys.Count -eq 1 -and $existingConfig.ContainsKey("theme_color")) {
            $needsProjectJsonRepair = $true
            Add-ValidationResult -Component "Project Configuration" -Status "WARN" -Details "Incomplete project.json (only theme_color)" -Action "Repair with full configuration"
        } elseif (-not $existingConfig.ContainsKey("standards")) {
            $needsProjectJsonRepair = $true
            Add-ValidationResult -Component "Project Configuration" -Status "WARN" -Details "Missing standards metadata" -Action "Add standards configuration"
        } else {
            Add-ValidationResult -Component "Project Configuration" -Status "PASS" -Details "Complete project configuration present"
        }
    } catch {
        $needsProjectJsonRepair = $true
        Add-ValidationResult -Component "Project Configuration" -Status "FAIL" -Details "Invalid JSON format" -Action "Repair configuration file"
    }
} else {
    $needsProjectJsonRepair = $true
    Add-ValidationResult -Component "Project Configuration" -Status "FAIL" -Details "project.json missing" -Action "Create configuration file"
}

if ($needsProjectJsonRepair) {
    $operation = Add-FileOperation -FilePath (Join-Path (Get-Location) $projectJsonPath) -Operation "REPAIR"
    
    try {
        # Preserve existing theme_color if present
        if ($existingConfig.ContainsKey("theme_color")) {
            $minimalProjectConfig["theme_color"] = $existingConfig["theme_color"]
        }
        
        # Merge any other existing configuration
        foreach ($key in $existingConfig.Keys) {
            if ($key -notin @("project_name", "version", "description", "standards", "retry_policy", "scenarios")) {
                $minimalProjectConfig[$key] = $existingConfig[$key]
            }
        }
        
        $projectJsonContent = $minimalProjectConfig | ConvertTo-Json -Depth 10
        Set-Content -Path $projectJsonPath -Value $projectJsonContent -Encoding UTF8NoBOM
        Update-FileOperation -Operation $operation -Status "REPAIRED"
        $script:repairActions = $script:repairActions + "Repaired project.json with complete configuration"
    } catch {
        Update-FileOperation -Operation $operation -Status "FAILED"
        Add-ValidationResult -Component "Project Configuration" -Status "FAIL" -Details "Repair failed: $($_.Exception.Message)"
    }
}

Write-Host ""
Write-Host "=== File Operations Summary ==="

# Safe count check with explicit null/empty handling
$fileOpCount = 0
if ($script:fileOperations -ne $null -and $script:fileOperations.Count) {
    $fileOpCount = $script:fileOperations.Count
}

if ($fileOpCount -gt 0) {
    Write-Host ('{0,-30} {1,-40} {2,-8} {3,-19} {4,-16} {5,-10}' -f 'Filename', 'Path', 'Size', 'Modified', 'SHA-256', 'Status')
    Write-Host ('-' * 130)
    
    foreach ($op in $script:fileOperations) {
        $filename = if ($op.Filename.Length -gt 29) { $op.Filename.Substring(0, 29) } else { $op.Filename }
        $path = if ($op.RelativePath.Length -gt 39) { $op.RelativePath.Substring(0, 39) } else { $op.RelativePath }
        $size = if ($op.SizeBytes -lt 1024) { "$($op.SizeBytes)B" } else { "{0:F1}KB" -f ($op.SizeBytes / 1024) }
        $sha = if ($op.SHA256.Length -gt 16) { $op.SHA256 } else { $op.SHA256 }
        $status = if ($op.Status.Length -gt 9) { $op.Status.Substring(0, 9) } else { $op.Status }
        
        Write-Host ('{0,-30} {1,-40} {2,-8} {3,-19} {4,-16} {5,-10}' -f $filename, $path, $size, $op.Modified, $sha, $status)
    }
    
    Write-Host ('-' * 130)
    Write-Host "Total file operations: $fileOpCount"
} else {
    Write-Host "No file repairs needed - project configuration is complete"
}

Write-Host ""
Write-Host "=== Health Check Summary ==="

# Safe counting with explicit null checks
$passCount = 0
$fixedCount = 0
$warnCount = 0
$failCount = 0

if ($script:validationResults -ne $null -and $script:validationResults.Count) {
    foreach ($result in $script:validationResults) {
        switch ($result.Status) {
            "PASS" { $passCount++ }
            "FIXED" { $fixedCount++ }
            "WARN" { $warnCount++ }
            "FAIL" { $failCount++ }
        }
    }
}

Write-Host "Validation Results:"
Write-Host "  PASS: $passCount components"
Write-Host "  FIXED: $fixedCount components"
Write-Host "  WARN: $warnCount components"
Write-Host "  FAIL: $failCount components"
Write-Host ""

# Safe repair actions display
$repairCount = 0
if ($script:repairActions -ne $null -and $script:repairActions.Count) {
    $repairCount = $script:repairActions.Count
}

if ($repairCount -gt 0) {
    Write-Host "Repair Actions Performed:"
    foreach ($action in $script:repairActions) {
        Write-Host "  + $action"
    }
    Write-Host ""
}

# Determine overall health status
if ($failCount -eq 0) {
    if ($warnCount -eq 0) {
        Write-Host "HEALTH CHECK: EXCELLENT"
        Write-Host "PromptForge project configuration is optimal."
        $exitCode = 0
    } else {
        Write-Host "HEALTH CHECK: GOOD"
        Write-Host "PromptForge project is operational with $warnCount warnings."
        $exitCode = 0
    }
} else {
    Write-Host "HEALTH CHECK: ATTENTION REQUIRED"
    Write-Host "PromptForge project has $failCount critical issues."
    $exitCode = 1
}

Write-Host ""
Write-Host "Enhanced app_selfcheck scenario - addresses project configuration validation and repair"
Write-Host ""

exit $exitCode