<#
  pf_backup_db.ps1
  Nightly-friendly backup of the working DB + JSON seeds snapshot.
  Supports rotation by weekday (max 7) or timestamped snapshots.
#>
param(
  [string]$RepoRoot = (Get-Location).Path,
  [string]$DbPath   = ".promptforge\promptforge.db",
  [string]$BackupDir = "seeds\backups",
  [ValidateSet("weekday","timestamp")]
  [string]$Mode = "weekday"
)
$ErrorActionPreference = "Stop"
Push-Location $RepoRoot
try {
  if (!(Test-Path -LiteralPath $DbPath)) { throw "DB not found: $DbPath" }
  New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

  if ($Mode -eq "weekday") {
    $day = (Get-Date).DayOfWeek.ToString()  # e.g., Monday
    $dbSnap   = Join-Path $BackupDir ("promptforge-{0}.db" -f $day)
    $seedsDir = Join-Path $BackupDir ("seeds-{0}" -f $day)

    # Overwrite the weekday slot
    if (Test-Path $dbSnap)   { Remove-Item -LiteralPath $dbSnap -Force }
    if (Test-Path $seedsDir) { Remove-Item -LiteralPath $seedsDir -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $seedsDir | Out-Null

    Copy-Item -LiteralPath $DbPath -Destination $dbSnap -Force
    & "$PSScriptRoot\pf_export_db.ps1" -RepoRoot $RepoRoot -DbPath $DbPath -OutDir $seedsDir

    Write-Host "Backup (weekday rotation) complete:" -ForegroundColor Green
    Write-Host "  DB:   $dbSnap"
    Write-Host "  JSON: $seedsDir"
  }
  else {
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $dbSnap   = Join-Path $BackupDir ("promptforge-{0}.db" -f $stamp)
    $seedsDir = Join-Path $BackupDir ("seeds-{0}" -f $stamp)
    New-Item -ItemType Directory -Force -Path $seedsDir | Out-Null

    Copy-Item -LiteralPath $DbPath -Destination $dbSnap -Force
    & "$PSScriptRoot\pf_export_db.ps1" -RepoRoot $RepoRoot -DbPath $DbPath -OutDir $seedsDir

    Write-Host "Backup (timestamp) complete:" -ForegroundColor Green
    Write-Host "  DB:   $dbSnap"
    Write-Host "  JSON: $seedsDir"
  }
}
finally { Pop-Location }
