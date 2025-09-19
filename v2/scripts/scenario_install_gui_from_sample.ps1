[CmdletBinding()]
param([string]$ProjectRoot)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'

if ($ProjectRoot) { Set-Location -LiteralPath $ProjectRoot }

# Use the modular sample payload already checked in
$payload = Join-Path (Get-Location) 'v2\samples\payload_v22_gui_modular.json'
if (-not (Test-Path -LiteralPath $payload)) {
  throw "Sample payload not found: $payload"
}

# Apply via PF's standard script
& .\scripts\apply_channel_a.ps1 -JsonPath $payload

# Run self-check so the UI only launches in a good state
& .\v2\scripts\scenario_app_selfcheck.ps1 -ProjectRoot .
