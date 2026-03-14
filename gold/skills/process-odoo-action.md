# Skill: process-odoo-action

## Purpose

Execute an approved Odoo accounting action (create invoice, post invoice, or
record payment) via the `odoo-mcp` MCP tool. This skill runs ONLY after a
human has approved the action by moving the file to `vault/Approved/`.

**HITL is non-negotiable**: this skill MUST verify human approval before
calling any Odoo tool. If approval cannot be confirmed, stop immediately.

---

## Safety Checks (verify ALL before executing)

1. **DRY_RUN check**: read `vault/.env` or environment for `DRY_RUN=true`.
   If `DRY_RUN=true` → log intent and stop. Do NOT call any Odoo tool.

2. **Human approval**: the approval file MUST have:
   - `status: approved` in frontmatter
   - `approved_by: human` in frontmatter
   - The file must be in `vault/Approved/` (not Pending_Approval/)

3. **Expiry check**: read `expires_at` from frontmatter.
   If `expires_at` is in the past → log `approval_expired` and stop.
   Do NOT execute an expired approval.

4. **Action type**: `action_type` in frontmatter must be one of:
   - `odoo_create_invoice`
   - `odoo_post_invoice`
   - `odoo_record_payment`

   If not one of these → this skill is not the right handler; stop.

---

## Input: Approval File

The approval file in `vault/Approved/` has this frontmatter:

```yaml
---
type: approval_request
action_type: odoo_create_invoice | odoo_post_invoice | odoo_record_payment
source_item: <VaultItem filename that triggered this>
plan_file: <ActionPlan filename>
created: <ISO-8601>
expires_at: <ISO-8601>
status: approved
approved_by: human
executed_at: null
# Action-specific fields:
partner_name: <for create_invoice>
amount: <for create_invoice or record_payment>
description: <for create_invoice>
currency: <for create_invoice, optional>
due_date: <for create_invoice, optional>
invoice_id: <for post_invoice or record_payment>
payment_date: <for record_payment, optional>
memo: <for record_payment, optional>
---
```

---

## Execution Steps

### For `odoo_create_invoice`:

1. Read `partner_name`, `amount`, `description`, `currency` (optional), `due_date` (optional) from frontmatter
2. Call `odoo-mcp` tool: `create_invoice` with those parameters
3. On success:
   - Record `invoice_id` and `invoice_name` from result
   - Move approval file to `vault/Done/`
   - Write AuditLogEntry to `vault/Logs/YYYY-MM-DD.json`:
     ```json
     {
       "action_type": "odoo_create_invoice",
       "actor": "claude_code",
       "target": "<invoice_name>",
       "parameters": { "partner": "<partner_name>", "amount": <amount>, "invoice_id": <id> },
       "approval_status": "human_approved",
       "approved_by": "human",
       "result": "success",
       "error": null
     }
     ```
4. On failure (any error code):
   - Write `SYSTEM_ODOO_FAILURE_{timestamp}.md` to `vault/Needs_Action/` with error details
   - Write AuditLogEntry with `result: "failure"` and `error: <error_code>`
   - Do NOT move approval file to Done/ (leave in Approved/ for investigation)

### For `odoo_post_invoice`:

1. Read `invoice_id` from frontmatter
2. Call `odoo-mcp` tool: `post_invoice` with `invoice_id`
3. On success:
   - Move approval file to `vault/Done/`
   - Write AuditLogEntry with `action_type: "odoo_post_invoice"`, `result: "success"`
4. On failure:
   - Check error code:
     - `ALREADY_POSTED` → log as success (idempotent), move to Done/
     - `INVOICE_NOT_FOUND` → write SYSTEM_ODOO_FAILURE, leave in Approved/
     - `ODOO_UNREACHABLE` → write SYSTEM_ODOO_UNREACHABLE alert (see below)
     - Other → write SYSTEM_ODOO_FAILURE, leave in Approved/

### For `odoo_record_payment`:

1. Read `invoice_id`, `amount`, `payment_date` (optional), `memo` (optional) from frontmatter
2. Call `odoo-mcp` tool: `record_payment` with those parameters
3. On success:
   - Move approval file to `vault/Done/`
   - Write AuditLogEntry with `action_type: "odoo_record_payment"`, `result: "success"`
   - Include `invoice_payment_state` in parameters
4. On failure:
   - `AMOUNT_EXCEEDS` → log error, write SYSTEM_ODOO_FAILURE alert, leave in Approved/
   - `ODOO_UNREACHABLE` → write SYSTEM_ODOO_UNREACHABLE alert (see below)
   - Other → write SYSTEM_ODOO_FAILURE, leave in Approved/

---

## ODOO_UNREACHABLE Handling

When any Odoo tool returns `error: "ODOO_UNREACHABLE"`:

1. Check if `vault/Needs_Action/SYSTEM_ODOO_UNREACHABLE.md` already exists.
   If it does, do not create a duplicate.

2. If it does not exist, write `vault/Needs_Action/SYSTEM_ODOO_UNREACHABLE.md`:
   ```markdown
   ---
   type: system
   priority: high
   status: pending
   detected_date: <ISO-8601>
   ---

   ## Odoo Unreachable

   The AI employee attempted to execute an Odoo accounting action but could not
   connect to Odoo at the configured URL.

   **Action attempted**: <action_type>
   **Approval file**: <filename>
   **Detected**: <timestamp>

   ## Resolution Steps

   1. Check Docker: `docker compose ps`
   2. Start Odoo if needed: `docker compose up -d`
   3. Verify Odoo URL in `.env`: `ODOO_URL=http://localhost:8069`
   4. After Odoo is running, move the approval file back to `vault/Approved/`
      to retry execution.

   ## Approval File (for retry)

   `<approval filename>` — still in `vault/Approved/` (not moved to Done/)
   ```

3. Write AuditLogEntry with `result: "failure"`, `error: "ODOO_UNREACHABLE"`

---

## SYSTEM_ODOO_FAILURE File Template

```markdown
---
type: system
priority: high
status: pending
detected_date: <ISO-8601>
error_code: <error code from odoo-mcp>
action_type: <odoo_create_invoice | odoo_post_invoice | odoo_record_payment>
---

## Odoo Action Failed

An approved Odoo action could not be completed.

**Action**: <action_type>
**Error**: <error_code>
**Details**: <error message>
**Approval file**: <filename in vault/Approved/>

## Resolution

Review the error, fix the underlying issue (partner name, invoice state,
payment amount), then move the approval file back to `vault/Approved/` to retry.
```

---

## AuditLogEntry Schema

Append one JSON line to `vault/Logs/YYYY-MM-DD.json` (NDJSON):

```json
{
  "timestamp": "<ISO-8601 UTC>",
  "action_type": "odoo_create_invoice | odoo_post_invoice | odoo_record_payment",
  "actor": "claude_code",
  "target": "<invoice_name or invoice_id>",
  "parameters": {},
  "approval_status": "human_approved",
  "approved_by": "human",
  "result": "success | failure | dry_run",
  "error": null
}
```

---

## DRY_RUN Output

If `DRY_RUN=true`, log:

```
[DRY_RUN] Would execute <action_type>:
  - Parameters: <extracted from frontmatter>
  - Odoo tool: <tool name>
  - Target: <partner or invoice_id>
  Skipping actual Odoo call. Set DRY_RUN=false to execute.
```

Then write a DRY_RUN AuditLogEntry with `result: "dry_run"` and stop.

---

## Quality Gate

Before writing any files:
- [ ] DRY_RUN check passed (or `DRY_RUN=false`)
- [ ] `approved_by: human` confirmed
- [ ] `expires_at` is in the future
- [ ] `action_type` is one of the three recognized types
- [ ] All required parameters present for the action type
- [ ] AuditLogEntry written (always — even on failure or dry_run)
