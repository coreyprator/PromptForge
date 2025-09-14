param(
  [string]$RepoRoot = (Get-Location).Path,
  [string]$DbPath   = ".promptforge\promptforge.db",
  [string]$SeedsDir = "seeds"
)
$ErrorActionPreference = "Stop"
Push-Location $RepoRoot
try {
  New-Item -ItemType Directory -Force -Path (Split-Path $DbPath) | Out-Null

  $py = @'
import json, sqlite3, sys, os
db   = sys.argv[1]
seeds= sys.argv[2]
con = sqlite3.connect(db)
cur = con.cursor()
cur.executescript("""
CREATE TABLE IF NOT EXISTS prompts(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL,
  scenario TEXT NOT NULL,
  task TEXT NOT NULL,
  content TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS requirements(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  text TEXT NOT NULL,
  tag TEXT
);
CREATE TABLE IF NOT EXISTS project_requirements(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project TEXT NOT NULL,
  req_id INTEGER NOT NULL,
  enabled INTEGER NOT NULL DEFAULT 1,
  UNIQUE(project, req_id),
  FOREIGN KEY(req_id) REFERENCES requirements(id) ON DELETE CASCADE
);
""")
def load(name):
    p = os.path.join(seeds, f"{name}.json")
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f: return json.load(f)
    return []
reqs  = load("requirements")
proj  = load("project_requirements")
proms = load("prompts")
if reqs:
    cur.executemany("INSERT INTO requirements(id,text,tag) VALUES(?,?,?)",
        [(r.get("id"), r["text"], r.get("tag")) for r in reqs])
if proj:
    cur.executemany("INSERT OR IGNORE INTO project_requirements(project,req_id,enabled) VALUES(?,?,?)",
        [(r["project"], r["req_id"], r.get("enabled",1)) for r in proj])
if proms:
    cur.executemany("INSERT INTO prompts(id,created_at,scenario,task,content) VALUES(?,?,?,?,?)",
        [(r.get("id"), r["created_at"], r["scenario"], r["task"], r["content"]) for r in proms])
con.commit()
con.close()
print("Rebuilt DB from seeds:", db)
'@
  $tmp = Join-Path $env:TEMP ("pf_import_db_{0}.py" -f ([guid]::NewGuid().ToString()))
  [System.IO.File]::WriteAllText($tmp, $py, (New-Object System.Text.UTF8Encoding $false))
  & python $tmp $DbPath $SeedsDir
  $code = $LASTEXITCODE
  Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
  if ($code -ne 0) { throw "python exited with $code" }
}
finally { Pop-Location }
