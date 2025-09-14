from __future__ import annotations
from .config import load_config

def build_prompt(task: str, scenario: str = "default") -> dict:
    cfg = load_config()
    sc = cfg.get("scenarios", {}).get(scenario, {})
    sys_rules = sc.get("system_rules", [])
    return {
        "system": "\n".join(f"- {r}" for r in sys_rules),
        "user": task.strip(),
    }
