from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from promptforge_core.builder import build_prompt
from promptforge_core.validator import validate_files_payload, ValidationError

def run_app():
    root = tk.Tk()
    root.title("PromptForge V2 — GUI (E2E)")
    root.geometry("900x600")

    # Layout
    frm = ttk.Frame(root, padding=10); frm.pack(fill="both", expand=True)
    task_var = tk.StringVar()
    ttk.Label(frm, text="Task:").pack(anchor="w")
    task = tk.Text(frm, height=6); task.pack(fill="x")

    out = tk.Text(frm); out.pack(fill="both", expand=True, pady=(10,0))

    def on_build():
        t = task.get("1.0","end").strip()
        if not t:
            messagebox.showwarning("PromptForge","Enter a task.")
            return
        prompt = build_prompt(t)
        out.delete("1.0","end")
        out.insert("end","=== SYSTEM ===\n"+prompt["system"]+"\n\n=== USER ===\n"+prompt["user"])

    def on_validate():
        buf = out.get("1.0","end")
        try:
            files = validate_files_payload(buf)
            messagebox.showinfo("Valid","Structured payload OK, files: "+str(len(files)))
        except ValidationError as e:
            messagebox.showerror("Invalid", str(e))

    btns = ttk.Frame(frm); btns.pack(fill="x", pady=6)
    ttk.Button(btns, text="Build Prompt", command=on_build).pack(side="left")
    ttk.Button(btns, text="Validate Reply", command=on_validate).pack(side="left", padx=6)

    root.mainloop()
