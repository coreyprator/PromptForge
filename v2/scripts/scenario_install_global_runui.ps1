[CmdletBinding()]
param([string]$ProjectRoot)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($PSBoundParameters.ContainsKey('ProjectRoot') -and $ProjectRoot) { Set-Location -LiteralPath $ProjectRoot }

$pfApp    = Join-Path $env:APPDATA 'PromptForge'
$runuiDir = Join-Path $pfApp 'RunUI'
New-Item -ItemType Directory -Force -Path $runuiDir | Out-Null

$helperSrc = Join-Path (Get-Location) 'v2/tools/RunUI.Helper.ps1'
$helperDst = Join-Path $runuiDir 'RunUI.Helper.ps1'
if (Test-Path -LiteralPath $helperSrc) { Copy-Item -LiteralPath $helperSrc -Destination $helperDst -Force }

if (-not (Test-Path -LiteralPath $helperDst)) {
  $helperCode = @'
[CmdletBinding()]
param([string]$ProjectRoot)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($PSBoundParameters.ContainsKey('ProjectRoot') -and $ProjectRoot) { Set-Location -LiteralPath $ProjectRoot }

function _GetPy {
  (Get-Command py -ErrorAction SilentlyContinue)?.Source `
    ?? (Get-Command python -ErrorAction SilentlyContinue)?.Source `
    ?? 'python'
}

$manifest = Join-Path (Get-Location) '.pf/runui.json'
if (-not (Test-Path -LiteralPath $manifest)) { throw 'RunUI.Helper: no .pf/runui.json found. Generate one via scenario_runui_write_manifest.ps1' }

$m = Get-Content $manifest -Raw | ConvertFrom-Json
$workdir = if ($m.workdir) { (Resolve-Path $m.workdir).Path } else { (Get-Location).Path }
$cmd = $m.command
if (-not $cmd) { throw 'runui.json missing .command' }

switch ($cmd.type) {
  'python' {
    $py = _GetPy
    $args = @($cmd.args) | Where-Object { $_ }
    if (-not $args) { $args = @('-X','utf8','./app.py') }
    Start-Process -FilePath $py -ArgumentList ($args -join ' ') -WorkingDirectory $workdir | Out-Null
  }
  'pwsh_script' {
    $pw = (Get-Command pwsh -ErrorAction SilentlyContinue)?.Source ?? 'pwsh'
    $path = $cmd.path
    if (-not $path) { throw 'pwsh_script requires .path' }
    $extra = @($cmd.args) -join ' '
    Start-Process -FilePath $pw -ArgumentList ('-NoLogo -NoProfile -File ' + $path + ' -ProjectRoot . ' + $extra) -WorkingDirectory $workdir | Out-Null
  }
  'exec' {
    $exec = @($cmd.exec) | Where-Object { $_ }
    if (-not $exec -or $exec.Count -lt 1) { throw 'exec requires .exec array' }
    Start-Process -FilePath $exec[0] -ArgumentList (($exec | Select-Object -Skip 1) -join ' ') -WorkingDirectory $workdir | Out-Null
  }
  default { throw ('Unknown command.type: {0}' -f $cmd.type) }
}
Write-Host ('RunUI: launched from ' + $workdir)
'@
  Set-Content -Encoding utf8NoBOM -Path $helperDst -Value $helperCode
}

$markerStart = '# >>> PromptForge RunUI >>>'
$markerEnd   = '# <<< PromptForge RunUI <<<'
$block = @'
# >>> PromptForge RunUI >>>
function RunUI {
  param([string]$ProjectRoot)
  try {
    $root   = if ($PSBoundParameters.ContainsKey('ProjectRoot') -and $ProjectRoot) { $ProjectRoot } else { (Get-Location).Path }
    $pfApp  = Join-Path $env:APPDATA 'PromptForge'
    $helper = Join-Path (Join-Path $pfApp 'RunUI') 'RunUI.Helper.ps1'
    & $helper -ProjectRoot $root
  } catch { Write-Error $_ }
}
Set-Alias run_ui RunUI
Set-Alias runui  RunUI
# <<< PromptForge RunUI <<<
'@

$targets = @()
if ($PROFILE.CurrentUserAllHosts) { $targets += $PROFILE.CurrentUserAllHosts }
if ($PROFILE) { $targets += $PROFILE }
$nl = [Environment]::NewLine
foreach($p in $targets){
  $dir = Split-Path -Parent $p
  if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  if (-not (Test-Path -LiteralPath $p))   { New-Item -ItemType File      -Force -Path $p   | Out-Null }
  $txt = (Get-Content $p -Raw) 2>$null
  if ($null -eq $txt) { $txt = '' }
  if ($txt -match [regex]::Escape($markerStart)) { $txt = ($txt -split [regex]::Escape($markerStart))[0]; $txt = $txt.TrimEnd() }
  Set-Content -Encoding utf8NoBOM -Path $p -Value ($txt + $nl + $block)
}

Write-Host ('Installed RunUI helper to: ' + $helperDst)
Write-Host ('Updated profiles: ' + ($targets -join ', '))
Write-Host 'Reload in this session if desired:'
if (Test-Path $PROFILE.CurrentUserAllHosts) { Write-Host '. $PROFILE.CurrentUserAllHosts' }
if (Test-Path $PROFILE) { Write-Host '. $PROFILE' }
