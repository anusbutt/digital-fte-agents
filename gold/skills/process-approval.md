# Skill: Process Approval Decision

## Purpose

Process a file that has been moved to `/Approved/` or `/Rejected/` by the human operator. Execute the approved action (if not already dispatched), log the decision, move related files to `/Done/`, and update the Dashboard.

Gold tier adds support for Facebook, Instagram, Twitter, and Odoo actions in addition to Silver's email, WhatsApp, and LinkedIn.

## Instructions

You are the AI Employee. Follow these steps precisely:

### Step 1: Read the Approval File and Handbook

Read `Company_Handbook.md` from vault root to understand approval thresholds and business rules.

Then read the approval request `.md` file provided as context. It was originally in `/Pending_Approval/` and has been moved to either `/Approved/` or `/Rejected/` by the user.

Extract the YAML frontmatter fields:
- `action` — one of: `payment`, `email_send`, `email_draft`, `whatsapp_reply`, `linkedin_post`, `facebook_reply`, `facebook_post`, `instagram_reply`, `instagram_post`, `twitter_reply`, `twitter_post`, `odoo_action`, `file_delete`, `external_api`
- `details` — human-readable description of what was requested
- `amount` — financial amount, if applicable
- `recipient` — target of the action (email address, contact name, or null)
- `reason` — why the action was needed
- `related_plan` — path to the ActionPlan in /Plans/
- `reply_content` — the actual reply/post text that was sent (or null)
- `status` — current status (pending, approved, rejected, expired)

### Step 2: Determine Decision

Based on which folder the file is now in:
- **If in `/Approved/`**: The user has approved the action
- **If in `/Rejected/`**: The user has rejected the action

### Step 3: Update the Approval File Status

Update the YAML frontmatter `status` field:
- Approved → set `status: approved`
- Rejected → set `status: rejected`

### Step 4: Handle Action-Specific Post-Processing

Based on the `action` field, determine if any remaining steps are needed:

**`email_send` or `email_draft`** (already dispatched by orchestrator via email-mcp):
- Log the sent/drafted email in the related plan
- No additional action needed

**`whatsapp_reply`** (already dispatched by orchestrator):
- Log the sent reply in the related plan
- No additional action needed

**`linkedin_post`** (already dispatched by orchestrator):
- Update `posted_date` in the related LINKEDIN_ file in /Pending_Approval/ or /Done/
- Log the publication in the related plan

**`facebook_reply` or `facebook_post`**:
- If approved AND not yet dispatched: call `scripts/social_post.post_facebook(text, user_data_dir)` with the `reply_content` field as `text`
- If DRY_RUN=true: log intent, skip actual call, record result="dry_run"
- Log the published reply/post in the related plan with `action_type: facebook_post`
- On dispatch failure: leave file in Approved/ and log `result: failure` — do NOT move to Done

**`instagram_reply` or `instagram_post`**:
- If approved AND not yet dispatched: call `scripts/social_post.post_instagram(text, user_data_dir)` with the `reply_content` field as `text`
- If DRY_RUN=true: log intent, skip actual call, record result="dry_run"
- Log the published reply/post in the related plan with `action_type: instagram_post`
- On dispatch failure: leave file in Approved/ and log `result: failure`

**`twitter_reply` or `twitter_post`**:
- If approved AND not yet dispatched: call `scripts/social_post.post_twitter(text, user_data_dir)` with the `reply_content` field as `text`
- If DRY_RUN=true: log intent, skip actual call, record result="dry_run"
- Log the published reply/tweet in the related plan with `action_type: twitter_post`
- On dispatch failure: leave file in Approved/ and log `result: failure`

**`odoo_create_invoice`, `odoo_post_invoice`, `odoo_record_payment`** (any `odoo_*` action type):
- **Delegate to the `process-odoo-action` skill** — do not directly call Odoo MCP from this skill
- Pass the full approval file path as context to `process-odoo-action`
- The `process-odoo-action` skill handles: DRY_RUN guard, ODOO_UNREACHABLE fallback, idempotency, and AuditLog
- After `process-odoo-action` completes: continue to Step 5 (update plan) and Step 6 (move to Done)

**`odoo_action`** (legacy action type — treat as `odoo_create_invoice`):
- Delegate to `process-odoo-action` skill as above

**`payment`** (requires manual execution):
- If approved: add a prominent note to the plan that payment must be executed manually
- Log the approval with the payment details and amount

**`file_delete`** (requires manual execution):
- If approved: add a note to the plan specifying which files to delete
- Log the approval

### Step 5: Process the Related Plan

Read the related ActionPlan from the `related_plan` path.

- **If approved**: Update the plan's `status` to `done`
- **If rejected**: Update the plan's `status` to `rejected`, add a note explaining the rejection

### Step 6: Move Files to /Done

Move the following files to `/Done/`:
1. The approval request file (from `/Approved/` or `/Rejected/`)
2. The related ActionPlan (from `/Plans/`)
3. The related VaultItem (from `/Needs_Action/` if still there)

When moving, preserve the original filenames. If a file with the same name already exists in `/Done/`, add a timestamp suffix.

**Important**: To "move" a file:
1. Read the file content
2. Write it to `/Done/{filename}`
3. Delete the original file

**Exception — Failed Actions**: If the action dispatch failed, do NOT move to Done. Leave the approval file in `/Approved/` for retry and log the failure.

### Step 7: Invoke update-dashboard Skill

After every processed approval (whether approved or rejected, regardless of action type),
invoke the `update-dashboard` skill to refresh `vault/Dashboard.md`.

The `update-dashboard` skill will:
- Recount all vault folder item counts
- Pull live Odoo financial data (if available)
- Update PM2 process status table
- Refresh Recent Activity (last 5 AuditLog entries)

Do NOT attempt to update Dashboard.md directly — always delegate to the skill.

## Rules

- NEVER modify the original file in /Inbox -- it stays untouched
- NEVER attempt to re-dispatch a failed action — leave in Approved/ for operator review
- Log every action with appropriate action_type:
  - Approved: `approval_granted`
  - Rejected: `approval_rejected`
  - Email sent: `email_sent`
  - Email drafted: `email_drafted`
  - WhatsApp replied: `whatsapp_triage`
  - LinkedIn posted: `linkedin_generated`
  - Facebook replied/posted: `facebook_post`
  - Instagram replied/posted: `instagram_post`
  - Twitter replied/posted: `twitter_post`
  - Odoo action: `odoo_create_invoice` / `odoo_post_invoice` / `odoo_record_payment`
- In DRY_RUN mode, log the intended actions but do NOT move files
- Always update Dashboard.md after processing

## Tools Required

- `Read` — read approval file, related plan, and Company_Handbook.md
- `Write` — write updated files to /Done
- `Edit` — update YAML frontmatter status fields and plan steps
- `Glob` — find related files across vault folders
- `Grep` — search for related items if paths are ambiguous
- `Bash` — call `scripts/social_post.py` for Facebook/Instagram/Twitter dispatch
- Skills: `process-odoo-action` (for all odoo_* action types), `update-dashboard` (Step 7)
