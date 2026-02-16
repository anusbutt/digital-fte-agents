# Feature Specification: AI Employee Foundation

**Feature Branch**: `001-ai-employee-foundation`
**Created**: 2026-02-15
**Status**: Draft
**Input**: User description: "A file-system-based AI Employee that monitors an Inbox folder for dropped files, triages and classifies them, creates action plans, manages a HITL approval workflow, updates an Obsidian dashboard, and generates weekly CEO briefings. All AI functionality implemented as Claude Code Agent Skills."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Drop File and Get It Triaged (Priority: P1)

As a freelancer, I drop a business document (invoice, receipt, client brief, contract) into my Inbox folder. The system detects the new file within seconds, classifies it by type, extracts key information, and creates a structured action item in the Needs_Action folder. I can see the new item appear in my Obsidian vault without any manual intervention.

**Why this priority**: This is the core value proposition. Without file detection and triage, nothing else works. This proves the system is "alive" and useful.

**Independent Test**: Drop a sample invoice PDF into /Inbox. Within 30 seconds, a metadata .md file appears in /Needs_Action with correct classification and extracted details.

**Acceptance Scenarios**:

1. **Given** the Inbox folder is being monitored, **When** I drop a file named "invoice_client_a.pdf" into /Inbox, **Then** within 30 seconds a metadata file appears in /Needs_Action with type "invoice", extracted client name, and status "pending"
2. **Given** a file is detected in /Inbox, **When** the watcher creates the metadata file, **Then** the original file is preserved and the metadata file contains YAML frontmatter with type, date, priority, and status fields
3. **Given** multiple files are dropped simultaneously, **When** the watcher processes them, **Then** each file gets its own metadata entry in /Needs_Action without data loss or corruption

---

### User Story 2 - Action Plan Creation and Dashboard Update (Priority: P2)

As a freelancer, after a file has been triaged into /Needs_Action, the AI reads the item, consults my Company Handbook rules, and creates an action plan with clear next steps. The Dashboard is updated to reflect the new pending item, giving me a single-pane view of my business status.

**Why this priority**: Triage alone is not enough -- the AI must reason about what to do and keep the dashboard current. This transforms raw file detection into actionable intelligence.

**Independent Test**: With a triaged item in /Needs_Action, trigger the AI. Verify a Plan .md file appears in /Plans with checkboxes, and Dashboard.md is updated with the new activity.

**Acceptance Scenarios**:

1. **Given** a triaged item exists in /Needs_Action, **When** the AI processes it, **Then** a plan file is created in /Plans with an objective, step-by-step checklist, and priority level
2. **Given** a plan is created, **When** the AI updates the dashboard, **Then** Dashboard.md shows the new item in the Recent Activity section with timestamp and description
3. **Given** the Company Handbook specifies "flag any invoice over $500 for approval", **When** the AI processes an invoice for $600, **Then** the plan includes an approval step and an approval request file is created in /Pending_Approval

---

### User Story 3 - HITL Approval Workflow (Priority: P2)

As a freelancer, when the AI determines an action requires my approval (based on Company Handbook rules), it creates an approval request file in /Pending_Approval and waits. I review the request in Obsidian, and either approve (move to /Approved) or reject (move to /Rejected). The system detects my decision and proceeds accordingly.

**Why this priority**: Safety-critical. Without HITL, the AI cannot be trusted with sensitive actions. This is essential for the security story (15% of judging).

**Independent Test**: Create a mock sensitive action. Verify approval file appears in /Pending_Approval. Move it to /Approved. Verify the system detects approval and logs the action.

**Acceptance Scenarios**:

1. **Given** the AI detects a sensitive action (per Company Handbook thresholds), **When** it creates an approval request, **Then** a file appears in /Pending_Approval with action details, amount, recipient, reason, and expiry date
2. **Given** an approval file exists in /Pending_Approval, **When** I move it to /Approved, **Then** the system logs the approved action to /Logs and moves all related files to /Done
3. **Given** an approval file exists in /Pending_Approval, **When** I move it to /Rejected, **Then** the system logs the rejection and moves related files to /Done with status "rejected"

---

### User Story 4 - Weekly CEO Briefing (Priority: P3)

As a freelancer, every week (or on demand) the AI generates a comprehensive CEO Briefing summarizing my week: completed tasks, revenue tracking against goals, bottlenecks, and proactive suggestions. The briefing appears in /Briefings and is linked from the Dashboard.

**Why this priority**: This is the "wow factor" demo feature. It transforms the AI from reactive to proactive. Judges will see this as the standout innovation feature.

**Independent Test**: With sample data in /Done, /Logs, and Business_Goals.md, trigger briefing generation. Verify a dated briefing file appears in /Briefings with executive summary, revenue tracking, completed tasks, bottlenecks, and suggestions.

**Acceptance Scenarios**:

1. **Given** completed items exist in /Done and goals are defined in Business_Goals.md, **When** the briefing is triggered, **Then** a dated briefing file is created in /Briefings with executive summary, revenue section, completed tasks list, bottlenecks table, and proactive suggestions
2. **Given** a briefing is generated, **When** the dashboard is updated, **Then** Dashboard.md includes a link to the latest briefing
3. **Given** no items were completed during the period, **When** the briefing is triggered, **Then** the briefing still generates with appropriate "no activity" messaging and flags it as a concern

---

### User Story 5 - Audit Logging (Priority: P3)

As a freelancer, every action the AI takes is logged in a structured daily log file. I can review what the AI did, when, and why. This gives me confidence and accountability.

**Why this priority**: Required for security judging criteria (15%). Also supports the CEO Briefing feature by providing data for weekly summaries.

**Independent Test**: Trigger several AI actions. Verify /Logs/YYYY-MM-DD.json contains structured entries with timestamp, action type, actor, target, result, and approval status for each action.

**Acceptance Scenarios**:

1. **Given** the AI performs any action (triage, plan creation, dashboard update), **When** the action completes, **Then** a structured log entry is appended to /Logs/YYYY-MM-DD.json
2. **Given** a log file exists, **When** I open it, **Then** each entry contains: timestamp, action_type, actor, target, parameters, result, and approval_status fields
3. **Given** an action fails, **When** the error is caught, **Then** the log entry records the failure with error details

---

### Edge Cases

- What happens when a file with an unrecognized type is dropped into /Inbox? → Classify as "unknown", create metadata with all available info, flag for manual review
- What happens when the same file is dropped twice? → Detect duplicate by filename, skip processing, log the duplicate event
- What happens when /Needs_Action has items but the AI is not running? → Items persist safely; processed when AI next runs
- What happens when a file is dropped while the watcher is restarting? → Watcher checks for unprocessed files on startup
- What happens when Dashboard.md is being edited by the user while AI tries to update? → AI detects file lock, retries after delay, max 3 attempts

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST detect new files in the /Inbox folder within 30 seconds of being dropped
- **FR-002**: System MUST create a metadata .md file in /Needs_Action for each detected file with YAML frontmatter containing type, date, priority, and status
- **FR-003**: System MUST classify files into categories: invoice, receipt, client_brief, contract, unknown
- **FR-004**: System MUST create action plans in /Plans with objective, step-by-step checklist, and priority
- **FR-005**: System MUST update Dashboard.md after every significant action (triage, plan creation, completion)
- **FR-006**: System MUST create approval request files in /Pending_Approval for sensitive actions as defined in Company_Handbook.md
- **FR-007**: System MUST detect when files are moved to /Approved or /Rejected and act accordingly
- **FR-008**: System MUST generate weekly CEO Briefing files in /Briefings with summary, revenue, tasks, bottlenecks, and suggestions
- **FR-009**: System MUST log every action to /Logs/YYYY-MM-DD.json with structured fields
- **FR-010**: System MUST operate in DRY_RUN mode by default where no external actions are executed
- **FR-011**: System MUST implement all AI functionality as Claude Code Agent Skills (.md files)
- **FR-012**: System MUST maintain vault folder structure: /Inbox, /Needs_Action, /Plans, /Pending_Approval, /Approved, /Rejected, /Done, /Logs, /Briefings

### Key Entities

- **VaultItem**: A file dropped into the system. Has: original filename, detected type, priority, status (pending/in_progress/done/rejected), timestamps
- **ActionPlan**: AI-generated plan for handling a VaultItem. Has: objective, steps (checklist), priority, linked VaultItem, approval_required flag
- **ApprovalRequest**: Request for human approval. Has: action type, details, amount (if financial), reason, created date, expiry date, status (pending/approved/rejected)
- **CEOBriefing**: Weekly summary document. Has: period dates, executive summary, revenue data, completed tasks, bottlenecks, suggestions
- **AuditLog**: Daily log file. Has: array of entries, each with timestamp, action_type, actor, target, parameters, result, approval_status

### Assumptions

- The user operates as a single freelancer (one user, no multi-user access)
- The Obsidian vault and the project repository are the same directory
- Files dropped into /Inbox can be of any type but are primarily business documents
- The system runs on the user's local machine (Windows 11)
- Claude Code is available and configured on the machine
- Internet connectivity is available for Claude Code API calls
- Business_Goals.md and Company_Handbook.md are manually maintained by the user

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Files dropped into /Inbox are detected and triaged within 30 seconds, 100% of the time while the watcher is running
- **SC-002**: 90% or more of common business documents (invoices, receipts, briefs) are correctly classified on first triage
- **SC-003**: Dashboard.md reflects current system state within 60 seconds of any action completing
- **SC-004**: All sensitive actions (as defined in Company Handbook) produce approval requests before execution, with zero bypasses
- **SC-005**: CEO Briefing generation completes within 2 minutes and covers all required sections
- **SC-006**: 100% of AI actions are captured in audit logs with complete structured data
- **SC-007**: System operates safely in DRY_RUN mode by default with no unintended external side effects
- **SC-008**: End-to-end flow (drop file → triage → plan → dashboard update → done) completes within 5 minutes
