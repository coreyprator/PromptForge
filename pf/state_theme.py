from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import datetime as dt
import json
import sys

try:
    import tkinter as tk  # type: ignore
    import tkinter.ttk as ttk  # type: ignore
except Exception:  # pragma: no cover
    tk = None  # type: ignore
    ttk = None  # type: ignore

from pf.utils import load_project_config


# ---------- logging ----------

def _now_iso() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _append_log(project_root: Path, line: str) -> None:
    try:
        p = Path(project_root) / ".pf" / "state.log"
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(f"{_now_iso()} {line}\n")
    except Exception:
        print(f"PF[state]: {line}", file=sys.stderr)


# ---------- tiny state helpers ----------

def _state_path(project_root: Path) -> Path:
    return Path(project_root) / ".pf" / "state.json"


def load_pf_state(project_root: Path) -> Dict[str, Any]:
    try:
        return json.loads(_state_path(project_root).read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_pf_state(project_root: Path, update: Dict[str, Any]) -> None:
    p = _state_path(project_root)
    p.parent.mkdir(parents=True, exist_ok=True)
    cur = load_pf_state(project_root)
    cur.update(update or {})
    p.write_text(json.dumps(cur, indent=2), encoding="utf-8")


# ---------- UI helpers ----------

def _root_of(app):
    """Return a usable Tk root."""
    r = getattr(app, "root", None) or getattr(app, "window", None)
    if r:
        return r
    try:
        if hasattr(app, "winfo_toplevel"):
            r = app.winfo_toplevel()
            if r:
                return r
    except Exception:
        pass
    return app


def apply_theme_from_config(app) -> None:
    """Use .pf/project.json['theme_color'] to hint a background tint."""
    try:
        cfg = load_project_config(app.project_root) or {}
        color: Optional[str] = cfg.get("theme_color")
        if not color or tk is None:
            return

        root = _root_of(app)
        try:
            root.configure(bg=color)
        except Exception:
            pass

        if ttk is not None:
            try:
                ttk.Style(root).configure(".", background=color)  # type: ignore[arg-type]
            except Exception:
                pass
    except Exception as e:
        _append_log(app.project_root, f"apply_theme_from_config error: {e}")


def show_project_color_badge(app) -> None:
    """Small colored dot in the header bar (falls back to root)."""
    try:
        if tk is None:
            return
        cfg = load_project_config(app.project_root) or {}
        color: Optional[str] = cfg.get("theme_color")
        if not color:
            return

        root = _root_of(app)
        parent = getattr(app, "header_frame", None) or root

        old = getattr(app, "_pf_color_badge", None)
        if old is not None:
            try:
                old.destroy()
            except Exception:
                pass

        try:
            bg = parent.cget("bg")
        except Exception:
            bg = None

        badge = tk.Label(parent, text="●", font=("Segoe UI", 14), fg=color, bg=bg)
        try:
            badge.pack(side="left", padx=6)
        except Exception:
            try:
                badge.grid(row=0, column=0, padx=6, sticky="w")
            except Exception:
                badge.place(x=6, y=6)

        app._pf_color_badge = badge  # type: ignore[attr-defined]
        _append_log(app.project_root, f"badge shown {color}")
    except Exception as e:
        _append_log(app.project_root, f"show_project_color_badge error: {e}")


def stamp_title_with_time(app) -> None:
    """Append '│ YYYY-MM-DD HH:MM:SS' to the window title."""
    try:
        root = _root_of(app)
        title = root.title() or ""
        base = title.split("│")[0].strip() if "│" in title else title.strip()
        stamped = f"{base} │ {_now_iso()}"
        root.title(stamped)
        _append_log(app.project_root, f"title stamped: {stamped}")
    except Exception as e:
        _append_log(app.project_root, f"stamp_title_with_time error: {e}")


def wire_scenario_persistence(app) -> None:
    """Restore last Scenario at startup; persist on change (no need to run)."""
    try:
        var = getattr(app, "scenario_var", None)
        if not hasattr(var, "get") or not hasattr(var, "set"):
            var = None
            for v in app.__dict__.values():
                if hasattr(v, "get") and hasattr(v, "set"):
                    var = v
                    break
        if not var:
            _append_log(app.project_root, "scenario var not found")
            return

        st = load_pf_state(app.project_root)
        last = st.get("last_scenario")
        if last:
            try:
                var.set(last)  # type: ignore[attr-defined]
            except Exception:
                pass

        def _save(*_):
            try:
                save_pf_state(app.project_root, {"last_scenario": var.get()})  # type: ignore[attr-defined]
            except Exception:
                pass

        try:
            var.trace_add("write", lambda *_: _save())  # type: ignore[attr-defined]
        except Exception:
            try:
                var.trace("w", lambda *_: _save())  # type: ignore[attr-defined]
            except Exception:
                pass

        _append_log(app.project_root, f"scenario persistence wired (restored: {last})")
    except Exception as e:
        _append_log(app.project_root, f"wire_scenario_persistence error: {e}")


def wire_project_auto_open(app) -> None:
    """When project dropdown changes, call app.open_project(...) if available."""
    try:
        var = getattr(app, "project_var", None)
        if not hasattr(var, "get"):
            _append_log(app.project_root, "project var not found")
            return

        def _changed(*_):
            try:
                sel = var.get()  # type: ignore[attr-defined]
            except Exception:
                sel = None
            fn = getattr(app, "open_project", None) or getattr(app, "on_open_clicked", None)
            if callable(fn):
                try:
                    if getattr(fn, "__code__", None) and fn.__code__.co_argcount >= 2:
                        fn(sel)  # accepts path/selection
                    else:
                        fn()  # button-style handler
                except Exception:
                    pass
            show_project_color_badge(app)

        try:
            var.trace_add("write", lambda *_: _changed())  # type: ignore[attr-defined]
        except Exception:
            try:
                var.trace("w", lambda *_: _changed())  # type: ignore[attr-defined]
            except Exception:
                pass
        _append_log(app.project_root, "project auto-open wired")
    except Exception as e:
        _append_log(app.project_root, f"wire_project_auto_open error: {e}")
