# Research: Digital FTE Silver

**Feature**: 001-digital-fte-silver
**Date**: 2026-02-18

## R1: Gmail API — OAuth2 Polling Pattern

**Decision**: Use Google Gmail API v1 with OAuth2 for polling unread emails.

**Rationale**: Official API with reliable authentication. Polling at 60s intervals stays well within Gmail API quotas (250 units/second for users, `messages.list` costs 5 units). OAuth2 provides secure, revocable access.

**Alternatives Considered**:
- IMAP with `imaplib`: Simpler but no push notifications, less reliable filtering, harder to manage labels.
- Gmail Push Notifications (Pub/Sub): More complex setup requiring Google Cloud project with Pub/Sub topic. Overkill for single-user polling.

**Key Implementation Details**:
- Python packages: `google-api-python-client`, `google-auth-oauthlib`, `google-auth-httplib2`
- Scopes: `https://www.googleapis.com/auth/gmail.readonly`, `https://www.googleapis.com/auth/gmail.modify` (to mark as read)
- Query filter: `is:unread -category:{promotions,social,updates,forums}`
- Additional filtering in code: skip subjects with OTP/verification patterns, skip senders with `noreply@`, `no-reply@`, known newsletter domains
- Token storage: `token.json` file (path in `.env`, excluded from git)
- Credentials: `credentials.json` from Google Cloud Console (path in `.env`)

## R2: Playwright — WhatsApp Web Scraping

**Decision**: Use Playwright with persistent Chromium context to monitor WhatsApp Web.

**Rationale**: WhatsApp has no public API for personal accounts. Playwright provides reliable browser automation with persistent sessions (survives restarts without re-scanning QR).

**Alternatives Considered**:
- Selenium: Older, slower, less reliable session management.
- whatsapp-web.js (Node.js): Reverse-engineers WhatsApp protocol. Risk of account ban. Less stable.
- WhatsApp Business API: Requires business verification, costs money, not for personal use.

**Key Implementation Details**:
- Python package: `playwright` (install browsers: `playwright install chromium`)
- Persistent context: `browser_type.launch_persistent_context(user_data_dir=...)` preserves login
- User data directory stored in `.env` as `WHATSAPP_USER_DATA_DIR`
- Detection flow:
  1. Navigate to `https://web.whatsapp.com`
  2. Wait for chat list to load (selector: `div[aria-label="Chat list"]` or similar)
  3. Find unread chat badges (green circles with numbers)
  4. Click into each unread chat, read latest messages
  5. Check message text against keyword list
  6. Extract: contact name, message text, timestamp
- QR code detection: check for QR canvas element → session expired → alert
- Polling interval: 30 seconds

## R3: Playwright — LinkedIn Posting

**Decision**: Use Playwright with persistent Chromium context to post on LinkedIn.

**Rationale**: LinkedIn API requires app approval (takes weeks). Playwright with persistent login is fastest for hackathon timeline.

**Alternatives Considered**:
- LinkedIn Marketing API: Official but requires app review, organization page. Too slow for hackathon.
- Manual copy-paste: Not automated. Defeats purpose.

**Key Implementation Details**:
- Persistent context shares pattern with WhatsApp (separate user data dir)
- User data directory in `.env` as `LINKEDIN_USER_DATA_DIR`
- Post flow:
  1. Navigate to `https://www.linkedin.com/feed/`
  2. Click "Start a post" button
  3. Type post content into editor
  4. Click "Post" button
  5. Verify post appeared
- CAPTCHA handling: detect CAPTCHA elements → log, alert, exit immediately (no retry)
- Rate limit: 1 post per day maximum

## R4: MCP Server — Node.js/TypeScript Email Implementation

**Decision**: Node.js MCP server written in TypeScript, using `@modelcontextprotocol/sdk` and `googleapis` npm packages. Executed directly via `tsx` (no build step).

**Rationale**: MCP SDK is most mature in Node.js. Hackathon requires 1 MCP server. Gmail API has excellent Node.js support. TypeScript adds type safety and better developer experience. `tsx` allows running TypeScript directly without a separate compilation step.

**Alternatives Considered**:
- Plain JavaScript: Works but lacks type safety; TypeScript catches errors at write time.
- Python MCP SDK: Exists (`mcp` package) but less documented for server creation.
- Direct Gmail API in Python: Works but doesn't fulfill hackathon's MCP server requirement.
- TypeScript with tsc build step: Adds complexity; `tsx` is simpler for a sidecar project.

**Key Implementation Details**:
- Transport: stdio (Claude Code connects via process spawn)
- Tools exposed:
  - `send_email`: `{to, subject, body, cc?, bcc?}` → `{success, messageId}`
  - `draft_email`: `{to, subject, body, cc?, bcc?}` → `{success, draftId}`
- OAuth2: shares credentials with Gmail watcher. Separate `token-mcp.json` (different scope: `gmail.send`)
- TypeScript executed via `tsx` (no build step): `npx tsx index.ts`
- Registration: Add to `.mcp.json` under `mcpServers`

## R5: PM2 — Process Management on Windows

**Decision**: PM2 with ecosystem config managing all long-running processes.

**Rationale**: PM2 is cross-platform, handles auto-restart, log rotation, and process monitoring. Already specified in constitution.

**Key Implementation Details**:
- Install: `npm install -g pm2`
- Config file: `scripts/pm2_ecosystem.config.js`
- Processes: filesystem-watcher, gmail-watcher, whatsapp-watcher, orchestrator, email-mcp
- Each process: `max_restarts: 10`, `restart_delay: 5000`, `autorestart: true`
- PM2 on Windows: works via `pm2 start ecosystem.config.js`
- Logs: PM2 logs separate from vault audit logs (PM2 logs are for debugging, vault logs for business audit)

## R6: Windows Task Scheduler — Scheduled Tasks

**Decision**: Python script using `schtasks` CLI to create Windows Task Scheduler entries.

**Rationale**: Native Windows scheduling. No additional dependencies. Constitution specifies Task Scheduler.

**Key Implementation Details**:
- `schtasks /create` commands for:
  - LinkedIn post: `/sc daily /st 09:00 /d MON,TUE,WED,THU,FRI`
  - CEO briefing: `/sc weekly /d MON /st 08:00`
  - PM2 health check: `/sc minute /mo 5`
- Each task runs a Python script or batch file
- "Run as soon as possible after missed trigger" flag: `/rl HIGHEST`
- Setup script: `scripts/setup_scheduler.py`

## R7: Vault Restructuring — File Migration

**Decision**: Move existing flat vault folders into `vault/` subdirectory.

**Rationale**: Constitution Principle I (Local-First Privacy) and Development Workflow rule 6 require separation.

**Key Implementation Details**:
- Folders to move: Inbox, Needs_Action, Plans, Pending_Approval, Approved, Rejected, Done, Briefings, Accounting (Logs created at runtime)
- Documents to move: Dashboard.md, Company_Handbook.md, Business_Goals.md
- Code changes: Update `VAULT_PATH` default in all watchers and orchestrator
- `.env.example`: Change `VAULT_PATH=./vault`
- Skills: Update vault path references
- Orchestrator: `vault_path` now points to `vault/` not repo root
- `skills_dir`: stays at repo root `skills/` (NOT inside vault — skills are code, not business docs)
