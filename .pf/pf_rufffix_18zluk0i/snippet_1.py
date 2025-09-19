from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional
import json
import sys
import tkinter as tk
try:
    import tkinter.ttk as ttk
except Exception:
    ttk = None  # type: ignore

from pf.utils import load_project_config

def _log(app_or_root, *msg: object) -> None:
    try:
        pr = getattr(app_or_root, 'project_root', None) or Path.cwd()
        p = Path(pr) / '.pf' / 'state.log'
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('a', encoding='utf-8') as f:
            f.write(' '.join(str(m) for m in msg) + '\n')
    except Exception:
        print('PF[theme]', *msg, file=sys.stderr)

# state read/write

def _state_path(project_root: Path) -> Path:
    return Path(project_root) / '.pf' / 'state.json'

def load_pf_state(project_root: Path) -> Dict[str, Any]:
    try:
        return json.loads(_state_path(project_root).read_text(encoding='utf-8'))
    except Exception:
        return {}

def save_pf_state(project_root: Path, update: Dict[str, Any]) -> None:
    p = _state_path(project_root)
    p.parent.mkdir(parents=True, exist_ok=True)
    cur = load_pf_state(project_root)
    cur.update(update or {})
    p.write_text(json.dumps(cur, indent=2), encoding='utf-8')

# features

def apply_theme_from_config(app) -> None:
    try:
        cfg = load_project_config(app.project_root) or {}
        color = cfg.get('theme_color')
        if not color:
            _log(app, 'no theme_color in .pf/project.json')
            return
        root = getattr(app, 'root', None) or getattr(app, 'window', None)
        if not root:
            _log(app, 'no root/window on app')
            return
        try: root.configure(bg=color)
        except Exception: pass
        if ttk:
            try: ttk.Style(root).configure('.', background=color)
            except Exception: pass
        parent = getattr(app, 'header_frame', None) or root
        try:
            old = getattr(app, '_pf_color_badge', None)
            if old: old.destroy()
        except Exception: pass
        try:
            bg = parent.cget('bg')
        except Exception:
            bg = None
        badge = tk.Label(parent, text='\u25CF', font=('Segoe UI', 14), fg=color, bg=bg)
        try: badge.pack(side='left', padx=6)
        except Exception:
            try: badge.grid(row=0, column=0, padx=6, sticky='w')
            except Exception: badge.place(x=6, y=6)
        app._pf_color_badge = badge
        try:
            t = (getattr(app, 'root', None) or getattr(app, 'window', None))
            if t: t.title(f"{t.title()} │ theme {color}")
        except Exception: pass
        _log(app, 'badge shown', color)
    except Exception as e:
        _log(app, 'apply_theme_from_config error:', e)

def persist_last_scenario(app) -> None:
    var = None
    for n in ('scenario_var', 'scenario_name_var'):
        v = getattr(app, n, None)
        if hasattr(v, 'get') and hasattr(v, 'set'):
            var = v; break
    if not var:
        _log(app, 'no scenario var found')
        return
    st = load_pf_state(app.project_root)
    last = st.get('last_scenario')
    try:
        if last: var.set(last)
    except Exception: pass
    def _save(*_):
        try: save_pf_state(app.project_root, {'last_scenario': var.get()})
        except Exception: pass
    try: var.trace_add('write', lambda *_: _save())
    except Exception:
        try: var.trace('w', lambda *_: _save())
        except Exception: pass
    _log(app, 'scenario persistence wired (restored:', last, ')')

def auto_open_on_project_change(app) -> None:
    var = getattr(app, 'project_var', None)
    if not var:
        _log(app, 'no project_var; skip auto-open')
        return
    def _do_open(sel: Optional[str]):
        if not sel: return
        for name in ('open_project', 'on_open_clicked', 'on_open_project', '_open_project'):
            fn = getattr(app, name, None)
            if callable(fn):
                try:
                    if getattr(fn, '__code__', None) and fn.__code__.co_argcount >= 2:
                        fn(sel)
                    else:
                        fn()
                except Exception:
                    pass
                break
    def _changed(*_):
        try: _do_open(var.get())
        except Exception: pass
    try: var.trace_add('write', lambda *_: _changed())
    except Exception:
        try: var.trace('w', lambda *_: _changed())
        except Exception: pass
    _log(app, 'project_var auto-open wired')

def after_construct(app) -> None:
    root = getattr(app, 'root', None) or getattr(app, 'window', None)
    if not root:
        _log(app, 'after_construct: no root; postpone')
        return
    def _go():
        try:
            apply_theme_from_config(app)
            persist_last_scenario(app)
            auto_open_on_project_change(app)
        except Exception as e:
            _log(app, 'after_construct error:', e)
    try:
        root.after(200, _go)
        _log(app, 'hooks scheduled')
    except Exception:
        _go()
