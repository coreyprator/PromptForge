"""
Enhanced fixes with debug output to track theme switching issues.
"""

import tkinter as tk
from tkinter import ttk
from pathlib import Path
import json


def wire_project_theme_persistence_debug(app_instance):
    """Wire project switching with debug output."""
    print("DEBUG: Wiring project theme persistence...")
    
    try:
        if not (hasattr(app_instance, 'project_var') and hasattr(app_instance, 'theme_color_var')):
            print("DEBUG: Missing required attributes - project_var or theme_color_var")
            return
        
        # Store original project change method
        if hasattr(app_instance, '_set_project_root'):
            original_set_project = app_instance._set_project_root
            print("DEBUG: Found _set_project_root method")
            
            def debug_set_project_root(new_root):
                print(f"DEBUG: Project switching to: {new_root}")
                
                # Call original method
                result = original_set_project(new_root)
                
                # Update theme color field with new project's color
                try:
                    config_file = new_root / ".pf" / "project.json"
                    print(f"DEBUG: Looking for config at: {config_file}")
                    print(f"DEBUG: Config exists: {config_file.exists()}")
                    
                    if config_file.exists():
                        config = json.loads(config_file.read_text(encoding='utf-8'))
                        theme_color = config.get("theme_color", "#880000")
                        print(f"DEBUG: Found theme color: {theme_color}")
                    else:
                        theme_color = "#880000"
                        print("DEBUG: Using default theme color: #880000")
                    
                    # Update the theme input field
                    current_color = app_instance.theme_color_var.get()
                    print(f"DEBUG: Current theme field value: {current_color}")
                    
                    app_instance.theme_color_var.set(theme_color)
                    print(f"DEBUG: Updated theme field to: {theme_color}")
                    
                    # Apply the theme immediately
                    apply_theme_immediately_debug(app_instance, theme_color)
                    
                    # Log the theme switch
                    from pf.state_theme import _log_to_state
                    _log_to_state(new_root, f"DEBUG: Project theme loaded: {theme_color}")
                    
                except Exception as e:
                    print(f"DEBUG: Theme update failed during project switch: {e}")
                    import traceback
                    traceback.print_exc()
                
                return result
            
            # Replace the method
            app_instance._set_project_root = debug_set_project_root
            print("DEBUG: Successfully wired project theme persistence with debug")
            
        else:
            print("DEBUG: _set_project_root method not found")
    
    except Exception as e:
        print(f"DEBUG: Failed to wire project theme persistence: {e}")
        import traceback
        traceback.print_exc()


def apply_theme_immediately_debug(app_instance, color):
    """Apply theme color with debug output."""
    print(f"DEBUG: Applying theme color: {color}")
    try:
        # Update background
        app_instance.configure(bg=color)
        print("DEBUG: Updated background color")
        
        # Update badge
        badge_found = False
        for child in app_instance.winfo_children():
            for widget in child.winfo_children():
                if hasattr(widget, '_pf_theme_badge'):
                    widget.configure(fg=color)
                    badge_found = True
                    print("DEBUG: Updated badge color")
                    break
        
        if not badge_found:
            print("DEBUG: No badge found to update")
            
    except Exception as e:
        print(f"DEBUG: Failed to apply theme immediately: {e}")
        import traceback
        traceback.print_exc()
