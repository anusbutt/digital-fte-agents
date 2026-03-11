# Skill: Triage Inbox Item

## Purpose

Process a triaged VaultItem from `/Needs_Action/`, consult `Company_Handbook.md` for business rules, create an ActionPlan in `/Plans/`, and determine if human approval is required.

## Instructions

You are the AI Employee. Follow these steps precisely:

### Step 1: Read the VaultItem

Read the VaultItem `.md` file provided as context from `/Needs_Action/`. Determine the item type from its filename prefix:

**FILE_ items** (filesystem watcher):
Extract YAML frontmatter fields:
- `type` (invoice, receipt, client_brief, contract, unknown)
- `original_name`
- `priority`
- `source_path`

**EMAIL_ items** (Gmail watcher):
Extract YAML frontmatter fields:
- `type` (email)
- `email_id` — Gmail message ID
- `from` — sender email address
- `from_name` — sender display name
- `subject` — email subject line
- `sensitivity` — sensitive or non-sensitive
- `priority` — high, medium, or low
- `has_attachments` — true or false

Read the full email body from the `## Email Content` section.

**WHATSAPP_ items** (WhatsApp watcher):
Extract YAML frontmatter fields:
- `type` (whatsapp)
- `contact` — sender contact name
- `phone` — sender phone number
- `message_text` — full message text
- `keywords_matched` — list of matched business keywords
- `priority` — high, medium, or low

Read the message from the `## Message Details` section.

### Step 2: Consult the Company Handbook

Read `Company_Handbook.md` from the vault root. Check:
- **Approval thresholds**: Does this item require human approval?
  - Invoices > $500 → approval required
  - External emails → approval required (unless non-sensitive reply to known contact)
  - File deletions → approval required
  - Email reply to known, non-sensitive → auto-send (no approval)
  - WhatsApp reply → always requires approval
- **Client priority tiers**: Determine response urgency
- **Communication tone**: Use appropriate style for plan
- **Email Sensitivity Rules** (for EMAIL_ items):
  - New/unknown sender → sensitive
  - Financial content (invoice, payment, amount, $) → sensitive
  - Attachments present → sensitive
  - Known sender + non-financial + no attachments → non-sensitive

### Step 3: Create ActionPlan

Create a plan file in `/Plans/` with the appropriate naming convention:

- **FILE_ items**: `PLAN_FILE_{original_name_without_ext}.md`
- **EMAIL_ items**: `PLAN_EMAIL_{message_id}.md`
- **WHATSAPP_ items**: `PLAN_WHATSAPP_{contact_slug}_{timestamp}.md`

Use this exact structure:

```yaml
---
type: action_plan
related_item: "Needs_Action/{VaultItem filename}"
objective: "{Clear one-line summary of what needs to happen}"
priority: {inherited from VaultItem or escalated}
approval_required: {true|false based on handbook rules}
action_type: {file_process|email_reply|email_draft|whatsapp_reply}
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

{Relevant information from Company Handbook and file/email content}
{Include why approval is/isn't needed}

## Reply Draft (if applicable)

{For EMAIL_ items: AI-generated reply text}
```

### Step 4: Handle Approval (if required)

If `approval_required` is true, create an ApprovalRequest in `/Pending_Approval/`:

**For FILE_ items**: `APPROVE_FILE_{original_name_without_ext}.md`
**For EMAIL_ items**: `APPROVE_EMAIL_{message_id}.md`
**For WHATSAPP_ items**: `APPROVE_WHATSAPP_{contact_slug}_{timestamp}.md`

**Determine the `action` field** based on what the plan requires:
- `payment` — invoice payments, refunds, financial transfers
- `email_send` — outgoing email reply (non-sensitive, but approval triggered by other rules)
- `email_draft` — email reply requiring human review before sending (sensitive)
- `whatsapp_reply` — WhatsApp reply (always requires approval)
- `social_post` — social media publications
- `file_delete` — removing files or records
- `external_api` — calling any external service or API

**Approval triggers** (from Company_Handbook.md):
- Invoice amount > $500 → `action: payment`, `approval_required: true`
- Email to unknown recipient → `action: email_draft`, `approval_required: true`
- Email with financial content → `action: email_draft`, `approval_required: true`
- Email with attachments → `action: email_draft`, `approval_required: true`
- Email reply to known, non-sensitive → `action: email_send`, `approval_required: false`
- WhatsApp reply → `action: whatsapp_reply`, `approval_required: true` (always)
- Any plan involving file deletion → `action: file_delete`, `approval_required: true`
- When uncertain about sensitivity → default to `approval_required: true`

Create the file with this structure:

```yaml
---
type: approval_request
action: {payment|email_send|email_draft|whatsapp_reply|linkedin_post|file_delete|external_api}
details: "{Human-readable description of what will happen}"
amount: {financial amount if applicable, or null}
recipient: "{target of the action — email address, contact name, or null}"
reason: "{Why this action is needed}"
related_plan: "Plans/PLAN_{prefix}_{identifier}.md"
reply_content: "{The actual reply text to be sent, or null}"
created: {current ISO 8601 timestamp}
expires: {24 hours from now ISO 8601}
status: pending
---

## Action Details

{Full description of what will happen if approved}

## Content to Send

{For EMAIL_ items: the actual email reply text}
{For WHATSAPP_ items: the actual WhatsApp reply text}
{For FILE_ items: description of planned action}

## To Approve

Move this file to the `/Approved/` folder.

## To Reject

Move this file to the `/Rejected/` folder.
```

### Step 5: Auto-Execute (if no approval needed)

**For EMAIL_ items with `sensitivity: non-sensitive`**:
- Set `approval_required: false` and `action_type: email_reply` in the plan
- The orchestrator will invoke the `compose-email-reply` skill to send automatically
- No approval file is created

**For WHATSAPP_ items**: Auto-execute is **never** allowed. Always create approval request.

### Step 6: Update Dashboard

After creating the plan, invoke the update-dashboard skill or directly update `Dashboard.md` to reflect the new plan.

## Rules

- NEVER auto-execute sensitive actions. Always create approval requests.
- ALWAYS preserve the original file in Inbox — never modify or delete it.
- Use professional, action-oriented language in plans.
- When uncertain about classification, set `approval_required: true` as a safety default.
- Every plan must have at least 2 actionable steps.
- For EMAIL_ items, always include a reply draft in the plan.
- For WHATSAPP_ items, always include a reply draft and set `approval_required: true`.
- Plan naming must match the VaultItem prefix: PLAN_FILE_ for files, PLAN_EMAIL_ for emails, PLAN_WHATSAPP_ for WhatsApp.

## Tools Required

- `Read` — to read VaultItem and Company_Handbook.md
- `Write` — to create plan and approval files
- `Glob` — to check for existing plans
