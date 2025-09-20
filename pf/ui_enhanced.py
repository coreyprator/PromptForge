"""
Enhanced UI components for PromptForge theme management.
"""

import tkinter as tk
from tkinter import messagebox, ttk
from pathlib import Path
import json
import subprocess
import os


def add_theme_controls(app_instance):
    """Add theme color input and log viewer to the toolbar."""
    try:
        # Find the first toolbar frame (tb1)
        for child in app_instance.winfo_children():
            if isinstance(child, tk.Frame):
                for subchild in child.winfo_children():
                    if isinstance(subchild, tk.Frame):
                        tb1 = subchild
                        break
                break
        else:
            return
        
        # Add theme color controls after the Reload button
        tk.Label(tb1, text="Theme:").pack(side="left", padx=(16,4))
        
        app_instance.theme_color_var = tk.StringVar()
        theme_entry = tk.Entry(tb1, textvariable=app_instance.theme_color_var, width=8)
        theme_entry.pack(side="left", padx=2)
        
        # Bind color change to update theme
        def update_theme(*args):
            color = app_instance.theme_color_var.get().strip()
            if color.startswith('#') and len(color) == 7:
                save_theme_color(app_instance, color)
                apply_theme_immediately(app_instance, color)
        
        app_instance.theme_color_var.trace_add('write', update_theme)
        
        tk.Button(tb1, text="📋", command=lambda: open_log_viewer(app_instance), 
                 width=3).pack(side="left", padx=4)
        
        # Load current theme color
        load_current_theme_color(app_instance)
        
        # Add tooltips
        add_enhanced_tooltips(app_instance)
        
    except Exception as e:
        print(f"Failed to add theme controls: {e}")


def load_current_theme_color(app_instance):
    """Load current theme color into the input field."""
    try:
        project_root = Path(app_instance.project_root)
        config_file = project_root / ".pf" / "project.json"
        
        if config_file.exists():
            config = json.loads(config_file.read_text(encoding='utf-8'))
            theme_color = config.get("theme_color", "#880000")
            app_instance.theme_color_var.set(theme_color)
    except Exception:
        app_instance.theme_color_var.set("#880000")


def save_theme_color(app_instance, color):
    """Save theme color to project config."""
    try:
        project_root = Path(app_instance.project_root)
        pf_dir = project_root / ".pf"
        pf_dir.mkdir(exist_ok=True)
        
        config_file = pf_dir / "project.json"
        config = {}
        if config_file.exists():
            config = json.loads(config_file.read_text(encoding='utf-8'))
        
        config["theme_color"] = color
        config_file.write_text(json.dumps(config, indent=2), encoding='utf-8')
        
        # Log the change
        from pf.state_theme import _log_to_state
        _log_to_state(project_root, f"Theme color updated manually: {color}")
        
    except Exception as e:
        print(f"Failed to save theme color: {e}")


def apply_theme_immediately(app_instance, color):
    """Apply theme color immediately without restart."""
    try:
        # Update background
        app_instance.configure(bg=color)
        
        # Update badge
        for child in app_instance.winfo_children():
            for widget in child.winfo_children():
                if hasattr(widget, '_pf_theme_badge'):
                    widget.configure(fg=color)
                    break
    except Exception as e:
        print(f"Failed to apply theme immediately: {e}")


def open_log_viewer(app_instance):
    """Open the state.log file in a simple viewer window."""
    try:
        project_root = Path(app_instance.project_root)
        log_file = project_root / ".pf" / "state.log"
        
        if not log_file.exists():
            messagebox.showinfo("Log Viewer", "No state.log file found yet.")
            return
        
        # Create log viewer window
        log_window = tk.Toplevel(app_instance)
        log_window.title(f"State Log - {project_root.name}")
        log_window.geometry("800x600")
        
        # Add refresh button and file path
        header = tk.Frame(log_window)
        header.pack(fill="x", padx=5, pady=5)
        
        tk.Button(header, text="Refresh", 
                 command=lambda: refresh_log_content(log_text, log_file)).pack(side="left")
        tk.Button(header, text="Open in Editor", 
                 command=lambda: open_in_editor(log_file)).pack(side="left", padx=5)
        tk.Label(header, text=str(log_file), fg="gray").pack(side="right")
        
        # Log content area
        log_frame = tk.Frame(log_window)
        log_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        log_text = tk.Text(log_frame, wrap="word", font=("Consolas", 9))
        scrollbar = tk.Scrollbar(log_frame, orient="vertical", command=log_text.yview)
        log_text.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        log_text.pack(side="left", fill="both", expand=True)
        
        # Load and display log content
        refresh_log_content(log_text, log_file)
        
    except Exception as e:
        messagebox.showerror("Log Viewer", f"Failed to open log viewer:\n{e}")


def refresh_log_content(log_text, log_file):
    """Refresh the log content in the viewer."""
    try:
        content = log_file.read_text(encoding='utf-8')
        log_text.delete("1.0", "end")
        log_text.insert("1.0", content)
        log_text.see("end")
    except Exception as e:
        log_text.delete("1.0", "end")
        log_text.insert("1.0", f"Error reading log file: {e}")


def open_in_editor(file_path):
    """Open file in external editor."""
    try:
        if os.name == "nt":
            # Windows - try VS Code first, then notepad
            try:
                subprocess.Popen(["code", str(file_path)])
            except:
                subprocess.Popen(["notepad", str(file_path)])
        else:
            # Unix-like systems
            subprocess.Popen(["xdg-open", str(file_path)])
    except Exception as e:
        print(f"Failed to open in editor: {e}")


def add_enhanced_tooltips(app_instance):
    """Add enhanced tooltips to scenarios and buttons."""
    
    # Scenario tooltips
    scenario_tooltips = {
        "app_selfcheck": "Sanity check that core files, Python, and PF layout are in place",
        "apply_freeform_paste": "Apply a Freeform block from the editor to disk",
        "apply_freeform_paste_clipboard": "Apply a Freeform block from clipboard to disk",
        "apply_freeform_paste_clipboard_run": "Apply Freeform block from clipboard and run PowerShell commands",
        "fix_linkify_paths": "Clean and linkify project paths in logs",
        "git_publish": "Stage, commit, and push changes to git",
        "install_gui_from_sample": "Install minimal GUI scaffold for new projects",
        "install_runui_command": "Install 'runui' command for easy app launching",
        "runui_debug_here": "Launch app with debug output in current console",
        "setup_run_ui": "Bootstrap PF structure and validate GUI setup",
        "test_and_lint": "Run tests and Ruff linting on changed files",
        "tool_commands": "List available PF tool commands and help",
        "venv_validate": "Verify Python version, venv, and required packages"
    }
    
    # Button tooltips
    button_tooltips = {
        "Add…": "Add a project path to the dropdown",
        "New…": "Create a new, empty PF project skeleton", 
        "Remove": "Remove selected project from dropdown (doesn't delete files)",
        "Reload": "Reload current project's config",
        "Run Scenario": "Execute the selected scenario PowerShell script",
        "Load JSON": "Load Channel-A JSON into editor pane",
        "Save JSON": "Save editor pane JSON to disk",
        "Validate Schema": "Validate Channel-A JSON against schema",
        "Run Compliance": "Run PF compliance gate (Ruff + policy checks)",
        "Quick Fix": "Apply lightweight text fixes to Channel-A",
        "Ruff Fix": "Execute Ruff --fix on relevant files",
        "Fix & Validate": "Run fixers then schema + compliance validation",
        "Apply": "Apply current operation (blocked if compliance fails)",
        "Undo": "Revert last apply-level change",
        "Open Latest Journal": "Open newest .pf/journal/*.jsonl file",
        "Retry": "Re-execute the last operation"
    }
    
    # Apply tooltips to widgets
    try:
        from pf.tooltip import ToolTip
        
        # Find and tooltip scenario combo
        if hasattr(app_instance, 'scenario_combo'):
            ToolTip(app_instance.scenario_combo, 
                   "Select scenario to run. Selection is automatically saved.")
        
        # Find and tooltip buttons by text
        def add_tooltips_recursive(widget):
            for child in widget.winfo_children():
                if isinstance(child, tk.Button):
                    button_text = child.cget('text')
                    if button_text in button_tooltips:
                        ToolTip(child, button_tooltips[button_text])
                add_tooltips_recursive(child)
        
        add_tooltips_recursive(app_instance)
        
    except ImportError:
        # Create simple tooltip class if not available
        pass


def remove_open_button(app_instance):
    """Remove the redundant 'Open' button since auto-open works."""
    try:
        def find_and_remove_button(widget, text):
            for child in widget.winfo_children():
                if isinstance(child, tk.Button) and child.cget('text') == text:
                    child.destroy()
                    return True
                if find_and_remove_button(child, text):
                    return True
            return False
        
        if find_and_remove_button(app_instance, "Open"):
            from pf.state_theme import _log_to_state, _get_project_root
            project_root = _get_project_root(app_instance)
            if project_root:
                _log_to_state(project_root, "Removed redundant 'Open' button (auto-open active)")
    
    except Exception as e:
        print(f"Failed to remove Open button: {e}")
