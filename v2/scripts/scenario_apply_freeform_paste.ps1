[CmdletBinding()]
param(
  [string]$ProjectRoot = "",
  [switch]$Run = $false
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Enhanced logging with timestamps (no ANSI colors for UI compatibility)
function Write-TimestampedLog {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $logEntry = "[$timestamp] [$Level] $Message"
    Write-Host $logEntry
}

# Set project root - default to clipboard mode
if ($ProjectRoot) { 
    Set-Location -LiteralPath $ProjectRoot 
    Write-TimestampedLog "Project root: $((Get-Location).Path)" "INFO"
} else {
    Write-TimestampedLog "Project root: $((Get-Location).Path)" "INFO"
}

Write-TimestampedLog "Starting freeform paste processing (clipboard mode)" "INFO"

function _Write-File([string]$Path,[string]$Content){
  $full = Join-Path (Get-Location) $Path
  $dir  = Split-Path -Parent $full
  if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  Set-Content -Encoding utf8NoBOM -LiteralPath $full -Value $Content
  Write-TimestampedLog "WROTE: $Path" "SUCCESS"
}

function _Try-JsonFiles([string]$Text){
  try {
    Write-TimestampedLog "Attempting Channel-A JSON parsing" "DEBUG"
    $obj = $Text | ConvertFrom-Json -ErrorAction Stop
    if ($obj -and $obj.files){
      Write-TimestampedLog "Valid Channel-A JSON detected with $($obj.files.Count) files" "SUCCESS"
      foreach($f in $obj.files){
        if ($f.path -and $null -ne $f.contents){
          _Write-File $f.path ([string]$f.contents)
        }
      }
      return $true
    } else {
      Write-TimestampedLog "JSON structure missing 'files' array" "DEBUG"
    }
  } catch {
    Write-TimestampedLog "JSON parsing failed: $($_.Exception.Message)" "DEBUG"
  }
  return $false
}

function _DetectPython {
  if (Test-Path -LiteralPath "./.pf/venv.json") {
    try {
      $j = Get-Content ./.pf/venv.json -Raw | ConvertFrom-Json
      if ($j.python) { return [string]$j.python }
    } catch {}
  }
  $c = (Get-Command py      -ErrorAction SilentlyContinue)?.Source; if ($c) { return $c }
  $c = (Get-Command python  -ErrorAction SilentlyContinue)?.Source; if ($c) { return $c }
  return $null
}

function _RunBlock([string]$Lang,[string]$Body){
  $lang = ($Lang ?? "").ToUpperInvariant()
  if ($lang -eq '' -or $lang -eq 'PS' -or $lang -eq 'POWERSHELL') {
    Write-TimestampedLog "Executing PowerShell block" "INFO"
    Invoke-Command -ScriptBlock ([scriptblock]::Create($Body))
    Write-TimestampedLog "PowerShell block completed" "INFO"
    return
  } elseif ($lang -eq 'PY' -or $lang -eq 'PYTHON') {
    $py = _DetectPython
    if (-not $py) { throw "Python not found (set .pf/venv.json with `"python`" or install py/python on PATH)." }
    $tmpDir = ".\.pf\tmp"; New-Item -ItemType Directory -Force -Path $tmpDir | Out-Null
    $tmp = Join-Path $tmpDir ("run_" + (Get-Date -Format "yyyyMMdd_HHmmss_fff") + ".py")
    Set-Content -Encoding utf8NoBOM -LiteralPath $tmp -Value $Body
    Write-TimestampedLog "Executing Python: $py $tmp" "INFO"
    & $py $tmp
    Write-TimestampedLog "Python execution completed (rc=$LASTEXITCODE)" "INFO"
    return
  } else {
    throw ("Unknown RUN language: {0} (use PS or PY)." -f $Lang)
  }
}

function _Parse-Freeform([string]$Text){
  Write-TimestampedLog "Parsing freeform content (length: $($Text.Length) chars)" "DEBUG"
  $res = [pscustomobject]@{ files=@(); runs=@() }

  # Show content preview for debugging
  $preview = if ($Text.Length -gt 200) { $Text.Substring(0, 200) + "..." } else { $Text }
  Write-TimestampedLog "Content preview: $preview" "DEBUG"

  # Support multiple file block formats
  $mFile = [regex]::Matches($Text,'(?ms)^[ \t]*>>>>?FILE:?[ \t]+(.+?)\r?\n(.*?)\r?\n[ \t]*>>>END[ \t]*')
  if ($mFile.Count -gt 0) {
    Write-TimestampedLog "Found $($mFile.Count) >>>FILE blocks" "DEBUG"
  }
  foreach($m in $mFile){ $res.files += [pscustomobject]@{ path=$m.Groups[1].Value.Trim(); contents=$m.Groups[2].Value } }

  # Block runs: >>>RUN:PS|PY ... >>>ENDRUN
  $mRunBlock = [regex]::Matches($Text,'(?ms)^[ \t]*>>>RUN(?::(?<lang>[A-Za-z]+))?[ \t]*\r?\n(?<body>.*?)\r?\n[ \t]*>>>ENDRUN[ \t]*')
  if ($mRunBlock.Count -gt 0) {
    Write-TimestampedLog "Found $($mRunBlock.Count) >>>RUN blocks" "DEBUG"
  }
  foreach($m in $mRunBlock){ $res.runs += [pscustomobject]@{ kind='block'; lang=$m.Groups['lang'].Value; body=$m.Groups['body'].Value } }

  # Single-line runs: >>>RUN <command>
  $lines = $Text -split "`r?`n"
  $singleRuns = 0
  foreach($line in $lines){
    if ($line -match '^[ \t]*>>>RUN[ \t]+(.+)$') {
      $res.runs += [pscustomobject]@{ kind='single'; cmd=$matches[1] }
      $singleRuns++
    }
  }
  if ($singleRuns -gt 0) {
    Write-TimestampedLog "Found $singleRuns single-line >>>RUN commands" "DEBUG"
  }

  # Fallback headers: A) path …  B) path …
  if ($res.files.Count -eq 0) {
    Write-TimestampedLog "No >>>FILE blocks found, checking for A)/B) headers" "DEBUG"
    $headers = @()
    for($j=0; $j -lt $lines.Length; $j++){
      if ($lines[$j] -match '^\s*[A-Z0-9]\)\s+(.+)$'){
        $headers += [pscustomobject]@{ idx=$j; path=$matches[1].Trim() }
      }
    }
    if ($headers.Count -gt 0) {
      Write-TimestampedLog "Found $($headers.Count) A)/B) style headers" "DEBUG"
      for($k=0; $k -lt $headers.Count; $k++){
        $start = $headers[$k].idx + 1
        $end   = if ($k -lt $headers.Count-1) { $headers[$k+1].idx } else { $lines.Length }
        $content = ($lines[$start..($end-1)] -join "`r`n")
        $res.files += [pscustomobject]@{ path=$headers[$k].path; contents=$content }
      }
    }
  }

  Write-TimestampedLog "Parsing result: $($res.files.Count) files, $($res.runs.Count) run blocks" "DEBUG"
  return $res
}

# Enhanced input acquisition - always try clipboard first
$text = $null
Write-TimestampedLog "Attempting to read from clipboard" "DEBUG"
try { 
    $text = Get-Clipboard -Raw 
    if ($text) {
        Write-TimestampedLog "Successfully read $($text.Length) characters from clipboard" "SUCCESS"
    } else {
        Write-TimestampedLog "Clipboard is empty" "WARN"
    }
} catch {
    Write-TimestampedLog "Clipboard read failed: $($_.Exception.Message)" "ERROR"
}

# Fallback to stdin if clipboard empty
if (-not $text) {
  Write-TimestampedLog "Attempting to read from stdin" "DEBUG"
  try { 
    if ([Console]::In.Peek() -ne -1) { 
        $text = [Console]::In.ReadToEnd() 
        Write-TimestampedLog "Read $($text.Length) characters from stdin" "SUCCESS"
    } else {
        Write-TimestampedLog "No stdin input available" "DEBUG"
    }
  } catch {
    Write-TimestampedLog "Stdin read failed: $($_.Exception.Message)" "ERROR"
  }
}

if (-not $text -or [string]::IsNullOrWhiteSpace($text)) { 
    $errorDetails = @(
        "No input text available from clipboard or stdin",
        "",
        "Troubleshooting:",
        "1. Copy Channel-A JSON or file blocks to clipboard before running",
        "2. Ensure clipboard contains valid content structure",
        "3. Try copying content again and re-running scenario"
    )
    
    Write-TimestampedLog "INPUT ERROR: No text available" "ERROR"
    foreach ($detail in $errorDetails) {
        if ($detail) { Write-TimestampedLog "  $detail" "ERROR" }
        else { Write-Host "" }
    }
    throw 'No input text available. Copy content to clipboard and try again.'
}

# Try Channel-A JSON first
if (_Try-JsonFiles $text) { 
    Write-TimestampedLog "Channel-A JSON processing completed successfully" "SUCCESS"
    exit 0
}

# Try free-form formats with detailed analysis
Write-TimestampedLog "Channel-A JSON failed, attempting freeform parsing" "INFO"
$parsed = _Parse-Freeform $text

if (($parsed.files.Count -eq 0) -and ($parsed.runs.Count -eq 0)) {
    $errorReport = @(
        "PASTE FORMAT ERROR: Content does not match any supported format",
        "",
        "Content Analysis:",
        "  Length: $($text.Length) characters",
        "  Lines: $(($text -split '`r?`n').Count)",
        "  Starts with: '$($text.Substring(0, [Math]::Min(50, $text.Length)))'",
        "",
        "Supported Formats:",
        "  1. Channel-A JSON: { `"files`": [{ `"path`": `"...`", `"contents`": `"...`" }] }",
        "  2. >>>FILE blocks: >>>FILE path/to/file.ext (content) >>>END",
        "  3. >>>>FILE: blocks: >>>>FILE: path/to/file.ext (content) >>>END", 
        "  4. >>>RUN blocks: >>>RUN:LANG (code) >>>ENDRUN",
        "  5. A)/B)/C) headers: A) path/to/file.ext (content)",
        "",
        "Recommendation: Use Channel-A JSON format for best compatibility"
    )
    
    foreach ($line in $errorReport) {
        Write-TimestampedLog $line "ERROR"
    }
    
    throw "Unrecognized paste format. See detailed error analysis above."
}

Write-TimestampedLog "Freeform parsing successful: $($parsed.files.Count) files, $($parsed.runs.Count) runs" "SUCCESS"

# Write all files
foreach($f in $parsed.files){ _Write-File $f.path $f.contents }

# Execute run blocks if requested
if ($Run -and $parsed.runs.Count -gt 0) {
  Write-TimestampedLog "Executing $($parsed.runs.Count) run blocks" "INFO"
  foreach($r in $parsed.runs){
    if ($r.kind -eq 'single') {
      Write-TimestampedLog "Executing: $($r.cmd)" "INFO"
      Invoke-Expression $r.cmd
    } else {
      _RunBlock $r.lang $r.body
    }
  }
  Write-TimestampedLog "All run blocks completed" "SUCCESS"
} else {
  Write-TimestampedLog "Freeform paste applied (no execution requested)" "SUCCESS"
}

exit 0