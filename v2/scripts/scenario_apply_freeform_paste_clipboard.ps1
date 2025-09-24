[CmdletBinding()]
param([string]$ProjectRoot)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
& .\v2\scripts\scenario_apply_freeform_paste.ps1 -ProjectRoot $ProjectRoot -FromClipboard:$true