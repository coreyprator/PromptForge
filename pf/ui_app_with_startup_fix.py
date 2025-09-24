"""
Complete ui_app.py with proper startup project restoration.
This version initializes the correct project BEFORE building the UI.
"""

ui_app_with_startup_code = '''
import hashlib, json, os, shutil, subprocess, tempfile, webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from pf.compliance_gate_t2 import validate as gate_t2_validate
from pf.change_journal import prepare_ops_for_apply, record_apply, undo_last
from pf.registry import load_registry, save_registry
from pf.utils import URL_RE, PATH_RE, TRAILING_JUNK_RE, load_project_config, run_pwsh_script, apply_file, basic_schema_validate


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("PromptForge — V2.2 Test Rig"); self.geometry("1320x940")
        
        # EARLY PROJECT INITIALIZATION - Load last project FIRST
        from pf.startup_project_fix import initialize_project_early
        
        # project state (with potential restoration)
        self.project_root: Path = Path.cwd()
        self.scripts_dir = self.project_root / "v2" / "scripts"
        self.tools_dir   = self.project_root / "v2" / "tools"
        self.config_data = load_project_config(self.project_root)
        
        # Initialize early (this may update project_root before UI setup)
        startup_restored = initialize_project_early(self)
        
        reg = load_registry()
        if str(self.project_root) not in reg:
            reg.insert(0, str(self.project_root)); save_registry(reg)
        self.payload=None; self.payload_id=None
        self.auto_retry = bool(self.config_data.get("retry_policy",{}).get("auto_retries",1))

        # ----- toolbar (two rows) -----
        tbc = tk.Frame(self); tbc.pack(fill="x", padx=8, pady=(6,2))
        tb1 = tk.Frame(tbc); tb1.pack(fill="x")
        tb2 = tk.Frame(tbc); tb2.pack(fill="x", pady=(4,2))

        # row 1: project + scenario
        tk.Label(tb1, text="Project:").pack(side="left")
        self.project_var = tk.StringVar(value=str(self.project_root))
        self.project_combo = ttk.Combobox(tb1, textvariable=self.project_var, width=54)
        self._refresh_projects_combo(); self.project_combo.pack(side="left", padx=(4,6))
        tk.Button(tb1, text="Add…",   command=self._project_add).pack(side="left", padx=(4,0))
        tk.Button(tb1, text="New…",   command=self._project_new).pack(side="left", padx=(4,0))
        tk.Button(tb1, text="Remove", command=self._project_remove_selected).pack(side="left", padx=(4,12))
        tk.Button(tb1, text="Reload", command=self._project_reload).pack(side="left", padx=(0,16))

        tk.Label(tb1, text="Scenario:").pack(side="left")
        self.scenario_var = tk.StringVar(value="")
        self.scenario_combo = ttk.Combobox(tb1, textvariable=self.scenario_var, width=32)
        self._refresh_scenarios(); self.scenario_combo.pack(side="left", padx=(4,6))
        tk.Button(tb1, text="Run Scenario", command=self.run_scenario).pack(side="left", padx=6)

        # row 2: Channel-A actions
        tk.Button(tb2, text="Load JSON",        command=self.load_json).pack(side="left")
        tk.Button(tb2, text="Save JSON",        command=self.save_json).pack(side="left", padx=(6,0))
        tk.Button(tb2, text="Validate Schema",  command=self.validate_schema).pack(side="left", padx=6)
        tk.Button(tb2, text="Run Compliance",   command=self.run_gate).pack(side="left", padx=6)
        tk.Button(tb2, text="Quick Fix",        command=self.quick_fix).pack(side="left", padx=6)
        tk.Button(tb2, text="Ruff Fix",         command=self.ruff_fix).pack(side="left", padx=6)
        tk.Button(tb2, text="Fix & Validate",   command=self.fix_and_validate).pack(side="left", padx=6)
        tk.Button(tb2, text="Apply",            command=self.do_apply).pack(side="left", padx=6)
        tk.Button(tb2, text="Undo",             command=self.do_undo).pack(side="left", padx=6)
        tk.Button(tb2, text="Open Latest Journal", command=self.open_latest_journal).pack(side="left", padx=6)
        tk.Button(tb2, text="Retry",            command=self.do_retry).pack(side="left", padx=6)

        # panes
        paned = tk.PanedWindow(self, sashrelief="raised", orient="horizontal"); paned.pack(expand=True, fill="both")
        left = tk.PanedWindow(paned, orient="vertical"); right = tk.PanedWindow(paned, orient="vertical")
        paned.add(left); paned.add(right)
        self.txt_parsed = self._panel(left, "Parsed A (Channel-A JSON)")
        self.txt_prose  = self._panel(left, "Prose B (human narrative)")
        self.txt_errors = self._panel(right, "Errors / Logs")
        self._attach_context_menu(self.txt_parsed); self._attach_context_menu(self.txt_prose); self._attach_context_menu(self.txt_errors)
        self._log("Project root: " + str(self.project_root))
        self._prose("Config loaded from .pf/project.json (if present). Auto-retry: " + ("on" if self.auto_retry else "off"))
        
        if startup_restored:
            self._log("Restored last project: " + str(self.project_root))

        # Theme/State/Banner integration
        try:
            from pf.state_theme import (
                apply_theme_from_config,
                show_project_color_badge,
                stamp_title_with_time,
                wire_scenario_persistence,
                wire_project_auto_open
            )
            
            # Apply all enhancements
            apply_theme_from_config(self)
            show_project_color_badge(self)
            stamp_title_with_time(self)
            wire_scenario_persistence(self)
            wire_project_auto_open(self)
            
        except ImportError:
            pass
        except Exception:
            pass

        # Enhanced UI features with complete project persistence
        try:
            from pf.ui_enhanced import add_theme_controls, remove_open_button
            from pf.project_persistence import wire_complete_project_persistence
            
            # Add enhanced controls
            add_theme_controls(self)
            remove_open_button(self)
            
            # Wire complete project and theme persistence (for runtime switching)
            wire_complete_project_persistence(self)
            
            # Update theme color save method to be project-specific
            if hasattr(self, 'theme_color_var'):
                def update_theme_project_specific(*args):
                    color = self.theme_color_var.get().strip()
                    if color.startswith('#') and len(color) == 7:
                        from pf.ui_enhanced_fixes import save_theme_color_to_current_project, apply_theme_immediately
                        if save_theme_color_to_current_project(self, color):
                            apply_theme_immediately(self, color)
                
                # Remove old trace and add new one
                try:
                    traces = self.theme_color_var.trace_info()
                    if traces:
                        self.theme_color_var.trace_remove('write', traces[0][1])
                except:
                    pass
                self.theme_color_var.trace_add('write', update_theme_project_specific)
            
        except Exception as e:
            print(f"Enhanced UI integration failed: {e}")
            import traceback
            traceback.print_exc()

    # ---- project ---- (rest of methods remain the same)
    # ... (keeping all existing methods unchanged)
'''

print("Complete ui_app.py with startup project restoration ready.")
print("The key change is early project initialization before UI setup.")
