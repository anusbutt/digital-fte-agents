# Skill: Process Approval Decision

## Purpose

Process a file that has been moved to `/Approved/` or `/Rejected/` by the human operator. Execute the approved action (if not already dispatched), log the decision, move related files to `/Done/`, and update the Dashboard.

## Instructions

You are the AI Employee. Follow these steps precisely:

### Step 1: Read the Approval File and Handbook

Read `Company_Handbook.md` from vault root to understand approval thresholds and business rules.

Then read the approval request `.md` file provided as context. It was originally in `/Pending_Approval/` and has been moved to either `/Approved/` or `/Rejected/` by the user (or the orchestrator after a successful action dispatch).

Extract the YAML frontmatter fields:
- `action` — one of: `payment`, `email_send`, `email_draft`, `whatsapp_reply`, `linkedin_post`, `file_delete`, `external_api`
- `details` — human-readable description of what was requested
- `amount` — financial amount, if applicable
- `recipient` — target of the action (email address, contact name, or null)
- `reason` — why the action was needed
- `related_plan` — path to the ActionPlan in /Plans/
- `reply_content` — the actual reply/post text that was sent (or null)
- `status` — current status (pending, approved, rejected, expired)

### Step 2: Determine Decision

Based on which folder the file is now in:
- **If in `/Approved/`**: The user has approved the action (or the orchestrator dispatched it successfully)
- **If in `/Rejected/`**: The user has rejected the action

### Step 3: Update the Approval File Status

Update the YAML frontmatter `status` field:
- Approved → set `status: approved`
- Rejected → set `status: rejected`

### Step 4: Handle Action-Specific Post-Processing

Based on the `action` field, determine if any remaining steps are needed:

**`email_send` or `email_draft`** (already dispatched by orchestrator via email-mcp):
- Log the sent/drafted email in the related plan
- No additional action needed — email was already sent/drafted

**`whatsapp_reply`** (already dispatched by orchestrator):
- Log the sent reply in the related plan
- No additional action needed — reply was already sent

**`linkedin_post`** (already dispatched by orchestrator):
- Update `posted_date` in the related LINKEDIN_ file in /Pending_Approval/ or /Done/
- Log the publication in the related plan
- No additional action needed — post was already published

**`payment`** (requires manual execution):
- If approved: add a prominent note to the plan that payment must be executed manually
- Log the approval with the payment details and amount

**`file_delete`** (requires manual execution):
- If approved: add a note to the plan specifying which files to delete
- Log the approval

**`file_process`** or other actions:
- Update the plan status to reflect the decision

**If action was previously dispatched but failed** (status may show retry needed):
- Log the failure note in the plan
- Do NOT attempt to re-dispatch — leave for operator review

### Step 5: Process the Related Plan

Read the related ActionPlan from the `related_plan` path (e.g., `Plans/PLAN_EMAIL_abc123.md`).

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

**Exception — Failed Actions**: If the action dispatch failed (check log entries or `status` field), do NOT move to Done. Leave the approval file in `/Approved/` for retry and log the failure.

### Step 7: Update Dashboard

Update `Dashboard.md` to reflect:
- Decreased count in Pending Approval
- Increased count in Done
- Add the decision to Recent Activity, including the action type

## Rules

- NEVER modify the original file in /Inbox -- it stays untouched
- NEVER attempt to re-dispatch a failed action — leave in Approved/ for operator review
- Log every action with appropriate action_type:
  - Approved: `approval_granted`
  - Rejected: `approval_rejected`
  - Email sent: `email_sent`
  - Email drafted: `email_drafted`
  - WhatsApp replied: `whatsapp_replied`
  - LinkedIn posted: `linkedin_posted`
- In DRY_RUN mode, log the intended actions but do NOT move files
- Always update Dashboard.md after processing
- For `whatsapp_reply` actions: always mark as requiring approval in activity log

## Tools Required

- `Read` -- to read approval file, related plan, and Company_Handbook.md
- `Write` -- to write updated files to /Done
- `Edit` -- to update YAML frontmatter status fields and plan steps
- `Glob` -- to find related files
- `Grep` -- to search for related items if paths are ambiguous
