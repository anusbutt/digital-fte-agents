# Skill: Process Approval Decision

## Purpose

Process a file that has been moved to `/Approved/` or `/Rejected/` by the human operator. Log the decision, move related files to `/Done/`, and update the Dashboard.

## Instructions

You are the AI Employee. Follow these steps precisely:

### Step 1: Read the Approval File and Handbook

Read `Company_Handbook.md` from vault root to understand approval thresholds and business rules.

Then read the approval request `.md` file provided as context. It was originally in `/Pending_Approval/` and has been moved to either `/Approved/` or `/Rejected/` by the user.

Extract the YAML frontmatter fields:
- `action` (payment, email_send, social_post, file_delete, external_api)
- `details` (what was requested)
- `amount` (financial amount, if applicable)
- `recipient` (target of the action)
- `reason` (why it was needed)
- `related_plan` (path to the ActionPlan in /Plans/)
- `status` (should still say "pending")

### Step 2: Determine Decision

Based on which folder the file is now in:
- **If in `/Approved/`**: The user has approved the action
- **If in `/Rejected/`**: The user has rejected the action

### Step 3: Update the Approval File Status

Update the YAML frontmatter `status` field:
- Approved → set `status: approved`
- Rejected → set `status: rejected`

### Step 4: Process the Related Plan

Read the related ActionPlan from the `related_plan` path (e.g., `Plans/PLAN_invoice_client_a.md`).

- **If approved**: Update the plan's `status` to `in_progress` or `done` depending on whether the action can be auto-completed
- **If rejected**: Update the plan's `status` to `rejected`, add a note explaining the rejection

### Step 5: Move Files to /Done

Move the following files to `/Done/`:
1. The approval request file (from `/Approved/` or `/Rejected/`)
2. The related ActionPlan (from `/Plans/`)
3. The related VaultItem metadata (from `/Needs_Action/` if still there)

When moving, preserve the original filenames. If a file with the same name already exists in `/Done/`, add a timestamp suffix.

**Important**: To "move" a file:
1. Read the file content
2. Write it to `/Done/{filename}`
3. Delete the original file

### Step 6: Update Dashboard

Update `Dashboard.md` to reflect:
- Decreased count in Pending Approval
- Increased count in Done
- Add the decision to Recent Activity

## Rules

- NEVER modify the original file in /Inbox -- it stays untouched
- Log every action with appropriate action_type:
  - Approved: `approval_granted`
  - Rejected: `approval_rejected`
- In DRY_RUN mode, log the intended actions but do NOT move files
- Always update Dashboard.md after processing

## Tools Required

- `Read` -- to read approval file, related plan, and Company_Handbook.md
- `Write` -- to write updated files to /Done
- `Edit` -- to update YAML frontmatter status fields
- `Glob` -- to find related files
- `Grep` -- to search for related items if paths are ambiguous
