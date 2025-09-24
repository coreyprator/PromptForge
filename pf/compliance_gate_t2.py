import json, subprocess, tempfile, ast, os, shutil
from pathlib import Path

PWSH_BIN = os.environ.get("PF_PWSH") or shutil.which("pwsh") or shutil.which("pwsh.exe") or "pwsh"

def _run(cmd, cwd=None):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr

def _run_pwsh(script: str):
    cmd = [PWSH_BIN, "-NoProfile", "-Command", script]
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr

def _psscriptanalyzer_ok(ps_source: str) -> list[str]:
    with tempfile.TemporaryDirectory() as td:
        f = Path(td, "snippet.ps1"); f.write_text(ps_source, encoding="utf-8")
        script = (
            "try { "
            "Import-Module PSScriptAnalyzer -ErrorAction Stop; "
            f"Invoke-ScriptAnalyzer -Path '{f}' -Severity Error | ConvertTo-Json -Compress "
            "} catch { $_ | Out-String | Write-Output; exit 120 }"
        )
        code, out, err = _run_pwsh(script)
        if code == 120 or ("Invoke-ScriptAnalyzer" in (out+err) and "not recognized" in (out+err)):
            return [
                "PSScriptAnalyzer not available to this PowerShell. Install in PowerShell 7:",
                "  Install-Module PSScriptAnalyzer -Scope CurrentUser -Force -AcceptLicense",
                "…or set PF_PWSH to a PowerShell 7 with PSScriptAnalyzer installed."
            ]
        if code != 0:
            return [err.strip() or out.strip() or "PSScriptAnalyzer failed"]
        if not out.strip():
            return []
        try:
            findings = json.loads(out)
            if isinstance(findings, dict):
                findings = [findings]
            return [f"{i.get('RuleName')} @ {i.get('Line')}:{i.get('Column')}: {i.get('Message')}" for i in findings]
        except Exception as ex:
            return [f"Analyzer parse error: {ex}"]

def _python_ok(py_source: str, ruff_bin: str = "ruff") -> list[str]:
    problems = []
    try:
        ast.parse(py_source)
    except SyntaxError as se:
        problems.append(f"SyntaxError: {se.msg} at {se.lineno}:{se.offset}")
        return problems
    with tempfile.TemporaryDirectory() as td:
        f = Path(td, "snippet.py"); f.write_text(py_source, encoding="utf-8")
        code, out, err = _run([ruff_bin, "check", str(f)])
        if code != 0:
            problems.append((out or err).strip() or "ruff failed")
    return problems

def validate(channel_a_payload: dict) -> dict:
    errs = []
    for f in channel_a_payload.get("files", []):
        lang = (f.get("language") or "").lower()
        src = f.get("contents") or ""
        if not src:
            continue
        if lang in ("powershell","pwsh","ps1"):
            errs += [f"[{f['path']}] {m}" for m in _psscriptanalyzer_ok(src)]
        elif lang in ("python","py"):
            errs += [f"[{f['path']}] {m}" for m in _python_ok(src)]
        else:
            pass
    return {"pass": not errs, "errors": errs, "artifacts": {}}
