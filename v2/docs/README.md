# PromptForge V2 — GUI‑first E2E

This package gives you a **single path through the whole stack** (GUI → core → provider → validation → review), so we always test the real chain.

## Architecture (clean splits)

- **promptforge_core/**
  - `builder.py` – turns *(Task + Scenario + Rules + Sentinels + Output Contract)* into SYSTEM/USER messages.
  - `output_schema.py` – the **single source of truth** JSON schema for Channel‑A (`files[]`).
  - `validator.py` – validates Channel‑A responses against the schema.
- **promptforge_providers/**
  - `openai_client.py` – calls OpenAI (or returns a deterministic **mock** when the API is unavailable). Pluggable for future providers.
- **promptforge_cli/**
  - `pf gui` – launches the GUI.
  - `pf make` – prints SYSTEM+USER preview for a task (useful in terminal or for scripting).
  - `pf bridge` – placeholder for the tiny HTTP server (next sprint).
- **promptforge_gui/**
  - `app.py` – **tabbed GUI**: Prompt · Rules · Sentinels · Output Contract · Scenarios · History · Help.
  - GUI shows **version + timestamp** in the title so you always know what you’re running.

## Channels (the contract with models)

- **Channel‑A (Structured)** – returns a **strict JSON payload**:
  ```json
  {
    "files": [
      {"path": "src/example/hello.py", "language": "python", "contents": "print('hello')\n"}
    ]
  }
  ```
  - The GUI’s **Validate Reply** checks this schema locally.
  - On **Call Model (A)**, we enforce JSON (when possible) and **always** re‑validate.
  - If the provider isn’t configured, the call returns a **deterministic mock** so the GUI still works E2E.

- **Channel‑B (Prose)** – free‑form text for rationale, decisions, risks, review notes.
  - On **Prose (B)**, we call the provider (or return a mock) and show the prose in the Review pane.

## Install / Run

1. **Python 3.12 only** (we pin via `pf_setup_v2_pin312.ps1`).
2. Install V2 from your repo (editable) and ensure shims exist:
   ```powershell
   C:\venvs\promptforge-v2\Scripts\python.exe -m pip install -e "G:\My Drive\Code\Python\PromptForge\v2"
   .\v2\scripts\pf.ps1 gui
   ```
3. (Optional) Enable OpenAI provider:
   ```powershell
   C:\venvs\promptforge-v2\Scripts\python.exe -m pip install openai
   $env:OPENAI_API_KEY = "<your key>"
   ```
   For persistence, see **Environment** below.

## Environment

- **Never commit secrets.** Add `.env` to `.gitignore` (see checklist below).
- To persist keys without editing code, run the helper once:
  ```powershell
  pwsh -NoProfile -ExecutionPolicy Bypass -File .\v2\scripts\pf_enable_dotenv.ps1 `
    -RepoRoot "G:\My Drive\Code\Python\PromptForge" `
    -Venv "C:\venvs\promptforge-v2"
  ```
  This creates a `sitecustomize.py` in your venv that automatically loads `G:\My Drive\Code\Python\PromptForge\.env`
  on every run of that interpreter.

- Alternative (Windows user env):
  ```powershell
  setx OPENAI_API_KEY "<your key>"
  ```
  Restart your terminal after `setx`.

## GUI walkthrough

- **Prompt tab**
  - Pick a **Scenario**, type a **Task**.
  - **Build Prompt** – preview SYSTEM and USER.
  - **Call Model (A)** – expects JSON; output goes to the left pane; parsed file list in Review.
  - **Prose (B)** – provider (or mock) returns free‑form rationale in Review.
  - **Validate Reply** – paste JSON into left pane and validate against `files[]`.
  - **Insert JSON Example** – drops a valid example for quick tests.

- **Rules / Sentinels / Output Contract**
  - Rules: scenario‑specific system constraints (one per line).
  - Sentinels: `start` and `end` markers if you want wraps (used for legacy models; optional now).
  - Output Contract: current format (`json`) and schema name (`files_payload`).

- **Scenarios**
  - Add/remove/rename scenarios and edit their system rules.
  - Save persists to `.promptforge/config.json` (kept out of Git by default).

- **History**
  - Reads `seeds/prompts.json` (if present) and newest `seeds/backups/*/prompts.json` for quick recall.

- **Help**
  - Quick reference of the above.

## Roadmap (short)

- **Apply to workspace** (next ZIP): preview per file → backup → write → undo.
- **HTTP Bridge**: `/v1/chat/structured` + `/v1/chat/prose` so GUI/VS Code share a common local API.
- **Compliance loop**: auto‑retry with correction prompts when schema fails.
- **Provider plugins**: Anthropic next; config toggle in GUI.

## Checklist (do once per machine)

- [ ] Python 3.12 installed; venv at `C:\venvs\promptforge-v2`.
- [ ] `.\v2\scripts\pf.ps1 gui` launches the GUI.
- [ ] `openai` installed into the venv **if** you want live calls.
- [ ] `.env` exists **but is not committed**; `.gitignore` contains `.env`.
- [ ] Optional: run `pf_enable_dotenv.ps1` to auto‑load `.env` every run.
