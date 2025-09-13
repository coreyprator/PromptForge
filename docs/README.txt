
PromptForge GitHub Automation Scripts
=====================================

Files:
- archive_source.ps1  — structure-preserving ZIP of the repo (excludes .promptforge/out)
- git_bootstrap.ps1   — initializes repo, sets remote to https://github.com/coreyprator/PromptForge.git, pushes main
- publish_all.ps1     — RIFF (Ruff format + fix), pytest, archive, commit, tag, push — one command

Quick start:
1) Open PowerShell 7
2) Set execution policy once if needed:
   Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

3) Bootstrap the repo (idempotent):
   pwsh /mnt/data/promptforge_scripts/git_bootstrap.ps1 -RepoRoot "G:\My Drive\Code\Python\PromptForge"

4) Publish a milestone (creates a branch, tags, pushes):
   pwsh /mnt/data/promptforge_scripts/publish_all.ps1 -RepoRoot "G:\My Drive\Code\Python\PromptForge" -Milestone "V1 baseline" -NewBranch -AutoTag

Notes:
- Scripts will install ruff/pytest if they are missing.
- Archive output goes to 'handoff/' in your repo by default.
