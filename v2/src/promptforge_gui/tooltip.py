from __future__ import annotations
import tkinter as tk
from tkinter import ttk

class ToolTip:
    """Lightweight tooltip for Tk widgets."""
    def __init__(self, widget: tk.Widget, text: str, delay_ms: int = 400):
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self._id = None
        self._tipwin = None
        widget.bind("<Enter>", self._on_enter, add="+")
        widget.bind("<Leave>", self._on_leave, add="+")
        widget.bind("<ButtonPress>", self._on_leave, add="+")

    def _on_enter(self, _evt=None):
        self._schedule()

    def _on_leave(self, _evt=None):
        self._unschedule()
        self._hide()

    def _schedule(self):
        self._unschedule()
        self._id = self.widget.after(self.delay_ms, self._show)

    def _unschedule(self):
        if self._id is not None:
            try:
                self.widget.after_cancel(self._id)
            except Exception:
                pass
            self._id = None

    def _show(self):
        if self._tipwin or not self.text:
            return
        x = self.widget.winfo_rootx() + 12
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        tw = self._tipwin = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        frame = ttk.Frame(tw, borderwidth=1, relief="solid", padding=(6, 3))
        frame.pack(fill="both", expand=True)
        lbl = ttk.Label(frame, text=self.text, justify="left")
        lbl.pack(fill="both", expand=True)

    def _hide(self):
        if self._tipwin:
            try:
                self._tipwin.destroy()
            except Exception:
                pass
            self._tipwin = None