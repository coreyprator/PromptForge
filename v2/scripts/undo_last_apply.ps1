param([string]$ProjectRoot = (Get-Location))

$bakRoot = Join-Path $ProjectRoot ".pf\backups"
if (!(Test-Path $bakRoot)) { Write-Error "No backups dir."; exit 1 }

$last = Get-ChildItem $bakRoot | Sort-Object Name -Descending | Select-Object -First 1
if (!$last) { Write-Error "No backups found."; exit 1 }

$manifest = Get-Content -Raw (Join-Path $last.FullName "manifest.json") | ConvertFrom-Json
foreach ($rel in $manifest.files) {
  $dest = Join-Path $ProjectRoot $rel
  $bak  = Join-Path $last.FullName (($rel -replace '[\\/]', '__') + ".bak")
  if (Test-Path $bak) {
    Copy-Item $bak $dest -Force
    Write-Host "Restored: $rel"
  } else {
    if (Test-Path $dest) { Remove-Item $dest -Force; Write-Host "Removed: $rel" }
  }
}
Write-Host "Undone: $($last.Name)"
