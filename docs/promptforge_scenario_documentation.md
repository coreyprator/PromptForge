# PromptForge V2.2 Scenario Documentation

## Scenario Documentation Standards

Each scenario follows this documentation structure:

### Standard Format
- **Purpose**: What the scenario accomplishes
- **Requirements**: Prerequisites and dependencies
- **Input Format**: Expected data/clipboard content
- **User Steps**: Step-by-step execution process
- **Success Criteria**: How to identify successful completion
- **Failure Modes**: Common failure cases and troubleshooting
- **Log Output**: Expected log patterns and interpretation
- **Related Scenarios**: Workflow connections

### Log Interpretation Guidelines
- **Project Context**: `Project root: "[path]"` identifies current project
- **Scenario Execution**: `[scenario_name] OK` or `[scenario_name] FAIL (code)`
- **Timestamp Format**: Standard PowerShell execution timestamps
- **Error Details**: Specific error messages for debugging

---

## Core Development Scenarios

### scenario_app_selfcheck
**Purpose**: Validates core PromptForge installation and project structure integrity

**Requirements**:
- Project must have `.pf/` directory structure
- Core PromptForge files must be present
- Valid project configuration

**Input Format**: None (system validation)

**User Steps**:
1. Select target project in PromptForge
2. Choose "app_selfcheck" scenario
3. Click "Run Scenario"

**Success Criteria**:
- All core files validated
- Project structure confirmed
- Configuration files accessible

**Failure Modes**:
- Missing `.pf/` directory
- Corrupted core files
- Invalid project structure

**Log Output**:
```
[app_selfcheck] OK
Self-check: PASS - All core components verified
```

---

### scenario_apply_freeform_paste_clipboard_run
**Purpose**: Processes Channel-A JSON or freeform code blocks from clipboard into project files

**Requirements**:
- Valid content in system clipboard
- Target project selected
- Write permissions to project directory

**Input Format**:
```json
{
  "files": [
    {
      "path": "relative/path/file.py",
      "language": "python",
      "contents": "# Complete file contents"
    }
  ]
}
```
OR freeform code blocks with `>>>FILE` delimiters

**User Steps**:
1. Copy Channel-A JSON or freeform content to clipboard
2. Select target project
3. Choose "apply_freeform_paste_clipboard_run" scenario
4. Click "Run Scenario"

**Success Criteria**:
- Files written to specified paths
- Compliance gates passed
- Change journal entry created

**Failure Modes**:
- Invalid JSON format
- Compliance gate failures
- Path permission errors
- Missing file language specifications

**Log Output**:
```
[apply_freeform_paste_clipboard_run] OK
WROTE: path/to/file.py
WROTE: path/to/file2.js
Project root: "[project_path]"
```

**Related Scenarios**: `launch_ui`, `venv_validate`

---

### scenario_launch_ui
**Purpose**: Executes code quality checks using Ruff and project test suites

**Requirements**:
- Ruff installed and accessible (optional)
- Python files in project
- Tests directory (optional)

**Input Format**: None (project file scanning)

**User Steps**:
1. Ensure code changes are saved
2. Select target project
3. Choose "launch_ui" scenario
4. Click "Run Scenario"

**Success Criteria**:
- All Python files pass Ruff linting (if available)
- Tests pass (if present)
- No critical code quality issues

**Failure Modes**:
- Linting errors requiring fixes
- Test failures
- Missing dependencies

**Log Output**:
```
[launch_ui] OK
Running ruff check ...
Running pytest -q ...
```

---

### scenario_venv_validate
**Purpose**: Validates Python virtual environment setup and dependencies

**Requirements**:
- Python virtual environment configured
- Project requirements.txt or pyproject.toml
- pip/poetry accessible

**Input Format**: None (environment introspection)

**User Steps**:
1. Activate desired virtual environment
2. Select target project
3. Choose "venv_validate" scenario
4. Click "Run Scenario"

**Success Criteria**:
- Virtual environment active and valid
- Required packages installed
- Python version compatibility confirmed

**Failure Modes**:
- No virtual environment active
- Missing dependencies
- Version conflicts

**Log Output**:
```
[venv_validate] OK
Python version: 3.12.x
Virtual environment: [path]
Dependencies: OK
```

---

### scenario_git_publish
**Purpose**: Automated git workflow for committing and pushing changes

**Requirements**:
- Git repository initialized
- Staged or unstaged changes
- Remote repository configured

**User Steps**:
1. Make code changes
2. Select target project
3. Choose "git_publish" scenario
4. Click "Run Scenario"

**Success Criteria**:
- Changes committed with descriptive message
- Successfully pushed to remote
- Clean git status

**Failure Modes**:
- No changes to commit
- Merge conflicts
- Remote push failures

**Log Output**:
```
[git_publish] OK
Committed: [commit_hash]
Pushed to: origin/branch_name
```

---

## System Installation Scenarios

### scenario_install_global_runui
**Purpose**: System-wide PowerShell installation enabling `runui` command from any project

**Requirements**:
- PowerShell execution policy allowing scripts
- Write access to PowerShell profile
- PromptForge project structure

**User Steps**:
1. Select PromptForge project
2. Choose "install_global_runui" scenario
3. Click "Run Scenario"
4. Restart PowerShell to activate

**Success Criteria**:
- `runui` function available globally
- PowerShell profile updated with PromptForge functions
- Command works from any project directory

**Failure Modes**:
- PowerShell execution policy restrictions
- Profile write permission errors
- Missing helper components

**Log Output**:
```
[install_global_runui] OK
Installed RunUI helper to: [path]
Updated profiles: [profile_paths]
```

**Related Scenarios**: `runui_write_manifest` (auto-called)

---

## Development/Debug Scenarios

### scenario_install_gui_from_sample
**Purpose**: Installs PromptForge UI components from pre-built sample payload

**Requirements**:
- Sample payload file exists in `v2/samples/`
- Target project structure prepared
- Apply permissions

**User Steps**:
1. Ensure project is properly initialized
2. Select target project
3. Choose "install_gui_from_sample" scenario
4. Click "Run Scenario"

**Success Criteria**:
- UI components installed from sample
- Self-check passes after installation
- PromptForge ready for use

**Failure Modes**:
- Missing sample payload
- Apply operation failures
- Post-install validation errors

**Log Output**:
```
[install_gui_from_sample] OK
Applied sample payload
Self-check: PASS
```

---

### scenario_runui_debug_here
**Purpose**: Launch project UI with Python debug flags for troubleshooting

**Requirements**:
- Python executable accessible
- Project has app.py or equivalent
- Debug flags supported

**User Steps**:
1. Select project with UI issues
2. Choose "runui_debug_here" scenario
3. Click "Run Scenario"
4. Observe debug output

**Success Criteria**:
- UI launches with enhanced debugging
- Detailed error information available
- Debug flags properly applied

**Failure Modes**:
- Missing UI entry point
- Python execution errors
- Debug flag incompatibility

**Log Output**:
```
[runui_debug_here] OK
[debug] using: [python_path]
[debug] app.py exited rc=0
```

---

## Background System Scenarios

### scenario_runui_write_manifest
**Purpose**: Auto-generates `.pf/runui.json` manifest by detecting project type

**Note**: This scenario is called automatically by `install_global_runui` and typically not run directly by users.

**Requirements**:
- Project structure analysis
- Write permissions to `.pf/` directory
- Detectable entry points (app.py, package.json, etc.)

**Success Criteria**:
- Manifest file created with correct project detection
- Entry point properly identified
- Compatible with global runui system

**Failure Modes**:
- Unable to detect project type
- No suitable entry points found
- Manifest write errors

**Log Output**:
```
[runui_write_manifest] OK
Wrote ./.pf/runui.json
```

---

## Enhanced Documentation Access (V2.3 Planned)

### Scenario Help Panel
**Planned Feature**: Dedicated documentation panel showing formatted scenario information

**Functionality**:
- Rich HTML formatting for better readability
- Real-time updates based on selected scenario
- Scrollable content for detailed information
- Integration with existing PromptForge UI

**Benefits**:
- Eliminates plain text tooltip limitations
- Provides comprehensive scenario guidance
- Improves user experience and discoverability

---

## Scenario Development Guidelines

### Creating New Scenarios
1. **Naming Convention**: `scenario_[descriptive_name].ps1`
2. **PowerShell Structure**:
   ```powershell
   param([string]$ProjectRoot)
   # Validation and setup
   # Main scenario logic
   # Success/failure reporting
   ```
3. **Error Handling**: Always use try-catch with meaningful messages
4. **Logging**: Include project context and clear success/failure indicators
5. **Documentation**: Follow standard format above

### Scenario Categories
- **Core Development**: Primary user workflows
- **System Installation**: One-time setup scenarios
- **Development/Debug**: Troubleshooting and development support
- **Background/System**: Auto-called scenarios not directly user-facing

---

## Multi-Environment Considerations

### Laptop/Desktop Synchronization
Current workflow using Google Drive mirroring is appropriate for single-user scenarios:

- **State File Synchronization**: `.pf/global_state.json` syncs across machines
- **Project Path Adaptation**: Manual path updates when switching environments
- **Virtual Environment Handling**: Per-machine venv setup with `venv_validate`

### State File Management
State files are frequently updated during normal operation:

- **Automatic Backup**: Consider implementing state backup before major operations
- **Recovery Capability**: Graceful degradation when state files are missing
- **Cross-Machine Compatibility**: Path adaptation for different drive layouts

## V2.3 Enhancement Planning

### Enhanced Documentation Access
- **Scenario Help Panel**: Rich formatted documentation display
- **Interactive Tooltips**: HTML-based tooltips with proper formatting
- **Context-Sensitive Help**: Dynamic help based on current selections

### Advanced Scenario Management
- **AI-Assisted Creation**: Natural language to PowerShell scenario generation
- **Validation Framework**: Automated scenario testing and validation
- **Template System**: Reusable scenario templates for common patterns