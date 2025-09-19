import json, re, shutil, subprocess
from pathlib import Path

URL_RE  = re.compile(r"(https?://\S+)")
PATH_RE = re.compile(r'((?:[A-Za-z]:[\\/]|\\\\[^\s/\\:*?"<>|]+[\\/]|/)[^\r\n]+)')
TRAILING_JUNK_RE = re.compile(r"[)\]\}.,;'\"]+$")


def load_project_config(root: Path) -> dict:
    cfg = root / ".pf" / "project.json"
    try:
        if cfg.exists():
            return json.loads(cfg.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {
        "version": "2.2",
        "retry_policy": {"auto_retries": 1, "manual_retry": True},
        "undo": {"mode": "history"},
        "scenarios": {"system": [
            "setup_run_ui","venv_validate","standard_test_and_lint","tool_commands","standard_git_publish"
        ]}
    }


def run_pwsh_script(script_path: Path, *args):
    cmd = ["pwsh","-NoProfile","-File",str(script_path),*args]
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def apply_file(project_root: Path, f: dict):
    op = (f.get("op") or "write").lower()
    path = project_root / f["path"]; path.parent.mkdir(parents=True, exist_ok=True)
    if op == "write":
        path.write_text(f.get("contents") or "", encoding="utf-8")
    elif op == "patch":
        if path.exists():
            existing = path.read_text(encoding="utf-8"); patch = f.get("contents") or ""
            if patch not in existing: path.write_text(existing+"\n"+patch, encoding="utf-8")
        else:
            path.write_text(f.get("contents") or "", encoding="utf-8")
    elif op == "delete":
        if path.exists(): path.unlink()
    elif op == "rename":
        src=f.get("from"); dst=f.get("to")
        if src and dst:
            (project_root/dst).parent.mkdir(parents=True, exist_ok=True)
            (project_root/src).replace(project_root/dst)


def basic_schema_validate(payload: dict) -> list[str]:
    errs=[]
    if not isinstance(payload, dict): return ["Payload must be a JSON object."]
    files = payload.get("files")
    if not isinstance(files, list) or not files:
        errs.append("Payload.files must be a non-empty list."); return errs
    for i,f in enumerate(files):
        if not isinstance(f, dict): errs.append(f"files[{i}] must be an object."); continue
        for req in ("path","op","language"):
            if not f.get(req): errs.append(f"files[{i}].{req} is required.")
        if f.get("op") not in ("write","patch","delete","rename"):
            errs.append("files[%d].op must be write|patch|delete|rename." % i)
        if f.get("op") in ("write","patch") and "contents" not in f:
            errs.append("files[%d].contents is required for op=%s." % (i, f.get("op")))
        if f.get("op") == "rename" and (not f.get("from") or not f.get("to")):
            errs.append("files[%d].from and .to required for op=rename." % i)
    return errs



