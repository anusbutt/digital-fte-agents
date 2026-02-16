# Data Model: AI Employee Foundation

**Branch**: `001-ai-employee-foundation` | **Date**: 2026-02-15

## Entities

All entities are represented as markdown files with YAML frontmatter.
This is the canonical schema for each entity type.

### VaultItem (in /Needs_Action/)

```yaml
---
type: invoice | receipt | client_brief | contract | unknown
original_name: "invoice_client_a.pdf"
detected_date: 2026-02-15T10:30:00Z
priority: high | medium | low
status: pending
source_path: "Inbox/invoice_client_a.pdf"
---

## File Details

[Extracted summary of file content]

## Suggested Actions

- [ ] Action item 1
- [ ] Action item 2
```

**Fields**:
- `type` (required): Classification category
- `original_name` (required): Original filename as dropped
- `detected_date` (required): ISO 8601 timestamp of detection
- `priority` (required): Derived from type and Company Handbook rules
- `status` (required): Always "pending" when created
- `source_path` (required): Relative path to original file in Inbox

**Validation**: All fields required. Type must be one of the 5 defined categories.

---

### ActionPlan (in /Plans/)

```yaml
---
type: action_plan
related_item: "Needs_Action/FILE_invoice_client_a.md"
objective: "Process and track Client A January invoice"
priority: high | medium | low
approval_required: true | false
created: 2026-02-15T10:35:00Z
status: pending
---

## Objective

[Clear statement of what needs to happen]

## Steps

- [ ] Step 1
- [ ] Step 2 (REQUIRES APPROVAL)
- [ ] Step 3

## Context

[Relevant information from Company Handbook and file content]
```

**Fields**:
- `type` (required): Always "action_plan"
- `related_item` (required): Path to the source VaultItem
- `objective` (required): One-line summary
- `priority` (required): Inherited from VaultItem or escalated
- `approval_required` (required): True if any step needs HITL
- `created` (required): ISO 8601 timestamp
- `status` (required): pending | in_progress | done

---

### ApprovalRequest (in /Pending_Approval/)

```yaml
---
type: approval_request
action: payment | email_send | social_post | file_delete | external_api
details: "Send invoice to Client A via email"
amount: 500.00
recipient: "Client A"
reason: "January 2026 invoice payment"
related_plan: "Plans/PLAN_invoice_client_a.md"
created: 2026-02-15T10:40:00Z
expires: 2026-02-16T10:40:00Z
status: pending
---

## Action Details

[Full description of what will happen if approved]

## To Approve

Move this file to /Approved folder.

## To Reject

Move this file to /Rejected folder.
```

**Fields**:
- `type` (required): Always "approval_request"
- `action` (required): Category of sensitive action
- `details` (required): Human-readable description
- `amount` (optional): Financial amount if applicable
- `recipient` (optional): Target of the action
- `reason` (required): Why this action is needed
- `related_plan` (required): Path to associated ActionPlan
- `created` (required): ISO 8601 timestamp
- `expires` (required): Auto-reject after this time
- `status` (required): Always "pending" when created

---

### CEOBriefing (in /Briefings/)

```yaml
---
type: ceo_briefing
generated: 2026-02-15T07:00:00Z
period_start: 2026-02-08
period_end: 2026-02-14
---

# Weekly CEO Briefing

## Executive Summary
[1-2 sentence overview]

## Revenue
- **This Week**: $X,XXX
- **MTD**: $X,XXX (XX% of target)
- **Trend**: On track | Behind | Ahead

## Completed Tasks
- [x] Task 1
- [x] Task 2

## Bottlenecks
| Task | Expected | Actual | Delay |
|------|----------|--------|-------|
| ... | ... | ... | ... |

## Proactive Suggestions
### Cost Optimization
- ...

### Upcoming Deadlines
- ...
```

**Fields**:
- `type` (required): Always "ceo_briefing"
- `generated` (required): ISO 8601 timestamp
- `period_start` (required): Start of reporting period
- `period_end` (required): End of reporting period

---

### AuditLog (in /Logs/)

File: `/Logs/YYYY-MM-DD.json` (JSON Lines format)

```json
{"timestamp":"2026-02-15T10:30:00Z","action_type":"file_triage","actor":"claude_code","target":"invoice_client_a.pdf","parameters":{"detected_type":"invoice","priority":"high"},"result":"success","approval_status":"not_required"}
{"timestamp":"2026-02-15T10:35:00Z","action_type":"plan_created","actor":"claude_code","target":"PLAN_invoice_client_a.md","parameters":{"approval_required":true},"result":"success","approval_status":"not_required"}
```

**Entry fields**:
- `timestamp` (required): ISO 8601
- `action_type` (required): file_triage | plan_created | dashboard_updated | approval_requested | approval_granted | approval_rejected | briefing_generated | file_moved | error
- `actor` (required): "claude_code" | "orchestrator" | "watcher"
- `target` (required): File or entity acted upon
- `parameters` (required): Action-specific key-value pairs
- `result` (required): "success" | "failure" | "skipped"
- `approval_status` (required): "not_required" | "pending" | "approved" | "rejected"

## State Transitions

```
VaultItem:  [dropped] → pending → in_progress → done
                                              → rejected

ActionPlan: [created] → pending → in_progress → done

ApprovalRequest: [created] → pending → approved → done
                                     → rejected → done
```

## Folder-to-Status Mapping

| Folder | Status | Meaning |
|--------|--------|---------|
| /Inbox | (raw) | Unprocessed drop |
| /Needs_Action | pending | Triaged, awaiting AI processing |
| /Plans | pending/in_progress | Action plan created |
| /Pending_Approval | pending | Awaiting human approval |
| /Approved | approved | Human approved, ready to execute |
| /Rejected | rejected | Human rejected |
| /Done | done | Fully processed and archived |
