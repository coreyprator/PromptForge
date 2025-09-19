[CmdletBinding()]
param([string]$ProjectRoot)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if ($PSBoundParameters.ContainsKey('ProjectRoot') -and $ProjectRoot) { Set-Location -LiteralPath $ProjectRoot }

# 1) Broaden PATH_RE to allow spaces + UNC
$utils = Join-Path (Get-Location) 'pf\utils.py'
if (-not (Test-Path -LiteralPath $utils)) { throw "Not found: $utils" }
$src = Get-Content -LiteralPath $utils -Raw -Encoding UTF8
$pattern = 'PATH_RE\s*=\s*re\.compile\([^\)]*\)'
$replacement = 'PATH_RE = re.compile(r"((?:[A-Za-z]:[\\/]|\\\\[^\\s/\\:*?\"<>|]+[\\/]|/)[^\\r\\n]+)")'
$dst = [regex]::Replace($src, $pattern, $replacement)
if ($dst -ne $src) { Set-Content -Encoding utf8NoBOM -LiteralPath $utils -Value $dst; Write-Host 'Patched PATH_RE in pf\\utils.py' } else { Write-Host 'PATH_RE already patched' }

# 2) Quote path prints in UI so links grab the full string
$ui = Join-Path (Get-Location) 'pf\ui_app.py'
if (Test-Path -LiteralPath $ui) {
  $u = Get-Content -LiteralPath $ui -Raw -Encoding UTF8
  $u = $u -replace 'Project root:\s*\{self\.project_root\}', 'Project root: "{self.project_root}"'
  $u = $u -replace 'Switched project\s*[\u2192\-]>?\s*\{target\}', 'Switched project → "{target}"'
  $u = $u -replace 'Switched project\s*[\u2192\-]>?\s*\{self\.project_root\}', 'Switched project → "{self.project_root}"'
  Set-Content -Encoding utf8NoBOM -LiteralPath $ui -Value $u
  Write-Host 'Patched pf\\ui_app.py path log formatting (quoted)'
} else {
  Write-Host 'pf\\ui_app.py not found here; skipped quoting patch.'
}

Write-Host 'Done. Relaunch PF (run_ui) to activate.'
