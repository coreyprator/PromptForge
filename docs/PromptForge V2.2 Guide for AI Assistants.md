# PromptForge V2.2 Guide for AI Assistants

## Overview
PromptForge is a Channel-A JSON development framework that processes structured file operations with automated compliance gates, change tracking, and project management. This guide enables AI assistants to work effectively with PromptForge-enabled projects.

## Core Concepts

### Channel-A JSON Format
All code changes must be structured as Channel-A JSON for PromptForge processing:

```json
{
  "files": [
    {
      "path": "src/components/widget.py",
      "language": "python",
      "contents": "#!/usr/bin/env python3\n# Complete file contents here\nclass Widget:\n    def __init__(self):\n        pass"
    },
    {
      "path": "tests/test_widget.py", 
      "language": "python",
      "contents": "import unittest\nfrom src.components.widget import Widget\n\nclass TestWidget(unittest.TestCase):\n    def test_creation(self):\n        widget = Widget()\n        self.assertIsNotNone(widget)"
    }
  ]
}
```

### Critical Requirements

1. **Complete Files Only**: Provide full file contents, not snippets or patches
2. **Relative Paths**: All paths relative to project root (no absolute paths)
3. **Language Specification**: Always include `"language"` field for syntax highlighting and processing
4. **Compliance Ready**: Code must pass Ruff linting for Python (PromptForge auto-fixes minor issues)

## Development Workflow

### Standard Process
1. **Analyze Requirements**: Understand the development task
2. **Structure as Channel-A**: Format all code changes as JSON
3. **Provide Complete Solution**: Include all necessary files
4. **Explain Implementation**: Document approach and key decisions

### Example Workflow
When asked to "add a new user authentication system":

```json
{
  "files": [
    {
      "path": "src/auth/authenticator.py",
      "language": "python", 
      "contents": "from typing import Optional\nfrom dataclasses import dataclass\n\n@dataclass\nclass User:\n    username: str\n    email: str\n    hashed_password: str\n\nclass Authenticator:\n    def __init__(self):\n        self.users = {}\n    \n    def register(self, username: str, email: str, password: str) -> bool:\n        if username in self.users:\n            return False\n        hashed_pw = self._hash_password(password)\n        self.users[username] = User(username, email, hashed_pw)\n        return True\n    \n    def authenticate(self, username: str, password: str) -> Optional[User]:\n        if username not in self.users:\n            return None\n        user = self.users[username]\n        if self._verify_password(password, user.hashed_password):\n            return user\n        return None\n    \n    def _hash_password(self, password: str) -> str:\n        import hashlib\n        return hashlib.sha256(password.encode()).hexdigest()\n    \n    def _verify_password(self, password: str, hashed: str) -> bool:\n        return self._hash_password(password) == hashed"
    },
    {
      "path": "tests/test_auth.py",
      "language": "python",
      "contents": "import unittest\nfrom src.auth.authenticator import Authenticator\n\nclass TestAuthenticator(unittest.TestCase):\n    def setUp(self):\n        self.auth = Authenticator()\n    \n    def test_register_new_user(self):\n        result = self.auth.register('testuser', 'test@example.com', 'password123')\n        self.assertTrue(result)\n    \n    def test_register_duplicate_user(self):\n        self.auth.register('testuser', 'test@example.com', 'password123')\n        result = self.auth.register('testuser', 'other@example.com', 'different')\n        self.assertFalse(result)\n    \n    def test_authenticate_valid_user(self):\n        self.auth.register('testuser', 'test@example.com', 'password123')\n        user = self.auth.authenticate('testuser', 'password123')\n        self.assertIsNotNone(user)\n        self.assertEqual(user.username, 'testuser')\n    \n    def test_authenticate_invalid_password(self):\n        self.auth.register('testuser', 'test@example.com', 'password123')\n        user = self.auth.authenticate('testuser', 'wrongpassword')\n        self.assertIsNone(user)\n    \n    def test_authenticate_nonexistent_user(self):\n        user = self.auth.authenticate('nonexistent', 'password')\n        self.assertIsNone(user)"
    },
    {
      "path": "src/auth/__init__.py",
      "language": "python",
      "contents": "from .authenticator import Authenticator, User\n\n__all__ = ['Authenticator', 'User']"
    }
  ]
}
```

## PromptForge Integration

### How PromptForge Processes Your Code
1. **Schema Validation**: Ensures JSON structure is correct
2. **Compliance Gates**: Runs Ruff linting on Python code
3. **Quick Fix**: Automatically corrects common formatting issues
4. **File Writing**: Creates/updates files in project structure
5. **Change Tracking**: Records all changes in project journal
6. **Undo Support**: Enables rollback of changes if needed

### Working with PromptForge UI
The developer will:
1. Copy your Channel-A JSON to clipboard
2. Select target project in PromptForge
3. Choose "apply_freeform_paste_clipboard_run" scenario
4. Execute to apply changes

### Success Indicators
Look for these log messages:
```
[apply_freeform_paste_clipboard_run] OK
WROTE: src/auth/authenticator.py
WROTE: tests/test_auth.py
WROTE: src/auth/__init__.py
Project root: "[project_path]"
```

### Common Failure Modes
- **Invalid JSON**: Syntax errors in JSON structure
- **Missing Language**: Forgot to specify `"language"` field
- **Compliance Failures**: Code doesn't pass Ruff linting
- **Path Issues**: Absolute paths or invalid relative paths

## Available PromptForge Scenarios

Understanding PromptForge scenarios helps you guide users effectively:

### Core Development Scenarios
- **app_selfcheck**: Validates project structure and PromptForge installation
- **apply_freeform_paste_clipboard_run**: Primary workflow for applying your Channel-A JSON
- **launch_ui**: Runs code quality checks (Ruff linting, pytest)
- **venv_validate**: Validates Python environment and dependencies
- **git_publish**: Automated git commit and push workflow

### Setup and Installation
- **install_global_runui**: Creates system-wide `runui` command for project launching
- **install_gui_from_sample**: Sets up PromptForge UI in new projects

### Development and Debug
- **runui_debug_here**: Launches project UI with debug flags for troubleshooting

### When to Reference Scenarios
- **Environment Setup**: Recommend `venv_validate` before development
- **Code Quality**: Suggest `launch_ui` after providing code changes
- **Project Validation**: Reference `app_selfcheck` for project structure issues
- **Version Control**: Mention `git_publish` for committing completed work

## Best Practices for AI Assistants

### Code Quality
- Write production-ready, complete code
- Include comprehensive error handling
- Add docstrings and type hints for Python
- Follow project's existing code style

### File Organization
- Structure files logically within project hierarchy
- Include necessary `__init__.py` files for Python packages
- Provide tests alongside implementation code
- Consider configuration files when needed

### Documentation
- Explain the approach and architecture decisions
- Highlight any dependencies or setup requirements
- Note any manual steps needed after code application
- Suggest follow-up PromptForge scenarios (testing, validation, etc.)

### Iterative Development
When building complex features:
1. Start with core functionality
2. Provide complete, working initial implementation
3. Suggest follow-up enhancements as separate Channel-A submissions
4. Maintain backward compatibility when possible

## Project-Specific Considerations

### Python Projects
- All code must be Ruff-compliant
- Use type hints consistently
- Follow PEP 8 conventions
- Include proper imports and package structure

### JavaScript/TypeScript Projects
- Specify correct language (`"javascript"` or `"typescript"`)
- Include proper module imports/exports
- Consider bundling and build requirements

### Configuration Files
- JSON: Use proper formatting and validation
- YAML: Maintain proper indentation
- Environment files: Follow project conventions

## Advanced PromptForge Features

### Project Persistence
PromptForge V2.2 automatically remembers:
- Last used project across application restarts
- Per-project scenario selections
- Project-specific theme colors and settings

### Enhanced Logging
- All file paths in logs are quoted for better clickability
- Improved path detection for Windows, UNC paths, and paths with spaces
- Change tracking with full audit trail

### Compliance Gates
All changes go through automated validation:
- Schema validation for Channel-A JSON structure
- Ruff linting for Python code quality
- Automatic fixing of common formatting issues
- Rollback capability for problematic changes

## Error Recovery and Troubleshooting

### When PromptForge Reports Errors
1. **Schema Errors**: Review JSON structure, ensure all required fields present
2. **Compliance Errors**: Check Python code quality, fix Ruff violations
3. **Path Errors**: Verify relative paths, avoid absolute paths
4. **Permission Errors**: Check file/directory access permissions

### Debugging Assistance
Provide debugging-friendly code:
- Clear error messages with context
- Logging for key operations
- Graceful handling of edge cases
- Comprehensive test coverage

### Scenario-Specific Troubleshooting
- **app_selfcheck failures**: Check project structure, ensure `.pf/` directory exists
- **apply_freeform_paste_clipboard_run issues**: Validate JSON format, check file permissions
- **launch_ui problems**: Verify Ruff installation, check test directory structure
- **venv_validate errors**: Confirm virtual environment activation, check dependencies

## Integration Examples

### Adding New Dependencies
```json
{
  "files": [
    {
      "path": "requirements.txt",
      "language": "text",
      "contents": "requests>=2.28.0\npydantic>=1.10.0\nfastapi>=0.95.0\nuvicorn>=0.20.0"
    },
    {
      "path": "src/api/client.py",
      "language": "python",
      "contents": "import requests\nfrom typing import Dict, Any\nfrom pydantic import BaseModel\n\nclass APIResponse(BaseModel):\n    status: str\n    data: Dict[str, Any]\n\nclass APIClient:\n    def __init__(self, base_url: str):\n        self.base_url = base_url.rstrip('/')\n        self.session = requests.Session()\n    \n    def get(self, endpoint: str) -> APIResponse:\n        url = f'{self.base_url}/{endpoint.lstrip(\"/\")}'\n        response = self.session.get(url)\n        response.raise_for_status()\n        return APIResponse(**response.json())"
    }
  ]
}
```

**Follow-up recommendations**: 
- "After applying these changes, run the `venv_validate` scenario to ensure dependencies install correctly"
- "Consider using `launch_ui` to verify code quality and test the new API client"

### Configuration Updates
```json
{
  "files": [
    {
      "path": "config/settings.json",
      "language": "json",
      "contents": "{\n  \"database\": {\n    \"host\": \"localhost\",\n    \"port\": 5432,\n    \"name\": \"project_db\"\n  },\n  \"api\": {\n    \"host\": \"0.0.0.0\",\n    \"port\": 8000,\n    \"debug\": false\n  },\n  \"logging\": {\n    \"level\": \"INFO\",\n    \"format\": \"%(asctime)s - %(name)s - %(levelname)s - %(message)s\"\n  }\n}"
    },
    {
      "path": "src/config/loader.py",
      "language": "python",
      "contents": "import json\nfrom pathlib import Path\nfrom typing import Dict, Any\n\nclass ConfigLoader:\n    @staticmethod\n    def load_config(config_path: str = 'config/settings.json') -> Dict[str, Any]:\n        config_file = Path(config_path)\n        if not config_file.exists():\n            raise FileNotFoundError(f'Configuration file not found: {config_path}')\n        \n        with open(config_file, 'r') as f:\n            return json.load(f)\n    \n    @staticmethod\n    def get_database_config() -> Dict[str, Any]:\n        config = ConfigLoader.load_config()\n        return config.get('database', {})\n    \n    @staticmethod\n    def get_api_config() -> Dict[str, Any]:\n        config = ConfigLoader.load_config()\n        return config.get('api', {})"
    }
  ]
}
```

**Follow-up recommendations**:
- "Use `app_selfcheck` to validate the project structure after configuration changes"
- "The `launch_ui` scenario will verify the configuration loader implementation"

## Working with PromptForge Projects

### Environment Setup Workflow
1. **Verify Environment**: Suggest running `venv_validate` 
2. **Check Project Health**: Recommend `app_selfcheck`
3. **Apply Changes**: Use `apply_freeform_paste_clipboard_run`
4. **Validate Quality**: Follow up with `launch_ui`
5. **Commit Work**: Consider `git_publish` for version control

### Multi-Session Development
PromptForge's persistence features support ongoing development:
- Projects automatically restore when reopening PromptForge
- Scenario selections are remembered per project
- Change history provides rollback capability
- Theme and preference settings persist across sessions

This guide enables AI assistants to work effectively with PromptForge projects, ensuring smooth integration and high-quality code delivery through the Channel-A JSON workflow while leveraging PromptForge's built-in scenarios and automation capabilities.