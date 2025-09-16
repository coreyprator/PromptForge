param(
  [string]$Py = "",
  [string]$Module = "",
  [string[]]$Args
)

# repo root = parent of tools\
$root = Resolve-Path (Join-Path $PSScriptRoot "..")

# load project config
$configPath = Join-Path $root ".pf\project.json"
$config = $null
if (Test-Path $configPath) { $config = Get-Content -Raw $configPath | ConvertFrom-Json }

# resolve src dir and entry module
$srcRel = if ($config -and $config.src_dir) { $config.src_dir } else { "src" }
$srcAbs = Resolve-Path (Join-Path $root $srcRel)
$entry  = if ($Module) { $Module } elseif ($config -and $config.ui.entry_module) { $config.ui.entry_module } else { "app" }
$cfgArgs = @()
if ($config -and $config.ui -and $config.ui.args) { $cfgArgs = @($config.ui.args) }

# pick python
if ($Py) {
  $python = $Py
} elseif ($config -and $config.venv_path -and (Test-Path $config.venv_path)) {
  $python = (Resolve-Path $config.venv_path).Path
} elseif (Test-Path (Join-Path $root ".venv\Scripts\python.exe")) {
  $python = (Resolve-Path (Join-Path $root ".venv\Scripts\python.exe")).Path
} else {
  $python = "py"
}

# set PYTHONPATH and run
$env:PYTHONPATH = $srcAbs.Path
Write-Host ("Running: {0} -m {1} {2}" -f $python, $entry, (($cfgArgs + $Args) -join ' ')) -ForegroundColor Cyan
if ($python -eq "py") {
  & py -3.12 -m $entry @cfgArgs @Args
} else {
  & $python -m $entry @cfgArgs @Args
}
exit $LASTEXITCODE
