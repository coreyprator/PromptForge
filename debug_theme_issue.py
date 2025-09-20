"""
Debug script to test theme color synchronization.
Run this to see what's happening with theme switching.
"""

import json
from pathlib import Path

def test_theme_switching():
    print("=== Theme Debug Test ===")
    
    # Test project paths
    pf_root = Path("G:/My Drive/Code/Python/PromptForge")
    cubist_root = Path("G:/My Drive/Code/Python/cubist_art")
    
    for project_name, project_path in [("PromptForge", pf_root), ("cubist_art", cubist_root)]:
        config_file = project_path / ".pf" / "project.json"
        print(f"\n--- {project_name} ---")
        print(f"Config file: {config_file}")
        print(f"Exists: {config_file.exists()}")
        
        if config_file.exists():
            try:
                config = json.loads(config_file.read_text(encoding='utf-8'))
                theme_color = config.get("theme_color", "NOT FOUND")
                print(f"Theme color: {theme_color}")
                print(f"Full config: {config}")
            except Exception as e:
                print(f"Error reading config: {e}")
        else:
            print("Config file does not exist")

if __name__ == "__main__":
    test_theme_switching()
