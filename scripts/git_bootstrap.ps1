param(
  [string]$RepoRoot = "G:\My Drive\Code\Python\PromptForge",
  [string]$Remote = "https://github.com/coreyprator/PromptForge.git",
  [string]$UserName = "",
  [string]$UserEmail = ""
)
$ErrorActionPreference = "Stop"

Push-Location $RepoRoot
try {
  if ($UserName) { git config user.name $UserName }
  if ($UserEmail) { git config user.email $UserEmail }

  if (-not (Test-Path ".git")) {
    git init
  }

  # Ensure default branch 'main'
  git checkout -B main

  # Set remote origin (idempotent)
  $hasOrigin = (git remote) -contains "origin"
  if (-not $hasOrigin) {
    git remote add origin $Remote
  } else {
    git remote set-url origin $Remote
  }

  git add -A
  git commit -m "chore: bootstrap PromptForge repo" --allow-empty
  git push -u origin main
  Write-Host "Repository bootstrapped and pushed to $Remote" -ForegroundColor Green
}
finally { Pop-Location }
