# Feature Specification: Digital FTE Silver — Functional Assistant

**Feature Branch**: `001-digital-fte-silver`
**Created**: 2026-02-18
**Status**: Draft
**Input**: Silver tier hackathon deliverables — multi-watcher, LinkedIn posting, email MCP, HITL approval, scheduling, Agent Skills

## User Scenarios & Testing

### User Story 1 — Vault Restructuring (Priority: P1)

As a developer, I want the Obsidian vault separated from the code
repository into a `vault/` subdirectory, so that Obsidian shows only
business documents and the codebase stays clean.

**Why this priority**: Foundational structural change. Every other story
writes to the vault. This MUST be done first.

**Independent Test**: Open `vault/` in Obsidian — verify only business
folders are visible. Run the filesystem watcher — verify it targets `vault/Inbox`.

**Acceptance Scenarios**:

1. **Given** the current flat structure (code mixed with vault folders),
   **When** the restructuring is applied,
   **Then** all vault folders (Inbox, Needs_Action, Plans, Pending_Approval,
   Approved, Rejected, Done, Briefings, Accounting, Logs) exist under `vault/`.

2. **Given** the restructured vault,
   **When** Obsidian opens the `vault/` directory,
   **Then** only business-relevant folders and documents are visible — no
   Python code, no .git, no pyproject.toml.

3. **Given** vault documents (Dashboard.md, Company_Handbook.md, Business_Goals.md),
   **When** the restructuring is applied,
   **Then** they reside in `vault/` and all watchers/orchestrator reference
   `vault/` as their working directory.

**Error Handling**:

- File move fails mid-operation: Verify all files present after move.
- Watcher references wrong path: Startup validation checks vault path
  exists before entering the watch loop.

---

### User Story 2 — Gmail Monitoring and Smart Reply (Priority: P1)

As the business owner, I want the AI Employee to monitor my Gmail inbox
and automatically reply to emails that request a response, so I never
miss a client inquiry while ignoring noise (OTPs, newsletters, software
notifications).

**Why this priority**: Email is the primary business communication channel.
Missing a client email directly costs revenue.

**Independent Test**: Send a test email asking "Can you send me a quote?" —
verify the system triages it, creates a plan, and either auto-sends or
creates an approval request.

**Acceptance Scenarios**:

1. **Given** a new unread important email from a client asking for a response,
   **When** the Gmail watcher polls and detects it,
   **Then** it creates an `EMAIL_{id}.md` file in `vault/Needs_Action/` with
   YAML frontmatter: type, from, subject, snippet, received date, priority,
   status=pending.

2. **Given** a triaged email in `vault/Needs_Action/`,
   **When** the orchestrator invokes the triage skill,
   **Then** Claude reads the email + Company_Handbook.md and creates a plan
   with reply steps and determines if approval is needed.

3. **Given** a non-sensitive email reply (known contact, no financial content),
   **When** the plan executes,
   **Then** the email-mcp sends the reply directly — no approval request created.

4. **Given** a sensitive email reply (new contact, financial content, invoice),
   **When** the plan executes,
   **Then** an approval request is created in `vault/Pending_Approval/` and
   the email is NOT sent until the human approves.

5. **Given** an OTP, newsletter, or software notification email,
   **When** the Gmail watcher detects it,
   **Then** it is ignored — no file created in `vault/Needs_Action/`.

**Error Handling**:

- Gmail API 401 (expired token): Log, pause polling, alert on Dashboard
  that re-authentication is needed.
- Gmail API 429 (rate limit): Exponential backoff, retry after delay.
- Gmail API network timeout: Log, skip cycle, retry next interval.
- Email-mcp send failure: Log, keep approval file, alert on Dashboard.

---

### User Story 3 — WhatsApp Monitoring and Reply (Priority: P1)

As the business owner, I want the AI Employee to monitor my WhatsApp Web
messages and reply to urgent/business messages, so I can respond to clients
even when away.

**Why this priority**: WhatsApp is a primary client communication channel
alongside email. Equal priority.

**Independent Test**: Send a WhatsApp message containing "invoice" — verify
the system detects it, creates a triage item, plans a reply, and requests
approval before sending.

**Acceptance Scenarios**:

1. **Given** a new unread WhatsApp message containing a business keyword
   (urgent, invoice, payment, pricing, help, quote, project, deadline),
   **When** the WhatsApp watcher scans via Playwright,
   **Then** it creates a `WHATSAPP_{contact}_{timestamp}.md` in
   `vault/Needs_Action/` with: type, from, message text, keywords, priority,
   status=pending.

2. **Given** a triaged WhatsApp item,
   **When** the orchestrator invokes the triage skill,
   **Then** Claude creates a plan with a suggested reply and marks it as
   approval_required=true (WhatsApp replies always require approval).

3. **Given** an approved WhatsApp reply,
   **When** the human moves the approval file to `vault/Approved/`,
   **Then** the reply skill uses Playwright to send the reply in WhatsApp
   Web and logs the action.

4. **Given** a casual message with no business keywords ("haha", "ok", "thanks"),
   **When** the WhatsApp watcher scans it,
   **Then** it is ignored — no file created.

**Error Handling**:

- WhatsApp Web session expired: Log, alert user on Dashboard to re-scan
  QR code. Pause watcher until session restored.
- Playwright browser crash: PM2 auto-restarts the watcher.
- Message send fails: Log, keep approval file for retry, alert Dashboard.
- Network timeout during scan: Log, skip cycle, retry next interval.

---

### User Story 4 — Email MCP Server (Priority: P2)

As the business owner, I want a dedicated MCP server for sending and
drafting emails through Gmail, so planned email actions execute
programmatically after approval.

**Why this priority**: Required by US2 (Gmail reply). Builds the action
layer that turns plans into real external actions.

**Independent Test**: Call email-mcp send_email with a test recipient —
verify email sent via Gmail API and logged.

**Acceptance Scenarios**:

1. **Given** an approved non-sensitive email action,
   **When** the orchestrator calls email-mcp `send_email`,
   **Then** the email is sent via Gmail API with to, subject, body, and
   optional attachment.

2. **Given** a sensitive email action,
   **When** the orchestrator prepares it,
   **Then** email-mcp `draft_email` creates a Gmail draft (not sent) and an
   approval request is created for human review.

3. **Given** the email-mcp server is running,
   **When** Claude Code invokes it,
   **Then** it authenticates via OAuth2 from environment variables.

4. **Given** an email is sent or drafted,
   **When** the action completes,
   **Then** the result (success/failure, message ID) is returned and logged.

**Error Handling**:

- OAuth2 token expired: Attempt refresh. If refresh fails, alert user.
- Gmail API 5xx: Retry once after 5 seconds. If still failing, log and alert.
- Invalid recipient: Return error, do NOT retry, log.
- Attachment not found: Return error, do NOT send partial email.
- MCP server crash: PM2 auto-restarts.

---

### User Story 5 — LinkedIn Auto-Posting (Priority: P2)

As an AI Engineer freelancer, I want the AI Employee to generate and post
business content on LinkedIn daily, so I maintain visibility and generate
leads without manual effort.

**Why this priority**: Revenue-generating but not time-sensitive. Functions
independently once core watchers work.

**Independent Test**: Trigger the posting skill — verify it generates a post,
creates an approval request, and after approval publishes via Playwright.

**Acceptance Scenarios**:

1. **Given** the scheduled daily posting time (default 9:00 AM weekdays),
   **When** Task Scheduler triggers the posting skill,
   **Then** Claude generates a professional LinkedIn post about AI automation,
   digital FTEs, or industry insights.

2. **Given** a generated LinkedIn post,
   **When** the post content is ready,
   **Then** an approval request is ALWAYS created in `vault/Pending_Approval/`.
   LinkedIn posts are never auto-sent.

3. **Given** an approved LinkedIn post,
   **When** the human moves the approval file to `vault/Approved/`,
   **Then** the poster uses Playwright to publish the post on LinkedIn.

4. **Given** a published post,
   **When** it succeeds,
   **Then** it is logged and Dashboard.md is updated.

**Error Handling**:

- LinkedIn session expired: Log, alert user to re-login. Pause posting.
- CAPTCHA/automation detection: Log, alert, pause. Do NOT retry automatically.
- Content generation fails: Log, skip this day, try next day.
- Playwright navigation timeout: Retry once, then log and skip.

---

### User Story 6 — HITL Approval Workflow (Priority: P2)

As the business owner, I want a clear approval workflow where the AI asks
permission before sensitive actions, so I maintain control.

**Why this priority**: Safety mechanism all action stories depend on.
Existing Bronze flow is extended for new action types.

**Independent Test**: Create a test approval file in `vault/Pending_Approval/`,
move to `vault/Approved/` — verify the orchestrator triggers the action.

**Acceptance Scenarios**:

1. **Given** any sensitive action (per Company Handbook rules),
   **When** the triage skill creates a plan,
   **Then** an approval request is created with: action type, details,
   amount (if financial), recipient, reason, related plan, created,
   expiry (24h), status=pending.

2. **Given** an approval file moved to `vault/Approved/`,
   **When** the orchestrator detects it (within 10 seconds),
   **Then** it triggers the planned action (email send, WhatsApp reply,
   LinkedIn post).

3. **Given** an approval file moved to `vault/Rejected/`,
   **When** the orchestrator detects it,
   **Then** it logs rejection, updates plan status, moves everything to Done/.

4. **Given** an expired approval request (24h passed),
   **When** expiry time is reached,
   **Then** system logs expiry but takes NO action. File stays for human.

5. **Given** an action meeting auto-approve criteria,
   **When** it is classified as non-sensitive,
   **Then** it executes immediately without an approval file.

**Error Handling**:

- Malformed YAML in approval file: Log, leave file in place, alert Dashboard.
- Action fails after approval: Log, do NOT move to Done/. Keep in Approved/
  for retry. Alert Dashboard.
- Missed file event: Startup scan catches unprocessed files on restart.

---

### User Story 7 — Scheduled Operations (Priority: P3)

As the business owner, I want automated scheduling so watchers run
continuously and periodic tasks trigger at the right times.

**Why this priority**: Makes the system truly autonomous. Added after core
functionality works.

**Independent Test**: Create a Task Scheduler entry for CEO briefing —
verify it triggers Monday morning and generates a briefing.

**Acceptance Scenarios**:

1. **Given** watchers need to run 24/7,
   **When** the system starts,
   **Then** PM2 launches and manages all watcher processes with auto-restart.

2. **Given** LinkedIn posting schedule (daily 9:00 AM weekdays),
   **When** the scheduled time arrives,
   **Then** Task Scheduler triggers the posting skill.

3. **Given** CEO Briefing schedule (Monday 8:00 AM),
   **When** Monday morning arrives,
   **Then** Task Scheduler triggers briefing generation to `vault/Briefings/`.

4. **Given** a scheduled task fails,
   **When** failure is detected,
   **Then** the error is logged and Dashboard reflects the missed task.

**Error Handling**:

- PM2 crashes: Task Scheduler watchdog checks PM2 every 5 minutes, restarts.
- Claude unavailable during scheduled task: Log, skip, try next time.
- System asleep during scheduled time: "Run as soon as possible after missed
  trigger" setting enabled.

---

### User Story 8 — Agent Skills for New Functionality (Priority: P3)

As a developer, I want all new AI capabilities packaged as Agent Skills
following the established pattern.

**Why this priority**: Cross-cutting concern. Skills are created alongside
each feature implementation.

**Independent Test**: Invoke each new skill with Claude CLI and mock
context — verify expected output structure.

**Acceptance Scenarios**:

1. **Given** any new AI capability,
   **When** it is implemented,
   **Then** it exists as a `.md` file in `skills/` with: Purpose, Instructions,
   Rules, and Tools Required.

2. **Given** an Agent Skill,
   **When** the orchestrator invokes it,
   **Then** it receives context files and vault path, produces output in
   correct vault folders.

3. **Given** existing Bronze skills (triage-inbox, update-dashboard,
   generate-briefing, process-approval),
   **When** Silver features are added,
   **Then** existing skills are updated to handle EMAIL_ and WHATSAPP_ types
   alongside FILE_ items.

**Error Handling**:

- Skill times out (>5 min): Log, mark plan as failed.
- Malformed output: Orchestrator validates YAML before accepting. Log and
  alert on malformed output.

---

### Edge Cases

- Gmail and WhatsApp detect the same conversation: Each creates a separate
  triage item. Claude may consolidate during planning.
- Multiple watchers write to Needs_Action simultaneously: Unique prefixes
  (EMAIL_, WHATSAPP_, FILE_) prevent filename collisions.
- vault/Logs/ grows very large: Logs older than 90 days may be archived
  during weekly maintenance.
- User offline for days: Watchers queue items. Approval requests accumulate.
  User processes backlog on return.
- LinkedIn blocks Playwright session: System detects, pauses LinkedIn, alerts
  Dashboard. No automatic retry to avoid account ban.
- Gmail quota exceeded for the day: Watcher continues detecting but email-mcp
  queues sends for next day. Alert on Dashboard.

## Requirements

### Functional Requirements

- **FR-001**: System MUST monitor Gmail for new unread emails and create
  triage items for emails requesting a response.
- **FR-002**: System MUST ignore non-actionable emails (OTPs, newsletters,
  software notifications, informational updates).
- **FR-003**: System MUST monitor WhatsApp Web for messages containing
  business keywords and create triage items.
- **FR-004**: System MUST generate daily LinkedIn posts about AI engineering
  services and industry insights.
- **FR-005**: System MUST provide an MCP server for sending and drafting
  emails via Gmail API.
- **FR-006**: System MUST create approval requests for all sensitive actions
  before execution.
- **FR-007**: System MUST auto-execute non-sensitive actions without approval.
- **FR-008**: System MUST run watchers continuously with auto-restart via PM2.
- **FR-009**: System MUST trigger scheduled tasks via Windows Task Scheduler.
- **FR-010**: System MUST implement all AI capabilities as Agent Skills.
- **FR-011**: System MUST separate the Obsidian vault into `vault/` subdirectory.
- **FR-012**: System MUST log every action in structured format to vault/Logs/.
- **FR-013**: System MUST update Dashboard.md after every state change.
- **FR-014**: System MUST reply to WhatsApp messages via Playwright after approval.
- **FR-015**: System MUST send email replies via email-mcp (auto for non-sensitive,
  approval for sensitive).

### Key Entities

- **EmailItem**: Gmail email detected by watcher. Fields: id, from, subject,
  snippet, received_date, priority, status. Stored as `EMAIL_{id}.md`.

- **WhatsAppItem**: WhatsApp message detected by watcher. Fields: contact,
  message_text, keywords, detected_date, priority, status. Stored as
  `WHATSAPP_{contact}_{timestamp}.md`.

- **LinkedInPost**: Generated post awaiting approval. Fields: content, topic,
  generated_date, status, posted_date. Stored as `LINKEDIN_{date}.md`.

- **ActionPlan**: (Extended from Bronze) Now handles EMAIL_, WHATSAPP_ types
  in addition to FILE_.

- **ApprovalRequest**: (Extended from Bronze) New action types: email_send,
  email_draft, whatsapp_reply, linkedin_post.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Gmail watcher detects and triages actionable emails within
  3 minutes of receipt.
- **SC-002**: WhatsApp watcher detects keyword messages within 1 minute.
- **SC-003**: LinkedIn posts generated and queued for approval daily on weekdays.
- **SC-004**: Non-sensitive email replies sent within 5 minutes of detection.
- **SC-005**: Zero unapproved sensitive actions executed.
- **SC-006**: Watchers achieve 99%+ uptime via PM2 (measured over 7 days).
- **SC-007**: CEO Briefing generated every Monday morning automatically.
- **SC-008**: Every external action is logged — zero unlogged actions.
- **SC-009**: Obsidian vault shows only business documents (no code files).
- **SC-010**: All new AI capabilities exist as Agent Skill files.

### Assumptions

- User has working Google OAuth2 credentials for Gmail access.
- User has WhatsApp Web logged in with a persistent Playwright session.
- User has LinkedIn logged in with a persistent Playwright session.
- Windows Task Scheduler available with permission to create tasks.
- PM2 installed globally via npm.
- Windows 11 with Python 3.13+ and Node.js v24+ installed.
- Stable internet connection for API calls.
- DRY_RUN mode available for safe testing of all external actions.
