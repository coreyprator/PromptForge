from __future__ import annotations
import json, os, pathlib, typing as t

DEFAULT_CONFIG = {
    "sentinels": {"start": "BEGIN OUTPUT", "end": "END OUTPUT"},
    "output_contract": {
        "format": "json",
        "schema_name": "files_payload"
    },
    "scenarios": {
        "default": {
            "title": "Default",
            "system_rules": [
                "Channel A must be strict JSON matching the schema.",
                "Never include prose in Channel A.",
                "Channel B: human-readable notes only, no code."
            ]
        }
    }
}

def config_path(root: os.PathLike[str] | None = None) -> pathlib.Path:
    base = pathlib.Path(root or ".").resolve()
    cfg = base / ".promptforge" / "config.json"
    return cfg

def load_config(root: os.PathLike[str] | None = None) -> dict:
    p = config_path(root)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(DEFAULT_CONFIG, indent=2), encoding="utf-8")
    return DEFAULT_CONFIG
