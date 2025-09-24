param(
  [Parameter(Mandatory=$true)][string]$PayloadPath,
  [string]$ProjectRoot = (Get-Location)
)

$payload = Get-Content -Raw $PayloadPath | ConvertFrom-Json

# Backup dir per run
$stamp = (Get-Date -Format 'yyyyMMdd-HHmmss')
$bakDir = Join-Path $ProjectRoot ".pf\backups\$stamp"
New-Item -ItemType Directory -Force -Path $bakDir | Out-Null

foreach ($f in $payload.files) {
  $dest   = Join-Path $ProjectRoot $f.path
  $destDir= Split-Path -Parent $dest
  New-Item -ItemType Directory -Force -Path $destDir | Out-Null

  # backup existing if present
  if (Test-Path $dest) {
    $rel = $f.path -replace '[\\/]', '__'
    Copy-Item $dest (Join-Path $bakDir "$rel.bak") -Force
  }

  $bytes = [System.Text.Encoding]::UTF8.GetBytes($f.contents)
  [System.IO.File]::WriteAllBytes($dest, $bytes)
  Write-Host "Applied: $($f.path) ($($bytes.Length) bytes)"
}

# Write a manifest so we can undo
$manifest = @{
  project_root = $ProjectRoot
  created_at   = (Get-Date).ToString('s')
  files        = $payload.files | ForEach-Object { $_.path }
}
$manifest | ConvertTo-Json -Depth 3 | Set-Content -Encoding utf8NoBOM (Join-Path $bakDir "manifest.json")

Write-Host "Backup: $bakDir"
