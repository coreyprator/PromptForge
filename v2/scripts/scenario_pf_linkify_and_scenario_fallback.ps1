[CmdletBinding()]
param([string]$ProjectRoot)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($PSBoundParameters.ContainsKey('ProjectRoot') -and $ProjectRoot) { Set-Location -LiteralPath $ProjectRoot }

# --- 1) Make clickable paths support spaces + UNC ---
$utils = Join-Path (Get-Location) 'pf\utils.py'
if (-not (Test-Path -LiteralPath $utils)) { throw "Not found: $utils" }
$src = Get-Content -LiteralPath $utils -Raw -Encoding UTF8
$pattern     = 'PATH_RE\s*=\s*re\.compile\([^\)]*\)'
$replacement = 'PATH_RE = re.compile(r"((?:[A-Za-z]:[\\/]|\\\\[^\\s/\\\\:*?\"<>|]+[\\/]|/)[^\\r\\n]+)")'
$dst = [regex]::Replace($src, $pattern, $replacement)
if ($dst -ne $src) { Set-Content -LiteralPath $utils -Encoding utf8NoBOM -Value $dst; Write-Host 'Patched PATH_RE in pf\utils.py' } else { Write-Host 'PATH_RE already patched' }

# --- 2) Allow scenarios to fall back to PF's own script folder ---
$ui = Join-Path (Get-Location) 'pf\ui_app.py'
if (-not (Test-Path -LiteralPath $ui)) { throw "Not found: $ui" }
$src = Get-Content -LiteralPath $ui -Raw -Encoding UTF8

# insert: self.install_scripts_dir = <PF root>\v2\scripts
$src = $src -replace 'self\.tools_dir\s+=\s+self\.project_root\s*/\s*"v2"\s*/\s*"tools"', "${0}`n        self.install_scripts_dir = Path(__file__).resolve().parent.parent / \"v2\" / \"scripts\""

# replace the _scenario_script_for one-liner with a fallback-aware version
$src = $src -replace 'def _scenario_script_for\(self, name: str\) -> Path: return .+', @"
    def _scenario_script_for(self, name: str) -> Path:
        p = self.scripts_dir / f\"scenario_{name}.ps1\"
        if p.exists():
            return p
        # fall back to PF's own script folder so system scenarios work in any project
        return self.install_scripts_dir / f\"scenario_{name}.ps1\"
"@.Trim()

Set-Content -LiteralPath $ui -Encoding utf8NoBOM -Value $src
Write-Host 'Patched pf\ui_app.py (scenario fallback)'

Write-Host 'Done. Restart PF (run_ui) to reload utils.py.'
