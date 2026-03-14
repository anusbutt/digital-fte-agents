# Skill: Triage Inbox Item

## Purpose

Process a triaged VaultItem from `/Needs_Action/`, consult `Company_Handbook.md` for business rules, create an ActionPlan in `/Plans/`, and determine if human approval is required.

Gold tier adds support for Facebook, Instagram, and Twitter item types in addition to Silver's FILE_, EMAIL_, and WHATSAPP_ items.

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

**FACEBOOK_ items** (Facebook watcher):
Extract YAML frontmatter fields:
- `type` (facebook)
- `contact` — sender name or page name
- `message_text` — message or comment text
- `keywords_matched` — list of matched business keywords
- `priority` — high, medium, or low

**INSTAGRAM_ items** (Instagram watcher):
Extract YAML frontmatter fields:
- `type` (instagram)
- `contact` — sender username
- `message_text` — DM or comment text
- `keywords_matched` — list of matched business keywords
- `priority` — high, medium, or low

**TWITTER_ items** (Twitter/X watcher):
Extract YAML frontmatter fields:
- `type` (twitter)
- `contact` — sender username (@handle)
- `message_text` — tweet or DM text
- `keywords_matched` — list of matched business keywords
- `priority` — high, medium, or low

### Step 2: Consult the Company Handbook

Read `Company_Handbook.md` from the vault root. Check:
- **Approval thresholds**: Does this item require human approval?
  - All social media replies/posts → approval required (always, per Gold Handbook)
  - External emails → approval required (unless non-sensitive reply to known contact)
  - WhatsApp reply → always requires approval
  - File deletions → approval required
  - Email reply to known, non-sensitive → auto-send (no approval)
- **Client priority tiers**: Determine response urgency
- **Communication tone**: Use appropriate style per platform
- **Social Media Content Rules**: Check platform-specific rules (char limits, hashtags, CTA)

### Step 3: Create ActionPlan

Create a plan file in `/Plans/` with the appropriate naming convention:

- **FILE_ items**: `PLAN_FILE_{original_name_without_ext}.md`
- **EMAIL_ items**: `PLAN_EMAIL_{message_id}.md`
- **WHATSAPP_ items**: `PLAN_WHATSAPP_{contact_slug}_{timestamp}.md`
- **FACEBOOK_ items**: `PLAN_FACEBOOK_{contact_slug}_{timestamp}.md`
- **INSTAGRAM_ items**: `PLAN_INSTAGRAM_{contact_slug}_{timestamp}.md`
- **TWITTER_ items**: `PLAN_TWITTER_{contact_slug}_{timestamp}.md`

Use this exact structure:

```yaml
---
type: action_plan
related_item: "Needs_Action/{VaultItem filename}"
objective: "{Clear one-line summary of what needs to happen}"
priority: {inherited from VaultItem or escalated}
approval_required: {true|false based on handbook rules}
action_type: {file_process|email_reply|email_draft|whatsapp_reply|facebook_reply|facebook_post|instagram_reply|instagram_post|twitter_reply|twitter_post}
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

{Relevant information from Company Handbook and item content}
{Include why approval is/isn't needed}
{For social media: note platform-specific rules applied}

## Reply Draft (if applicable)

{For EMAIL_ items: AI-generated reply text}
{For WHATSAPP_ items: AI-generated reply text}
{For FACEBOOK_ items: AI-generated reply or post text}
{For INSTAGRAM_ items: AI-generated reply text with hashtags if applicable}
{For TWITTER_ items: AI-generated reply (max 280 chars, max 2 hashtags)}
```

### Step 4: Handle Approval (if required)

If `approval_required` is true, create an ApprovalRequest in `/Pending_Approval/`:

**For FILE_ items**: `APPROVE_FILE_{original_name_without_ext}.md`
**For EMAIL_ items**: `APPROVE_EMAIL_{message_id}.md`
**For WHATSAPP_ items**: `APPROVE_WHATSAPP_{contact_slug}_{timestamp}.md`
**For FACEBOOK_ items**: `APPROVE_FACEBOOK_{contact_slug}_{timestamp}.md`
**For INSTAGRAM_ items**: `APPROVE_INSTAGRAM_{contact_slug}_{timestamp}.md`
**For TWITTER_ items**: `APPROVE_TWITTER_{contact_slug}_{timestamp}.md`

**Determine the `action` field** based on what the plan requires:
- `payment` — invoice payments, refunds, financial transfers
- `email_send` — outgoing email reply (non-sensitive)
- `email_draft` — email reply requiring human review before sending (sensitive)
- `whatsapp_reply` — WhatsApp reply (always requires approval)
- `facebook_reply` — Facebook reply to message or comment
- `facebook_post` — New Facebook post
- `instagram_reply` — Instagram DM or comment reply
- `instagram_post` — New Instagram post
- `twitter_reply` — Twitter/X reply or DM
- `twitter_post` — New Twitter/X post
- `linkedin_post` — LinkedIn post
- `odoo_action` — Odoo accounting action (create/post invoice, record payment)
- `file_delete` — removing files or records
- `external_api` — calling any external service or API

**Approval triggers** (from Company_Handbook.md Gold tier):
- Any Facebook reply or post → `approval_required: true` (always)
- Any Instagram reply or post → `approval_required: true` (always)
- Any Twitter/X reply, post, or DM → `approval_required: true` (always)
- WhatsApp reply → `approval_required: true` (always)
- Email to unknown recipient → `approval_required: true`
- Email with financial content → `approval_required: true`
- Email with attachments → `approval_required: true`
- Email reply to known, non-sensitive → `approval_required: false`
- When uncertain about sensitivity → default to `approval_required: true`

Create the approval file with this structure:

```yaml
---
type: approval_request
action: {action_type}
details: "{Human-readable description of what will happen}"
amount: {financial amount if applicable, or null}
recipient: "{target of the action — contact name, email, or null}"
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
{For FACEBOOK_ items: the actual Facebook reply or post text}
{For INSTAGRAM_ items: the actual Instagram reply/caption with hashtags}
{For TWITTER_ items: the actual tweet (max 280 chars)}
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

**For all social media items (Facebook, Instagram, Twitter, WhatsApp)**: Auto-execute is **never** allowed. Always create approval request.

### Step 6: Update Dashboard

After creating the plan, invoke the update-dashboard skill or directly update `Dashboard.md` to reflect the new plan.

## Decision Matrix

| Item Type | Always Requires Approval | Auto-Execute Possible |
|-----------|--------------------------|----------------------|
| FILE_ | No (depends on action) | No |
| EMAIL_ sensitive | Yes | No |
| EMAIL_ non-sensitive | No | Yes (auto-send) |
| WHATSAPP_ | Yes | No |
| FACEBOOK_ | Yes | No |
| INSTAGRAM_ | Yes | No |
| TWITTER_ | Yes | No |

## Rules

- NEVER auto-execute sensitive actions. Always create approval requests.
- ALWAYS preserve the original file in Inbox — never modify or delete it.
- Use professional, action-oriented language in plans.
- When uncertain about classification, set `approval_required: true` as a safety default.
- Every plan must have at least 2 actionable steps.
- For EMAIL_ items, always include a reply draft in the plan.
- For WHATSAPP_ items, always include a reply draft and set `approval_required: true`.
- For FACEBOOK_/INSTAGRAM_/TWITTER_ items, always include a reply draft and set `approval_required: true`.
- Respect platform-specific content rules from Company_Handbook.md:
  - Facebook: Include CTA, max 500 words
  - Instagram: Include 3-5 hashtags, keep concise
  - Twitter/X: Max 280 characters total, max 2 hashtags

## Tools Required

- `Read` — to read VaultItem and Company_Handbook.md
- `Write` — to create plan and approval files
- `Glob` — to check for existing plans
