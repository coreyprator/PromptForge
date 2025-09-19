[CmdletBinding()]
param(
  [string]$ProjectRoot,
  [switch]$FromClipboard,   # prefer clipboard if set; otherwise read stdin if available
  [switch]$Run              # execute >>>RUN blocks if present
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($PSBoundParameters.ContainsKey('ProjectRoot') -and $ProjectRoot) {
  Set-Location -LiteralPath $ProjectRoot
}
Write-Host ("Project root: " + (Get-Location).Path)

function _Write-File([string]$Path,[string]$Content){
  $full = Join-Path (Get-Location) $Path
  $dir  = Split-Path -Parent $full
  if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  Set-Content -Encoding utf8NoBOM -LiteralPath $full -Value $Content
  Write-Host ("WROTE: " + $Path)
}

function _Try-JsonFiles([string]$Text){
  try {
    $obj = $Text | ConvertFrom-Json -ErrorAction Stop
    if ($obj -and $obj.files){
      foreach($f in $obj.files){
        if ($f.path -and $null -ne $f.contents){
          _Write-File $f.path ([string]$f.contents)
        }
      }
      return $true
    }
  } catch {}
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
    Write-Host "[RUN:PS] >>>"
    Invoke-Command -ScriptBlock ([scriptblock]::Create($Body))
    Write-Host "[RUN:PS] <<<"
    return
  } elseif ($lang -eq 'PY' -or $lang -eq 'PYTHON') {
    $py = _DetectPython
    if (-not $py) { throw "Python not found (set .pf/venv.json with `"python`" or install py/python on PATH)." }
    $tmpDir = ".\.pf\tmp"; New-Item -ItemType Directory -Force -Path $tmpDir | Out-Null
    $tmp = Join-Path $tmpDir ("run_" + (Get-Date -Format "yyyyMMdd_HHmmss_fff") + ".py")
    Set-Content -Encoding utf8NoBOM -LiteralPath $tmp -Value $Body
    Write-Host "[RUN:PY] $py $tmp"
    & $py $tmp
    Write-Host ("[RUN:PY] rc=" + $LASTEXITCODE)
    return
  } else {
    throw ("Unknown RUN language: {0} (use PS or PY)." -f $Lang)
  }
}

function _Parse-Freeform([string]$Text){
  $res = [pscustomobject]@{ files=@(); runs=@() }

  # 1) >>>FILE path ... >>>END   (supports spaces/UNC/etc)
  $mFile = [regex]::Matches($Text,'(?ms)^[ \t]*>>>FILE[ \t]+(.+?)\r?\n(.*?)\r?\n[ \t]*>>>END[ \t]*')
  foreach($m in $mFile){ $res.files += [pscustomobject]@{ path=$m.Groups[1].Value.Trim(); contents=$m.Groups[2].Value } }

  # 2) Block runs: >>>RUN:PS|PY ... >>>ENDRUN
  $mRunBlock = [regex]::Matches($Text,'(?ms)^[ \t]*>>>RUN(?::(?<lang>[A-Za-z]+))?[ \t]*\r?\n(?<body>.*?)\r?\n[ \t]*>>>ENDRUN[ \t]*')
  foreach($m in $mRunBlock){ $res.runs += [pscustomobject]@{ kind='block'; lang=$m.Groups['lang'].Value; body=$m.Groups['body'].Value } }

  # 3) Single-line runs: >>>RUN <command>
  $lines = $Text -split "`r?`n"
  foreach($line in $lines){
    if ($line -match '^[ \t]*>>>RUN[ \t]+(.+)$') {
      $res.runs += [pscustomobject]@{ kind='single'; cmd=$matches[1] }
    }
  }

  # 4) Fallback headers: A) path …  B) path …  (content between headers)
  if ($res.files.Count -eq 0) {
    $headers = @()
    for($j=0; $j -lt $lines.Length; $j++){
      if ($lines[$j] -match '^\s*[A-Z0-9]\)\s+(.+)$'){
        $headers += [pscustomobject]@{ idx=$j; path=$matches[1].Trim() }
      }
    }
    if ($headers.Count -gt 0) {
      for($k=0; $k -lt $headers.Count; $k++){
        $start = $headers[$k].idx + 1
        $end   = if ($k -lt $headers.Count-1) { $headers[$k+1].idx } else { $lines.Length }
        $content = ($lines[$start..($end-1)] -join "`r`n")
        $res.files += [pscustomobject]@{ path=$headers[$k].path; contents=$content }
      }
    }
  }

  return $res
}

# --- Acquire text (clipboard first, else stdin) ---
$text = $null
if ($FromClipboard) { try { $text = Get-Clipboard -Raw } catch {} }
if (-not $text) {
  try { if ([Console]::In.Peek() -ne -1) { $text = [Console]::In.ReadToEnd() } } catch {}
}
if (-not $text) { try { $text = Get-Clipboard -Raw } catch {} }
if (-not $text -or [string]::IsNullOrWhiteSpace($text)) { throw 'No input text (clipboard/stdin).' }

# 1) Channel-A JSON?
if (_Try-JsonFiles $text) { Write-Host 'Applied Channel-A JSON.'; return }

# 2) Free-form formats
$parsed = _Parse-Freeform $text
if (($parsed.files.Count -eq 0) -and ($parsed.runs.Count -eq 0)) {
  throw 'Unrecognized paste format. Supported: Channel-A JSON; >>>FILE blocks; >>>RUN / >>>RUN:LANG blocks; A)/B)/C)/1)/2) headers (with optional ``` fences).'
}

foreach($f in $parsed.files){ _Write-File $f.path $f.contents }

if ($Run -and $parsed.runs.Count -gt 0) {
  foreach($r in $parsed.runs){
    if ($r.kind -eq 'single') {
      Write-Host ("[RUN] " + $r.cmd)
      Invoke-Expression $r.cmd
    } else {
      _RunBlock $r.lang $r.body
    }
  }
  Write-Host 'Freeform paste applied + executed.'
} else {
  Write-Host 'Freeform paste applied (no execution).'
}