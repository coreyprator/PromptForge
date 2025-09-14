param(
  [Parameter(ValueFromRemainingArguments=$true)]
  [string[]]$Args
)
$venv = "C:\venvs\promptforge-v2"
$exe = Join-Path $venv "Scripts\python.exe"

if($Args.Count -eq 0 -or $Args[0] -eq "gui"){
  & $exe -m promptforge_cli gui
  exit $LASTEXITCODE
}
if($Args[0] -eq "pip"){
  & $exe -m pip @($Args[1..($Args.Count-1)])
  exit $LASTEXITCODE
}
& $exe @Args