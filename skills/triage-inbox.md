# Skill: Triage Inbox Item

## Purpose

Process a triaged VaultItem from `/Needs_Action/`, consult `Company_Handbook.md` for business rules, create an ActionPlan in `/Plans/`, and determine if human approval is required.

## Instructions

You are the AI Employee. Follow these steps precisely:

### Step 1: Read the VaultItem

Read the VaultItem `.md` file provided as context from `/Needs_Action/`. Extract the YAML frontmatter fields:
- `type` (invoice, receipt, client_brief, contract, unknown)
- `original_name`
- `priority`
- `source_path`

### Step 2: Consult the Company Handbook

Read `Company_Handbook.md` from the vault root. Check:
- **Approval thresholds**: Does this item require human approval?
  - Invoices > $500 → approval required
  - External emails → approval required
  - File deletions → approval required
- **Client priority tiers**: Determine response urgency
- **Communication tone**: Use appropriate style for plan

### Step 3: Create ActionPlan

Create a plan file in `/Plans/` named `PLAN_{original_name_without_ext}.md` with this exact structure:

```yaml
---
type: action_plan
related_item: "Needs_Action/{VaultItem filename}"
objective: "{Clear one-line summary of what needs to happen}"
priority: {inherited from VaultItem or escalated}
approval_required: {true|false based on handbook rules}
created: {current ISO 8601 timestamp}
status: pending
---
```

Then add these sections:

```markdown
## Objective

{Clear statement of what needs to happen with this item}

## Steps

- [ ] Step 1: {first action}
- [ ] Step 2: {second action}
- [ ] Step 3: {third action}
{Add REQUIRES APPROVAL note to any step that needs it}

## Context

{Relevant information from Company Handbook and file content}
{Include why approval is/isn't needed}
```

### Step 4: Handle Approval (if required)

If `approval_required` is true, create an ApprovalRequest in `/Pending_Approval/` named `APPROVE_{original_name_without_ext}.md`.

**Determine the `action` field** based on what the plan requires:
- `payment` -- invoice payments, refunds, financial transfers
- `email_send` -- any outgoing client or external communication
- `social_post` -- social media publications
- `file_delete` -- removing files or records
- `external_api` -- calling any external service or API

**Approval triggers** (from Company_Handbook.md):
- Invoice amount > $500 → `action: payment`, `approval_required: true`
- Any plan involving external email → `action: email_send`, `approval_required: true`
- Any plan involving file deletion → `action: file_delete`, `approval_required: true`
- When uncertain about sensitivity → default to `approval_required: true`

Create the file with this structure:

```yaml
---
type: approval_request
action: {payment|email_send|social_post|file_delete|external_api}
details: "{Human-readable description of what will happen}"
amount: {financial amount if applicable, or null}
recipient: "{target of the action, or null}"
reason: "{Why this action is needed}"
related_plan: "Plans/PLAN_{name}.md"
created: {current ISO 8601 timestamp}
expires: {24 hours from now ISO 8601}
status: pending
---

## Action Details

{Full description of what will happen if approved}

## To Approve

Move this file to the `/Approved/` folder.

## To Reject

Move this file to the `/Rejected/` folder.
```

### Step 5: Update Dashboard

After creating the plan, invoke the update-dashboard skill or directly update `Dashboard.md` to reflect the new plan.

## Rules

- NEVER auto-execute sensitive actions. Always create approval requests.
- ALWAYS preserve the original file in Inbox -- never modify or delete it.
- Use professional, action-oriented language in plans.
- When uncertain about classification, set `approval_required: true` as a safety default.
- Every plan must have at least 2 actionable steps.

## Tools Required

- `Read` -- to read VaultItem and Company_Handbook.md
- `Write` -- to create plan and approval files
- `Glob` -- to check for existing plans
