"""
Complete project and theme persistence system.
Handles last project memory and bidirectional theme switching.
"""

import json
from pathlib import Path
from typing import Optional


def get_global_state_file() -> Path:
    """Get the global state file for cross-project persistence."""
    # Store in PromptForge directory for global access
    pf_root = Path("G:/My Drive/Code/Python/PromptForge")
    return pf_root / ".pf" / "global_state.json"


def load_global_state() -> dict:
    """Load global application state."""
    state_file = get_global_state_file()
    try:
        if state_file.exists():
            return json.loads(state_file.read_text(encoding='utf-8'))
    except Exception:
        pass
    return {}


def save_global_state(state: dict) -> None:
    """Save global application state."""
    state_file = get_global_state_file()
    try:
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(json.dumps(state, indent=2), encoding='utf-8')
    except Exception:
        pass


def get_last_project() -> Optional[str]:
    """Get the last used project path."""
    state = load_global_state()
    last_project = state.get("last_project")
    if last_project and Path(last_project).exists():
        return last_project
    return None


def set_last_project(project_path: str) -> None:
    """Set the last used project path."""
    state = load_global_state()
    state["last_project"] = str(project_path)
    save_global_state(state)


def wire_complete_project_persistence(app_instance):
    """Wire complete project persistence with theme switching."""
    print("DEBUG: Wiring complete project persistence...")
    
    try:
        # Set initial project to last used project
        last_project = get_last_project()
        if last_project and last_project != str(app_instance.project_root):
            print(f"DEBUG: Restoring last project: {last_project}")
            app_instance._set_project_root(Path(last_project))
        
        # Hook project switching methods
        if hasattr(app_instance, '_set_project_root'):
            original_set_project = app_instance._set_project_root
            print("DEBUG: Found _set_project_root method")
            
            def enhanced_set_project_root(new_root):
                print(f"DEBUG: Project switching from {app_instance.project_root} to {new_root}")
                
                # Save as last used project
                set_last_project(str(new_root))
                print(f"DEBUG: Saved last project: {new_root}")
                
                # Call original method
                result = original_set_project(new_root)
                
                # Update theme after project change
                update_theme_for_project(app_instance, new_root)
                
                return result
            
            # Replace the method
            app_instance._set_project_root = enhanced_set_project_root
            print("DEBUG: Successfully hooked _set_project_root")
        
        # Also hook the dropdown selection method
        if hasattr(app_instance, '_project_open_selected'):
            original_open_selected = app_instance._project_open_selected
            print("DEBUG: Found _project_open_selected method")
            
            def enhanced_project_open_selected():
                selected_path = app_instance.project_var.get().strip('"')
                print(f"DEBUG: Dropdown selection changed to: {selected_path}")
                return original_open_selected()
            
            app_instance._project_open_selected = enhanced_project_open_selected
            print("DEBUG: Successfully hooked _project_open_selected")
        
        # Hook the project variable changes (for auto-open)
        if hasattr(app_instance, 'project_var'):
            def on_project_var_change(*args):
                selected_path = app_instance.project_var.get().strip('"')
                current_path = str(app_instance.project_root)
                
                if selected_path != current_path and Path(selected_path).exists():
                    print(f"DEBUG: Project var changed: {current_path} → {selected_path}")
                    app_instance._set_project_root(Path(selected_path))
            
            app_instance.project_var.trace_add('write', on_project_var_change)
            print("DEBUG: Successfully hooked project_var changes")
        
    except Exception as e:
        print(f"DEBUG: Failed to wire complete project persistence: {e}")
        import traceback
        traceback.print_exc()


def update_theme_for_project(app_instance, project_root: Path):
    """Update theme color when project changes."""
    try:
        print(f"DEBUG: Updating theme for project: {project_root}")
        
        # Load theme color for this project
        config_file = project_root / ".pf" / "project.json"
        print(f"DEBUG: Looking for theme config at: {config_file}")
        
        if config_file.exists():
            config = json.loads(config_file.read_text(encoding='utf-8'))
            theme_color = config.get("theme_color", "#880000")
            print(f"DEBUG: Found theme color: {theme_color}")
        else:
            theme_color = "#880000"
            print("DEBUG: No config found, using default: #880000")
        
        # Update theme input field if it exists
        if hasattr(app_instance, 'theme_color_var'):
            current_color = app_instance.theme_color_var.get()
            print(f"DEBUG: Current theme field: {current_color}")
            
            if current_color != theme_color:
                app_instance.theme_color_var.set(theme_color)
                print(f"DEBUG: Updated theme field to: {theme_color}")
                
                # Apply theme visually
                apply_theme_immediately(app_instance, theme_color)
            else:
                print("DEBUG: Theme color unchanged")
        
        # Log the change
        from pf.state_theme import _log_to_state
        _log_to_state(project_root, f"Project loaded with theme: {theme_color}")
        
    except Exception as e:
        print(f"DEBUG: Theme update failed: {e}")
        import traceback
        traceback.print_exc()


def apply_theme_immediately(app_instance, color):
    """Apply theme color immediately."""
    try:
        print(f"DEBUG: Applying theme color: {color}")
        
        # Update background
        app_instance.configure(bg=color)
        
        # Update badge
        for child in app_instance.winfo_children():
            for widget in child.winfo_children():
                if hasattr(widget, '_pf_theme_badge'):
                    widget.configure(fg=color)
                    break
        
        print("DEBUG: Theme applied successfully")
        
    except Exception as e:
        print(f"DEBUG: Theme application failed: {e}")
