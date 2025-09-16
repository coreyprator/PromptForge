from __future__ import annotations
import subprocess, pathlib

PWSH = "pwsh"

# All helpers return either a Popen handle (for run_ui) or (rc, stdout, stderr)

def _pwsh_args():
    return [PWSH, "-NoProfile", "-ExecutionPolicy", "Bypass"]


def run_ui(project_root: str):
    root = pathlib.Path(project_root).resolve()
    # Prefer tools\run_ui.ps1 in the target project; else fall back to PF shim
    candidate = root / "tools" / "run_ui.ps1"
    if candidate.exists():
        cmd = _pwsh_args() + ["-File", str(candidate)]
    else:
        shim = root / "v2" / "scripts" / "run_ui_here.ps1"
        cmd = _pwsh_args() + ["-File", str(shim), "-ProjectRoot", str(root)]
    return subprocess.Popen(cmd)


def apply_payload(project_root: str, payload_path: str):
    root = pathlib.Path(project_root).resolve()
    payload = pathlib.Path(payload_path).resolve()
    tool = root / "v2" / "scripts" / "apply_payload.ps1"
    cmd = _pwsh_args() + [
        "-File", str(tool),
        "-PayloadPath", str(payload),
        "-ProjectRoot", str(root),
    ]
    cp = subprocess.run(cmd, capture_output=True, text=True)
    return cp.returncode, cp.stdout, cp.stderr


def undo_last(project_root: str):
    root = pathlib.Path(project_root).resolve()
    tool = root / "v2" / "scripts" / "undo_last_apply.ps1"
    cmd = _pwsh_args() + ["-File", str(tool), "-ProjectRoot", str(root)]
    cp = subprocess.run(cmd, capture_output=True, text=True)
    return cp.returncode, cp.stdout, cp.stderr
