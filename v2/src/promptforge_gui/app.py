from __future__ import annotations
import json, os, glob, traceback, base64, time, sys, subprocess, webbrowser
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from pathlib import Path

from promptforge_core import VERSION as PF_VERSION
from promptforge_core.builder import build_prompt
from promptforge_core.config import load_config, config_path
from promptforge_core.validator import validate_files_payload, ValidationError
from promptforge_core.output_schema import example_payload
from promptforge_core.logger import get_logger
from promptforge_providers.openai_client import call_structured_channel_a, call_prose_channel_b

from promptforge_gui.tooltip import ToolTip
from promptforge_gui.apply import generate_plan, perform_apply, undo_last_apply

log = get_logger()

def _build_title() -> str:
    try:
        ts = datetime.fromtimestamp(Path(__file__).stat().st_mtime)
    except Exception:
        ts = datetime.now()
    stamp = ts.strftime("%Y-%m-%d %H:%M:%S")
    return f"PromptForge GUI E2E (v{PF_VERSION} {stamp})"

class App(ttk.Frame):
    def __init__(self, master: tk.Tk):
        super().__init__(master, padding=10)
        self.master = master
        self.pack(fill="both", expand=True)

        self.cfg = load_config()
        self.current_scenario = tk.StringVar(value=self._first_scenario_name() or "default")
        self.project_root = tk.StringVar(value=str(Path.cwd()))
        self.provider = tk.StringVar(value=self.cfg.get("provider", {}).get("name", "openai"))
        self.model_a = tk.StringVar(value=self.cfg.get("provider", {}).get("model_a", os.getenv("PF_MODEL_A", "gpt-4o-mini")))
        self.model_b = tk.StringVar(value=self.cfg.get("provider", {}).get("model_b", os.getenv("PF_MODEL_B", "gpt-4o-mini")))
        self.attachments: list[Path] = []

        self.nb = ttk.Notebook(self); self.nb.pack(fill="both", expand=True)
        self._init_tab_prompt(); self._init_tab_rules(); self._init_tab_sentinels()
        self._init_tab_output_contract(); self._init_tab_scenarios(); self._init_tab_history()
        self._init_tab_settings(); self._init_tab_help()

        footer = ttk.Frame(self); footer.pack(fill="x", pady=(8, 0))
        ttk.Button(footer, text="Save Config", command=self.on_save_config).pack(side="left")
        ttk.Button(footer, text="Reload Config", command=self.on_reload_config).pack(side="left", padx=6)
        ttk.Label(footer, text=f"Config: {config_path().as_posix()}", foreground="#666").pack(side="right")

        self._refresh_tabs()

    # ---------- HELP ----------
    def _init_tab_help(self):
        tab = ttk.Frame(self.nb, padding=8); self.nb.add(tab, text="Help")
        tk.Message(tab, width=900, text=(
            "V2 quick tour:\n"
            "1) Prompt tab → enter Task, add attachments, Build Prompt.\n"
            "2) Call Model (A) for structured JSON {files[]} or Prose (B) for rationale.\n"
            "3) Validate Reply parses/validates A-output. Apply Files… writes to Project Root with backups.\n"
            "4) Settings → Test OpenAI, install Pillow, open logs.\n"
            "5) History reads seeds/prompts.json under Project Root.\n"
        )).pack(fill="x")

    # ---------- PROMPT ----------
    def _init_tab_prompt(self):
        tab = ttk.Frame(self.nb, padding=8); self.nb.add(tab, text="Prompt")
        top = ttk.Frame(tab); top.pack(fill="x")

        ttk.Label(top, text="Scenario:").pack(side="left")
        self.scenario_combo = ttk.Combobox(top, state="readonly")
        self.scenario_combo.pack(side="left", padx=6)
        ToolTip(self.scenario_combo, "Select a scenario; each has its own rules.")

        ttk.Label(top, text="Project Root:").pack(side="left", padx=(12,2))
        self.project_entry = ttk.Entry(top, width=40, textvariable=self.project_root)
        self.project_entry.pack(side="left")
        ToolTip(self.project_entry, "Workspace folder used for Apply and History.")
        ttk.Button(top, text="Browse…", command=self.on_browse_project).pack(side="left", padx=4)

        btns_top = ttk.Frame(top); btns_top.pack(side="right")
        self.btn_call_a = ttk.Button(btns_top, text="Call Model (A)", command=self.on_call_model_a); self.btn_call_a.pack(side="left", padx=6)
        ToolTip(self.btn_call_a, "Structured channel: expects JSON { files[] }.")
        self.btn_call_b = ttk.Button(btns_top, text="Prose (B)", command=self.on_call_model_b); self.btn_call_b.pack(side="left")
        ToolTip(self.btn_call_b, "Prose channel: rationale / notes.")

        ttk.Label(tab, text="Task:").pack(anchor="w", pady=(8, 0))
        self.task_txt = tk.Text(tab, height=6); self.task_txt.pack(fill="x")

        attach_row = ttk.Frame(tab); attach_row.pack(fill="x", pady=(6,0))
        ttk.Label(attach_row, text="Attachments:").pack(side="left")
        self.attach_list = tk.Listbox(attach_row, height=3); self.attach_list.pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(attach_row, text="+ Add Files", command=self.on_add_attachments).pack(side="left")
        ttk.Button(attach_row, text="– Remove Selected", command=self.on_remove_attachments).pack(side="left", padx=4)
        ttk.Button(attach_row, text="Paste Screenshot", command=self.on_paste_screenshot).pack(side="left", padx=8)

        splitter = ttk.Panedwindow(tab, orient="vertical"); splitter.pack(fill="both", expand=True, pady=(8,0))
        left = ttk.Frame(splitter); right = ttk.Frame(splitter); splitter.add(left, weight=3); splitter.add(right, weight=2)

        ttk.Label(left, text="Prompt Preview").pack(anchor="w")
        self.output_txt = tk.Text(left); self.output_txt.pack(fill="both", expand=True)

        header = ttk.Frame(right); header.pack(fill="x")
        ttk.Label(header, text="Review (files parsed / prose / errors)").pack(side="left")
        ttk.Button(header, text="Copy Review", command=self.on_copy_review).pack(side="right")
        self.review_txt = tk.Text(right); self.review_txt.pack(fill="both", expand=True)

        row = ttk.Frame(tab); row.pack(fill="x", pady=(8, 0))
        ttk.Button(row, text="Build Prompt", command=self.on_build_prompt).pack(side="left")
        ttk.Button(row, text="Validate Reply", command=self.on_validate_reply).pack(side="left", padx=6)
        ttk.Button(row, text="Insert JSON Example", command=self.on_insert_json_example).pack(side="left", padx=6)
        ttk.Button(row, text="Apply Files…", command=self.on_apply_dialog).pack(side="left", padx=12)
        ttk.Button(row, text="Undo Last Apply", command=self.on_undo_last).pack(side="left")

    def on_copy_review(self):
        txt = self.review_txt.get("1.0","end")
        self.master.clipboard_clear(); self.master.clipboard_append(txt); self.master.update()

    def _show_error(self, title: str, err: Exception | str):
        msg = err if isinstance(err, str) else f"{type(err).__name__}: {err}"
        log.exception("%s: %s", title, msg)
        tb = traceback.format_exc()
        self.review_txt.delete("1.0","end")
        self.review_txt.insert("end", f"{title}\n{msg}\n\nTraceback:\n{tb}")
        messagebox.showerror(title, msg)

    def on_paste_screenshot(self):
        try:
            from PIL import ImageGrab
        except Exception:
            messagebox.showwarning("Paste Screenshot",
                "Pillow not installed.\nInstall into this venv:\n\n  python -m pip install pillow")
            return
        img = ImageGrab.grabclipboard()
        if img is None:
            messagebox.showwarning("Paste Screenshot", "Clipboard has no image.")
            return
        base = Path(self.project_root.get()).resolve()
        inbox = (base / ".promptforge" / "inbox"); inbox.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y%m%d-%H%M%S")
        path = inbox / f"screenshot-{ts}.png"
        img.save(path); self.attachments.append(path); self.attach_list.insert("end", str(path))
        messagebox.showinfo("Paste Screenshot", f"Saved and attached:\n{path}")

    def on_browse_project(self):
        folder = filedialog.askdirectory(title="Select Project Root", initialdir=self.project_root.get())
        if folder: self.project_root.set(folder)

    def _compose_with_attachments(self, task: str, scenario: str) -> dict:
        out = build_prompt(task, scenario=scenario)
        parts = [out["user"], ""]
        for p in self.attachments:
            p = Path(p)
            if p.suffix.lower() in (".png",".jpg",".jpeg",".gif",".webp",".bmp"):
                parts.append(f"\n\n# Attachment: {p.name} (image attached)")
                continue
            try:
                data = p.read_text(encoding="utf-8")
                if len(data.encode("utf-8")) <= 100_000:
                    parts.append(f"\n\n# Attachment: {p.name}\n```\n{data}\n```")
                else:
                    parts.append(f"\n\n# Attachment: {p.name} (too large to inline)")
            except Exception:
                parts.append(f"\n\n# Attachment: {p.name} (unreadable)")
        out["user"] = "".join(parts)
        return out

    def on_add_attachments(self):
        paths = filedialog.askopenfilenames(title="Select files to attach")
        for p in paths:
            self.attachments.append(Path(p)); self.attach_list.insert("end", p)

    def on_remove_attachments(self):
        sel = list(self.attach_list.curselection()); sel.reverse()
        for i in sel:
            self.attach_list.delete(i)
            try: del self.attachments[i]
            except Exception: pass

    def on_build_prompt(self):
        scenario = self.scenario_combo.get().strip() or "default"
        task = self.task_txt.get("1.0", "end").strip()
        if not task: messagebox.showwarning("PromptForge", "Enter a task."); return
        self.current_scenario.set(scenario)
        out = self._compose_with_attachments(task, scenario)
        self.output_txt.delete("1.0", "end")
        self.output_txt.insert("end", "=== SYSTEM ===\n"+out["system"]+"\n\n=== USER ===\n"+out["user"])

    def on_validate_reply(self):
        buf = self.output_txt.get("1.0", "end")
        try:
            files = validate_files_payload(buf); self.last_files_payload = files
            self.review_txt.delete("1.0","end")
            self.review_txt.insert("end", f"Structured payload OK\nfiles: {len(files)}\n\n")
            for f in files: self.review_txt.insert("end", f"- {f['path']} ({len(f['contents'])} bytes)\n")
            messagebox.showinfo("Valid", f"Structured payload OK (files: {len(files)})")
        except ValidationError as e:
            self._show_error("Invalid payload", e)

    def on_insert_json_example(self):
        self.output_txt.delete("1.0", "end"); self.output_txt.insert("end", example_payload())

    def on_call_model_a(self):
        try:
            task = self.task_txt.get("1.0", "end").strip()
            if not task: messagebox.showwarning("PromptForge", "Enter a task."); return
            scenario = self.scenario_combo.get().strip() or "default"
            prompt = self._compose_with_attachments(task, scenario)
            files_payload, err = call_structured_channel_a(
                prompt["system"], prompt["user"], model=self.model_a.get(),
                attachments=[str(p) for p in self.attachments],
            )
            self.review_txt.delete("1.0", "end")
            if err: self.review_txt.insert("end", f"[Notice] {err}\n\n")
            if files_payload:
                try:
                    files = validate_files_payload(files_payload); self.last_files_payload = files
                    self.output_txt.delete("1.0","end"); self.output_txt.insert("end", json.dumps(files_payload, indent=2))
                    self.review_txt.insert("end", f"Channel A OK (files: {len(files)})\n")
                    for f in files: self.review_txt.insert("end", f"- {f['path']} ({len(f['contents'])} bytes)\n")
                except ValidationError as ve:
                    self._show_error("Validation error", ve)
            else:
                self.review_txt.insert("end", "No payload returned.")
        except Exception as e:
            self._show_error("Call Model (A) failed", e)

    def on_call_model_b(self):
        try:
            task = self.task_txt.get("1.0", "end").strip()
            if not task: messagebox.showwarning("PromptForge", "Enter a task."); return
            scenario = self.scenario_combo.get().strip() or "default"
            prompt = self._compose_with_attachments(task, scenario)
            prose, err = call_prose_channel_b(
                prompt["system"], prompt["user"], model=self.model_b.get(),
                attachments=[str(p) for p in self.attachments],
            )
            if err: prose = f"[Notice] {err}\n\n{prose}"
            self.review_txt.delete("1.0","end"); self.review_txt.insert("end", prose)
        except Exception as e:
            self._show_error("Prose (B) failed", e)

    # ---------- APPLY ----------
    def on_apply_dialog(self):
        if not hasattr(self, "last_files_payload") or not self.last_files_payload:
            messagebox.showwarning("Apply", "No validated files. Use Call Model (A) or Validate Reply first."); return
        base = Path(self.project_root.get()).resolve()
        plan = generate_plan(self.last_files_payload, base)

        win = tk.Toplevel(self); win.title("Apply Files"); win.geometry("980x600")
        left = ttk.Frame(win, padding=8); left.pack(side="left", fill="y")
        right = ttk.Frame(win, padding=8); right.pack(side="left", fill="both", expand=True)

        ttk.Label(left, text="Files to apply").pack(anchor="w")
        canvas = tk.Canvas(left, borderwidth=0, highlightthickness=0)
        frame = ttk.Frame(canvas); vs = ttk.Scrollbar(left, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vs.set); vs.pack(side="right", fill="y"); canvas.pack(side="left", fill="y")
        canvas.create_window((0,0), window=frame, anchor="nw")
        frame.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))

        checks = []; selected_idx = tk.IntVar(value=-1)
        def show_diff(idx: int):
            diff_txt.delete("1.0","end")
            if 0 <= idx < len(plan): diff_txt.insert("end", plan[idx].diff or "(no changes)")

        for i, fp in enumerate(plan):
            var = tk.BooleanVar(value=True); row = ttk.Frame(frame); row.pack(fill="x", pady=2)
            ttk.Checkbutton(row, variable=var).pack(side="left")
            ttk.Button(row, text=fp.path, style="Toolbutton",
                       command=lambda idx=i: (selected_idx.set(idx), show_diff(idx))).pack(side="left")
            ttk.Label(row, text=("EXISTS" if fp.exists else "NEW"), foreground=("#444" if fp.exists else "#0a0")).pack(side="right")
            checks.append(var)

        ttk.Label(right, text="Diff preview").pack(anchor="w"); diff_txt = tk.Text(right); diff_txt.pack(fill="both", expand=True)
        btns = ttk.Frame(win); btns.pack(fill="x", pady=6)
        ttk.Button(btns, text="All", command=lambda: [c.set(True) for c in checks]).pack(side="left")
        ttk.Button(btns, text="None", command=lambda: [c.set(False) for c in checks]).pack(side="left", padx=6)
        def do_apply():
            selected = [p for p, v in zip(plan, checks) if v.get()]
            if not selected: messagebox.showwarning("Apply", "No files selected."); return
            patch = perform_apply(selected, Path(self.project_root.get()).resolve())
            messagebox.showinfo("Apply", f"Applied {len(selected)} file(s).\nBackup: {patch}"); win.destroy()
        ttk.Button(btns, text="Apply Selected", command=do_apply).pack(side="right")
        if plan: show_diff(0)

    def on_undo_last(self):
        ok, msg = undo_last_apply(Path(self.project_root.get()).resolve())
        (messagebox.showinfo if ok else messagebox.showwarning)("Undo", msg)

    # ---------- RULES / SENTINELS / CONTRACT / SCENARIOS / HISTORY / SETTINGS ----------
    def _init_tab_rules(self):
        tab = ttk.Frame(self.nb, padding=8); self.nb.add(tab, text="Rules")
        ttk.Label(tab, text="System Rules for current scenario (one per line):").pack(anchor="w")
        self.rules_txt = tk.Text(tab, height=12); self.rules_txt.pack(fill="both", expand=True)

    def _init_tab_sentinels(self):
        tab = ttk.Frame(self.nb, padding=8); self.nb.add(tab, text="Sentinels")
        row1 = ttk.Frame(tab); row1.pack(fill="x", pady=(0,6))
        ttk.Label(row1, text="Start sentinel:").pack(side="left"); self.sentinel_start = ttk.Entry(row1, width=40); self.sentinel_start.pack(side="left", padx=6)
        row2 = ttk.Frame(tab); row2.pack(fill="x")
        ttk.Label(row2, text="End sentinel:").pack(side="left"); self.sentinel_end = ttk.Entry(row2, width=40); self.sentinel_end.pack(side="left", padx=6)

    def _init_tab_output_contract(self):
        tab = ttk.Frame(self.nb, padding=8); self.nb.add(tab, text="Output Contract")
        frm = ttk.Frame(tab); frm.pack(fill="x")
        ttk.Label(frm, text="Format:").grid(row=0, column=0, sticky="w", padx=(0,6)); self.contract_format = ttk.Entry(frm, width=18); self.contract_format.grid(row=0, column=1, sticky="w")
        ttk.Label(frm, text="Schema name:").grid(row=1, column=0, sticky="w", padx=(0,6), pady=(6,0)); self.contract_schema = ttk.Entry(frm, width=24); self.contract_schema.grid(row=1, column=1, sticky="w", pady=(6,0))
        ttk.Label(tab, text="V2 uses strict JSON for Channel A.", foreground="#666").pack(anchor="w", pady=(8,0))

    def _init_tab_scenarios(self):
        tab = ttk.Frame(self.nb, padding=8); self.nb.add(tab, text="Scenarios")
        left = ttk.Frame(tab); left.pack(side="left", fill="y")
        right = ttk.Frame(tab); right.pack(side="left", fill="both", expand=True, padx=(8,0))
        ttk.Label(left, text="Scenarios").pack(anchor="w"); self.scenario_list = tk.Listbox(left, height=10); self.scenario_list.pack(fill="y", expand=False)
        self.scenario_list.bind("<<ListboxSelect>>", self.on_select_scenario)
        btns = ttk.Frame(left); btns.pack(fill="x", pady=(6,0))
        ttk.Button(btns, text="+ Add", command=self.on_add_scenario).pack(side="left")
        ttk.Button(btns, text="– Remove", command=self.on_remove_scenario).pack(side="left", padx=6)
        ttk.Label(right, text="Scenario name:").pack(anchor="w"); self.scenario_name = ttk.Entry(right); self.scenario_name.pack(fill="x")
        ttk.Label(right, text="Title:").pack(anchor="w", pady=(6,0)); self.scenario_title = ttk.Entry(right); self.scenario_title.pack(fill="x")
        ttk.Label(right, text="System rules (one per line):").pack(anchor="w", pady=(6,0)); self.scenario_rules = tk.Text(right, height=12); self.scenario_rules.pack(fill="both", expand=True)
        ttk.Button(right, text="Save Scenario", command=self.on_save_scenario).pack(anchor="e", pady=(6,0))

    def on_select_scenario(self, _evt=None):
        idxs = self.scenario_list.curselection()
        if not idxs: return
        name = self.scenario_list.get(idxs[0]); self._load_scenario_editor(name)

    def on_add_scenario(self):
        base = "scenario"; i = 1; names = set(self.cfg.get("scenarios", {}).keys())
        while f"{base}{i}" in names: i += 1
        name = f"{base}{i}"; self.cfg.setdefault("scenarios", {})[name] = {"title": name.title(), "system_rules": []}
        self._refresh_tabs(select=name)

    def on_remove_scenario(self):
        idxs = self.scenario_list.curselection()
        if not idxs: return
        name = self.scenario_list.get(idxs[0])
        if messagebox.askyesno("Remove scenario", f"Delete '{name}'?"):
            self.cfg.get("scenarios", {}).pop(name, None)
            if self.current_scenario.get() == name: self.current_scenario.set(self._first_scenario_name() or "default")
            self._refresh_tabs()

    def on_save_scenario(self):
        name = self.scenario_name.get().strip(); title = self.scenario_title.get().strip()
        rules = [line for line in self.scenario_rules.get("1.0","end").splitlines() if line.strip()]
        if not name: messagebox.showwarning("Scenarios", "Scenario name cannot be empty."); return
        scenarios = self.cfg.setdefault("scenarios", {})
        original = self.scenario_combo.get().strip() or name
        if original != name: scenarios[name] = scenarios.pop(original, {"title": title, "system_rules": rules})
        sc = scenarios.setdefault(name, {}); sc["title"] = title or name; sc["system_rules"] = rules
        self.current_scenario.set(name); self._refresh_tabs(select=name)

    def _init_tab_history(self):
        tab = ttk.Frame(self.nb, padding=8); self.nb.add(tab, text="History")
        ttk.Label(tab, text="Recent prompts (seeds/prompts.json if present)").pack(anchor="w")
        self.history_list = tk.Listbox(tab, height=12); self.history_list.pack(fill="both", expand=True, pady=(6,0))
        row = ttk.Frame(tab); row.pack(fill="x", pady=(6,0))
        ttk.Button(row, text="Refresh", command=self._load_history).pack(side="left")

    def _load_history(self):
        self.history_list.delete(0, "end")
        base = Path(self.project_root.get()).resolve()
        candidates = []
        p1 = base / "seeds" / "prompts.json"
        if p1.exists(): candidates.append(p1)
        backup_glob = str(base / "seeds" / "backups" / "*" / "prompts.json")
        backs = sorted(glob.glob(backup_glob), reverse=True)
        for b in backs: candidates.append(Path(b))
        seen = set()
        for path in candidates:
            try:
                data = json.loads(Path(path).read_text(encoding="utf-8"))
                items = data if isinstance(data, list) else data.get("prompts", [])
                for it in items[:100]:
                    text = it.get("task") or it.get("prompt") or str(it)[:80]
                    line = f"{path.name} — {text[:120].replace('\\n',' ')}"
                    if line in seen: continue
                    self.history_list.insert("end", line); seen.add(line)
            except Exception: continue
        if self.history_list.size() == 0:
            self.history_list.insert("end", "No seeds/prompts.json found under selected Project Root.")

    def _init_tab_settings(self):
        tab = ttk.Frame(self.nb, padding=8); self.nb.add(tab, text="Settings")
        ttk.Label(tab, text="Provider:").grid(row=0, column=0, sticky="w")
        prov = ttk.Combobox(tab, state="readonly", values=["openai"]); prov.set(self.provider.get()); prov.grid(row=0, column=1, sticky="w", padx=6)
        prov.bind("<<ComboboxSelected>>", lambda _e: self.provider.set(prov.get()))
        ttk.Label(tab, text="Model (Channel A):").grid(row=1, column=0, sticky="w", pady=(6,0))
        ttk.Entry(tab, width=24, textvariable=self.model_a).grid(row=1, column=1, sticky="w", padx=6, pady=(6,0))
        ttk.Label(tab, text="Model (Channel B):").grid(row=2, column=0, sticky="w")
        ttk.Entry(tab, width=24, textvariable=self.model_b).grid(row=2, column=1, sticky="w", padx=6)
        ttk.Label(tab, text="OpenAI key is read from environment (.env supported).").grid(row=3, column=0, columnspan=2, sticky="w", pady=(8,0))
        ttk.Button(tab, text="Test OpenAI", command=self.on_test_openai).grid(row=4, column=0, pady=(8,0), sticky="w")
        self.test_result = ttk.Label(tab, text="", foreground="#555"); self.test_result.grid(row=4, column=1, sticky="w")
        tools = ttk.Frame(tab); tools.grid(row=5, column=0, columnspan=2, sticky="w", pady=(12,0))
        ttk.Button(tools, text="Install Pillow", command=self.on_install_pillow).pack(side="left")
        ttk.Button(tools, text="Open Logs Folder", command=self.on_open_logs).pack(side="left", padx=6)

    def on_open_logs(self):
        folder = (Path(self.project_root.get())/".promptforge"/"out"/"logs").resolve()
        folder.mkdir(parents=True, exist_ok=True)
        try:
            if os.name == "nt": os.startfile(folder)
            else: webbrowser.open(folder.as_uri())
        except Exception as e:
            self._show_error("Open Logs", e)

    def on_install_pillow(self):
        try:
            cmd = [sys.executable, "-m", "pip", "install", "pillow"]
            subprocess.check_call(cmd)
            messagebox.showinfo("Install Pillow", "Pillow installed into this venv.")
        except Exception as e:
            self._show_error("Install Pillow failed", e)

    def on_test_openai(self):
        try:
            from openai import OpenAI
            key = os.getenv("OPENAI_API_KEY")
            if not key: raise RuntimeError("OPENAI_API_KEY is not set.")
            cl = OpenAI(api_key=key)
            r = cl.chat.completions.create(
                model=self.model_b.get(),
                messages=[{"role":"user","content":"Reply with the single word: pong"}],
                max_tokens=4, temperature=0.0
            )
            txt = (r.choices[0].message.content or "").strip()
            msg = f"OK (reply='{txt[:32]}')"; self.test_result.config(text=msg, foreground="#0a0")
        except Exception as e:
            self.test_result.config(text=f"ERROR: {e}", foreground="#a00"); self._show_error("OpenAI test failed", e)

    # ---------- CONFIG SAVE/RELOAD ----------
    def on_save_config(self):
        try:
            cfg = dict(self.cfg) if isinstance(self.cfg, dict) else {}
            cfg["provider"] = {
                "name": self.provider.get().strip() or "openai",
                "model_a": self.model_a.get().strip() or "gpt-4o-mini",
                "model_b": self.model_b.get().strip() or "gpt-4o-mini",
            }
            cfg["sentinels"] = {
                "start": self.sentinel_start.get().strip() or "BEGIN OUTPUT",
                "end": self.sentinel_end.get().strip() or "END OUTPUT",
            }
            cfg["output_contract"] = {
                "format": self.contract_format.get().strip() or "json",
                "schema_name": self.contract_schema.get().strip() or "files_payload",
            }
            name = self.scenario_name.get().strip() or (self._first_scenario_name() or "default")
            title = self.scenario_title.get().strip() or name
            rules = [ln for ln in self.scenario_rules.get("1.0","end").splitlines() if ln.strip()]
            scs = cfg.setdefault("scenarios", {})
            scs[name] = {"title": title, "system_rules": rules}
            live_rules = [ln for ln in self.rules_txt.get("1.0","end").splitlines() if ln.strip()]
            scs[self.current_scenario.get()] = scs.get(self.current_scenario.get(), {"title": self.current_scenario.get()})
            scs[self.current_scenario.get()]["system_rules"] = live_rules or rules

            path = config_path(); path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
            self.cfg = cfg
            self.review_txt.delete("1.0","end"); self.review_txt.insert("end", f"Saved config → {path}\n")
            messagebox.showinfo("Config", f"Saved: {path}")
            self._refresh_tabs(select=self.current_scenario.get())
        except Exception as e:
            self._show_error("Save Config failed", e)

    def on_reload_config(self):
        try:
            self.cfg = load_config()
            self.review_txt.delete("1.0","end"); self.review_txt.insert("end", f"Reloaded config ← {config_path()}\n")
            self._refresh_tabs(select=self.current_scenario.get())
            messagebox.showinfo("Config", "Reloaded configuration.")
        except Exception as e:
            self._show_error("Reload Config failed", e)

    # ---------- UTIL ----------
    def _first_scenario_name(self) -> str | None:
        sc = self.cfg.get("scenarios", {}); return next(iter(sc.keys()), None)

    def _get_current_rules(self):
        sc = self.cfg.get("scenarios", {}).get(self.current_scenario.get(), {})
        return sc.get("system_rules", [])

    def _load_scenario_editor(self, name: str):
        sc = self.cfg.get("scenarios", {}).get(name, {"title": name, "system_rules": []})
        self.scenario_name.delete(0,"end"); self.scenario_name.insert(0, name)
        self.scenario_title.delete(0,"end"); self.scenario_title.insert(0, sc.get("title", name))
        self.scenario_rules.delete("1.0","end"); self.scenario_rules.insert("end", "\n".join(sc.get("system_rules", [])))
        self.rules_txt.delete("1.0","end"); self.rules_txt.insert("end", "\n".join(sc.get("system_rules", [])))

    def _refresh_tabs(self, select: str | None = None):
        """Sync all UI widgets from self.cfg."""
        try:
            # Provider & models
            prov = self.cfg.get("provider", {})
            self.provider.set(prov.get("name", self.provider.get()))
            self.model_a.set(prov.get("model_a", self.model_a.get()))
            self.model_b.set(prov.get("model_b", self.model_b.get()))

            # Scenarios list & combo
            names = sorted(self.cfg.get("scenarios", {}).keys())
            if not names:
                # seed a default
                self.cfg.setdefault("scenarios", {})["default"] = {"title":"Default","system_rules":[]}
                names = ["default"]
            if select and select in names:
                self.current_scenario.set(select)
            elif self.current_scenario.get() not in names:
                self.current_scenario.set(names[0])

            self.scenario_combo["values"] = names
            self.scenario_combo.set(self.current_scenario.get())

            # Left "Scenarios" listbox
            self.scenario_list.delete(0,"end")
            for n in names: self.scenario_list.insert("end", n)
            try:
                idx = names.index(self.current_scenario.get())
                self.scenario_list.selection_clear(0,"end")
                self.scenario_list.selection_set(idx); self.scenario_list.see(idx)
            except Exception:
                pass

            # Rules text
            self.rules_txt.delete("1.0","end")
            self.rules_txt.insert("end", "\n".join(self._get_current_rules()))

            # Sentinels
            s = self.cfg.get("sentinels", {})
            self.sentinel_start.delete(0,"end"); self.sentinel_start.insert(0, s.get("start","BEGIN OUTPUT"))
            self.sentinel_end.delete(0,"end"); self.sentinel_end.insert(0, s.get("end","END OUTPUT"))

            # Output contract
            oc = self.cfg.get("output_contract", {})
            self.contract_format.delete(0,"end"); self.contract_format.insert(0, oc.get("format","json"))
            self.contract_schema.delete(0,"end"); self.contract_schema.insert(0, oc.get("schema_name","files_payload"))

            # Scenario editor pane (right side)
            self._load_scenario_editor(self.current_scenario.get())

            # Clear preview/review panes on refresh
            self.output_txt.delete("1.0","end")
            self.review_txt.delete("1.0","end")
        except Exception as e:
            self._show_error("Refresh UI failed", e)

def run_app():
    root = tk.Tk(); root.title(_build_title()); root.geometry("1180x800")
    try: root.tk.call("tk", "scaling", 1.2)
    except Exception: pass
    App(root); root.mainloop()