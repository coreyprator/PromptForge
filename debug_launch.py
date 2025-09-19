#!/usr/bin/env python3
"""
Debug launcher for PromptForge to catch startup errors.
Save this as debug_launch.py in your PromptForge root directory.
"""

import sys
import traceback
from pathlib import Path
import os

def main():
    try:
        print("Debug: Starting PromptForge...")
        print(f"Debug: Python executable: {sys.executable}")
        print(f"Debug: Working directory: {Path.cwd()}")
        print(f"Debug: Python path: {sys.path[:3]}...")  # First 3 entries
        
        # Check if we're in the right directory
        if not Path("pf").exists():
            print("ERROR: pf directory not found. Are you in the PromptForge root?")
            return
            
        print("Debug: Found pf directory")
        
        # Try importing the state_theme module first
        print("Debug: Testing state_theme import...")
        try:
            import pf.state_theme
            print("SUCCESS: pf.state_theme imported")
        except Exception as e:
            print(f"ERROR importing pf.state_theme: {e}")
            traceback.print_exc()
            return
        
        # Try importing your main app
        print("Debug: Looking for main app file...")
        possible_mains = ["app.py", "main.py", "run.py", "PromptForge.py"]
        main_file = None
        
        for filename in possible_mains:
            if Path(filename).exists():
                main_file = filename
                print(f"Debug: Found main file: {filename}")
                break
        
        if not main_file:
            print("ERROR: Could not find main application file")
            print(f"Available .py files: {[f.name for f in Path('.').glob('*.py')]}")
            return
        
        print(f"Debug: Executing {main_file}...")
        
        # Execute the main file
        with open(main_file, 'r') as f:
            code = f.read()
        
        exec(code, {'__name__': '__main__'})
        
    except KeyboardInterrupt:
        print("\nDebug: Interrupted by user")
    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
    finally:
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()