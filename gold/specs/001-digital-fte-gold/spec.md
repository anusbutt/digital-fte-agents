# Feature Specification: Digital FTE Gold — Autonomous AI Employee

**Feature Branch**: `001-digital-fte-gold`
**Created**: 2026-03-13
**Status**: Draft
**Input**: Gold tier Digital FTE autonomous employee with Odoo accounting MCP,
Facebook/Instagram/Twitter watchers, Ralph Wiggum loop, enhanced CEO briefing,
multiple MCP servers, and comprehensive error recovery.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Social Media Monitoring & Posting (Priority: P1)

As the business owner, I want the AI employee to monitor my Facebook,
Instagram, and Twitter/X accounts for mentions, direct messages, and comments,
and to draft posts for my approval before publishing — so that my social media
presence is managed proactively without me spending time on it daily.

**Why this priority**: Social media is a lead generation channel. Missing
messages or failing to post consistently costs revenue. This extends Silver's
proven LinkedIn pattern to three new platforms.

**Independent Test**: Drop a simulated Facebook message file into
`vault/Inbox/`, verify it appears in `vault/Needs_Action/`, verify Claude
creates a plan in `vault/Plans/`, verify an approval request appears in
`vault/Pending_Approval/`, move it to `vault/Approved/`, verify the post
script runs (DRY_RUN=true logs the action), verify `vault/Done/` contains
the completed item and `vault/Logs/` contains the JSON audit entry.

**Acceptance Scenarios**:

1. **Given** a new Facebook DM arrives, **When** the Facebook watcher polls
   and detects it, **Then** a structured `.md` file appears in
   `vault/Needs_Action/` within the watcher's poll interval (≤ 60s).

2. **Given** a `FACEBOOK_` item in `vault/Needs_Action/`, **When** the
   orchestrator triggers the triage skill, **Then** Claude creates an action
   plan in `vault/Plans/` and an approval request in `vault/Pending_Approval/`
   (all social actions require HITL per constitution Principle IV).

3. **Given** a scheduled daily social post time (configurable), **When** the
   orchestrator triggers the generate-social-post skill, **Then** a draft post
   covering all three platforms (Facebook, Instagram, Twitter) appears in
   `vault/Pending_Approval/` for human review.

4. **Given** an approval file is moved to `vault/Approved/`, **When** the
   orchestrator detects it, **Then** the appropriate post script (facebook,
   instagram, or twitter) executes and logs the result to `vault/Logs/`.

5. **Given** `DRY_RUN=true`, **When** any social action is triggered,
   **Then** no actual post is published; the action is logged with
   `"result": "dry_run"`.

---

### User Story 2 — Odoo Accounting Integration via MCP (Priority: P1)

As the business owner, I want the AI employee to create invoices, record
payments, and retrieve financial summaries directly from my local Odoo
accounting system — so that my books are always up to date and I never
have to manually enter transactions.

**Why this priority**: Accounting automation is a core Gold requirement and
the primary differentiator from Silver. Without it, the CEO briefing has no
live financial data.

**Independent Test**: With Odoo running via Docker, trigger a manual invoice
creation request by dropping a file into `vault/Inbox/`. Verify the triage
skill creates a plan, an approval request appears for the invoice creation,
approve it, verify the odoo-mcp tool is called (DRY_RUN logs the call),
verify the invoice appears in Odoo (or is logged in dry-run mode), verify
audit log is written.

**Acceptance Scenarios**:

1. **Given** a client invoice request arrives (via any channel), **When**
   the triage skill identifies it as an invoice action, **Then** an approval
   request is created in `vault/Pending_Approval/` with invoice details
   (client, amount, description) before any Odoo call is made.

2. **Given** an approved invoice creation request, **When** the orchestrator
   calls the odoo-mcp `create_invoice` tool, **Then** a draft invoice appears
   in Odoo with the correct client, amount, and line items.

3. **Given** an approved `post_invoice` action, **When** odoo-mcp calls
   `post_invoice`, **Then** the Odoo invoice status changes from `draft` to
   `posted` and an email-ready PDF is available.

4. **Given** a `get_financial_summary` request from the briefing skill,
   **When** odoo-mcp queries Odoo, **Then** it returns MTD revenue, total
   outstanding, count of unpaid invoices, and list of overdue invoices
   (> 30 days) within 5 seconds.

5. **Given** Odoo is unreachable (Docker stopped), **When** odoo-mcp is
   called, **Then** the error is caught, logged as `"result": "failure"`,
   and a `SYSTEM_ODOO_UNREACHABLE.md` file is written to `vault/Needs_Action/`
   to alert the human — no retry is attempted for financial actions.

---

### User Story 3 — Enhanced CEO Briefing with Live Accounting Data (Priority: P2)

As the business owner, I want my Monday morning CEO briefing to include live
financial data pulled directly from Odoo — revenue earned, unpaid invoices,
overdue clients, and proactive suggestions — so that I start each week with
a complete business picture in under 2 minutes of reading.

**Why this priority**: Depends on US2 (Odoo MCP) being complete. Transforms
the briefing from a Markdown summary into a real executive dashboard with
live numbers.

**Independent Test**: Trigger `python main.py briefing` with Odoo running and
at least one posted invoice. Verify the generated briefing in
`vault/Briefings/` contains: MTD revenue figure, count of unpaid invoices,
list of overdue items, completed tasks from the week, and at least one
proactive suggestion (e.g., overdue invoice reminder or unused subscription
flag).

**Acceptance Scenarios**:

1. **Given** it is the scheduled briefing day and time, **When** the
   orchestrator triggers the `generate-accounting-briefing` skill, **Then**
   Claude calls odoo-mcp for financial data and produces a briefing written
   to `vault/Briefings/YYYY-MM-DD_Briefing.md` within 60 seconds.

2. **Given** the briefing is generated, **When** a human opens
   `vault/Dashboard.md`, **Then** it shows a link to the latest briefing,
   current MTD revenue vs. target, and count of overdue invoices.

3. **Given** an invoice is overdue by more than 30 days, **When** the
   briefing skill detects it, **Then** the briefing includes a proactive
   suggestion: "Client X invoice of $Y is 30+ days overdue — send reminder?"
   routed to `vault/Pending_Approval/` as an optional action.

---

### User Story 4 — Ralph Wiggum Loop: Autonomous Multi-Step Task Completion (Priority: P2)

As the business owner, I want the AI employee to keep working on a multi-step
task until it is fully complete — without me having to re-run commands — so
that complex tasks like "process all inbox items" complete autonomously.

**Why this priority**: Without the Ralph Wiggum loop, Claude exits after each
task and the orchestrator must re-invoke it. The loop enables true autonomy
for multi-step workflows.

**Independent Test**: Place 3 files in `vault/Inbox/`. Run the orchestrator.
Verify that without any manual re-invocation, all 3 files are processed
through the full pipeline (Needs_Action → Plans → Pending_Approval or Done)
before Claude exits. Verify the stop hook fires between items and re-injects
the prompt.

**Acceptance Scenarios**:

1. **Given** multiple items in `vault/Needs_Action/`, **When** Claude begins
   processing and tries to exit after completing one item, **Then** the stop
   hook checks if remaining items exist and re-injects the orchestrator prompt.

2. **Given** all items have been processed (moved to `vault/Done/` or
   `vault/Pending_Approval/`), **When** Claude tries to exit, **Then** the
   stop hook allows the exit cleanly.

3. **Given** the loop has iterated 10 times (max iterations), **When** items
   still remain unprocessed, **Then** the stop hook allows exit and writes a
   `SYSTEM_MAX_ITERATIONS.md` warning to `vault/Needs_Action/`.

---

### User Story 5 — Comprehensive Error Recovery & Graceful Degradation (Priority: P3)

As the business owner, I want the AI employee to recover automatically from
common failures (network timeouts, expired tokens, crashed watchers) and alert
me only when human intervention is truly needed — so that the system runs
reliably 24/7 without babysitting.

**Why this priority**: Foundational for always-on operation. Builds on Silver's
basic backoff with full error taxonomy and degradation strategies per
constitution Principle VI.

**Independent Test**: Stop the Docker Odoo container mid-operation. Verify the
system writes an alert file to `vault/Needs_Action/`, does not crash other
watchers, and continues processing non-Odoo items. Restart Docker. Verify
operations resume normally.

**Acceptance Scenarios**:

1. **Given** a watcher experiences a transient network error, **When** the
   error occurs, **Then** the watcher retries with exponential backoff
   (1s, 2s, 4s) before escalating — no human alert for transient failures.

2. **Given** a Gmail OAuth token expires, **When** the Gmail watcher detects
   a 401 response, **Then** it immediately pauses, writes
   `SYSTEM_AUTH_FAILURE_GMAIL.md` to `vault/Needs_Action/`, and does not
   retry until the human re-authenticates.

3. **Given** a watcher process crashes, **When** PM2 detects the exit,
   **Then** PM2 automatically restarts the process within 5 seconds without
   human intervention.

4. **Given** `DRY_RUN=true` is set, **When** any action is triggered
   (email send, social post, Odoo call, WhatsApp reply), **Then** the action
   is logged with `"result": "dry_run"` and zero external side effects occur.

---

### Edge Cases

- What happens when Odoo Docker container is stopped during an MCP call?
  → Error caught, logged, alert written to vault, no retry for financial actions.
- What happens when a social media session expires (Playwright cookie timeout)?
  → Watcher writes `SYSTEM_AUTH_FAILURE_<PLATFORM>.md`, pauses that watcher only.
- What happens when `vault/Pending_Approval/` has an item older than 24 hours?
  → Orchestrator marks it `status: expired`, moves to `vault/Done/`, logs the expiry.
- What happens when Ralph Wiggum loop hits max iterations (10)?
  → Stop hook allows exit, writes `SYSTEM_MAX_ITERATIONS.md` to `vault/Needs_Action/`.
- What happens when all 3 social platforms are down simultaneously?
  → Each watcher fails independently with backoff; others continue unaffected.
- What happens when `DRY_RUN=true` and human approves an action?
  → Action is logged as `"result": "dry_run"`, no external call made.
- What happens when two watchers detect the same item (duplicate detection)?
  → File prefix + timestamp in filename ensures uniqueness; orchestrator skips
  already-processed items by checking `vault/Plans/` for existing plan files.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST monitor Facebook, Instagram, and Twitter/X accounts
  for new messages, mentions, and comments using browser-based automation.
- **FR-002**: System MUST draft social media posts for all three platforms and
  route them to `vault/Pending_Approval/` before any publishing occurs.
- **FR-003**: System MUST connect to a local Odoo Community instance and expose
  at minimum these operations: get invoices, create invoice, post invoice,
  record payment, get partners, get financial summary.
- **FR-004**: All Odoo financial actions (invoice creation, posting, payment
  recording) MUST require human approval via the vault HITL workflow.
- **FR-005**: The CEO briefing MUST pull live financial data from Odoo and
  include: MTD revenue, outstanding balance, unpaid invoice count, overdue
  invoices list, and at least one proactive suggestion.
- **FR-006**: System MUST implement a stop hook that re-injects the
  orchestrator prompt when Claude exits with unprocessed items remaining in
  `vault/Needs_Action/`, up to a maximum of 10 iterations.
- **FR-007**: System MUST implement error recovery per constitution Principle
  VI: exponential backoff for transient errors, immediate pause + human alert
  for auth errors, PM2 auto-restart for process crashes.
- **FR-008**: Every action MUST be logged to `vault/Logs/YYYY-MM-DD.json` in
  the schema defined in constitution Principle VII.
- **FR-009**: System MUST operate safely with `DRY_RUN=true` as default —
  no external actions occur until explicitly set to `DRY_RUN=false`.
- **FR-010**: Gold tier MUST be fully self-contained; no runtime dependencies
  on `bronze/` or `silver/` directories.
- **FR-011**: All AI logic MUST be implemented as Markdown agent skills;
  no business logic inside Python watchers or MCP servers.
- **FR-012**: System MUST expose a CLI (`main.py`) with commands for all
  watchers, MCP setup, social media posting, briefing generation, and
  health checks.
- **FR-013**: Approval files older than 24 hours MUST be automatically expired
  by the orchestrator and moved to `vault/Done/` with `status: expired`.
- **FR-014**: The `vault/Dashboard.md` MUST be updated after every significant
  vault state change (new item, approval, completion, expiry, error).

### Key Entities

- **VaultItem**: A Markdown file representing one unit of work; has type
  (email, whatsapp, facebook, instagram, twitter, file, system), status,
  source, timestamp, priority.
- **ActionPlan**: A Markdown file in `vault/Plans/` describing steps Claude
  will take; has `approval_required` boolean flag and action type.
- **ApprovalRequest**: A Markdown file in `vault/Pending_Approval/` with
  action details, created timestamp, expiry (24h), and status field.
- **AuditLogEntry**: A JSON object appended to `vault/Logs/YYYY-MM-DD.json`;
  follows the schema in constitution Principle VII exactly.
- **OdooInvoice**: Represents an Odoo `account.move` record; has partner,
  amount, currency, state (draft/posted/paid), due date.
- **CEOBriefing**: A Markdown file in `vault/Briefings/` combining vault
  activity (Done/ counts), Odoo financial data, and proactive suggestions.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All three social media watchers (Facebook, Instagram, Twitter)
  detect new items within their configured poll interval (≤ 60 seconds) and
  create structured vault items without human intervention.
- **SC-002**: The Odoo MCP server responds to all 6 tool calls within 5 seconds
  under normal operating conditions (Odoo Docker running locally).
- **SC-003**: The CEO briefing is generated within 60 seconds of being triggered
  and includes at least 4 sections: Revenue, Unpaid Invoices, Completed Tasks,
  and Proactive Suggestions — all populated with live data.
- **SC-004**: The Ralph Wiggum loop successfully processes a batch of 5 inbox
  items end-to-end (Inbox → Done/Pending_Approval) without any manual
  re-invocation of Claude.
- **SC-005**: With `DRY_RUN=true`, the full system runs for 10 minutes with
  simulated inputs and produces zero external side effects (no emails sent,
  no social posts published, no Odoo records created).
- **SC-006**: PM2 auto-restarts any crashed watcher process within 10 seconds,
  and the Dashboard reflects the restart within the next poll cycle.
- **SC-007**: Every action logged to `vault/Logs/` passes schema validation
  (all 9 required fields present, ISO timestamp format, valid action_type value).
- **SC-008**: The full Gold setup (Docker Odoo + all watchers + PM2) can be
  reproduced on a fresh machine by following the `quickstart.md` guide in
  under 60 minutes.
