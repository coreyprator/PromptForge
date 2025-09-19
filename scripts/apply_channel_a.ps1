<#
Applies a Channel-A JSON payload (files[].{path,op,contents}) to the working tree.

Usage:
  pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass `
    -File .\scripts\apply_channel_a.ps1 -JsonPath .\v2\samples\bootstrap_payload.json

Or pipe/clipboard:
  Get-Content .\v2\samples\bootstrap_payload.json -Raw | pwsh -File .\scripts\apply_channel_a.ps1
  Get-Clipboard | pwsh -File .\scripts\apply_channel_a.ps1
#>

[CmdletBinding()]
param(
  [string]$JsonPath,
  [switch]$FromClipboard
)

function Write-Utf8NoBom {
  param([string]$Path,[string]$Text)
  $dir = Split-Path -Parent $Path
  if ($dir -and -not (Test-Path -LiteralPath $dir)) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
  }
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  # Do NOT Resolve-Path here; the file may not exist yet.
  [System.IO.File]::WriteAllText($Path, $Text, $utf8NoBom)
}

# 1) Read JSON
if ($FromClipboard) {
  $jsonText = Get-Clipboard
} elseif ($JsonPath) {
  $jsonText = Get-Content -LiteralPath $JsonPath -Raw -ErrorAction Stop
} else {
  $jsonText = [Console]::In.ReadToEnd()
}
if (-not ($jsonText -and $jsonText.Trim())) { throw "No JSON provided." }

# 2) Parse JSON
try { $payload = $jsonText | ConvertFrom-Json -Depth 100 }
catch { throw "Invalid JSON: $($_.Exception.Message)" }

if (-not $payload.files) { throw "Payload missing 'files' array." }

# 3) Apply operations
$results = @()
foreach ($f in $payload.files) {
  $op = ($f.op ?? "write").ToLowerInvariant()
  $path = $f.path
  if (-not $path) {
    $results += [pscustomobject]@{Path="";Op=$op;Status="fail";Message="Missing path"}
    continue
  }

  # Compute a full path string even if the file doesn't exist yet
  $fullInfo = Resolve-Path -LiteralPath $path -ErrorAction SilentlyContinue
  if ($null -ne $fullInfo) {
    $full = $fullInfo.Path
  } else {
    $full = [System.IO.Path]::GetFullPath( (Join-Path (Get-Location) $path) )
  }

  try {
    switch ($op) {
      'write' {
        $contents = [string]($f.contents ?? "")
        Write-Utf8NoBom -Path $full -Text $contents
        $results += [pscustomobject]@{Path=$path;Op=$op;Status="ok";Message="wrote"}
      }
      'patch' {
        $contents = [string]($f.contents ?? "")
        if (Test-Path -LiteralPath $full) {
          $existing = Get-Content -LiteralPath $full -Raw
          if ($existing.Contains($contents)) {
            $results += [pscustomobject]@{Path=$path;Op=$op;Status="skip";Message="already present"}
          } else {
            # append a newline + patch text
            Add-Content -LiteralPath $full -Value "`r`n$contents" -Encoding utf8
            $results += [pscustomobject]@{Path=$path;Op=$op;Status="ok";Message="appended"}
          }
        } else {
          Write-Utf8NoBom -Path $full -Text $contents
          $results += [pscustomobject]@{Path=$path;Op=$op;Status="ok";Message="created (patch->write)"}
        }
      }
      'delete' {
        if (Test-Path -LiteralPath $full) {
          Remove-Item -LiteralPath $full -Force
          $results += [pscustomobject]@{Path=$path;Op=$op;Status="ok";Message="deleted"}
        } else {
          $results += [pscustomobject]@{Path=$path;Op=$op;Status="skip";Message="not found"}
        }
      }
      'rename' {
        $from = $f.from; $to = $f.to
        if (-not $from -or -not $to) { throw "rename requires 'from' and 'to'." }
        $fromFull = (Resolve-Path -LiteralPath $from -ErrorAction Stop).Path
        $toDir = Split-Path -Parent $to
        if ($toDir -and -not (Test-Path -LiteralPath $toDir)) {
          New-Item -ItemType Directory -Path $toDir -Force | Out-Null
        }
        Move-Item -LiteralPath $fromFull -Destination $to -Force
        $results += [pscustomobject]@{Path="$from -> $to";Op=$op;Status="ok";Message="renamed"}
      }
      default {
        $results += [pscustomobject]@{Path=$path;Op=$op;Status="skip";Message="unsupported op"}
      }
    }
  } catch {
    $results += [pscustomobject]@{Path=$path;Op=$op;Status="fail";Message=$_.Exception.Message}
  }
}

$results | Format-Table -AutoSize
