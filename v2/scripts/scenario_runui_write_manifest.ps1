[CmdletBinding()]
param([string]$ProjectRoot)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if ($PSBoundParameters.ContainsKey('ProjectRoot') -and $ProjectRoot) { Set-Location -LiteralPath $ProjectRoot }

$cand = @()
if (Test-Path -LiteralPath './v2/scripts/scenario_run_ui_here.ps1') { $cand += [pscustomobject]@{ score=90; type='pwsh_script'; path='v2/scripts/scenario_run_ui_here.ps1'; args=@('-ProjectRoot','.') } }
if (Test-Path -LiteralPath './app.py')                              { $cand += [pscustomobject]@{ score=80; type='python';      args=@('-X','utf8','./app.py') } }
if (Test-Path -LiteralPath './package.json') {
  try { $pkg = Get-Content ./package.json -Raw | ConvertFrom-Json
    if ($pkg.scripts.start) { $cand += [pscustomobject]@{ score=70; type='exec'; exec=@('npm','run','start') } }
    elseif ($pkg.scripts.dev) { $cand += [pscustomobject]@{ score=65; type='exec'; exec=@('npm','run','dev') } }
  } catch {}
}
$csproj = Get-ChildItem -Filter *.csproj -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
if ($csproj) { $cand += [pscustomobject]@{ score=60; type='exec'; exec=@('dotnet','run','--project', $csproj.FullName) } }

if (-not $cand) { throw 'Could not detect an entry point. Create .pf/runui.json manually.' }
$choice = $cand | Sort-Object score -Descending | Select-Object -First 1

$manifest = [ordered]@{ precheck=@('app_selfcheck'); workdir='.'; env=@{}; command=@{} }

switch ($choice.type) {
  'python'      { $manifest.command = @{ type='python';     args=$choice.args } }
  'pwsh_script' { $manifest.command = @{ type='pwsh_script'; path=$choice.path; args=$choice.args } }
  default       { $manifest.command = @{ type='exec';       exec=$choice.exec } }
}

$out = ConvertTo-Json $manifest -Depth 6
$dst = './.pf/runui.json'
New-Item -ItemType Directory -Force -Path './.pf' | Out-Null
$out | Set-Content -Encoding utf8NoBOM $dst
Write-Host ('Wrote ' + $dst)
