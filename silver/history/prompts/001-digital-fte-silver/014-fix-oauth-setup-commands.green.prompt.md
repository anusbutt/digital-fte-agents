---
id: 014
title: Fix OAuth Setup Commands
stage: green
date: 2026-03-08
surface: agent
model: claude-sonnet-4-6
feature: 001-digital-fte-silver
branch: 001-digital-fte-silver
user: PC
command: "yes. do it then explain in simple terms. what you have done."
labels: ["oauth", "bugfix", "setup", "gmail", "email-mcp"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - main.py
tests:
  - manual: python main.py setup gmail (verify no AttributeError)
  - manual: python main.py setup email-mcp (verify token-mcp.json created)
---

## Prompt

yes. do it then explain in simple terms. what you have done.

## Response snapshot

Fixed two bugs in main.py:

1. **Bug fix**: `_setup_gmail()` was calling `watcher._authenticate()` (an instance method that doesn't exist on GmailWatcher). Fixed to import and call the module-level `_authenticate()` function directly with `interactive=True`.

2. **New command**: Added `_setup_email_mcp()` function that runs the OAuth2 consent flow with the correct scopes (`gmail.send` + `gmail.compose`) and saves the result to `token-mcp.json`. Added `email-mcp` as a valid choice in the CLI parser and dispatcher.

Commands now work as:
- `python main.py setup gmail` → generates `token.json` (read/modify scopes)
- `python main.py setup email-mcp` → generates `token-mcp.json` (send/compose scopes)

## Outcome

- ✅ Impact: `setup gmail` no longer crashes; `setup email-mcp` now exists and generates the correct token
- 🧪 Tests: Manual verification required (needs credentials.json present)
- 📁 Files: main.py (2 functions modified, 1 function added, 1 parser choice added)
- 🔁 Next prompts: Run setup commands with real credentials.json to verify end-to-end
- 🧠 Reflection: Root cause was that module-level function was confused for instance method. The MCP token gap was a design oversight — two separate OAuth flows needed for read vs send scopes.

## Evaluation notes (flywheel)

- Failure modes observed: AttributeError on setup gmail; FileNotFoundError on email-mcp startup
- Graders run and results (PASS/FAIL): static code review PASS
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): add integration test that mocks the OAuth flow
