import hashlib, json, os, shutil, subprocess, tempfile, webbrowser
from pathlib import Path
from datetime import datetime
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
        
        # Load persistent state first
        self._load_persistent_state()
        
        # Try to restore last project, fallback to current directory
        if not self._restore_initial_project():
            self.project_root: Path = Path.cwd()
            self.scripts_dir = self.project_root / "v2" / "scripts"
            self.tools_dir   = self.project_root / "v2" / "tools"
            self.config_data = load_project_config(self.project_root)
        
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
        self.scenario_combo.bind("<<ComboboxSelected>>", lambda e: self._on_scenario_selected())
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
        self._log(f'Project root: "{self.project_root}"')
        self._prose("Config loaded from .pf/project.json (if present). Auto-retry: " + ("on" if self.auto_retry else "off"))

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
            
            # Wire complete project and theme persistence
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

    def _load_persistent_state(self):
        """Load persistent state for project and scenario."""
        self._persistent_state = {}
        
        # Look for global state file
        try:
            global_state_file = Path.cwd() / ".pf" / "global_state.json"
            if global_state_file.exists():
                with open(global_state_file, 'r', encoding='utf-8') as f:
                    self._persistent_state = json.load(f)
                print(f"STARTUP: Loaded persistent state from {global_state_file}")
        except Exception as e:
            print(f"STARTUP: Failed to load persistent state: {e}")
            self._persistent_state = {}
    
    def _save_persistent_state(self):
        """Save current state to persistent storage."""
        try:
            # Ensure .pf directory exists
            pf_dir = self.project_root / ".pf"
            pf_dir.mkdir(exist_ok=True)
            
            # Save to global state file - use per-project scenario tracking
            global_state_file = pf_dir / "global_state.json"
            
            # Load existing state to preserve per-project scenarios
            existing_state = {}
            if global_state_file.exists():
                try:
                    with open(global_state_file, 'r', encoding='utf-8') as f:
                        existing_state = json.load(f)
                except:
                    pass
            
            # Update with current project scenario
            project_scenarios = existing_state.get('project_scenarios', {})
            project_scenarios[str(self.project_root)] = self.scenario_var.get()
            
            state_data = {
                'last_project': str(self.project_root),
                'last_scenario': self.scenario_var.get(),
                'project_scenarios': project_scenarios,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(global_state_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)
            
            print(f"PERSISTENCE: Saved state - Project: {state_data['last_project']}, Scenario: {state_data['last_scenario']}")
            
        except Exception as e:
            print(f"PERSISTENCE: Failed to save state: {e}")
    
    def _restore_initial_project(self):
        """Restore the last used project on startup."""
        saved_project = self._persistent_state.get('last_project')
        if saved_project:
            saved_path = Path(saved_project)
            if saved_path.exists() and (saved_path / ".pf").exists():
                print(f"STARTUP: Restoring last project: {saved_path}")
                # Update project_root without triggering full reload
                self.project_root = saved_path
                self.scripts_dir = self.project_root / "v2" / "scripts"
                self.tools_dir = self.project_root / "v2" / "tools"
                self.config_data = load_project_config(self.project_root)
                self.auto_retry = bool(self.config_data.get("retry_policy",{}).get("auto_retries",1))
                return True
        return False
    
    def _restore_scenario_selection(self):
        """Restore the last selected scenario for the current project."""
        # Get project-specific scenario
        project_scenarios = self._persistent_state.get('project_scenarios', {})
        saved_scenario = project_scenarios.get(str(self.project_root))
        
        if saved_scenario:
            # Check if the scenario exists in current project
            current_scenarios = list(self.scenario_combo['values'])
            if saved_scenario in current_scenarios:
                self.scenario_var.set(saved_scenario)
                print(f"STARTUP: Restored scenario for {self.project_root.name}: {saved_scenario}")
            else:
                print(f"STARTUP: Scenario '{saved_scenario}' not available in project {self.project_root.name}")
        else:
            print(f"STARTUP: No saved scenario for project {self.project_root.name}")

    def _on_scenario_selected(self):
        """Handle scenario selection and save state."""
        self._save_persistent_state()

    def _get_promptforge_scripts_dir(self) -> Path:
        """Always return PromptForge's scripts directory, regardless of current project."""
        # Find PromptForge installation directory
        # This should be the directory containing the ui_app.py file
        ui_app_file = Path(__file__).resolve()
        promptforge_root = ui_app_file.parent.parent  # Go up from pf/ui_app.py to project root
        return promptforge_root / "v2" / "scripts"

    # ---- project ----
    def _set_project_root(self, new_root: Path) -> None:
        new_root = new_root.resolve()
        if not new_root.exists():
            messagebox.showerror("Project", f"Folder not found:\n{new_root}"); return
        self.project_root = new_root
        self.scripts_dir  = self.project_root / "v2" / "scripts"
        self.tools_dir    = self.project_root / "v2" / "tools"
        self.config_data  = load_project_config(self.project_root)
        self.auto_retry   = bool(self.config_data.get("retry_policy",{}).get("auto_retries",1))
        self._refresh_scenarios(); self._log(f'Switched project → "{str(new_root)}"')
        self._prose("Project changed. Auto-retry: "+("on" if self.auto_retry else "off"))
        # Save state after project change
        self._save_persistent_state()

    def _refresh_projects_combo(self) -> None:
        reg = load_registry()
        if str(self.project_root) not in reg: reg.insert(0, str(self.project_root)); save_registry(reg)
        self.project_combo["values"] = reg; self.project_var.set(str(self.project_root))

    def _project_open_selected(self) -> None:
        self._set_project_root(Path(self.project_var.get().strip('"'))); self._refresh_projects_combo()

    def _project_add(self) -> None:
        d = filedialog.askdirectory(title="Add project folder");
        if not d: return
        p = str(Path(d)); reg = load_registry()
        if p not in reg: reg.insert(0, p); save_registry(reg)
        self._set_project_root(Path(p)); self._refresh_projects_combo()

    def _project_new(self) -> None:
        d = filedialog.askdirectory(title="Create/select folder for NEW project");
        if not d: return
        root = Path(d); (root/".pf"/"journal").mkdir(parents=True, exist_ok=True)
        cfg = root/".pf"/"project.json"
        if not cfg.exists():
            starter = load_project_config(root); cfg.write_text(json.dumps(starter, indent=2, ensure_ascii=False), encoding="utf-8")
        try:
            # Copy scenarios from PromptForge, not current project
            promptforge_scripts = self._get_promptforge_scripts_dir()
            if not (root/"v2"/"scripts").exists() and promptforge_scripts.exists(): 
                shutil.copytree(promptforge_scripts, root/"v2"/"scripts")
        except Exception:
            (root/"v2"/"scripts").mkdir(parents=True, exist_ok=True)
        try:
            if not (root/"v2"/"tools").exists() and self.tools_dir.exists(): shutil.copytree(self.tools_dir, root/"v2"/"tools")
        except Exception:
            (root/"v2"/"tools").mkdir(parents=True, exist_ok=True)
        reg = load_registry(); sp = str(root)
        if sp not in reg: reg.insert(0, sp); save_registry(reg)
        self._set_project_root(root); self._refresh_projects_combo(); messagebox.showinfo("New Project", f"Initialized project at:\n{root}")

    def _project_remove_selected(self) -> None:
        sel = self.project_var.get().strip(); reg = load_registry()
        if sel in reg: reg.remove(sel); save_registry(reg)
        if sel == str(self.project_root):
            reg = load_registry(); new_root = Path(reg[0]) if reg else Path.cwd(); self._set_project_root(new_root)
        self._refresh_projects_combo()

    def _project_reload(self) -> None: self._set_project_root(self.project_root)

    # ---- UI helpers ----
    def _panel(self, parent, title: str) -> tk.Text:
        frame = tk.Frame(parent); parent.add(frame); tk.Label(frame, text=title, anchor="w").pack(fill="x")
        text = tk.Text(frame, wrap="word", undo=True); text.pack(expand=True, fill="both"); return text

    def _attach_context_menu(self, widget: tk.Text) -> None:
        menu = tk.Menu(widget, tearoff=0)
        menu.add_command(label="Copy",  command=lambda w=widget: w.event_generate("<<Copy>>"))
        menu.add_command(label="Paste", command=lambda w=widget: w.event_generate("<<Paste>>"))
        menu.add_command(label="Cut",   command=lambda w=widget: w.event_generate("<<Cut>>"))
        menu.add_separator(); menu.add_command(label="Select All", command=lambda w=widget: w.tag_add("sel","1.0","end-1c"))
        menu.add_command(label="Open Selection", command=lambda w=widget: self._open_selection(w))
        def show(evt):
            try: menu.tk_popup(evt.x_root, evt.y_root)
            finally: menu.grab_release()
        widget.bind("<Button-3>", show); widget.bind("<Control-Button-1>", show)

    def _open_selection(self, widget: tk.Text) -> None:
        try: sel = widget.get("sel.first","sel.last").strip()
        except tk.TclError: sel = ""
        if sel: self._open_target(sel)

    def _linkify(self, widget: tk.Text) -> None:
        content = widget.get("1.0","end")
        for m in URL_RE.finditer(content): self._tag_link(widget, m.start(), m.end(), m.group(1))
        for m in PATH_RE.finditer(content): self._tag_link(widget, m.start(1), m.end(1), m.group(1))

    def _tag_link(self, widget: tk.Text, start: int, end: int, target: str) -> None:
        s = self._idx(widget,start); e = self._idx(widget,end); tag=f"link_{start}_{end}"
        widget.tag_add(tag,s,e); widget.tag_config(tag,foreground="blue",underline=True)
        widget.tag_bind(tag,"<Enter>", lambda _e: widget.config(cursor="hand2"))
        widget.tag_bind(tag,"<Leave>", lambda _e: widget.config(cursor=""))
        widget.tag_bind(tag,"<Button-1>", lambda _e, t=target: self._open_target(t))

    def _idx(self, widget: tk.Text, n: int) -> str:
        content = widget.get("1.0","end"); before = content[:n]
        return f"{before.count('\n')+1}.{len(before.rsplit('\n',1)[-1])+1}"

    def _open_target(self, target: str) -> None:
        val = TRAILING_JUNK_RE.sub("", target.strip())
        if val.startswith("http://") or val.startswith("https://"): webbrowser.open(val); return
        path = Path(val)
        editor = os.environ.get("PF_EDITOR_CMD")
        if editor:
            cmd = editor.format(path=str(path)) if "{path}" in editor else f"{editor} {path}"; subprocess.Popen(cmd, shell=True); return
        code = shutil.which("code")
        if code:
            try:
                subprocess.Popen([code, "-g", str(path)]) if path.is_file() else subprocess.Popen([code, str(path if path.exists() else path.parent)])
                return
            except Exception: pass
        if os.name == "nt":
            try:
                subprocess.Popen(["explorer","/select,",str(path)]) if path.is_file() else subprocess.Popen(["explorer", str(path if path.exists() else path.parent)])
                return
            except Exception: pass
        try:
            if hasattr(os, "startfile"): os.startfile(str(path))  # type: ignore[attr-defined]
            else: subprocess.Popen(["xdg-open", str(path)])
        except Exception as exc:
            messagebox.showerror("Open", f"Failed to open:\n{path}\n\n{exc}")

    def _log(self, msg: str) -> None:
        self.txt_errors.insert("end", msg+"\n"); self.txt_errors.see("end"); self._linkify(self.txt_errors)

    def _prose(self, msg: str) -> None:
        self.txt_prose.insert("end", msg+"\n"); self.txt_prose.see("end"); self._linkify(self.txt_prose)

    # ---- scenarios ----
    def _refresh_scenarios(self) -> None:
        # Use consistent scenario list across all projects to avoid confusion
        # Start with a standardized list
        standard_scenarios = [
            "app_selfcheck",
            "venv_validate", 
            "apply_freeform_paste_clipboard_run",
            "launch_ui",
            "git_publish"
        ]
        
        # Get project-specific scenarios from config
        sys_list = list(self.config_data.get("scenarios",{}).get("system",[]))
        proj_list = list(self.config_data.get("scenarios",{}).get("project",[]))
        
        # Discover additional scenarios from PromptForge scripts directory (not current project)
        discovered = []
        try:
            promptforge_scripts = self._get_promptforge_scripts_dir()
            if promptforge_scripts.exists():
                for p in sorted(promptforge_scripts.glob("scenario_*.ps1")):
                    name = p.stem.replace("scenario_","")
                    discovered.append(name)
        except Exception:
            pass
        
        # Combine all scenarios: standard + system + project + discovered, removing duplicates
        all_scenarios = []
        for scenario_list in [standard_scenarios, sys_list, proj_list, discovered]:
            for scenario in scenario_list:
                if scenario not in all_scenarios:
                    all_scenarios.append(scenario)
        
        # Fallback to standard list if nothing found
        if not all_scenarios:
            all_scenarios = standard_scenarios
            
        self.scenario_combo["values"] = all_scenarios
        
        # Set default to first scenario if none selected
        if not self.scenario_var.get() and all_scenarios:
            self.scenario_var.set(all_scenarios[0])
        
        # Always try to restore scenario for current project (not just on startup)
        self._restore_scenario_selection()

    def _scenario_script_for(self, name: str) -> Path:
        """Get scenario script path from PromptForge directory, not current project."""
        return self._get_promptforge_scripts_dir() / f"scenario_{name}.ps1"

    # ---- file actions ----
    def load_json(self) -> None:
        path = filedialog.askopenfilename(title="Select Channel-A JSON", filetypes=[("JSON files","*.json"),("All files","*.*")])
        if not path: return
        with open(path,"r",encoding="utf-8") as h: self.payload = json.load(h)
        self.txt_parsed.delete("1.0","end"); self.txt_parsed.insert("1.0", json.dumps(self.payload, indent=2, ensure_ascii=False))
        self._log(f"Loaded payload: {path}")

    def save_json(self) -> None:
        if not self.payload:
            try: self.payload = json.loads(self.txt_parsed.get("1.0","end").strip())
            except Exception as exc: messagebox.showerror("Save JSON", f"No valid JSON loaded/typed.\n{exc}"); return
        dest = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON","*.json")])
        if not dest: return
        with open(dest,"w",encoding="utf-8") as h: json.dump(self.payload, h, indent=2, ensure_ascii=False)
        self._log(f"Saved payload: {dest}")

    def _read_payload_from_editor(self) -> dict | None:
        try: return json.loads(self.txt_parsed.get("1.0","end").strip())
        except Exception as exc: messagebox.showerror("Invalid JSON", str(exc)); return None

    def _compute_payload_id(self, payload: dict) -> str:
        norm = json.dumps(payload, sort_keys=True, ensure_ascii=False); return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:8]

    def validate_schema(self) -> None:
        payload = self._read_payload_from_editor()
        if not payload: return
        errs = basic_schema_validate(payload)
        if errs: self._log("SCHEMA: FAIL"); [self._log(" - "+e) for e in errs]; messagebox.showerror("Schema","FAIL — see Errors panel")
        else:
            self.payload_id = self._compute_payload_id(payload)
            msg = f"SCHEMA: PASS — PayloadID: {self.payload_id}"; self._log(msg); self._prose(msg); messagebox.showinfo("Schema", msg)
        self.payload = payload

    def run_gate(self) -> None:
        payload = self._read_payload_from_editor()
        if not payload: return
        res = gate_t2_validate(payload)
        if res.get("pass"): self._log("Compliance Gate: PASS"); messagebox.showinfo("Compliance","PASS")
        else: self._log("Compliance Gate: FAIL"); [self._log(e) for e in res.get("errors",[])]; messagebox.showerror("Compliance","FAIL — see Errors panel")
        self.payload = payload

    def quick_fix(self) -> None:
        raw = self.txt_parsed.get("1.0","end").strip();
        if not raw: messagebox.showerror("Quick Fix","No JSON in Parsed panel."); return
        try: json.loads(raw)
        except Exception: messagebox.showerror("Quick Fix","Invalid JSON in Parsed panel."); return
        tmp_in  = self.project_root/"v2"/"samples"/"_last_fix_input.json"
        tmp_out = self.project_root/"v2"/"samples"/"_last_fix_input.fixed.json"
        tmp_in.parent.mkdir(parents=True, exist_ok=True); tmp_in.write_text(raw, encoding="utf-8")
        fixer = self.tools_dir/"fix_channel_a.py"; 
        if not fixer.exists(): messagebox.showerror("Quick Fix", f"Missing fixer: {fixer}"); return
        py = os.environ.get("PF_PY") or shutil.which("py") or shutil.which("python") or "python"
        cmd = [py, "-3.12", str(fixer), "-i", str(tmp_in), "-o", str(tmp_out), "--report-json-only"] if str(py).endswith("py") else [py, str(fixer), "-i", str(tmp_in), "-o", str(tmp_out), "--report-json-only"]
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if proc.returncode not in (0,): self._log("Quick Fix failed:"); self._log(proc.stdout or ""); self._log(proc.stderr or ""); messagebox.showerror("Quick Fix","Failed — see Errors panel"); return
        try: report = json.loads((proc.stdout or "").strip() or "{}")
        except Exception: report = {"status":"unknown","messages":[(proc.stdout or "").strip()]}
        outp = report.get("output_path", str(tmp_out))
        if Path(outp).exists():
            fixed = json.loads(Path(outp).read_text(encoding="utf-8")); self.payload = fixed
            self.txt_parsed.delete("1.0","end"); self.txt_parsed.insert("1.0", json.dumps(fixed, indent=2, ensure_ascii=False))
        changed = [m for m in report.get("messages",[]) if any(k in m for k in ("defaulted","inferred","filled"))]
        prose_msg = f"Quick Fix: {report.get('status','unknown').upper()}. Wrote: {outp}" + (("\nChanges:\n - "+"\n - ".join(changed)) if changed else "")
        self._prose(prose_msg); self._log("Quick Fix report: "+json.dumps(report, ensure_ascii=False)); messagebox.showinfo("Quick Fix", f"Fixed payload written to:\n{outp}")

    def ruff_fix(self) -> None:
        payload = self._read_payload_from_editor()
        if not payload: return
        ruff = shutil.which("ruff")
        if not ruff: messagebox.showerror("Ruff Fix","ruff is not on PATH."); return
        tmpdir = Path(tempfile.mkdtemp(prefix="pf_rufffix_", dir=str(self.project_root/".pf") if (self.project_root/".pf").exists() else None))
        changed = 0; details=[]
        for idx,f in enumerate(payload.get("files", [])):
            lang = (f.get("language") or "").lower(); src = f.get("contents")
            if lang not in ("python","py") or src is None: continue
            t = tmpdir/f"snippet_{idx}.py"; t.write_text(src, encoding="utf-8")
            subprocess.run([ruff, "check", "--fix", str(t)], capture_output=True, text=True, encoding="utf-8", errors="replace")
            new_src = t.read_text(encoding="utf-8")
            if new_src != src: payload["files"][idx]["contents"] = new_src; changed += 1; details.append(f"files[{idx}] fixed via ruff → {t.name}")
        if changed:
            self.payload = payload; self.txt_parsed.delete("1.0","end"); self.txt_parsed.insert("1.0", json.dumps(payload, indent=2, ensure_ascii=False))
            self._prose(f"Ruff Fix: updated {changed} Python file(s) in payload.");
            if details: self._log("; ".join(details)); messagebox.showinfo("Ruff Fix", f"Updated {changed} Python file(s)")
        else: messagebox.showinfo("Ruff Fix", "No Python files changed.")

    def fix_and_validate(self) -> None:
        self.quick_fix(); self.ruff_fix();
        payload = self._read_payload_from_editor()
        if not payload: return
        res = gate_t2_validate(payload)
        if res.get("pass"): self._prose("Fix & Validate: PASS — ready to Apply."); messagebox.showinfo("Fix & Validate","PASS")
        else: self._log("Fix & Validate: Compliance FAIL"); [self._log(e) for e in res.get("errors",[])]; messagebox.showerror("Fix & Validate","Compliance FAIL — see Errors panel")

    def do_apply(self) -> None:
        payload = self._read_payload_from_editor()
        if not payload: return
        s_errs = basic_schema_validate(payload)
        if s_errs: self._log("Apply blocked — schema invalid."); [self._log(" - "+e) for e in s_errs]; messagebox.showerror("Apply","Blocked by Schema."); return
        res = gate_t2_validate(payload)
        if not res.get("pass"):
            self._log("Apply blocked — compliance failed."); [self._log(e) for e in res.get("errors",[])];
            if self.auto_retry: self._log("Tip: use Fix & Validate, then Retry.")
            messagebox.showerror("Apply","Blocked by Compliance Gate."); return
        files = payload.get("files", [])
        ops = prepare_ops_for_apply(self.project_root, files)
        for f in files: apply_file(self.project_root, f)
        jf = record_apply(self.project_root, ops); msg = f"APPLY: PASS — JournalID: {jf.stem}\nPath: {jf}"
        self._log(msg); self._prose(msg); messagebox.showinfo("Apply", msg); self.payload = payload

    def open_latest_journal(self) -> None:
        jroot = self.project_root/".pf"/"journal"
        if not jroot.exists(): messagebox.showwarning("Journal","No .pf/journal found yet."); return
        files = sorted(jroot.glob("*.jsonl"))
        if not files: messagebox.showwarning("Journal","No journal entries yet."); return
        latest = files[-1]; self._open_target(str(latest)); self._prose(f"Opened latest journal: {latest}")

    def do_undo(self) -> None:
        res = undo_last(self.project_root)
        if res.get("ok"): self._log(res["message"]); messagebox.showinfo("Undo", res["message"]) 
        else: self._log(res.get("message","Undo failed")); messagebox.showwarning("Undo", res.get("message","Undo failed"))

    def do_retry(self) -> None:
        if not self.payload: self._log("Nothing to retry."); return
        res = gate_t2_validate(self.payload)
        if res.get("pass"): self._log("Retry: Compliance Gate now PASS")
        else: self._log("Retry: still FAIL"); [self._log(e) for e in res.get("errors",[])]

    def run_scenario(self) -> None:
        name = self.scenario_var.get().strip()
        if not name: messagebox.showerror("Scenario","No scenario selected."); return
        script = self._scenario_script_for(name)
        if not script.exists(): self._log(f"Scenario script not found: {script}"); messagebox.showerror("Scenario", f"Missing: {script.name}"); return
        try: result = run_pwsh_script(script, "-ProjectRoot", str(self.project_root))
        except Exception as exc: self._log(f"[{name}] ERROR — {exc}"); messagebox.showerror("Scenario", str(exc)); return
        rc = getattr(result, "returncode", -1); out = getattr(result, "stdout", "") or ""; err = getattr(result, "stderr", "") or ""
        if rc == 0:
            self._log(f"[{name}] OK"); 
            if out.strip(): self._log(out.strip()); messagebox.showinfo("Scenario", f"{name}: OK")
        else:
            self._log(f"[{name}] FAIL ({rc})"); 
            if out.strip(): self._log(out.strip()); 
            if err.strip(): self._log(err.strip()); messagebox.showerror("Scenario", f"{name}: FAIL — see Errors panel")