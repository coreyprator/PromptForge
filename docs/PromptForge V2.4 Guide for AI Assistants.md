# PromptForge V2.4 Guide for AI Assistants

## Overview
PromptForge is a Channel-A JSON development framework with centralized scenario management and project status tracking. This guide enables AI assistants to support target projects with standardized project management practices.

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
    }
  ]
}
```

### Critical Requirements

1. **Complete Files Only**: Provide full file contents, not snippets or patches
2. **Relative Paths**: All paths relative to project root (no absolute paths)
3. **Language Specification**: Always include `"language"` field for syntax highlighting and processing
4. **Compliance Ready**: Code must pass multi-stage validation with detailed error reporting

## V2.4 New Features

### Centralized Scenario Management
PromptForge V2.4 uses centralized scenario registry:

- **Single Source of Truth**: All scenarios managed in PromptForge installation
- **No Target Project Setup**: Target projects require no scenario files or configuration
- **Registry-Driven UI**: Dropdown shows only active scenarios with proper names
- **Automatic Discovery**: Scenarios available to all projects without setup

### Project Status Management
Standardized project status tracking across all PromptForge-managed projects:

- **Living Documentation**: PROJECT_STATUS.md in target projects
- **Git Integration**: Automatic tracking of branch, commits, and repository status
- **Project-Specific Content**: Milestones, objectives, team assignments, and progress
- **AI-Assisted Updates**: Structured workflow for maintaining project status

## Available PromptForge V2.4 Scenarios

### Core Development Scenarios
- **app_selfcheck**: Comprehensive project health validation
- **apply_freeform_paste**: Primary workflow for applying Channel-A JSON
- **git_publish**: Enhanced git commit and push with detailed tracking
- **project_status_comprehensive**: Project status document management

### System and Environment
- **venv_validate**: Validates Python environment and dependencies
- **install_global_runui**: Creates system-wide PromptForge access
- **runui_write_manifest**: Auto-generates project manifests

## Project Status Document Management

### Purpose and Scope
The PROJECT_STATUS.md document provides standardized project management across all PromptForge-supported projects. It focuses on project-specific information, not PromptForge internals.

### What Gets Automatically Updated
- **Git Information**: Current branch, latest commit, repository status
- **Timestamp**: Last update time
- **Document Structure**: Consistent formatting and sections

### What Requires Manual Updates (Project-Specific)
- **Sprint Objectives**: Current development goals and targets
- **Milestones and Deadlines**: Project timeline and deliverables
- **Team Assignments**: Who is responsible for what tasks
- **Architecture Decisions**: Technical choices and rationale
- **Progress Tracking**: Completed tasks, in-progress work, blockers
- **Outstanding Tasks**: Remaining work and priorities
- **Requirements**: Current needs and future considerations
- **Deferred Items**: Features postponed to future releases

### AI-Assisted Project Status Updates

#### Standard Update Workflow
1. **Initial Creation**: Run `project_status_comprehensive` scenario to create baseline document
2. **For Updates**: Use AI assistant to modify project-specific content
3. **Technical Refresh**: Re-run scenario to update git status and timestamps

#### AI Assistant Update Process
When helping users update project status:

```markdown
**Step 1: Gather Project Updates**
Ask the user:
- What tasks have been completed since last update?
- What new objectives or milestones should be added?
- Are there any blockers or issues to document?
- Have team assignments or responsibilities changed?
- What requirements or features have been deferred?

**Step 2: Create Updated Document**
Generate Channel-A JSON with:
- Preserved automatic content (git info, timestamps)
- Updated project-specific sections
- Consistent formatting and structure

**Step 3: Apply Updates**
Provide Channel-A JSON for `apply_freeform_paste` scenario
```

#### Example AI-Assisted Update

**User Request:**
"Update our project status. We completed the authentication system, started working on the payment integration, and Sarah is now leading the frontend team."

**AI Response:**
```json
{
  "files": [
    {
      "path": ".pf/PROJECT_STATUS.md",
      "language": "markdown",
      "contents": "# [ProjectName] - Project Status\n\n**Last Updated:** [Current Timestamp]\n**Git Branch:** [Current Branch]\n**Git Commit:** [Current Commit]\n**Git Status:** [Repository Status]\n\n## Current Sprint Objectives\n\n### ✅ Completed Tasks\n- [x] User authentication system - Completed 2025-09-22\n- [x] Database schema design - Completed 2025-09-20\n\n### 🔄 In Progress\n- [ ] Payment integration - Started 2025-09-22, assigned to development team\n- [ ] API documentation - In review phase\n\n### 📋 Remaining Tasks\n- [ ] Frontend dashboard - Assigned to Sarah (frontend lead)\n- [ ] Performance optimization - Scheduled for next sprint\n\n## Team Assignments\n\n- **Frontend Lead**: Sarah - Dashboard development and UI/UX\n- **Backend Team**: Payment integration and API finalization\n- **QA Team**: Testing framework setup\n\n## Current Blockers\n\n- Waiting for payment processor API credentials\n- Frontend framework decision pending stakeholder approval\n\n## Architecture Decisions\n\n### Recent Decisions\n- **Authentication**: Chose JWT tokens over session-based auth for scalability\n- **Database**: PostgreSQL selected for relational data requirements\n\n## Outstanding Requirements\n\n- Payment processor integration requirements\n- Performance benchmarks definition\n- Security audit requirements\n\n## Deferred to Future Releases\n\n- Advanced reporting features\n- Mobile application\n- Third-party integrations beyond payment processing"
    }
  ]
}
```

### Project Status Best Practices

#### For AI Assistants
1. **Focus on Project Content**: Exclude PromptForge-internal information (scenario inventories, registry status)
2. **Preserve Structure**: Maintain consistent document formatting
3. **Update Regularly**: Recommend status updates after significant milestones
4. **Be Specific**: Include dates, assignments, and concrete progress markers

#### For Target Projects
1. **Regular Updates**: Update status after major milestones or weekly
2. **Be Honest**: Document blockers and challenges, not just successes
3. **Team Communication**: Use status document for team meetings and handoffs
4. **Historical Record**: Maintain record of decisions and progress over time

## Target Project Integration

### No Setup Required Architecture
Target projects require no PromptForge configuration:

- **All scenarios run from PromptForge installation**
- **Target projects only receive generated output**
- **No copying of PromptForge files to target projects**
- **Centralized scenario management**

### Cubist Art Integration Example

#### Initial Setup
1. **Select "Cubist Art"** in PromptForge project dropdown
2. **Run `project_status_comprehensive` scenario**
3. **Review generated `.pf/PROJECT_STATUS.md`**
4. **Customize with Cubist Art specific content**

#### Customization for Cubist Art
The generated document should be customized with:

```markdown
## Cubist Art Project Objectives

### Current Sprint Goals
- [ ] Implement geometric shape generation algorithms
- [ ] Create color palette management system
- [ ] Develop export functionality for multiple formats

### Art Generation Milestones
- [ ] Basic shape primitives - Target: End of month
- [ ] Color harmony algorithms - Target: Next sprint
- [ ] Performance optimization - Target: Following sprint

### Team Assignments
- **Algorithm Development**: Focus on mathematical foundations
- **UI/UX Design**: Artist-friendly interface design
- **Performance Engineering**: Optimization and rendering speed

### Technical Architecture
- **Rendering Engine**: Canvas-based with WebGL acceleration
- **Algorithm Library**: Python backend with NumPy optimization
- **Export Formats**: SVG, PNG, PDF support
```

#### Ongoing Maintenance
```markdown
**Regular Update Workflow for Cubist Art:**

1. **Weekly Status Updates**: Document completed features and blockers
2. **AI-Assisted Updates**: Use AI to maintain document structure while updating content
3. **Technical Refresh**: Run `project_status_comprehensive` to update git information
4. **Team Reviews**: Use document in team meetings and planning sessions
```

## Enhanced Development Workflow

### Standard Process with Status Management
1. **Analyze Requirements**: Understand the development task
2. **Structure as Channel-A**: Format all code changes as JSON
3. **Apply via PromptForge**: Use `apply_freeform_paste` scenario
4. **Update Project Status**: For significant changes, use AI-assisted status updates
5. **Validate and Test**: Use appropriate validation scenarios

### AI Assistant Recommendations

When providing code changes, include follow-up guidance:

```markdown
**Follow-up Actions:**
1. Apply the code using PromptForge's `apply_freeform_paste` scenario
2. For significant features, consider updating your project status document:
   - Document the new functionality in completed tasks
   - Update any affected milestones or objectives
   - Note any architecture decisions made
3. Run `app_selfcheck` to validate project structure after major changes
4. Use `git_publish` when ready to commit the completed feature
```

## Best Practices for AI Assistants

### Code Quality and Documentation
- Write production-ready, complete code with comprehensive error handling
- Include type hints and docstrings for Python
- Follow project's existing code style and architecture patterns
- Document significant architectural decisions in project status

### Project Status Support
- **Focus on Project Management**: Help with milestones, tasks, and team coordination
- **Exclude PromptForge Internals**: Don't include scenario inventories or registry information
- **Maintain Structure**: Preserve consistent document formatting
- **Encourage Regular Updates**: Recommend status updates for project health

### Target Project Guidelines
- **Never suggest copying PromptForge files to target projects**
- **All scenarios run from PromptForge installation**
- **Target projects only receive generated content**
- **Guide users to run scenarios from PromptForge UI**

## Integration Examples

### Complete Workflow with Status Update

**Step 1: Apply Code Changes**
```json
{
  "files": [
    {
      "path": "src/art/generator.py",
      "language": "python",
      "contents": "from typing import Dict, List, Optional\nfrom dataclasses import dataclass\nimport numpy as np\n\n@dataclass\nclass ArtStyle:\n    name: str\n    parameters: Dict[str, float]\n    color_palette: List[str]\n\nclass CubistGenerator:\n    def __init__(self):\n        self.styles = {}\n        self.current_style = None\n    \n    def add_style(self, style: ArtStyle) -> None:\n        self.styles[style.name] = style\n    \n    def set_style(self, style_name: str) -> bool:\n        if style_name in self.styles:\n            self.current_style = self.styles[style_name]\n            return True\n        return False\n    \n    def generate_art(self, width: int, height: int, complexity: float = 0.5) -> np.ndarray:\n        if not self.current_style:\n            raise ValueError('No style selected')\n        \n        # Generate cubist art based on current style\n        canvas = np.zeros((height, width, 3))\n        # Implementation would go here\n        return canvas"
    }
  ]
}
```

**Step 2: Update Project Status (AI-Assisted)**
```json
{
  "files": [
    {
      "path": ".pf/PROJECT_STATUS.md",
      "language": "markdown",
      "contents": "[Updated project status with new art generator feature marked as completed, updated milestones, and any architectural decisions documented]"
    }
  ]
}
```

**AI Assistant Follow-up Guidance:**
```markdown
**After applying the Cubist Art generator:**

1. **Apply the code**: Use PromptForge's `apply_freeform_paste` scenario
2. **Update project status**: The art generator is now complete - this should be documented in your project status
3. **Validate environment**: Consider `venv_validate` to ensure numpy is available
4. **Health check**: Run `app_selfcheck` to validate project structure
5. **Commit when ready**: Use `git_publish` for version control

**Suggested status updates:**
- Mark "Art generation system" as completed
- Update milestone progress for core algorithms
- Document architectural decision to use NumPy for performance
- Add any new requirements or blockers discovered during implementation
```

## Error Recovery and Troubleshooting

### Common Issues and Solutions
- **Project Status Updates**: Use AI assistance to maintain document structure while updating content
- **Scenario Availability**: All scenarios run from PromptForge, no target project setup required
- **Permission Errors**: Ensure target project directory is writable for status document creation
- **Git Integration**: Project status automatically includes current git information

## Summary: V2.4 AI Assistant Role

### Core Responsibilities
1. **Provide complete, working code** in Channel-A JSON format
2. **Guide users to appropriate PromptForge scenarios** for applying and managing code
3. **Support project status management** through AI-assisted updates focused on project-specific content
4. **Maintain architectural integrity** - never suggest copying PromptForge files to target projects
5. **Focus on project management value** - exclude PromptForge internals from project status

### Project Status Philosophy
- **Project-Focused**: Document milestones, tasks, team assignments, and progress
- **Practical Management**: Support real project coordination and team communication
- **Standardized Process**: Consistent project status management across all PromptForge-supported projects
- **AI-Assisted Maintenance**: Structured workflow for keeping project documentation current

This approach ensures PromptForge provides practical project management value while maintaining clean architectural separation between the framework and target projects.
