"""
Fix for startup project restoration timing issue.
This ensures the last project is loaded BEFORE the UI is fully initialized.
"""

import json
from pathlib import Path
from typing import Optional


def get_startup_project() -> Optional[Path]:
    """Get the project that should be loaded on startup."""
    try:
        # Load global state
        pf_root = Path("G:/My Drive/Code/Python/PromptForge")
        state_file = pf_root / ".pf" / "global_state.json"
        
        if state_file.exists():
            state = json.loads(state_file.read_text(encoding='utf-8'))
            last_project = state.get("last_project")
            
            if last_project and Path(last_project).exists():
                print(f"STARTUP: Found last project: {last_project}")
                return Path(last_project)
        
        print("STARTUP: No valid last project found, using default")
        return None
        
    except Exception as e:
        print(f"STARTUP: Error loading last project: {e}")
        return None


def initialize_project_early(app_instance):
    """Initialize project before UI setup is complete."""
    try:
        startup_project = get_startup_project()
        
        if startup_project and startup_project != app_instance.project_root:
            print(f"STARTUP: Switching from {app_instance.project_root} to {startup_project}")
            
            # Update project attributes directly (before UI is complete)
            app_instance.project_root = startup_project.resolve()
            app_instance.scripts_dir = app_instance.project_root / "v2" / "scripts"
            app_instance.tools_dir = app_instance.project_root / "v2" / "tools"
            
            # Load project config
            from pf.utils import load_project_config
            app_instance.config_data = load_project_config(app_instance.project_root)
            app_instance.auto_retry = bool(app_instance.config_data.get("retry_policy",{}).get("auto_retries",1))
            
            # Update project variable if it exists
            if hasattr(app_instance, 'project_var'):
                app_instance.project_var.set(str(app_instance.project_root))
            
            # Update window title if possible
            try:
                current_title = app_instance.title()
                if "PromptForge" in current_title:
                    project_name = app_instance.project_root.name
                    new_title = current_title.replace("PromptForge", f"PromptForge ({project_name})")
                    app_instance.title(new_title)
            except:
                pass
            
            print(f"STARTUP: Successfully initialized with project: {startup_project}")
            return True
        else:
            print("STARTUP: Using default project")
            return False
            
    except Exception as e:
        print(f"STARTUP: Project initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False
