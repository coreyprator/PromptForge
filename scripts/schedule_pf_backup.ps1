<#
  schedule_pf_backup.ps1
  Registers a Windows Scheduled Task for nightly DB backups.
#>
param(
  [string]$RepoRoot   = "G:\My Drive\Code\Python\PromptForge",
  [string]$ScriptPath = "G:\My Drive\Code\Python\PromptForge\scripts\pf_backup_db.ps1",
  [string]$TaskName   = "PromptForge DB Nightly Backup",
  [string]$Time       = "02:00",  # 24h HH:MM
  [ValidateSet("weekday","timestamp")]
  [string]$Mode       = "weekday"
)

$ErrorActionPreference = "Stop"

# Parse HH:MM into a DateTime for today at that time
$parts  = $Time.Split(":")
$hour   = [int]$parts[0]
$minute = [int]$parts[1]
$at     = (Get-Date).Date.AddHours($hour).AddMinutes($minute)   # DateTime

# Action: run PowerShell 7 with our backup script (with Mode)
$ps = (Get-Command pwsh).Source
$arguments = @(
  "-NoProfile","-ExecutionPolicy","Bypass",
  "-File",$ScriptPath,
  "-RepoRoot",$RepoRoot,
  "-Mode",$Mode
)
$action  = New-ScheduledTaskAction -Execute $ps -Argument ($arguments -join " ")

# Trigger: daily at the requested time
$trigger = New-ScheduledTaskTrigger -Daily -At $at

# Register (will prompt for creds if policy requires)
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Description "Nightly backup of PromptForge DB and seeds"

Write-Host "Scheduled task '$TaskName' created for $Time daily (mode=$Mode)." -ForegroundColor Green
