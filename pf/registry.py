import json, os
from pathlib import Path


def _registry_dir() -> Path:
    appdata = os.environ.get("APPDATA")
    return (Path(appdata) / "PromptForge") if appdata else (Path.home() / ".promptforge")


def _registry_path() -> Path:
    p = _registry_dir(); p.mkdir(parents=True, exist_ok=True); return p / "projects.json"


def load_registry() -> list[str]:
    p = _registry_path()
    try:
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return [str(Path(x)) for x in data]
    except Exception:
        pass
    return []


def save_registry(items: list[str]) -> None:
    p = _registry_path()
    uniq, seen = [], set()
    for x in items:
        x = str(Path(x))
        if x not in seen:
            seen.add(x); uniq.append(x)
    p.write_text(json.dumps(uniq, indent=2, ensure_ascii=False), encoding="utf-8")
