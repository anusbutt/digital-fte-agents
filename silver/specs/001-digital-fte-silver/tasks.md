# Tasks: Digital FTE Silver — Functional Assistant

**Input**: Design documents from `specs/001-digital-fte-silver/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Not explicitly requested — test tasks omitted. DRY_RUN mode serves as integration validation.

**Organization**: Tasks grouped by user story (8 stories from spec). Setup + Foundational first, then US1-US8 in priority order, then Polish.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1-US8)
- Exact file paths included

---

## Phase 1: Setup

**Purpose**: Update project config, dependencies, and ignore files for Silver tier

- [X] T001 Update project metadata in pyproject.toml (name: silver, description, add dependencies: google-api-python-client, google-auth-oauthlib, google-auth-httplib2, playwright)
- [X] T002 [P] Update .env.example with all Silver environment variables (GMAIL_POLL_INTERVAL, WHATSAPP_POLL_INTERVAL, GOOGLE_CREDENTIALS_PATH, GMAIL_TOKEN_PATH, EMAIL_MCP_TOKEN_PATH, WHATSAPP_USER_DATA_DIR, LINKEDIN_USER_DATA_DIR, LINKEDIN_POST_TIME, BRIEFING_DAY, BRIEFING_TIME) per data-model.md
- [X] T003 [P] Update .gitignore to add vault/Logs/, email-mcp/node_modules/, playwright-data/, token.json, token-mcp.json, credentials.json
- [X] T004 [P] Create email-mcp/package.json with dependencies: @modelcontextprotocol/sdk, googleapis per contracts/email-mcp-tools.md
- [X] T005 Run `playwright install chromium` after dependency install to set up browser binaries for WhatsApp and LinkedIn automation

**Checkpoint**: Project config ready. Dependencies installable via `uv sync` and `npm install`.

---

## Phase 2: Foundational — Vault Restructuring (US1, Priority: P1) 🎯 MVP

**Goal**: Separate Obsidian vault into `vault/` subdirectory. All other stories depend on this.

**Independent Test**: Open `vault/` in Obsidian — only business folders visible. Run filesystem watcher — targets `vault/Inbox`.

- [X] T006 [US1] Create vault/ directory and move all vault folders (Inbox, Needs_Action, Plans, Pending_Approval, Approved, Rejected, Done, Briefings, Accounting) into vault/ with .gitkeep files
- [X] T007 [US1] Move vault documents (Dashboard.md, Company_Handbook.md, Business_Goals.md) into vault/
- [X] T008 [US1] Create vault/Logs/ directory with .gitkeep
- [X] T009 [US1] Remove old vault folders and documents from repo root (Inbox/, Needs_Action/, Plans/, Pending_Approval/, Approved/, Rejected/, Done/, Briefings/, Accounting/, Dashboard.md, Company_Handbook.md, Business_Goals.md) after confirming vault/ has all content
- [X] T010 [US1] Update vault/Company_Handbook.md business tier from "Bronze" to "Silver" and add new approval rules for email_send, whatsapp_reply, linkedin_post per spec.md US6
- [X] T011 [US1] Refactor watchers/base_watcher.py — generalize check_for_updates() return type and create_action_file() parameter from Path to Any (Union[Path, dict]) so Gmail and WhatsApp watchers can return message data instead of file paths, keep backward-compatible for FilesystemWatcher
- [X] T012 [US1] Update watchers/filesystem_watcher.py — change vault_path resolution to use VAULT_PATH env var defaulting to `./vault`, update all directory references (inbox_dir, needs_action_dir, log_dir)
- [X] T013 [US1] Update watchers/orchestrator.py — change vault_path resolution to use VAULT_PATH env var defaulting to `./vault`, update skills_dir to reference repo root `skills/` (not vault/skills/), update all directory references
- [X] T014 [US1] Update main.py — change entry point to use VAULT_PATH=./vault as default, load dotenv from repo root

**Checkpoint**: Vault restructured. Obsidian shows only business docs. Existing filesystem watcher + orchestrator work with vault/ paths. BaseWatcher supports generic source types.

---

## Phase 3: Gmail Pipeline (US2 + US4, Priority: P1 + P2)

**Goal**: Monitor Gmail for actionable emails, create triage items, enable email send/draft via MCP.

**Independent Test**: Send a test email asking "Can you send me a quote?" — verify EMAIL_*.md created in vault/Needs_Action/ with correct frontmatter.

### US4: Email MCP Server (prerequisite for US2 email replies)

- [X] T015 [US4] Implement email-mcp/index.ts — Node.js/TypeScript MCP server with stdio transport, OAuth2 authentication via googleapis, send_email tool per contracts/email-mcp-tools.md
- [X] T016 [US4] Add draft_email tool to email-mcp/index.ts per contracts/email-mcp-tools.md
- [X] T017 [US4] Add email-mcp/.env.example with GOOGLE_CREDENTIALS_PATH and EMAIL_MCP_TOKEN_PATH
- [X] T018 [US4] Register email-mcp in Claude Code config — add mcpServers entry to .mcp.json per MCP server standard (tsx index.ts)

### US2: Gmail Watcher

- [X] T019 [US2] Create watchers/gmail_watcher.py — extend BaseWatcher, implement Gmail API client initialization with OAuth2 credentials from GOOGLE_CREDENTIALS_PATH, store token at GMAIL_TOKEN_PATH per research.md R1
- [X] T020 [US2] Implement gmail_watcher check_for_updates() — query Gmail API for unread messages with filter `is:unread -category:{promotions,social,updates,forums}`, filter out OTPs/newsletters (noreply@, no-reply@, subject contains OTP/verification), return list of actionable message dicts with exponential backoff on 429/timeout per spec US2 error handling
- [X] T021 [US2] Implement gmail_watcher create_action_file() — create EMAIL_{message_id}.md in vault/Needs_Action/ per data-model.md EMAIL_ VaultItem schema, with full email body, sensitivity classification, priority classification, atomic write, duplicate detection, mark email as read after processing
- [X] T022 [US2] Add CLI entry point to gmail_watcher with argparse — --auth flag for OAuth2 initial setup (opens browser for consent), startup scan for unprocessed emails, main polling loop
- [X] T023 [US2] Create skills/compose-email-reply.md — Agent Skill that reads EMAIL_ VaultItem + Company_Handbook.md, drafts a professional reply, determines sensitivity (sensitive → draft_email via MCP, non-sensitive → send_email via MCP)
- [X] T024 [US2] Update skills/triage-inbox.md — add EMAIL_ VaultItem handling alongside FILE_, update classification rules for email sensitivity, update plan naming to PLAN_EMAIL_{message_id}.md per data-model.md

**Checkpoint**: Gmail watcher detects actionable emails within 60s polling. Email MCP can send/draft. Triage skill handles EMAIL_ items. Compose-email-reply skill generates appropriate replies.

---

## Phase 4: WhatsApp Pipeline (US3, Priority: P1)

**Goal**: Monitor WhatsApp Web for business keyword messages, create triage items, enable reply via Playwright.

**Independent Test**: Send a WhatsApp message containing "invoice" — verify WHATSAPP_*.md created in vault/Needs_Action/.

- [X] T025 [US3] Create watchers/whatsapp_watcher.py — extend BaseWatcher, launch Playwright Chromium with persistent context (WHATSAPP_USER_DATA_DIR), implement --setup flag for first-time QR code scan per research.md R2
- [X] T026 [US3] Implement whatsapp_watcher check_for_updates() — scan WhatsApp Web for unread chat indicators, click into unread chats, read latest messages, check against business keywords list (urgent, invoice, payment, pricing, help, quote, project, deadline), return list of keyword-matching message dicts
- [X] T027 [US3] Implement whatsapp_watcher create_action_file() — create WHATSAPP_{contact_slug}_{YYYYMMDD_HHMMSS}.md in vault/Needs_Action/ per data-model.md WHATSAPP_ VaultItem schema, with contact info, message text, matched keywords, duplicate detection by contact+timestamp
- [X] T028 [US3] Add QR code session expiry detection — check for QR canvas element, if detected log alert, update Dashboard.md with re-auth needed message, pause watcher. Add CLI entry point with argparse (--setup flag for initial login, main polling loop)
- [X] T029 [US3] Create skills/compose-whatsapp-reply.md — Agent Skill that reads WHATSAPP_ VaultItem + Company_Handbook.md, drafts a professional reply, always sets approval_required=true (WhatsApp replies always need approval per spec)
- [X] T030 [US3] Implement WhatsApp reply function in watchers/whatsapp_watcher.py — send_reply(contact, message) method that uses Playwright to navigate to contact chat and type+send message, called by orchestrator after approval
- [X] T031 [US3] Update skills/triage-inbox.md — add WHATSAPP_ VaultItem handling alongside FILE_ and EMAIL_, update plan naming to PLAN_WHATSAPP_{contact}_{timestamp}.md per data-model.md

**Checkpoint**: WhatsApp watcher detects keyword messages within 30s. Triage skill handles WHATSAPP_ items. Reply function can send messages via Playwright after approval.

---

## Phase 5: LinkedIn Pipeline (US5, Priority: P2)

**Goal**: Generate daily LinkedIn posts, publish via Playwright after human approval.

**Independent Test**: Trigger generate-linkedin-post skill — verify LINKEDIN_*.md created in vault/Pending_Approval/. After approval, verify post published via Playwright.

- [X] T032 [US5] Create skills/generate-linkedin-post.md — Agent Skill that generates a professional LinkedIn post about AI automation, digital FTEs, or industry insights per spec.md US5, creates LINKEDIN_{YYYY-MM-DD}.md in vault/Pending_Approval/ per data-model.md LinkedInPost schema, always requires approval
- [X] T033 [US5] Create scripts/linkedin_post.py — Playwright script with persistent Chromium context (LINKEDIN_USER_DATA_DIR), --setup flag for first-time login, post(content) function that navigates to LinkedIn feed, clicks "Start a post", types content, publishes per research.md R3. Include CAPTCHA/automation detection (log alert, update Dashboard.md, exit immediately — no retry per spec), session expiry detection, DRY_RUN support (log post content but skip Playwright publish, log via logger.py)
- [X] T034 [US5] Add run_linkedin_post() method to watchers/orchestrator.py — entry point callable from Task Scheduler that invokes generate-linkedin-post skill, similar to existing run_briefing() pattern, add --linkedin CLI flag to orchestrator argparse

**Checkpoint**: LinkedIn post generation skill creates approval-ready posts. Playwright poster publishes approved posts. Task Scheduler has a callable entry point.

---

## Phase 6: Orchestrator Extension + HITL (US6, Priority: P2)

**Goal**: Extend orchestrator to handle EMAIL_, WHATSAPP_, LINKEDIN_ items and dispatch to correct action executors after approval.

**Independent Test**: Create test approval file in vault/Pending_Approval/, move to vault/Approved/ — verify orchestrator triggers the correct action.

- [X] T035 [US6] Update watchers/orchestrator.py startup scan — extend to detect EMAIL_*, WHATSAPP_*, LINKEDIN_* prefixes alongside FILE_* in vault/Needs_Action/ and vault/Pending_Approval/
- [X] T036 [US6] Update watchers/orchestrator.py _process_needs_action_item() — route to triage-inbox skill for all item types (EMAIL_, WHATSAPP_, FILE_), pass correct context files based on type. Add auto-execution path: when triage returns approval_required=false (non-sensitive emails per spec US2 scenario 3), execute action immediately without creating approval file
- [X] T037 [US6] Update watchers/orchestrator.py _process_approval() — add action dispatchers: email_send → invoke email-mcp send_email, email_draft → invoke email-mcp draft_email, whatsapp_reply → invoke whatsapp_watcher.send_reply(), linkedin_post → invoke scripts/linkedin_post.py post(). Handle failed actions: keep file in vault/Approved/ for retry, log error per spec US6
- [X] T038 [US6] Add approval expiry check to orchestrator — on each cycle, scan vault/Pending_Approval/ for expired approvals (24h past created timestamp), log expiry but take no action per spec US6
- [X] T039 [US6] Update skills/process-approval.md — add handling for new action types (email_send, email_draft, whatsapp_reply, linkedin_post), update move-to-done logic, handle failed actions (keep in Approved/ for retry per spec)

**Checkpoint**: Orchestrator correctly routes all item types through triage → plan → approval → action execution. Non-sensitive emails auto-execute. Failed actions stay in Approved/ for retry.

---

## Phase 7: Scheduling + Process Management (US7, Priority: P3)

**Goal**: PM2 keeps all watchers alive. Task Scheduler triggers periodic tasks.

**Independent Test**: Create Task Scheduler entry for CEO briefing — verify it triggers and generates a briefing.

- [X] T040 [US7] Create scripts/pm2_ecosystem.config.js — PM2 ecosystem config with 5 processes (filesystem-watcher, gmail-watcher, whatsapp-watcher, orchestrator, email-mcp) per plan.md AD-7, configure auto-restart, max_restarts: 10, restart_delay: 5000
- [X] T041 [US7] Create scripts/setup_scheduler.py — Python script using schtasks CLI to create Windows Task Scheduler entries per research.md R6: LinkedIn post (daily 9AM weekdays via orchestrator --linkedin), CEO briefing (Monday 8AM via orchestrator --briefing), PM2 health check (every 5 min)
- [X] T042 [US7] Create scripts/pm2_healthcheck.py — runs `pm2 jlist`, checks all processes are "online", restarts any stopped processes, logs via logger.py
- [X] T043 [US7] Update watchers/orchestrator.py run_briefing() — ensure it works with vault/ path, generates briefing to vault/Briefings/, callable from Task Scheduler

**Checkpoint**: `pm2 start scripts/pm2_ecosystem.config.js` launches all 5 processes. Task Scheduler entries created and functional.

---

## Phase 8: Agent Skills Update (US8, Priority: P3)

**Goal**: All AI capabilities as Agent Skills following standard pattern. Existing skills updated for Silver.

**Independent Test**: Invoke each skill with Claude CLI and mock context — verify expected output structure.

- [X] T044 [US8] Update skills/update-dashboard.md — add EMAIL_, WHATSAPP_, LINKEDIN_ item type counts to Dashboard summary, add watcher status section, add scheduling status
- [X] T045 [US8] Update skills/generate-briefing.md — update vault path references to vault/Briefings/, include email and WhatsApp activity in weekly briefing summary
- [X] T046 [US8] Verify all 7 skills follow standard structure — each .md has: Purpose, Instructions (numbered steps), Rules, Tools Required per constitution Principle IV. Skills: triage-inbox, update-dashboard, generate-briefing, process-approval, compose-email-reply, compose-whatsapp-reply, generate-linkedin-post

**Checkpoint**: All 7 skills follow standard pattern and handle all Silver item types.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end validation, documentation, DRY_RUN testing

- [X] T047 [P] Update main.py — add CLI subcommands for launching individual watchers, orchestrator, briefing, linkedin, and setup commands
- [X] T048 [P] Verify .env.example is complete with all required environment variables and documentation comments
- [X] T049 Run DRY_RUN end-to-end validation — start all processes via PM2, drop file in vault/Inbox/ (filesystem watcher), verify EMAIL_/WHATSAPP_/FILE_ flow through entire pipeline in DRY_RUN mode
- [X] T050 Verify vault/Logs/ audit entries contain all required fields per constitution Principle VII (timestamp, action_type, actor, target, parameters, result, approval_status)
- [X] T051 Verify vault/Dashboard.md updates correctly after state changes per constitution Principle VI

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Vault Restructuring / US1)**: Depends on Phase 1 — BLOCKS all other phases
- **Phase 3 (Gmail + Email MCP / US2 + US4)**: Depends on Phase 2
- **Phase 4 (WhatsApp / US3)**: Depends on Phase 2. Can run in parallel with Phase 3
- **Phase 5 (LinkedIn / US5)**: Depends on Phase 2. Can run in parallel with Phase 3/4
- **Phase 6 (Orchestrator + HITL / US6)**: Depends on Phases 3, 4, 5 (needs all watchers and skills to dispatch to)
- **Phase 7 (Scheduling / US7)**: Depends on Phase 6 (orchestrator must be extended first)
- **Phase 8 (Skills / US8)**: Depends on Phases 3, 4, 5 (skills reference new item types)
- **Phase 9 (Polish)**: Depends on all previous phases

### User Story Dependencies

- **US1 (Vault Restructuring)**: FOUNDATIONAL — blocks everything
- **US2 (Gmail)**: Depends on US1. Partially depends on US4 (email-mcp for replies)
- **US3 (WhatsApp)**: Depends on US1. Independent of US2
- **US4 (Email MCP)**: Depends on US1. Implemented alongside US2
- **US5 (LinkedIn)**: Depends on US1. Independent of US2/US3
- **US6 (HITL)**: Depends on US2, US3, US5 (needs action types to dispatch)
- **US7 (Scheduling)**: Depends on US6 (orchestrator extension)
- **US8 (Skills)**: Cross-cutting — tasks distributed across other phases

### Within Each Phase

- MCP server before watcher (watcher may need MCP for replies)
- Watcher core before CLI/error handling
- Skills alongside their parent phase
- Triage skill updated in same phase as its watcher (not deferred)

### Parallel Opportunities

```
Phase 2 (US1) ──────────────────────────────────────┐
                                                      │
After Phase 2:                                        ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ Phase 3 (US2+4)  │  │ Phase 4 (US3)    │  │ Phase 5 (US5)    │
│ Gmail + MCP      │  │ WhatsApp         │  │ LinkedIn         │
└────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
         │                     │                      │
         └─────────────────────┼──────────────────────┘
                               │
                               ▼
                    Phase 6 (US6) — Orchestrator + HITL
                               │
                               ▼
                    Phase 7 (US7) — Scheduling
                               │
                               ▼
                    Phase 8 (US8) — Skills Polish
                               │
                               ▼
                    Phase 9 — End-to-End Validation
```

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Vault Restructuring (US1)
3. **STOP and VALIDATE**: Obsidian opens vault/ cleanly, existing watcher works
4. This is the minimum viable Silver foundation

### Incremental Delivery

1. Setup + US1 → Foundation ready
2. Add US2 + US4 → Gmail pipeline functional → Test with real email
3. Add US3 → WhatsApp pipeline functional → Test with real message
4. Add US5 → LinkedIn pipeline functional → Test with mock post
5. Add US6 → Full HITL flow → Test approval/rejection
6. Add US7 → Fully automated → Test scheduling
7. Add US8 + Polish → Production ready

---

## Audit Log

**Fixes applied from pre-implementation audit (2026-02-18):**

| Issue | Type | Fix Applied |
|-------|------|-------------|
| A: T040 triage-inbox update too late | Mis-sequence | Split into T024 (EMAIL_ in Phase 3) and T031 (WHATSAPP_ in Phase 4) |
| B: T014 missed removing root documents | Mis-sequence | Merged document + folder removal into T009 |
| C: No BaseWatcher generalization | Missing task | Added T011 (refactor base_watcher.py for generic types) |
| D: No auto-execution path | Missing task | Added to T036 (auto-execute when approval_required=false) |
| E: No orchestrator LinkedIn entry point | Missing task | Added T034 (run_linkedin_post method + --linkedin flag) |
| F: No playwright install task | Missing task | Added T005 (playwright install chromium) |
| G: Root docs not removed | Missing task | Merged into Issue B fix (T009) |
| H: T020/T023 overlap on --auth | Repeatable | Removed --auth from T019 (core watcher), kept in T022 (CLI task) |
| I: T005 empty placeholders | Repeatable | Removed — files created in actual phases |
| J: T012 logger no-op | Repeatable | Removed entirely |
| K: T015 test_data no-op | Repeatable | Removed entirely |
| L: T003 email-mcp/ in gitignore | Incompatible | Changed to email-mcp/node_modules/ |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [USn] label maps to spec.md user stories for traceability
- DRY_RUN mode is the primary testing strategy — all external actions logged but not executed
- Each phase checkpoint validates independently before moving forward
- Total: 51 tasks across 9 phases covering 8 user stories
- Triage skill updates co-located with their watcher phase (not deferred to Phase 6)
