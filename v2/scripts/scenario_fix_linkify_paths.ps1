[CmdletBinding()]
param([string]$ProjectRoot)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($PSBoundParameters.ContainsKey('ProjectRoot') -and $ProjectRoot) { Set-Location -LiteralPath $ProjectRoot }

$utils = Join-Path (Get-Location) 'pf\utils.py'
if (-not (Test-Path -LiteralPath $utils)) { throw "Not found: $utils" }

$src = Get-Content -LiteralPath $utils -Raw -Encoding UTF8
$pattern = 'PATH_RE\s*=\s*re\.compile\([^)]*\)'
$replacement = 'PATH_RE = re.compile(r"((?:[A-Za-z]:[\\/]|\\\\[^\s/\\:*?\"<>|]+[\\/]|/)[^\r\n]+)")'
$dst = [regex]::Replace($src, $pattern, $replacement)

if ($dst -ne $src) {
  Set-Content -Encoding utf8NoBOM -LiteralPath $utils -Value $dst
  Write-Host "Patched PATH_RE in $utils"
} else {
  Write-Host "No change (already patched?)"
}
