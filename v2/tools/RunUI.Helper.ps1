[CmdletBinding()]
param([string]$ProjectRoot)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($PSBoundParameters.ContainsKey('ProjectRoot') -and $ProjectRoot) {
  Set-Location -LiteralPath $ProjectRoot
}

function _GetPy {
  (Get-Command py -ErrorAction SilentlyContinue)?.Source `
    ?? (Get-Command python -ErrorAction SilentlyContinue)?.Source `
    ?? 'python'
}

function _RunSelfChecks([string[]]$names) {
  foreach($n in $names){
    if ([string]::IsNullOrWhiteSpace($n)) { continue }
    $p = Join-Path (Get-Location) ("v2/scripts/scenario_{0}.ps1" -f $n)
    if (Test-Path -LiteralPath $p) { & $p -ProjectRoot . | Out-Null }
  }
}

$manifest = Join-Path (Get-Location) '.pf/runui.json'
if (Test-Path -LiteralPath $manifest) {
  $m = Get-Content $manifest -Raw | ConvertFrom-Json
  $pre = @($m.precheck) | Where-Object { $_ }
  _RunSelfChecks $pre
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
      $argLine = '-NoLogo -NoProfile -File ' + $path + ' -ProjectRoot . ' + $extra
      Start-Process -FilePath $pw -ArgumentList $argLine -WorkingDirectory $workdir | Out-Null
    }
    'exec' {
      $exec = @($cmd.exec) | Where-Object { $_ }
      if (-not $exec -or $exec.Count -lt 1) { throw 'exec requires .exec array' }
      Start-Process -FilePath $exec[0] -ArgumentList (($exec | Select-Object -Skip 1) -join ' ') -WorkingDirectory $workdir | Out-Null
    }
    default { throw ('Unknown command.type: {0}' -f $cmd.type) }
  }
  Write-Host ('RunUI: launched via manifest from {0}' -f $workdir)
  return
}

$cand = @()
if (Test-Path -LiteralPath './v2/scripts/scenario_run_ui_here.ps1') { $cand += [pscustomobject]@{ score=90; kind='pwsh_script'; path='v2/scripts/scenario_run_ui_here.ps1'; args=@('-ProjectRoot','.') } }
if (Test-Path -LiteralPath './app.py') { $cand += [pscustomobject]@{ score=80; kind='python'; args=@('-X','utf8','./app.py') } }
if (Test-Path -LiteralPath './package.json') {
  try {
    $pkg = Get-Content ./package.json -Raw | ConvertFrom-Json
    if ($pkg.scripts.start) { $cand += [pscustomobject]@{ score=70; kind='exec'; exec=@('npm','run','start') } }
    elseif ($pkg.scripts.dev) { $cand += [pscustomobject]@{ score=65; kind='exec'; exec=@('npm','run','dev') } }
  } catch {}
}
$csproj = Get-ChildItem -Filter *.csproj -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
if ($csproj) { $cand += [pscustomobject]@{ score=60; kind='exec'; exec=@('dotnet','run','--project', $csproj.FullName) } }

if (-not $cand) { throw 'RunUI: no entry point detected; create .pf/runui.json' }
$choice = $cand | Sort-Object score -Descending | Select-Object -First 1
switch ($choice.kind) {
  'pwsh_script' { $pw = (Get-Command pwsh -ErrorAction SilentlyContinue)?.Source ?? 'pwsh'; Start-Process -FilePath $pw -ArgumentList ('-NoLogo -NoProfile -File ' + $choice.path + ' -ProjectRoot .') -WorkingDirectory (Get-Location).Path | Out-Null }
  'python'      { $py = _GetPy; Start-Process -FilePath $py -ArgumentList ($choice.args -join ' ') -WorkingDirectory (Get-Location).Path | Out-Null }
  'exec'        { Start-Process -FilePath $choice.exec[0] -ArgumentList (($choice.exec | Select-Object -Skip 1) -join ' ') -WorkingDirectory (Get-Location).Path | Out-Null }
}
Write-Host 'RunUI: launched via auto-detect'
