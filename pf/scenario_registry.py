"""PromptForge Scenario Registry Management

Centralized scenario configuration system that replaces the scattered
hardcoded lists, config files, and directory scanning approach.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ScenarioInfo:
    """Complete scenario information from registry."""
    id: str
    display_name: str
    script_file: str
    category: str
    description: str
    tooltip: str
    parameters: List[str]
    requires_project: bool
    eoodf_tested: bool
    last_tested: str
    test_status: str
    documentation: str
    notes: Optional[str] = None
    removal_target: Optional[str] = None


class ScenarioRegistry:
    """Centralized scenario configuration management."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.registry_file = project_root / ".pf" / "scenario_registry.json"
        self.scripts_dir = project_root / "v2" / "scripts"
        self._registry_data = None
        self._load_registry()
    
    def _load_registry(self) -> None:
        """Load scenario registry from JSON file."""
        if not self.registry_file.exists():
            raise FileNotFoundError(f"Scenario registry not found: {self.registry_file}")
        
        with open(self.registry_file, 'r', encoding='utf-8') as f:
            self._registry_data = json.load(f)
    
    def get_all_scenarios(self, include_deprecated: bool = False) -> List[ScenarioInfo]:
        """Get all scenarios from registry."""
        scenarios = []
        
        # Add core scenarios
        for scenario_data in self._registry_data["scenarios"]["core"]:
            scenarios.append(ScenarioInfo(**scenario_data))
        
        # Add untested scenarios  
        for scenario_data in self._registry_data["scenarios"]["untested"]:
            scenarios.append(ScenarioInfo(**scenario_data))
        
        # Optionally add deprecated scenarios
        if include_deprecated:
            for scenario_data in self._registry_data["scenarios"]["deprecated"]:
                scenarios.append(ScenarioInfo(**scenario_data))
        
        return scenarios
    
    def get_scenario_by_id(self, scenario_id: str) -> Optional[ScenarioInfo]:
        """Get specific scenario by ID."""
        for scenario in self.get_all_scenarios(include_deprecated=True):
            if scenario.id == scenario_id:
                return scenario
        return None
    
    def get_scenarios_by_category(self, category: str) -> List[ScenarioInfo]:
        """Get scenarios filtered by category."""
        return [s for s in self.get_all_scenarios() if s.category == category]
    
    def get_scenarios_by_test_status(self, status: str) -> List[ScenarioInfo]:
        """Get scenarios filtered by test status."""
        return [s for s in self.get_all_scenarios(include_deprecated=True) if s.test_status == status]
    
    def get_dropdown_scenarios(self) -> List[tuple]:
        """Get scenarios formatted for UI dropdown: [(display_name, id), ...]"""
        scenarios = self.get_all_scenarios(include_deprecated=False)
        return [(s.display_name, s.id) for s in sorted(scenarios, key=lambda x: x.display_name)]
    
    def get_script_path(self, scenario_id: str) -> Optional[Path]:
        """Get full path to scenario script file."""
        scenario = self.get_scenario_by_id(scenario_id)
        if scenario:
            return self.scripts_dir / scenario.script_file
        return None
    
    def validate_registry(self) -> Dict[str, List[str]]:
        """Validate registry against actual files and return issues."""
        issues = {
            "missing_files": [],
            "orphaned_files": [],
            "invalid_categories": [],
            "missing_documentation": []
        }
        
        # Check if script files exist
        all_scenarios = self.get_all_scenarios(include_deprecated=True)
        for scenario in all_scenarios:
            script_path = self.scripts_dir / scenario.script_file
            if not script_path.exists():
                issues["missing_files"].append(f"{scenario.id}: {scenario.script_file}")
        
        # Check for orphaned script files
        if self.scripts_dir.exists():
            registered_files = {s.script_file for s in all_scenarios}
            actual_files = {f.name for f in self.scripts_dir.glob("scenario_*.ps1")}
            orphaned = actual_files - registered_files
            issues["orphaned_files"] = list(orphaned)
        
        # Check category validity
        valid_categories = set(self._registry_data["categories"].keys())
        for scenario in all_scenarios:
            if scenario.category not in valid_categories:
                issues["invalid_categories"].append(f"{scenario.id}: {scenario.category}")
        
        return issues
    
    def update_scenario_test_status(self, scenario_id: str, status: str, 
                                  tested_date: Optional[str] = None) -> bool:
        """Update scenario test status in registry."""
        if tested_date is None:
            tested_date = datetime.now().strftime("%Y-%m-%d")
        
        # Find and update scenario in registry data
        for section in ["core", "untested", "deprecated"]:
            scenarios = self._registry_data["scenarios"][section]
            for i, scenario in enumerate(scenarios):
                if scenario["id"] == scenario_id:
                    scenarios[i]["test_status"] = status
                    scenarios[i]["last_tested"] = tested_date
                    self._save_registry()
                    return True
        
        return False
    
    def _save_registry(self) -> None:
        """Save registry data back to JSON file."""
        with open(self.registry_file, 'w', encoding='utf-8') as f:
            json.dump(self._registry_data, f, indent=2, ensure_ascii=False)


# Example usage for PromptForge UI integration
def get_scenarios_for_dropdown(project_root: Path) -> List[tuple]:
    """Simple function for UI integration."""
    try:
        registry = ScenarioRegistry(project_root)
        return registry.get_dropdown_scenarios()
    except Exception as e:
        # Fallback to directory scanning if registry fails
        scripts_dir = project_root / "v2" / "scripts"
        if scripts_dir.exists():
            scenarios = []
            for script_file in scripts_dir.glob("scenario_*.ps1"):
                scenario_id = script_file.stem.replace("scenario_", "")
                display_name = scenario_id.replace("_", " ").title()
                scenarios.append((display_name, scenario_id))
            return sorted(scenarios)
        return []


def validate_scenario_files(project_root: Path) -> Dict[str, Any]:
    """Validation function for use in scenario testing."""
    try:
        registry = ScenarioRegistry(project_root)
        issues = registry.validate_registry()
        scenarios_by_status = {
            status: len(registry.get_scenarios_by_test_status(status))
            for status in ["PASS", "FAIL", "FIXING", "UNTESTED", "REVIEW_NEEDED", "DEPRECATED"]
        }
        
        return {
            "validation_issues": issues,
            "scenario_counts": scenarios_by_status,
            "total_scenarios": len(registry.get_all_scenarios(include_deprecated=True))
        }
    except Exception as e:
        return {"error": str(e)}

