# Tasks: Nestaro Pilot Nestaro Pilot — Autonomous AI employee

**Input**: Design documents from `specs/001-nestaro-pilot/`
**Prerequisites**: plan.md ✅ spec.md ✅ research.md ✅ data-model.md ✅ contracts/ ✅ quickstart.md ✅

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1–US5 maps to spec.md user stories
- Every task includes exact file path

---

## Phase 1: Setup — Project Scaffold

**Purpose**: Initialize ./ as a self-contained project based on earlier prototype's
proven structure. All earlier prototype components are copied here — ./ has zero
runtime dependency on earlier prototype/.

- [x] T001 Create ./ top-level folder structure: `watchers/`, `skills/`, `email-mcp/`, `odoo-mcp/`, `scripts/`, `vault/` (9 subfolders), `.claude/hooks/`, `specs/`
- [x] T002 Copy `earlier prototype/pyproject.toml` to `./pyproject.toml` and add no new deps (all earlier prototype deps already cover Nestaro Pilot needs)
- [x] T003 [P] Create `./.env.example` with all Nestaro Pilot environment variables (DRY_RUN, VAULT_PATH, Gmail OAuth, WhatsApp, LinkedIn, Facebook, Instagram, Twitter session paths, Odoo URL/DB/API key, all poll intervals, scheduling config)
- [x] T004 [P] Create `./vault/` with all 9 subfolders: `Inbox/`, `Needs_Action/`, `Plans/`, `Pending_Approval/`, `Approved/`, `Rejected/`, `Done/`, `Logs/`, `Briefings/`, `Accounting/` — add `.gitkeep` to each
- [x] T005 [P] Create `./vault/Company_Handbook.md` with classification rules expanded for Facebook, Instagram, Twitter channels; approval thresholds per constitution Principle IV
- [x] T006 [P] Create `./vault/Business_Goals.md` with Q1 2026 revenue targets ($8K/month), KPIs, active projects, subscription audit rules, alert triggers
- [x] T007 [P] Create `./docker-compose.yml` with `odoo:17.0` + `postgres:15` services, port 8069, environment variables, volume mounts for data persistence
- [x] T008 [P] Create `./vault/Dashboard.md` with initial template matching vault-schema.md Dashboard required sections

**Checkpoint**: Nestaro Pilot scaffold ready — vault initialized, Docker config present, env template complete.

---

## Phase 2: Foundational — Shared Infrastructure

**Purpose**: Core infrastructure that ALL user stories depend on. MUST be
complete before any user story work begins.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T009 Copy `earlier prototype/watchers/base_watcher.py` to `./watchers/base_watcher.py` (exponential backoff: base 1s, max 60s, 3 attempts; abstract `check_for_updates()` and `create_action_file()`)
- [x] T010 Copy `earlier prototype/watchers/logger.py` to `./watchers/logger.py` and expand `action_type` enum with: `facebook_reply`, `facebook_post`, `instagram_reply`, `instagram_post`, `twitter_reply`, `twitter_post`, `odoo_create_invoice`, `odoo_post_invoice`, `odoo_record_payment`, `auth_failure`, `system_alert`
- [x] T011 [P] Copy `earlier prototype/watchers/filesystem_watcher.py` to `./watchers/filesystem_watcher.py` (unchanged)
- [x] T012 [P] Copy `earlier prototype/watchers/gmail_watcher.py` to `./watchers/gmail_watcher.py` (unchanged)
- [x] T013 [P] Copy `earlier prototype/watchers/whatsapp_watcher.py` to `./watchers/whatsapp_watcher.py` (unchanged)
- [x] T014 Copy `earlier prototype/watchers/orchestrator.py` to `./watchers/orchestrator.py` as base; verify it handles: Needs_Action/ polling, Approved/ polling, Rejected/ polling, skill invocation via Claude Code, expiry checking (24h)
- [x] T015 [P] Copy `earlier prototype/email-mcp/` directory to `./email-mcp/` (index.ts + package.json unchanged)
- [x] T016 [P] Copy earlier prototype skills to ./skills/: `compose-email-reply.md`, `compose-whatsapp-reply.md`, `generate-linkedin-post.md`, `process-approval.md`, `update-dashboard.md` — these are starting points that will be expanded in later phases
- [x] T017 [P] Copy `earlier prototype/scripts/linkedin_post.py` to `./scripts/linkedin_post.py` (unchanged)
- [x] T018 [P] Copy `earlier prototype/scripts/pm2_healthcheck.py` to `./scripts/pm2_healthcheck.py` as base (will be expanded in polish phase)
- [x] T019 Create `./watchers/__init__.py`, `./watchers/` package init (empty)
- [x] T020 Create `./.mcp.json` with email-mcp server entry; leave odoo-mcp entry as placeholder (filled in US2)
- [x] T021 Expand `./skills/triage-inbox.md` to handle all Nestaro Pilot item types: add facebook, instagram, twitter to type classification; add decision matrix rows for all social channels (all social → approval_required=true per constitution); reference contracts/skill-contracts.md decision matrix

**Checkpoint**: Foundation ready — base watcher, logger, orchestrator, email-mcp, earlier prototype skills all present. Triage skill handles all Nestaro Pilot item types.

---

## Phase 3: User Story 1 — Social Media Monitoring & Posting (P1) 🎯 MVP

**Goal**: Facebook, Instagram, Twitter watchers detect new messages/mentions
and route them through the HITL vault pipeline. Daily social post drafts
generated and sent to Pending_Approval/ for human review.

**Independent Test**: Drop a `FACEBOOK_test_20260313.md` file directly into
`vault/Needs_Action/`. Verify orchestrator creates a PLAN_ file and an
APPROVAL_ file in `vault/Pending_Approval/`. Move approval to `vault/Approved/`.
Verify `vault/Done/` has the item and `vault/Logs/YYYY-MM-DD.json` has an
entry with `"result": "dry_run"` (DRY_RUN=true).

### Implementation for User Story 1

- [x] T022 [P] [US1] Create `./watchers/facebook_watcher.py`: extend BaseWatcher; use Playwright persistent context (`FACEBOOK_USER_DATA_DIR`); navigate to `facebook.com/messages/`; detect unread DMs by aria-label or unread badge; filter by keywords from Company_Handbook; call `create_action_file()` writing `FACEBOOK_{thread_id}_{timestamp}.md` to `vault/Needs_Action/` with VaultItem frontmatter (type: facebook, raw_id for dedup)
- [x] T023 [P] [US1] Create `./watchers/instagram_watcher.py`: extend BaseWatcher; use Playwright persistent context (`INSTAGRAM_USER_DATA_DIR`); navigate to `instagram.com/direct/inbox/`; detect unread DMs; filter by keywords; write `INSTAGRAM_{thread_id}_{timestamp}.md` to `vault/Needs_Action/`
- [x] T024 [P] [US1] Create `./watchers/twitter_watcher.py`: extend BaseWatcher; use Playwright persistent context (`TWITTER_USER_DATA_DIR`); navigate to `twitter.com/notifications` and `twitter.com/messages`; detect new mentions and DMs; filter by keywords; write `TWITTER_{tweet_id}_{timestamp}.md` to `vault/Needs_Action/`
- [x] T025 [P] [US1] Create `./scripts/facebook_post.py`: use Playwright persistent context; navigate to Facebook page composer; type post content from approval file; click Post button; log result; move approval file to Done/; write AuditLogEntry — respect DRY_RUN flag
- [x] T026 [P] [US1] Create `./scripts/instagram_post.py`: use Playwright persistent context; navigate to Instagram new post flow; enter caption and hashtags from approval file; submit; log result; move approval file to Done/; write AuditLogEntry — respect DRY_RUN flag
- [x] T027 [P] [US1] Create `./scripts/twitter_post.py`: use Playwright persistent context; navigate to `twitter.com`; open compose dialog; enter tweet text (≤ 280 chars) from approval file; submit; log result; move approval file to Done/; write AuditLogEntry — respect DRY_RUN flag
- [x] T028 [US1] Create `./skills/generate-social-post.md`: reads Business_Goals.md and Company_Handbook.md for brand voice; reads Done/ last 7 days for content ideas; generates three separate approval files (SOCIAL_POST_FACEBOOK_, SOCIAL_POST_INSTAGRAM_, SOCIAL_POST_TWITTER_) in Pending_Approval/; Twitter post ≤ 280 chars; Instagram post includes 3-5 hashtags; Facebook post includes CTA; all files routed to Pending_Approval/ (never auto-post)
- [x] T029 [US1] Expand `./watchers/orchestrator.py` to: recognize FACEBOOK_, INSTAGRAM_, TWITTER_ prefixes in Needs_Action/; route to triage-inbox skill; after approval dispatch FACEBOOK_POST/REPLY to `scripts/facebook_post.py`, INSTAGRAM_POST/REPLY to `scripts/instagram_post.py`, TWITTER_POST/REPLY to `scripts/twitter_post.py`; trigger generate-social-post skill on daily schedule (configurable via `SOCIAL_POST_TIME` env var)
- [x] T030 [US1] Add social setup commands to `./main.py`: `python main.py setup facebook`, `python main.py setup instagram`, `python main.py setup twitter` — each opens Playwright browser for manual login and saves session to configured data dir; add `python main.py facebook`, `python main.py instagram`, `python main.py twitter` watcher start commands

**Checkpoint**: US1 fully functional. Drop a Facebook DM item into vault, follow pipeline to Done/. Social post drafts generated daily and routed to Pending_Approval/.

---

## Phase 4: User Story 2 — Odoo Accounting Integration via MCP (P1)

**Goal**: odoo-mcp TypeScript server exposes 7 Odoo tools to Claude. Invoice
creation, posting, and payment recording all require HITL approval. Odoo
unreachable = graceful alert, no crash.

**Independent Test**: With Docker Odoo running, manually trigger
`python main.py odoo-test` (or drop an invoice request file into vault/Inbox/).
Verify triage creates a plan with `action_type: odoo_create_invoice`, approval
request appears, move to Approved/, verify odoo-mcp is called (DRY_RUN logs
call), verify AuditLogEntry written. Stop Docker, re-trigger — verify
SYSTEM_ODOO_UNREACHABLE.md appears in Needs_Action/, no crash.

### Implementation for User Story 2

- [x] T031 [US2] Create `./odoo-mcp/package.json`: `name: "odoo-mcp"`, dependencies: `@modelcontextprotocol/sdk`, `zod`, `tsx`; scripts: `start: tsx index.ts`
- [x] T032 [US2] Create `./odoo-mcp/index.ts`: implement Odoo JSON-RPC client (POST to `ODOO_URL/web/dataset/call_kw`, Bearer auth with `ODOO_API_KEY`); implement all 7 tools per contracts/odoo-mcp-tools.md (`get_invoices`, `create_invoice`, `post_invoice`, `record_payment`, `get_partners`, `get_financial_summary`, `get_transactions`); implement error handling: catch fetch errors → return `{ success: false, error: "ODOO_UNREACHABLE" }`; 401 → `AUTH_FAILED`; 404 → `NOT_FOUND`; register all tools with MCP SDK server; start stdio transport
- [x] T033 [US2] Create `./skills/process-odoo-action.md`: reads approval file; verifies DRY_RUN flag (if true → log dry_run, stop); verifies `approved_by: human`; verifies not expired; determines action_type (odoo_create_invoice / odoo_post_invoice / odoo_record_payment); calls appropriate odoo-mcp tool via Claude MCP call; on success → move file to Done/, write AuditLogEntry with result:success; on failure → write `SYSTEM_ODOO_FAILURE_{timestamp}.md` to Needs_Action/, write AuditLogEntry with result:failure, do NOT retry
- [x] T034 [US2] Expand `./watchers/orchestrator.py`: recognize `odoo_create_invoice`, `odoo_post_invoice`, `odoo_record_payment` action types in approved files; route all odoo action types to `process-odoo-action` skill (never direct dispatch); handle SYSTEM_ODOO_UNREACHABLE by writing alert to Dashboard.md
- [x] T035 [US2] Update `./.mcp.json`: add odoo-mcp server entry with `command: "node"`, `args: ["./odoo-mcp/index.ts"]`, env vars: `ODOO_URL`, `ODOO_DB`, `ODOO_API_KEY`
- [x] T036 [US2] Add `python main.py setup odoo` to `./main.py`: prints Docker setup instructions, prompts user to enter ODOO_API_KEY, writes to .env; add `python main.py odoo-status` command that calls odoo-mcp `get_financial_summary` and prints result

**Checkpoint**: US2 fully functional. Odoo invoice creation through full HITL pipeline. Odoo unreachable handled gracefully.

---

## Phase 5: User Story 3 — Enhanced CEO Briefing with Live Accounting Data (P2)

**Goal**: Weekly CEO briefing pulls live Odoo financial data and combines with
vault activity. Overdue invoices trigger proactive approval suggestions.
Dashboard updated with financial snapshot.

**Independent Test**: With Odoo running and at least one posted invoice, run
`python main.py briefing`. Verify `vault/Briefings/YYYY-MM-DD_Briefing.md`
exists and contains Revenue section (with real $ figures from Odoo), Unpaid
Invoices table, Communications Activity, Completed Tasks, and at least one
Proactive Suggestion. Verify Dashboard.md updated with financial snapshot.

### Implementation for User Story 3

- [x] T037 [US3] Create `./skills/generate-accounting-briefing.md`: reads Business_Goals.md (revenue target); calls odoo-mcp `get_financial_summary()` for MTD revenue + outstanding; calls odoo-mcp `get_invoices(payment_state="not_paid")` for unpaid list; reads vault/Done/ last 7 days for completed tasks count; reads vault/Logs/ last 7 days for action counts by type; generates briefing with all required sections per data-model.md CEOBriefing schema; writes to `vault/Briefings/YYYY-MM-DD_Briefing.md`; for each invoice overdue > 30 days: writes APPROVAL_odoo_send_reminder_{client}_{timestamp}.md to Pending_Approval/; calls update-dashboard skill
- [x] T038 [US3] Expand `./skills/update-dashboard.md`: add Odoo Financial Snapshot section; call odoo-mcp `get_financial_summary()` with graceful fallback if Odoo offline (show "Odoo: offline — start with `docker compose up -d`"); add Recent Activity section from last 5 AuditLogEntries in today's Logs/ file; add System Health section listing all 8 PM2 process names and their status
- [x] T039 [US3] Update `./watchers/orchestrator.py`: trigger `generate-accounting-briefing` skill on `BRIEFING_DAY`/`BRIEFING_TIME` schedule (replace `generate-briefing` from earlier prototype)

**Checkpoint**: US3 fully functional. `python main.py briefing` produces complete CEO briefing with live Odoo data and Dashboard updated.

---

## Phase 6: User Story 4 — Ralph Wiggum Loop (P2)

**Goal**: Claude does not exit while items remain in vault/Needs_Action/.
Stop hook re-injects orchestrator prompt up to 10 iterations.

**Independent Test**: Place 3 test `.md` files in `vault/Inbox/`. Start the
orchestrator with `python main.py orchestrator`. Without any manual
intervention, verify all 3 files reach `vault/Plans/` or
`vault/Pending_Approval/` before Claude exits. Check logs for multiple
iteration cycles.

### Implementation for User Story 4

- [x] T040 [US4] Create `./.claude/hooks/stop.py`: read `VAULT_PATH` env var (default `./vault`); glob `vault/Needs_Action/*.md` excluding SYSTEM_ prefixed files; read `RALPH_ITERATION` env var (default 0) and `RALPH_MAX_ITER` (default 10); if items remain AND iteration < max_iter: set `RALPH_ITERATION=iteration+1`, print remaining item count to stderr, exit with code 2 (re-inject); else: exit with code 0 (allow exit); if max_iter reached: write `SYSTEM_MAX_ITERATIONS_{timestamp}.md` to Needs_Action/ with count of unprocessed items
- [x] T041 [US4] Update `./watchers/orchestrator.py`: set `RALPH_ITERATION=0` at start of each orchestration cycle invocation; set `RALPH_MAX_ITER=10`; export both as environment variables before invoking Claude; ensure orchestrator prompt passed to Claude is idempotent (safe to re-run multiple times)

**Checkpoint**: US4 fully functional. Multi-item batches processed autonomously without manual re-invocation.

---

## Phase 7: User Story 5 — Comprehensive Error Recovery (P3)

**Goal**: All 6 watchers implement full error taxonomy (transient/auth/logic/
system). DRY_RUN guaranteed across all execution paths. Approval expiry
enforced. End-to-end smoke test passes.

**Independent Test**: (a) Kill Docker Odoo mid-operation — verify
SYSTEM_ODOO_UNREACHABLE.md in Needs_Action/, no other watcher crashes.
(b) Set DRY_RUN=true, trigger all action types — verify zero external calls,
all log entries show `"result": "dry_run"`. (c) Create approval file with
`expires_at` 25 hours ago — verify orchestrator moves it to Done/ with
`status: expired`.

### Implementation for User Story 5

- [x] T042 [P] [US5] Add auth error handling to `./watchers/gmail_watcher.py`: catch 401/403 from Gmail API; immediately pause watcher loop; write `SYSTEM_AUTH_FAILURE_GMAIL_{timestamp}.md` to `vault/Needs_Action/` with instructions to re-run `python main.py setup gmail`; do not retry until file is resolved
- [x] T043 [P] [US5] Add auth error handling to `./watchers/facebook_watcher.py`: detect Playwright navigation to login page (session expired); pause watcher; write `SYSTEM_AUTH_FAILURE_FACEBOOK_{timestamp}.md` to Needs_Action/
- [x] T044 [P] [US5] Add auth error handling to `./watchers/instagram_watcher.py`: same pattern as Facebook — detect login redirect, pause, write SYSTEM_ alert
- [x] T045 [P] [US5] Add auth error handling to `./watchers/twitter_watcher.py`: same pattern — detect login redirect, pause, write SYSTEM_ alert
- [x] T046 [US5] Add approval expiry check to `./watchers/orchestrator.py`: on every cycle, scan `vault/Pending_Approval/*.md`; parse `expires_at` frontmatter; if `now > expires_at`: update frontmatter `status: expired`; move file to `vault/Done/`; write AuditLogEntry with `action_type: approval_expired`, `result: success`; update Dashboard.md
- [x] T047 [US5] Create `./scripts/validate_dry_run.py`: end-to-end smoke test with DRY_RUN=true; creates synthetic VaultItems for each type (email, whatsapp, facebook, instagram, twitter, file); runs full pipeline; asserts all log entries have `"result": "dry_run"`; asserts vault/Done/ has all items; asserts zero external API calls made; prints PASS/FAIL report

**Checkpoint**: US5 fully functional. System resilient to component failures. DRY_RUN bulletproof across all paths.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Integrate all components; PM2 ecosystem; full CLI; README;
end-to-end validation.

- [x] T048 Create `./scripts/pm2_ecosystem.config.js` with all 8 process definitions: filesystem-watcher, gmail-watcher, whatsapp-watcher, facebook-watcher, instagram-watcher, twitter-watcher, orchestrator, email-mcp — each with `interpreter: python3` or `node`, `restart_delay: 5000`, `max_restarts: 10`, `env: { DRY_RUN, VAULT_PATH }`
- [x] T049 Expand `./scripts/pm2_healthcheck.py` for 8 processes: check each PM2 process status; restart stopped processes; write SYSTEM_PM2_RESTART_{process}_{timestamp}.md to Needs_Action/ when a process is restarted; print health table
- [x] T050 [P] Update `./scripts/setup_scheduler.py` for nestaro-pilot: create Windows Task Scheduler entries for PM2 startup on login, daily briefing, daily social post generation, weekly health check
- [x] T051 Create `./main.py` full CLI with all subcommands: `filesystem`, `gmail`, `whatsapp`, `facebook`, `instagram`, `twitter`, `orchestrator`, `briefing`, `social`, `healthcheck`, `setup gmail`, `setup email-mcp`, `setup whatsapp`, `setup linkedin`, `setup facebook`, `setup instagram`, `setup twitter`, `setup odoo`, `setup scheduler`, `setup pm2`
- [x] T052 [P] Expand `./skills/process-approval.md`: add dispatch handlers for `facebook_post`, `facebook_reply`, `instagram_post`, `instagram_reply`, `twitter_post`, `twitter_reply` → call respective scripts/; add delegate-to-process-odoo-action for all `odoo_*` action types; update to call `update-dashboard` skill after every processed approval
- [x] T053 [P] Create `./README.md`: architecture overview (Perception→Reasoning→Action diagram), tech stack table, quickstart (reference quickstart.md), CLI reference table, vault state machine diagram, tier comparison (Earlier Prototype/earlier prototype/Nestaro Pilot), Nestaro Pilot-specific features section, security disclosure
- [x] T054 Run `python scripts/validate_dry_run.py` end-to-end smoke test — verify PASS on all checks
- [x] T055 [P] Verify `vault/Dashboard.md` updates correctly after each vault state change by running orchestrator with 1 test item and inspecting Dashboard after each stage

**Checkpoint**: All 8 phases complete. Full Nestaro Pilot tier operational. validate_dry_run.py PASS.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 only — starts after Foundation
- **US2 (Phase 4)**: Depends on Phase 2 only — can run parallel with US1
- **US3 (Phase 5)**: Depends on US2 completion (needs odoo-mcp working)
- **US4 (Phase 6)**: Depends on Phase 2 only — can run parallel with US1/US2
- **US5 (Phase 7)**: Depends on US1, US2, US4 — all paths must exist before testing
- **Polish (Phase 8)**: Depends on all user story phases complete

### User Story Dependencies

- **US1** (P1): After Foundation — no story deps
- **US2** (P1): After Foundation — no story deps, parallel with US1
- **US3** (P2): After US2 — needs Odoo MCP working
- **US4** (P2): After Foundation — no story deps, parallel with US1/US2
- **US5** (P3): After US1 + US2 + US4 — tests all paths

### Parallel Opportunities

Within Phase 1: T003–T008 all run in parallel
Within Phase 2: T011–T018 all run in parallel
Within Phase 3: T022–T027 all run in parallel (6 files, no deps between them)
Within Phase 7: T042–T045 all run in parallel (4 different watcher files)
US1 (Phase 3) and US2 (Phase 4) can run in parallel after Foundation
US4 (Phase 6) can run in parallel with US1 and US2

---

## Implementation Strategy

### MVP First (US1 + US2 only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: US1 (social media) → **STOP and VALIDATE independently**
4. Complete Phase 4: US2 (Odoo MCP) → **STOP and VALIDATE independently**
5. Demo: drop Facebook DM → vault pipeline → Done/; create Odoo invoice via HITL

### Incremental Delivery

1. Setup + Foundation → base working
2. Add US1 → social channels live (MVP!)
3. Add US2 → accounting live
4. Add US3 → CEO briefing with live data
5. Add US4 → autonomous multi-step processing
6. Add US5 → hardened error recovery
7. Polish → production-ready Nestaro Pilot tier

### Parallel Strategy (if working with more than one dev)

- Dev A: US1 (social watchers + scripts: T022–T030)
- Dev B: US2 (odoo-mcp + skill: T031–T036)
- After Foundation complete, both streams run fully independently

---

## Notes

- **[P]** tasks = different files, no dependencies between them
- **[Story]** label maps task to spec.md user story for traceability
- Each user story is independently completable and testable
- DRY_RUN=true MUST be verified at every action-execution task
- Commit after each phase checkpoint
- earlier prototype is NOT modified — Nestaro Pilot is fully self-contained
- odoo-mcp runs on-demand (Claude MCP), NOT as PM2 process
- Ralph Wiggum exit code 2 = re-inject; exit code 0 = allow exit

---

## Task Count Summary

| Phase | Tasks | Story | Parallel |
|-------|-------|-------|---------|
| Phase 1: Setup | T001–T008 | — | T003–T008 (6 tasks) |
| Phase 2: Foundational | T009–T021 | — | T011–T018 (8 tasks) |
| Phase 3: US1 Social Media | T022–T030 | US1 | T022–T027 (6 tasks) |
| Phase 4: US2 Odoo MCP | T031–T036 | US2 | none |
| Phase 5: US3 CEO Briefing | T037–T039 | US3 | none |
| Phase 6: US4 Ralph Wiggum | T040–T041 | US4 | none |
| Phase 7: US5 Error Recovery | T042–T047 | US5 | T042–T045 (4 tasks) |
| Phase 8: Polish | T048–T055 | — | T050, T052, T053, T055 |
| **Total** | **55 tasks** | | **24 parallelizable** |
