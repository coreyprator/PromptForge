from __future__ import annotations
import logging, logging.handlers
from pathlib import Path

_LOGGER = None

def get_logger():
    global _LOGGER
    if _LOGGER: return _LOGGER
    root = Path.cwd()
    log_dir = root/".promptforge"/"out"/"logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    fh = logging.handlers.RotatingFileHandler(
        (log_dir/"pfv2.log"), maxBytes=2_000_000, backupCount=3, encoding="utf-8"
    )
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    fh.setFormatter(fmt)
    lg = logging.getLogger("promptforge")
    lg.setLevel(logging.INFO)
    if not any(isinstance(h, logging.handlers.RotatingFileHandler) for h in lg.handlers):
        lg.addHandler(fh)
    _LOGGER = lg
    return _LOGGER