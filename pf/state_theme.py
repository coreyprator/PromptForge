"""
PromptForge UI theme, state persistence, and banner management.
FIXED VERSION - handles tk.Tk apps correctly.
"""

import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Component version for banner display
PF_THEME_VERSION = "1.0.1"

# Compute module SHA-256 at import time for logging
_MODULE_PATH = Path(__file__)
try:
    _MODULE_SHA256 = hashlib.sha256(_MODULE_PATH.read_bytes()).hexdigest()[:8]
except Exception:
    _MODULE_SHA256 = "unknown"


def _get_project_root(app_instance) -> Optional[Path]:
    """Extract project root from app instance."""
    try:
        # For tk.Tk based apps, project_root might be an attribute directly
        if hasattr(app_instance, 'project_root'):
            if isinstance(app_instance.project_root, Path):
                return app_instance.project_root
            elif hasattr(app_instance.project_root, 'get'):
                # StringVar
                project_path = app_instance.project_root.get().strip()
            else:
                # String attribute
                project_path = str(app_instance.project_root).strip()
            
            if project_path and Path(project_path).exists():
                return Path(project_path)
    except Exception:
        pass
    return None


def _ensure_pf_dir(project_root: Path) -> Path:
    """Ensure .pf directory exists and return its path."""
    pf_dir = project_root / ".pf"
    pf_dir.mkdir(exist_ok=True)
    return pf_dir


def _load_json_safe(file_path: Path, default: Optional[Dict] = None) -> Dict[str, Any]:
    """Load JSON file safely, returning default dict on error."""
    if default is None:
        default = {}
    try:
        if file_path.exists():
            return json.loads(file_path.read_text(encoding='utf-8'))
    except Exception:
        pass
    return default


def _save_json_safe(file_path: Path, data: Dict[str, Any]) -> bool:
    """Save JSON file safely, returning success status."""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
        return True
    except Exception:
        return False


def _log_to_state(project_root: Path, message: str, is_session_start: bool = False) -> None:
    """Log timestamped message to .pf/state.log."""
    try:
        pf_dir = _ensure_pf_dir(project_root)
        log_file = pf_dir / "state.log"
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if is_session_start:
            project_name = project_root.name
            log_line = (
                f"[{timestamp}] SESSION START - pf.state_theme/{PF_THEME_VERSION} "
                f"(SHA:{_MODULE_SHA256}) project:{project_name} root:{project_root}"
            )
        else:
            log_line = f"[{timestamp}] {message}"
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_line + '\n')
    except Exception:
        pass


def apply_theme_from_config(app_instance) -> None:
    """Apply theme color from project configuration."""
    try:
        # Check if tkinter is available
        import tkinter as tk
    except ImportError:
        return
    
    project_root = _get_project_root(app_instance)
    if not project_root:
        return
    
    # Start session logging
    _log_to_state(project_root, "", is_session_start=True)
    
    # Load theme configuration
    config_file = project_root / ".pf" / "project.json"
    config = _load_json_safe(config_file)
    theme_color = config.get("theme_color", "#880000")
    
    # Apply background tint (best effort)
    try:
        # For tk.Tk based apps, app_instance IS the root
        if hasattr(app_instance, 'configure'):
            app_instance.configure(bg=theme_color)
            _log_to_state(project_root, f"Theme applied: background tinted {theme_color}")
    except Exception:
        _log_to_state(project_root, f"Theme color loaded ({theme_color}) but background tint failed")


def show_project_color_badge(app_instance) -> None:
    """Show colored badge in header or root as fallback."""
    try:
        import tkinter as tk
    except ImportError:
        return
    
    project_root = _get_project_root(app_instance)
    if not project_root:
        return
    
    # Load theme color
    config_file = project_root / ".pf" / "project.json"
    config = _load_json_safe(config_file)
    theme_color = config.get("theme_color", "#880000")
    
    # Find badge parent - look for toolbar frame first, then use root
    badge_parent = None
    
    # Look for a toolbar or header frame in the widget hierarchy
    if hasattr(app_instance, 'winfo_children'):
        for child in app_instance.winfo_children():
            # Look for Frame widgets that might be toolbars
            if isinstance(child, tk.Frame):
                badge_parent = child
                break
    
    # Fallback to app_instance itself
    if not badge_parent:
        badge_parent = app_instance
    
    # Check for existing badge to avoid duplicates
    for child in badge_parent.winfo_children():
        if hasattr(child, '_pf_theme_badge'):
            return
    
    # Create badge
    try:
        badge = tk.Label(
            badge_parent,
            text="●",
            fg=theme_color,
            bg=badge_parent.cget('bg') if hasattr(badge_parent, 'cget') else 'SystemButtonFace',
            font=('Arial', 12, 'bold')
        )
        badge._pf_theme_badge = True
        
        # Pack badge (prefer pack, fallback to grid/place if needed)
        try:
            badge.pack(side='right', padx=5)
            placement_method = "pack(side='right')"
        except Exception:
            try:
                badge.grid(row=0, column=99, sticky='e', padx=5)
                placement_method = "grid(row=0, col=99)"
            except Exception:
                badge.place(relx=1.0, rely=0.0, anchor='ne', x=-5, y=5)
                placement_method = "place(relx=1.0, anchor='ne')"
        
        _log_to_state(
            project_root,
            f"Badge placed via {placement_method} with color {theme_color} on {type(badge_parent).__name__}"
        )
        
    except Exception as e:
        _log_to_state(project_root, f"Badge creation failed: {str(e)}")


def stamp_title_with_time(app_instance) -> None:
    """Stamp window title with timestamp and component version."""
    try:
        import tkinter as tk
    except ImportError:
        return
    
    project_root = _get_project_root(app_instance)
    if not project_root:
        return
    
    # Check if we have a title method
    if not hasattr(app_instance, 'title'):
        return
    
    # Check if title already stamped to avoid duplicates
    try:
        current_title = app_instance.title()
    except Exception:
        current_title = ""
    
    if f"pf.state_theme/{PF_THEME_VERSION}" in current_title:
        return
    
    # Create timestamp and version stamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    stamp = f"│ {timestamp} │ pf.state_theme/{PF_THEME_VERSION}"
    
    # Append to existing title
    if current_title:
        new_title = f"{current_title} {stamp}"
    else:
        new_title = f"PromptForge {stamp}"
    
    try:
        app_instance.title(new_title)
        _log_to_state(project_root, f"Title stamped: {stamp}")
    except Exception as e:
        _log_to_state(project_root, f"Title stamping failed: {str(e)}")


def wire_scenario_persistence(app_instance) -> None:
    """Wire scenario persistence across application runs."""
    try:
        import tkinter as tk
    except ImportError:
        return
    
    project_root = _get_project_root(app_instance)
    if not project_root:
        return
    
    # Find scenario variable
    scenario_var = None
    if hasattr(app_instance, 'scenario_var'):
        scenario_var = app_instance.scenario_var
    elif hasattr(app_instance, 'scenario_name_var'):
        scenario_var = app_instance.scenario_name_var
    
    if not scenario_var:
        _log_to_state(project_root, "Scenario persistence: no scenario variable found")
        return
    
    # Load and restore last scenario
    state_file = project_root / ".pf" / "state.json"
    state = _load_json_safe(state_file)
    last_scenario = state.get("last_scenario", "")
    
    if last_scenario:
        try:
            scenario_var.set(last_scenario)
            _log_to_state(project_root, f"Scenario restored: {last_scenario}")
        except Exception as e:
            _log_to_state(project_root, f"Scenario restore failed: {str(e)}")
    
    # Wire save-on-change
    def _save_scenario(*args):
        try:
            current_scenario = scenario_var.get()
            if current_scenario:
                state = _load_json_safe(state_file)
                state["last_scenario"] = current_scenario
                if _save_json_safe(state_file, state):
                    _log_to_state(project_root, f"Scenario saved: {current_scenario}")
        except Exception as e:
            _log_to_state(project_root, f"Scenario save failed: {str(e)}")
    
    # Check if already wired to avoid duplicates
    if not hasattr(scenario_var, '_pf_scenario_wired'):
        scenario_var.trace_add('write', _save_scenario)
        scenario_var._pf_scenario_wired = True
        _log_to_state(project_root, "Scenario persistence wired (trace_add)")


def wire_project_auto_open(app_instance) -> None:
    """Wire project dropdown to auto-open on selection change."""
    try:
        import tkinter as tk
        from tkinter import ttk
    except ImportError:
        return
    
    project_root = _get_project_root(app_instance)
    if not project_root:
        return
    
    # Find project variable
    project_var = None
    if hasattr(app_instance, 'project_var'):
        project_var = app_instance.project_var
    
    if not project_var:
        _log_to_state(project_root, "Project auto-open: no project variable found")
        return
    
    # Find open method
    open_method = None
    open_method_name = ""
    
    if hasattr(app_instance, '_project_open_selected'):
        open_method = lambda: app_instance._project_open_selected()
        open_method_name = "_project_open_selected()"
    elif hasattr(app_instance, 'open_project'):
        # Check if open_project accepts path argument
        try:
            import inspect
            sig = inspect.signature(app_instance.open_project)
            if len(sig.parameters) >= 2:  # self + path
                open_method = lambda: app_instance.open_project(project_var.get())
                open_method_name = "open_project(path)"
            else:
                open_method = lambda: app_instance.open_project()
                open_method_name = "open_project()"
        except Exception:
            pass
    elif hasattr(app_instance, 'on_open_clicked'):
        open_method = lambda: app_instance.on_open_clicked()
        open_method_name = "on_open_clicked()"
    
    if not open_method:
        _log_to_state(project_root, "Project auto-open: no suitable open method found")
        return
    
    # Wire auto-open handler
    def _auto_open(*args):
        try:
            selected_path = project_var.get().strip()
            if selected_path and Path(selected_path).exists() and str(selected_path) != str(project_root):
                open_method()
                _log_to_state(project_root, f"Auto-opened project: {selected_path} via {open_method_name}")
        except Exception as e:
            _log_to_state(project_root, f"Auto-open failed: {str(e)}")
    
    # Check if already wired to avoid duplicates
    if hasattr(project_var, '_pf_auto_open_wired'):
        return
    
    try:
        project_var.trace_add('write', _auto_open)
        project_var._pf_auto_open_wired = True
        _log_to_state(project_root, f"Project auto-open wired via trace_add to {open_method_name}")
    except Exception as e:
        _log_to_state(project_root, f"Project auto-open wiring failed: {str(e)}")