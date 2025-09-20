"""
Universal PromptForge launcher - works from any project root.
Usage: python runui.py
"""

import sys
import subprocess
from pathlib import Path


def find_app_entry():
    """Find the correct app entry point."""
    cwd = Path.cwd()
    
    # Look for V2.2 Test Rig first (preferred)
    test_rig = cwd / "pf" / "ui_app.py"
    if test_rig.exists():
        return "test_rig", test_rig
    
    # Look for main app.py
    main_app = cwd / "app.py"
    if main_app.exists():
        return "main_app", main_app
    
    return None, None


def launch_app():
    """Launch the appropriate PromptForge app."""
    app_type, app_path = find_app_entry()
    
    if not app_path:
        print("Error: No PromptForge app found in current directory.")
        print("Expected: pf/ui_app.py or app.py")
        sys.exit(1)
    
    print(f"Launching PromptForge ({app_type})...")
    
    if app_type == "test_rig":
        # Launch V2.2 Test Rig with theme integration
        cmd = [sys.executable, "-c", 
               "from pf.ui_app import App; import tkinter as tk; app = App(); app.mainloop()"]
    else:
        # Launch main app
        cmd = [sys.executable, str(app_path)]
    
    try:
        subprocess.run(cmd, cwd=app_path.parent if app_type == "main_app" else Path.cwd())
    except KeyboardInterrupt:
        print("\nApplication terminated by user.")
    except Exception as e:
        print(f"Error launching application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    launch_app()
