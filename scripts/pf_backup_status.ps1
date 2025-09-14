<#
  pf_backup_status.ps1
  Shows the status of PromptForge DB backups and the scheduled task.
#>
param(
  [string]$RepoRoot   = (Get-Location).Path,
  [string]$BackupDir  = "seeds\backups",
  [string]$TaskName   = "PromptForge DB Nightly Backup",
  [int]$StaleHours    = 36
)
$ErrorActionPreference = "Stop"
Push-Location $RepoRoot
try {
  if (!(Test-Path -LiteralPath $BackupDir)) {
    Write-Host "No backup directory found at $BackupDir" -ForegroundColor Yellow
    return
  }

  function NiceSize([long]$bytes){
    if($bytes -ge 1GB){ "{0:N2} GB" -f ($bytes/1GB) }
    elseif($bytes -ge 1MB){ "{0:N2} MB" -f ($bytes/1MB) }
    elseif($bytes -ge 1KB){ "{0:N2} KB" -f ($bytes/1KB) }
    else { "$bytes B" }
  }

  $weekdayPattern = '^promptforge-(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\.db$'
  $stampPattern   = '^promptforge-\d{8}-\d{6}\.db$'

  $allDbs = Get-ChildItem -LiteralPath $BackupDir -Filter 'promptforge-*.db' -ErrorAction SilentlyContinue

  $weekdayDbs = $allDbs | Where-Object { $_.Name -match $weekdayPattern } | Sort-Object Name
  $stampDbs   = $allDbs | Where-Object { $_.Name -match $stampPattern }   | Sort-Object LastWriteTime -Descending

  if ($weekdayDbs) {
    Write-Host "== Weekday rotation snapshots ==" -ForegroundColor Cyan
    foreach($d in $weekdayDbs){
      $day = ($d.BaseName -replace '^promptforge-','')
      "{0,-10}  {1,-16}  {2,8}" -f $day, $d.LastWriteTime.ToString("yyyy-MM-dd HH:mm"), (NiceSize $d.Length)
    }
    Write-Host ""
  }

  if ($stampDbs) {
    $latest = $stampDbs | Select-Object -First 1
    Write-Host "== Latest timestamped snapshot ==" -ForegroundColor Cyan
    "{0}  {1}  {2}" -f $latest.Name, $latest.LastWriteTime.ToString("yyyy-MM-dd HH:mm"), (NiceSize $latest.Length)
    Write-Host ""
  }

  # Freshness (newest of either style)
  $newest = @($weekdayDbs + $stampDbs) | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if ($null -ne $newest) {
    $ageHrs = [math]::Round(((Get-Date) - $newest.LastWriteTime).TotalHours, 1)
    $status = if ($ageHrs -le $StaleHours) { "OK" } else { "STALE" }
    $color  = ($status -eq "OK") ? "Green" : "Yellow"
    Write-Host ("Last backup: {0} ({1} hours ago)  => {2}" -f $newest.LastWriteTime.ToString("yyyy-MM-dd HH:mm"), $ageHrs, $status) -ForegroundColor $color
  } else {
    Write-Host "No backups found yet." -ForegroundColor Yellow
  }

  # Scheduled task status
  try {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
    $info = Get-ScheduledTaskInfo -TaskName $TaskName
    Write-Host ""
    Write-Host "== Scheduled Task ==" -ForegroundColor Cyan
    Write-Host ("Name:   {0}" -f $TaskName)
    Write-Host ("State:  {0}" -f $task.State)
    Write-Host ("Last:   {0}" -f $info.LastRunTime.ToString("yyyy-MM-dd HH:mm"))
    Write-Host ("Next:   {0}" -f $info.NextRunTime.ToString("yyyy-MM-dd HH:mm"))
    if ($info.LastTaskResult -ne 0) {
      Write-Host ("Last Result: {0}" -f $info.LastTaskResult) -ForegroundColor Yellow
    }
  } catch {
    Write-Host "Scheduled task not found: $TaskName" -ForegroundColor Yellow
  }
}
finally { Pop-Location }
