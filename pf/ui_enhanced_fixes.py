"""
Fixes for Enhanced UI - Project theme persistence and dynamic scenario tooltips.
"""

import tkinter as tk
from tkinter import ttk
from pathlib import Path
import json


def wire_project_theme_persistence(app_instance):
    """Wire project switching to update theme color field automatically."""
    try:
        if not (hasattr(app_instance, 'project_var') and hasattr(app_instance, 'theme_color_var')):
            return
        
        # Store original project change method
        if hasattr(app_instance, '_set_project_root'):
            original_set_project = app_instance._set_project_root
            
            def enhanced_set_project_root(new_root):
                # Call original method
                result = original_set_project(new_root)
                
                # Update theme color field with new project's color
                try:
                    config_file = new_root / ".pf" / "project.json"
                    if config_file.exists():
                        config = json.loads(config_file.read_text(encoding='utf-8'))
                        theme_color = config.get("theme_color", "#880000")
                    else:
                        theme_color = "#880000"
                    
                    # Update the theme input field
                    app_instance.theme_color_var.set(theme_color)
                    
                    # Apply the theme immediately
                    apply_theme_immediately(app_instance, theme_color)
                    
                    # Log the theme switch
                    from pf.state_theme import _log_to_state
                    _log_to_state(new_root, f"Project theme loaded: {theme_color}")
                    
                except Exception as e:
                    print(f"Theme update failed during project switch: {e}")
                
                return result
            
            # Replace the method
            app_instance._set_project_root = enhanced_set_project_root
            
            from pf.state_theme import _log_to_state, _get_project_root
            project_root = _get_project_root(app_instance)
            if project_root:
                _log_to_state(project_root, "Project theme persistence wired")
    
    except Exception as e:
        print(f"Failed to wire project theme persistence: {e}")


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


def add_dynamic_scenario_tooltip(app_instance):
    """Add dynamic tooltip that changes based on selected scenario."""
    try:
        if not hasattr(app_instance, 'scenario_combo'):
            return
            
        # Scenario descriptions
        scenario_descriptions = {
            "app_selfcheck": "Sanity check that core files, Python, and PF layout are in place. Verifies project structure and dependencies.",
            "apply_freeform_paste": "Apply a Freeform block (>>>FILE ... >>>END) from the editor to disk. Creates/updates files as specified.",
            "apply_freeform_paste_clipboard": "Apply a Freeform block from clipboard to disk. Same as above but reads from clipboard instead of editor.",
            "apply_freeform_paste_clipboard_run": "Apply Freeform block from clipboard AND run any PowerShell commands (>>>RUN:PS). One-shot patching with script execution.",
            "fix_linkify_paths": "Clean and linkify project paths in logs. Makes paths clickable and fixes formatting issues.",
            "git_publish": "Stage, commit, and push changes to git repository. Uses conventional commit messages if none provided.",
            "install_gui_from_sample": "Install minimal GUI scaffold for new projects. Copies app.py, pf/ui_app.py, etc. to empty projects.",
            "install_runui_command": "Install 'runui' PowerShell helper for easy app launching. Adds runui function to PowerShell profile.",
            "pf_link_and_log_quotes": "Fix PF path links in logs and ensure safe default scenario selection. Prevents stale scenario errors.",
            "runui_debug_here": "Launch app with debug output in current console. Shows crashes and errors that normally get hidden.",
            "runui_write_manifest": "Create a snapshot manifest of important PF files and versions in .pf/backups/<timestamp>/manifest.json.",
            "setup_run_ui": "One-time bootstrap: create .pf structure, write sample configs, validate GUI setup. Initial project setup.",
            "test_and_lint": "Run unit tests and Ruff linting on changed files. Fast quality check before commits.",
            "tool_commands": "List available PF tool/script commands with short descriptions. Reference documentation.",
            "venv_validate": "Verify Python version, virtual environment activation, and required package imports. Environment health check."
        }
        
        # Create dynamic tooltip
        current_tooltip = None
        
        def update_scenario_tooltip(*args):
            nonlocal current_tooltip
            
            # Remove existing tooltip
            if current_tooltip:
                try:
                    current_tooltip.hidetip()
                except:
                    pass
            
            # Get selected scenario
            selected_scenario = app_instance.scenario_combo.get()
            description = scenario_descriptions.get(selected_scenario, "Custom scenario - no description available")
            
            # Create new tooltip with updated description
            from pf.tooltip import ToolTip
            current_tooltip = ToolTip(app_instance.scenario_combo, 
                                    f"{selected_scenario}: {description}")
        
        # Wire to scenario selection changes
        if hasattr(app_instance, 'scenario_var'):
            app_instance.scenario_var.trace_add('write', update_scenario_tooltip)
        
        # Set initial tooltip
        app_instance.scenario_combo.bind('<<ComboboxSelected>>', update_scenario_tooltip)
        update_scenario_tooltip()  # Set initial state
        
        from pf.state_theme import _log_to_state, _get_project_root
        project_root = _get_project_root(app_instance)
        if project_root:
            _log_to_state(project_root, "Dynamic scenario tooltips enabled")
    
    except Exception as e:
        print(f"Failed to add dynamic scenario tooltip: {e}")


def save_theme_color_to_current_project(app_instance, color):
    """Save theme color to the currently active project's config."""
    try:
        project_root = Path(app_instance.project_root) if hasattr(app_instance, 'project_root') else None
        if not project_root:
            return
            
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
        _log_to_state(project_root, f"Theme color updated for project {project_root.name}: {color}")
        
        return True
    except Exception as e:
        print(f"Failed to save theme color: {e}")
        return False
