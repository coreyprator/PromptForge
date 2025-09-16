# Integrate three buttons into the PF GUI (V2.2)

This adds **Run UI / Apply / Undo** without changing business logic.

## 1) Import helpers in app.py
```python
# near other imports in v2/src/promptforge_gui/app.py
from promptforge_gui.actions import run_ui as pf_run_ui, apply_payload as pf_apply, undo_last as pf_undo
```

## 2) Add three buttons to your toolbar/panel
Where you build the main actions row (Tkinter):
```python
import tkinter as tk
...
btn_run = tk.Button(actions_frame, text="Run UI", command=self._on_run_ui)
btn_apply = tk.Button(actions_frame, text="Apply Payload", command=self._on_apply)
btn_undo = tk.Button(actions_frame, text="Undo Last Apply", command=self._on_undo)
for b in (btn_run, btn_apply, btn_undo):
    b.pack(side=tk.LEFT, padx=4)
```

## 3) Hook up handlers in your App class
Assumes you already track `self.project_root` and the review JSON path `self.last_files_json_path`.
```python
def _on_run_ui(self):
    try:
        pf_run_ui(self.project_root)
        self._log_info("Run UI launched")
    except Exception as e:
        self._log_error(f"Run UI failed: {e}")

def _on_apply(self):
    if not getattr(self, "last_files_json_path", None):
        return self._log_error("No payload JSON to apply. Call Model (A) first.")
    rc, out, err = pf_apply(self.project_root, self.last_files_json_path)
    self._log_info(out.strip())
    if rc != 0:
        self._log_error(err.strip() or "Apply failed")

def _on_undo(self):
    rc, out, err = pf_undo(self.project_root)
    self._log_info(out.strip())
    if rc != 0:
        self._log_error(err.strip() or "Undo failed")
```

> Note: If your app currently doesn’t persist `self.last_files_json_path`, save the latest **Review** JSON to a temp file whenever Call Model (A) succeeds (you already had code printing the parsed summary). Store that path on `self` so **Apply** knows where to read from.

## 4) Windows-only assumption
These helpers shell to **pwsh**. That matches our Sprint constraints (Windows 11 + PowerShell 7).
