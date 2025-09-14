from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Tuple
import json, difflib, time

@dataclass
class FilePlan:
    path: str
    exists: bool
    old_text: str
    new_text: str
    diff: str

PATCH_ROOT = Path(".promptforge/out/patches")

def _read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""
    except Exception:
        try:
            return p.read_bytes().decode("utf-8", errors="replace")
        except Exception:
            return ""

def generate_plan(files_payload: List[Dict], base_dir: Path) -> List[FilePlan]:
    plan: List[FilePlan] = []
    for f in files_payload:
        rel = Path(f["path"])
        target = (base_dir / rel).resolve()
        old_text = _read_text(target) if target.exists() else ""
        new_text = f.get("contents", "")
        diff = "\n".join(difflib.unified_diff(
            old_text.splitlines(), new_text.splitlines(),
            fromfile=str(rel) + (" (existing)" if target.exists() else " (new)"),
            tofile=str(rel) + " (proposed)",
            lineterm="",
        ))
        plan.append(FilePlan(path=str(rel).replace("\\","/"),
                             exists=target.exists(),
                             old_text=old_text,
                             new_text=new_text,
                             diff=diff))
    return plan

def perform_apply(selected: List[FilePlan], base_dir: Path) -> Path:
    ts = time.strftime("%Y%m%d-%H%M%S")
    patch_dir = (base_dir / PATCH_ROOT / ts).resolve()
    originals_dir = patch_dir / "originals"
    patch_dir.mkdir(parents=True, exist_ok=True)
    (patch_dir / "selected.json").write_text(
        json.dumps([fp.__dict__ for fp in selected], indent=2), encoding="utf-8")
    originals_dir.mkdir(parents=True, exist_ok=True)

    manifest = {"applied_at": ts, "files": []}
    for fp in selected:
        rel = Path(fp.path)
        target = (base_dir / rel).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            backup = originals_dir / rel
            backup.parent.mkdir(parents=True, exist_ok=True)
            backup.write_text(fp.old_text, encoding="utf-8")
            manifest["files"].append({"path": fp.path, "existed": True})
        else:
            manifest["files"].append({"path": fp.path, "existed": False})
        target.write_text(fp.new_text, encoding="utf-8")

    (patch_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (base_dir / PATCH_ROOT / "LAST_APPLY.txt").write_text(str(patch_dir), encoding="utf-8")
    return patch_dir

def undo_last_apply(base_dir: Path) -> Tuple[bool, str]:
    pointer = (base_dir / PATCH_ROOT / "LAST_APPLY.txt")
    if not pointer.exists():
        return False, "No LAST_APPLY.txt found."
    patch_dir = Path(pointer.read_text(encoding="utf-8").strip())
    manifest_path = patch_dir / "manifest.json"
    if not manifest_path.exists():
        return False, "manifest.json missing; cannot undo."
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    originals_dir = patch_dir / "originals"

    for item in manifest.get("files", []):
        rel = Path(item["path"])
        target = (base_dir / rel).resolve()
        if item.get("existed"):
            backup = originals_dir / rel
            if backup.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            if target.exists():
                try:
                    target.unlink()
                except Exception:
                    pass
    try:
        pointer.unlink()
    except Exception:
        pass
    return True, f"Undo complete from patch: {patch_dir}"