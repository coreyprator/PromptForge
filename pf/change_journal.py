import hashlib
import json
import time
from pathlib import Path

def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def _read_bytes(p: Path) -> bytes:
    return p.read_bytes() if p.exists() else b""

def _write_bytes(p: Path, b: bytes):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b)

def record_apply(project_root: Path, ops: list[dict]) -> Path:
    jroot = project_root / ".pf" / "journal"
    jroot.mkdir(parents=True, exist_ok=True)
    jf = jroot / (time.strftime("%Y-%m-%dT%H-%M-%SZ") + ".jsonl")
    with jf.open("a", encoding="utf-8") as w:
        for op in ops:
            w.write(json.dumps(op, ensure_ascii=False) + "\n")
    return jf

def prepare_ops_for_apply(project_root: Path, files: list[dict]) -> list[dict]:
    ops = []
    for f in files:
        path = project_root / f["path"]
        before = _read_bytes(path)
        after = (f.get("contents") or "").encode("utf-8")
        ops.append({
            "op": f.get("op") or "write",
            "path": str(path),
            "before_sha": _sha(before) if before else None,
            "after_sha": _sha(after) if after else None,
            "before_bytes": before.decode("utf-8", errors="ignore") if (before and len(before) < 200_000) else None,
            "after_bytes": (f.get("contents") if len(after) < 200_000 else None),
        })
    return ops

def undo_last(project_root: Path) -> dict:
    jroot = project_root / ".pf" / "journal"
    files = sorted(jroot.glob("*.jsonl"))
    if not files:
        return {"ok": False, "message": "No journal entries"}
    jf = files[-1]
    entries = [json.loads(x) for x in jf.read_text(encoding="utf-8").splitlines() if x.strip()]
    for entry in reversed(entries):
        p = Path(entry["path"])
        if entry.get("before_bytes") is not None:
            _write_bytes(p, entry["before_bytes"].encode("utf-8"))
    return {"ok": True, "message": f"Undid {len(entries)} changes from {jf.name}"}