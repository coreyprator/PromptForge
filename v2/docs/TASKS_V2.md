# PromptForge V2 — Tasks & Milestones

## Now (V2.1)

- [ ] **Apply flow (GUI)**
  - [ ] Right‑pane list of returned files with checkboxes
  - [ ] Diff preview (current vs. proposed)
  - [ ] Write selected files; backup originals under `.promptforge/out/patches/<timestamp>/`
  - [ ] Undo last apply

- [ ] **Bridge (local HTTP)**
  - [ ] `/v1/chat/structured` → returns `{ files, warnings }`
  - [ ] `/v1/chat/prose` → returns `{ content }`
  - [ ] Config: port and provider selection

- [ ] **Compliance loop**
  - [ ] If Channel‑A invalid → auto compose “correction prompt” and retry (N strikes)
  - [ ] Display compliance log in Review

- [ ] **Provider options in GUI**
  - [ ] OpenAI / Anthropic dropdown
  - [ ] Model name text box
  - [ ] “Test provider” button

## Soon (V2.2)

- [ ] **VS Code handshake**
  - [ ] Minimal commands/tasks to call the bridge
  - [ ] Read‑write workspace gateway with guardrails
  - [ ] Status bar indicator for Bridge

- [ ] **Prompt seeds lifecycle**
  - [ ] Append to `seeds/prompts.json` from GUI
  - [ ] Export/Import seeds
  - [ ] Wire into `publish_all.ps1` pre‑commit step

- [ ] **Tooltips & inline help**
  - [ ] Hover text on key widgets
  - [ ] F1 opens local docs

## Later

- [ ] **Multi‑agent supervision**
- [ ] **Project templates** for common stacks (fastapi, streamlit, node, etc.)
- [ ] **Team mode** (shared seeds/config, role‑based apply privileges)

---

## Acceptance checks

- [ ] GUI can generate valid Channel‑A payload and **Apply** it to repo safely.
- [ ] Bridge accepts both channels and returns within contract.
- [ ] Compliance loop shows reasons + retries when schema fails.
- [ ] Provider dropdown switches backends without GUI code changes.
