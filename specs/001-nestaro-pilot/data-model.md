# Data Model: Nestaro Pilot Nestaro Pilot — Autonomous AI employee

**Branch**: `001-nestaro-pilot` | **Date**: 2026-03-13

---

## 1. VaultItem

Represents one unit of work. Exists as a `.md` file in vault folders.

**Filename pattern**: `{TYPE}_{SOURCE}_{YYYYMMDD_HHMMSS}.md`
- Examples: `EMAIL_client_a_20260313_084500.md`
- `FACEBOOK_john_doe_20260313_091200.md`
- `FILE_invoice_q1.md`
- `SYSTEM_AUTH_FAILURE_GMAIL.md`

**Frontmatter schema** (YAML in .md file):
```yaml
---
type: email | whatsapp | facebook | instagram | twitter | file | linkedin | system
source: <sender name or platform identifier>
subject: <subject or message snippet, max 200 chars>
received: <ISO-8601 timestamp>
priority: high | medium | low
status: pending | in_progress | done | expired
channel: gmail | whatsapp | facebook | instagram | twitter | filesystem
raw_id: <platform message ID for deduplication>
---
```

**State transitions**:
```
vault/Inbox/           → vault/Needs_Action/    (watcher moves/copies)
vault/Needs_Action/    → vault/Plans/           (orchestrator + triage skill)
vault/Plans/           → vault/Pending_Approval/ (if approval_required=true)
vault/Plans/           → vault/Done/            (if approval_required=false, auto-executed)
vault/Pending_Approval/ → vault/Approved/       (human moves)
vault/Pending_Approval/ → vault/Rejected/       (human moves)
vault/Pending_Approval/ → vault/Done/           (orchestrator: expired after 24h)
vault/Approved/        → vault/Done/            (orchestrator after execution)
vault/Rejected/        → vault/Done/            (orchestrator after logging)
```

---

## 2. ActionPlan

Created by Claude (triage-inbox skill) in `vault/Plans/`.

**Filename**: `PLAN_{original_item_name}`

**Schema**:
```yaml
---
created: <ISO-8601>
source_item: <filename of the VaultItem that triggered this plan>
action_type: email_send | email_draft | whatsapp_reply | facebook_reply |
             instagram_reply | twitter_reply | linkedin_post | facebook_post |
             instagram_post | twitter_post | odoo_create_invoice |
             odoo_post_invoice | odoo_record_payment | no_action | escalate
approval_required: true | false
status: pending | approved | rejected | expired | executed
expires_at: <ISO-8601, 24h from created>
---
```

**Body sections**:
- `## Context` — summary of the triggering item
- `## Proposed Action` — what Claude proposes to do
- `## Steps` — checkbox list of steps (some checked by Claude, rest pending)
- `## Approval Required` — only if `approval_required: true`

---

## 3. ApprovalRequest

Created by Claude in `vault/Pending_Approval/` when `approval_required=true`.

**Filename**: `APPROVAL_{action_type}_{source}_{timestamp}.md`

**Schema**:
```yaml
---
type: approval_request
action_type: <same as ActionPlan.action_type>
source_item: <VaultItem filename>
plan_file: <ActionPlan filename>
created: <ISO-8601>
expires_at: <ISO-8601, 24h from created>
status: pending | approved | rejected | expired
approved_by: human | null
executed_at: <ISO-8601 or null>
---
```

**Body sections**:
- `## Action Details` — what will happen if approved
- `## To Approve` — "Move this file to vault/Approved/"
- `## To Reject` — "Move this file to vault/Rejected/"

---

## 4. AuditLogEntry

Appended to `vault/Logs/YYYY-MM-DD.json` (one JSON object per line, NDJSON).

**Schema** (exact — per constitution Principle VII):
```json
{
  "timestamp": "2026-03-13T09:15:00Z",
  "action_type": "facebook_post | instagram_post | twitter_post |
                  email_send | email_draft | whatsapp_reply |
                  linkedin_post | odoo_create_invoice | odoo_post_invoice |
                  odoo_record_payment | approval_expired | system_alert |
                  watcher_error | auth_failure",
  "actor": "claude_code | orchestrator | human",
  "target": "<recipient, platform URL, or system name>",
  "parameters": {},
  "approval_status": "auto_approved | human_approved | human_rejected | expired | n/a",
  "approved_by": "human | system | null",
  "result": "success | failure | dry_run",
  "error": null
}
```

**Validation rules**:
- All 9 fields MUST be present
- `timestamp` MUST be ISO-8601 UTC
- `result` MUST be one of: success, failure, dry_run
- `error` is `null` on success, string on failure
- File is append-only; never truncated or overwritten

---

## 5. OdooInvoice (MCP representation)

Returned by `odoo-mcp` tools. Maps to Odoo `account.move` model.

```typescript
interface OdooInvoice {
  id: number;
  name: string;               // e.g. "INV/2026/001"
  partner_id: [number, string]; // [id, "Client Name"]
  amount_total: number;
  amount_residual: number;    // unpaid amount
  currency_id: [number, string];
  state: "draft" | "posted" | "cancel";
  payment_state: "not_paid" | "in_payment" | "paid" | "partial";
  invoice_date: string;       // YYYY-MM-DD
  invoice_date_due: string;   // YYYY-MM-DD
  invoice_line_ids: number[];
}
```

---

## 6. FinancialSummary (MCP representation)

Returned by `odoo-mcp.get_financial_summary`.

```typescript
interface FinancialSummary {
  period_start: string;       // YYYY-MM-DD
  period_end: string;         // YYYY-MM-DD
  mtd_revenue: number;        // sum of posted+paid invoices in period
  total_outstanding: number;  // sum of amount_residual on posted invoices
  paid_invoice_count: number;
  unpaid_invoice_count: number;
  overdue_invoices: Array<{
    id: number;
    name: string;
    partner: string;
    amount: number;
    due_date: string;
    days_overdue: number;
  }>;
  currency: string;           // e.g. "USD"
}
```

---

## 7. CEOBriefing

Written to `vault/Briefings/YYYY-MM-DD_Briefing.md` by
`generate-accounting-briefing` skill.

**Required sections**:
- `# Monday Morning CEO Briefing` (or day of week)
- `## Executive Summary` — 2–3 sentence overview
- `## Revenue` — MTD revenue, % of monthly target, trend (from Odoo)
- `## Unpaid Invoices` — table of outstanding invoices (from Odoo)
- `## Communications Activity` — emails, WhatsApp, social media handled this week
- `## Completed Tasks` — items moved to Done/ this week (from vault)
- `## Proactive Suggestions` — overdue invoice reminders, unused subscriptions
- `---` footer with generation timestamp

---

## 8. RalphWiggumState

Ephemeral state managed by the stop hook via environment variables.

```python
RALPH_ITERATION: int   # current iteration count (0-10)
RALPH_MAX_ITER: int    # max iterations before force-exit (default: 10)
VAULT_PATH: str        # path to vault/ directory
```

**Exit codes from stop hook**:
- `0` — allow Claude to exit (no items remaining or max iterations reached)
- `2` — block exit, re-inject orchestrator prompt

---

## 9. PM2 Process Registry

| Process Name | Script | Restart Policy |
|---|---|---|
| filesystem-watcher | `watchers/filesystem_watcher.py` | always |
| gmail-watcher | `watchers/gmail_watcher.py` | always |
| whatsapp-watcher | `watchers/whatsapp_watcher.py` | always |
| facebook-watcher | `watchers/facebook_watcher.py` | always |
| instagram-watcher | `watchers/instagram_watcher.py` | always |
| twitter-watcher | `watchers/twitter_watcher.py` | always |
| orchestrator | `watchers/orchestrator.py` | always |
| email-mcp | `email-mcp/index.ts` | always |

*(odoo-mcp is invoked on-demand by Claude Code via .mcp.json, not PM2)*
