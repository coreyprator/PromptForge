param(
  [string]$RepoRoot = (Get-Location).Path,
  [string]$DbPath   = ".promptforge\promptforge.db",
  [string]$OutDir   = "seeds"
)
$ErrorActionPreference = "Stop"
Push-Location $RepoRoot
try {
  if (!(Test-Path -LiteralPath $DbPath)) { throw "DB not found: $DbPath" }
  New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

  $py = @'
import json, sqlite3, sys, os
db   = sys.argv[1]
outd = sys.argv[2]
con = sqlite3.connect(db)
con.row_factory = sqlite3.Row
cur = con.cursor()
tables = ["requirements","project_requirements","prompts"]
for t in tables:
    try:
        rows = [dict(r) for r in cur.execute(f"SELECT * FROM {t}")]
        if rows:
            with open(os.path.join(outd, f"{t}.json"), "w", encoding="utf-8") as f:
                json.dump(rows, f, indent=2, ensure_ascii=False)
    except Exception:
        pass
con.close()
print("Exported JSON seeds to", outd)
'@
  $tmp = Join-Path $env:TEMP ("pf_export_db_{0}.py" -f ([guid]::NewGuid().ToString()))
  [System.IO.File]::WriteAllText($tmp, $py, (New-Object System.Text.UTF8Encoding $false))
  & python $tmp $DbPath $OutDir
  $code = $LASTEXITCODE
  Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
  if ($code -ne 0) { throw "python exited with $code" }
}
finally { Pop-Location }
