# Implementation Plan: Digital FTE Silver — Functional Assistant

**Branch**: `001-digital-fte-silver` | **Date**: 2026-02-18 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/001-digital-fte-silver/spec.md`

## Summary

Upgrade Digital FTE from Bronze (filesystem-only) to Silver (multi-channel). Add Gmail polling watcher, WhatsApp Playwright watcher, LinkedIn Playwright poster, Node.js/TypeScript email-mcp server, extended HITL approval workflow, PM2 process management, and Windows Task Scheduler integration. Restructure vault into `vault/` subdirectory. All AI capabilities as Agent Skills.

## Technical Context

**Language/Version**: Python 3.13+ (watchers, orchestrator), Node.js v24+ with TypeScript (email-mcp)
**Primary Dependencies**: watchdog, python-dotenv, google-auth-oauthlib, google-api-python-client, playwright, @modelcontextprotocol/sdk, googleapis (npm)
**Storage**: Local Markdown files in Obsidian vault (`vault/` directory)
**Testing**: pytest (Python), manual integration tests, DRY_RUN mode
**Target Platform**: Windows 11
**Project Type**: Single project (Python + Node.js/TypeScript MCP sidecar)
**Performance Goals**: Gmail detection <3min, WhatsApp detection <1min, LinkedIn daily post
**Constraints**: Local-only, no cloud. OAuth2 for Gmail. Playwright sessions for WhatsApp/LinkedIn.
**Scale/Scope**: Single user, 3 watchers + 1 orchestrator + 1 MCP server, ~15 files modified/created

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Local-First Privacy | PASS | All data in `vault/`. Secrets in `.env`. No cloud storage. |
| II. Perception-Reasoning-Action | PASS | Watchers (perception) → Claude skills (reasoning) → MCP/Playwright (action). No layer bypass. |
| III. Human-in-the-Loop | PASS | Sensitive actions → `vault/Pending_Approval/`. WhatsApp/LinkedIn always require approval. Auto-send only non-sensitive email replies. |
| IV. Agent Skills First | PASS | All AI capabilities as `.md` skill files. No inline prompts in Python. |
| V. Watcher Resilience | PASS | PM2 for auto-restart. Exponential backoff. Structured logging via `logger.py`. |
| VI. Vault-as-Protocol | PASS | File movement = state transitions. YAML frontmatter on all vault files. Fixed folder names. |
| VII. Observability and Audit | PASS | All actions logged via `logger.py` to `vault/Logs/YYYY-MM-DD.md`. |
| VIII. Spec-Driven Development | PASS | Following SDD lifecycle: Constitution → Spec → Plan → Tasks → Implementation. |

**Gate Result**: ALL PASS. Proceeding to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/001-digital-fte-silver/
├── plan.md              # This file
├── research.md          # Phase 0: technology decisions
├── data-model.md        # Phase 1: entity schemas
├── quickstart.md        # Phase 1: setup and run guide
└── tasks.md             # Phase 2 (/sp.tasks)
```

### Source Code (repository root)

```text
silver/
├── vault/                          # Obsidian vault (separated from code)
│   ├── Inbox/                      # File drops
│   ├── Needs_Action/               # Triaged items (EMAIL_, WHATSAPP_, FILE_)
│   ├── Plans/                      # ActionPlans
│   ├── Pending_Approval/           # HITL approval requests
│   ├── Approved/                   # Human-approved actions
│   ├── Rejected/                   # Human-rejected actions
│   ├── Done/                       # Completed items
│   ├── Briefings/                  # CEO briefings
│   ├── Accounting/                 # Financial documents
│   ├── Logs/                       # Audit logs (YYYY-MM-DD.md)
│   ├── Dashboard.md                # Real-time status
│   ├── Company_Handbook.md         # Business rules
│   └── Business_Goals.md           # Strategic goals
│
├── watchers/                       # Python perception layer
│   ├── __init__.py
│   ├── base_watcher.py             # Abstract base (existing, updated)
│   ├── filesystem_watcher.py       # Inbox monitor (existing, path update)
│   ├── gmail_watcher.py            # NEW: Gmail API polling
│   ├── whatsapp_watcher.py         # NEW: WhatsApp Web via Playwright
│   ├── orchestrator.py             # Extended for EMAIL_/WHATSAPP_ types
│   └── logger.py                   # Audit logging (existing)
│
├── skills/                         # Agent Skills (.md)
│   ├── triage-inbox.md             # Updated: handle EMAIL_, WHATSAPP_ types
│   ├── update-dashboard.md         # Updated: new item types in summary
│   ├── generate-briefing.md        # Existing (path update)
│   ├── process-approval.md         # Updated: email_send, whatsapp_reply, linkedin_post actions
│   ├── compose-email-reply.md      # NEW: draft email reply content
│   ├── compose-whatsapp-reply.md   # NEW: draft WhatsApp reply content
│   └── generate-linkedin-post.md   # NEW: generate daily LinkedIn post
│
├── email-mcp/                      # NEW: Node.js MCP server (TypeScript)
│   ├── package.json
│   ├── tsconfig.json               # TypeScript configuration
│   ├── index.ts                    # MCP server with send_email + draft_email tools
│   └── .env.example
│
├── scripts/                        # NEW: Scheduling and management
│   ├── linkedin_post.py            # LinkedIn Playwright poster
│   ├── setup_scheduler.py          # Windows Task Scheduler setup
│   └── pm2_ecosystem.config.js     # PM2 process configuration
│
├── pyproject.toml                  # Updated: new dependencies
├── .env.example                    # Updated: new env vars
├── .gitignore                      # Updated: vault/Logs/, node_modules/
├── main.py                         # Updated: entry point
└── test_data/                      # Test files
```

**Structure Decision**: Single project with Python root + Node.js/TypeScript sidecar (`email-mcp/`). This matches the Bronze pattern (flat Python modules) while adding the required Node.js MCP server (written in TypeScript, executed via `tsx`) as a self-contained subdirectory. No monorepo tooling needed.

## Architecture Decisions

### AD-1: Vault Restructuring Strategy

**Decision**: Move all vault folders and documents into `vault/` subdirectory. Update all path references in watchers and orchestrator.

**Approach**:
1. Create `vault/` directory
2. Move folders: Inbox, Needs_Action, Plans, Pending_Approval, Approved, Rejected, Done, Briefings, Accounting, Logs
3. Move documents: Dashboard.md, Company_Handbook.md, Business_Goals.md
4. Update all Python code to reference `vault/` as base path
5. Update `.env.example` with `VAULT_PATH=./vault`
6. Update `.gitignore` for new paths

**Rationale**: Constitution Principle I requires separation. Obsidian opens `vault/` as its root — no code files visible.

### AD-2: Gmail Watcher — Polling Architecture

**Decision**: Python watcher using Google Gmail API with OAuth2. Polls every 60 seconds for unread messages.

**Approach**:
1. Extend `BaseWatcher` with `GmailWatcher` class
2. Use `google-api-python-client` + `google-auth-oauthlib` for OAuth2
3. Query: `is:unread -category:promotions -category:social -category:updates -category:forums`
4. Filter out OTPs (subject contains "OTP", "verification code", "one-time")
5. Filter out newsletters (has `List-Unsubscribe` header or known sender patterns)
6. For actionable emails: create `EMAIL_{message_id}.md` in `vault/Needs_Action/`
7. Mark processed emails as read after creating vault item
8. Store `credentials.json` path and `token.json` path in `.env`

**Error Handling**:
- 401: Log, pause, alert Dashboard
- 429: Exponential backoff (2s, 4s, 8s, max 300s)
- Network timeout: Skip cycle, retry next interval

### AD-3: WhatsApp Watcher — Playwright Scraping

**Decision**: Python watcher using Playwright to scrape WhatsApp Web for new messages.

**Approach**:
1. Extend `BaseWatcher` with `WhatsAppWatcher` class
2. Launch Chromium with persistent context (reuse logged-in session)
3. Poll every 30 seconds: scan unread chat indicators
4. For each unread chat: read latest messages, check for business keywords
5. Keywords: `urgent, invoice, payment, pricing, help, quote, project, deadline`
6. For keyword matches: create `WHATSAPP_{contact}_{timestamp}.md` in `vault/Needs_Action/`
7. Track processed messages by contact+timestamp to avoid duplicates

**Session Management**:
- Store Playwright user data dir in `.env` (`WHATSAPP_USER_DATA_DIR`)
- On session expiry: detect QR code screen, log alert, pause watcher
- PM2 auto-restarts on crash

### AD-4: Email MCP Server — Node.js with TypeScript

**Decision**: Standalone Node.js MCP server written in TypeScript, wrapping Gmail API with two tools: `send_email` and `draft_email`.

**Approach**:
1. Use `@modelcontextprotocol/sdk` for MCP server framework
2. Use `googleapis` npm package for Gmail API
3. TypeScript source (`index.ts`) executed directly via `tsx` (no build step)
4. OAuth2 credentials shared with Gmail watcher (same Google app, separate token)
5. `send_email(to, subject, body, cc?, bcc?, attachments?)` → sends immediately
6. `draft_email(to, subject, body, cc?, bcc?)` → creates Gmail draft
7. Both return `{success, message_id}` or `{error, details}`
8. Claude Code connects via stdio transport

**Registration**: Add to Claude Code MCP config (`.mcp.json`).

### AD-5: LinkedIn Poster — Playwright Script

**Decision**: Standalone Python script (not a watcher) triggered by Task Scheduler daily.

**Approach**:
1. Script `scripts/linkedin_post.py` reads approved post from `vault/Approved/`
2. Uses Playwright with persistent browser context (reuse LinkedIn session)
3. Navigates to LinkedIn feed, clicks "Start a post", types content, publishes
4. Logs success/failure via `logger.py`
5. On CAPTCHA/detection: log, alert Dashboard, exit (no retry)

**Flow**:
- Task Scheduler → `generate-linkedin-post` skill (creates post in `vault/Pending_Approval/`)
- Human approves → moves to `vault/Approved/`
- Orchestrator detects → invokes `linkedin_post.py` via Playwright

### AD-6: Orchestrator Extension

**Decision**: Extend existing orchestrator to handle `EMAIL_`, `WHATSAPP_`, `LINKEDIN_` prefixes alongside `FILE_`.

**Changes**:
1. Startup scan: check for `EMAIL_*`, `WHATSAPP_*`, `FILE_*` in `vault/Needs_Action/`
2. Plan name generation: `PLAN_{prefix}_{name}.md` (preserve prefix)
3. Approval processing: dispatch to correct action executor based on `action` field
4. New action executors:
   - `email_send` → invoke email-mcp `send_email` tool
   - `email_draft` → invoke email-mcp `draft_email` tool
   - `whatsapp_reply` → invoke WhatsApp Playwright reply function
   - `linkedin_post` → invoke LinkedIn Playwright post function
5. Update `invoke_claude()` allowed tools to include MCP tools when needed

### AD-7: PM2 Process Management

**Decision**: PM2 ecosystem config managing all long-running processes.

**Processes**:
1. `filesystem-watcher` — `python -m watchers.filesystem_watcher`
2. `gmail-watcher` — `python -m watchers.gmail_watcher`
3. `whatsapp-watcher` — `python -m watchers.whatsapp_watcher`
4. `orchestrator` — `python -m watchers.orchestrator`
5. `email-mcp` — `npx tsx email-mcp/index.ts`

**Config**: `scripts/pm2_ecosystem.config.js` with auto-restart, max restarts, restart delay.

### AD-8: Windows Task Scheduler Integration

**Decision**: Python setup script creates Task Scheduler entries.

**Scheduled Tasks**:
1. LinkedIn post generation — daily 9:00 AM weekdays
2. CEO briefing generation — Monday 8:00 AM
3. PM2 health check — every 5 minutes

## Implementation Phases

### Phase 1: Foundation (US1 — Vault Restructuring)
1. Create `vault/` directory structure
2. Move all vault folders and documents
3. Update all path references in existing code
4. Update `.env.example`, `.gitignore`
5. Verify Obsidian opens cleanly on `vault/`

### Phase 2: Gmail Pipeline (US2 + US4)
1. Implement `gmail_watcher.py` (extends BaseWatcher)
2. Implement `email-mcp/` Node.js/TypeScript MCP server
3. Create `compose-email-reply.md` skill
4. Update `triage-inbox.md` for EMAIL_ items
5. Update orchestrator for email action dispatch

### Phase 3: WhatsApp Pipeline (US3)
1. Implement `whatsapp_watcher.py` (extends BaseWatcher)
2. Create `compose-whatsapp-reply.md` skill
3. Update `triage-inbox.md` for WHATSAPP_ items
4. Update orchestrator for WhatsApp reply dispatch

### Phase 4: LinkedIn Pipeline (US5)
1. Implement `scripts/linkedin_post.py`
2. Create `generate-linkedin-post.md` skill
3. Update orchestrator for LinkedIn post dispatch

### Phase 5: HITL + Scheduling (US6 + US7)
1. Update `process-approval.md` for new action types
2. Create PM2 ecosystem config
3. Create Task Scheduler setup script
4. Update Company_Handbook.md with new approval rules

### Phase 6: Agent Skills + Polish (US8)
1. Verify all skills follow standard structure
2. Update `update-dashboard.md` for new item types
3. Update `generate-briefing.md` paths
4. End-to-end DRY_RUN testing

## Complexity Tracking

> No constitution violations. No complexity justifications needed.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Node.js/TypeScript sidecar (email-mcp) | MCP SDK is Node.js-native; hackathon requirement for 1 MCP server; TypeScript adds type safety | Python MCP SDK exists but is less mature and documented |
