# Skill: Update Dashboard

## Purpose

Regenerate `Dashboard.md` with current status by reading all vault folders, counting items by type, reading recent logs, reporting watcher health, and reflecting the current state of all business operations including email, WhatsApp, and LinkedIn channels.

## Instructions

You are the AI Employee. Follow these steps precisely to regenerate the dashboard.

### Step 1: Count Items in Each Folder

Use `Glob` to count files (excluding `.gitkeep`) in each folder:

| Folder | What to Count |
|--------|--------------|
| `Inbox/` | Unprocessed files (exclude .gitkeep) |
| `Needs_Action/` | All triaged items awaiting processing (*.md, exclude .gitkeep) |
| `Plans/` | Active plans (*.md, exclude .gitkeep) |
| `Pending_Approval/` | Items awaiting human approval (*.md, exclude .gitkeep) |
| `Approved/` | Approved items waiting for action execution (*.md, exclude .gitkeep) |
| `Done/` | Completed items (*.md, exclude .gitkeep) |

Within `Needs_Action/`, also count by prefix type:
- `FILE_*` — filesystem watcher items
- `EMAIL_*` — Gmail watcher items
- `WHATSAPP_*` — WhatsApp watcher items

Within `Pending_Approval/`, also count by type:
- `APPROVE_EMAIL_*` — email approval requests
- `APPROVE_WHATSAPP_*` — WhatsApp approval requests
- `LINKEDIN_*` — LinkedIn post drafts awaiting approval
- `APPROVE_FILE_*` — file action approvals

### Step 2: Read Recent Activity

Read the most recent log file from `Logs/` (today's date: `Logs/YYYY-MM-DD.json`). Extract the last 10 entries. For each entry, format as:

```
- **{timestamp}** | {action_type} | {target} → {result}
```

If no log file exists for today, check yesterday's. If none exist, show "No recent activity."

Also tally from today's log:
- Emails sent / drafted
- WhatsApp replies dispatched
- LinkedIn posts generated
- Errors encountered

### Step 3: Read Business Goals and Handbook

Read `Business_Goals.md` and `Company_Handbook.md` from vault root. Extract from Business_Goals.md:
- Monthly revenue target
- Active project count
- Any alert conditions that are triggered

### Step 4: Find Latest Briefing

Use `Glob` to find the most recent file in `Briefings/` matching `*_Briefing.md`. If found, create a link to it. If none exist, show "No briefings generated yet."

### Step 5: Check Pending Approvals Detail

For each file in `Pending_Approval/`, read the YAML frontmatter and extract:
- `type` (approval_request or linkedin_post)
- `action` (email_send, email_draft, whatsapp_reply, linkedin_post)
- `recipient` or contact name
- `expires` timestamp
- `status`

Flag any items where `expires` is within 2 hours as "⚠️ Expiring Soon".

### Step 6: Check Watcher Status

Use `Glob` to find the most recent log file in `Logs/`. Scan recent log entries (last 50) for `actor` values to determine which watchers have been active today:
- `gmail_watcher` — Gmail pipeline active
- `whatsapp_watcher` — WhatsApp pipeline active
- `orchestrator` — Orchestrator active
- `watcher` (filesystem) — Filesystem watcher active

Report each as "Active" (seen in today's logs) or "No activity today".

### Step 7: Check Scheduling Status

Use `Glob` to look for the most recent files:
- `Briefings/*_Briefing.md` — last briefing generation date
- `Pending_Approval/LINKEDIN_*.md` or `Done/LINKEDIN_*.md` — last LinkedIn post date

Report when each scheduled task last ran.

### Step 8: Write Dashboard.md

Overwrite `Dashboard.md` at vault root with this structure:

```markdown
# Dashboard

> **Business**: Freelance Software Development & Consulting
> **Last Updated**: {current date and time}

## Quick Stats

| Metric | Count |
|--------|-------|
| Inbox (unprocessed) | {count} |
| Needs Action (total) | {count} |
| ↳ FILE_ items | {count} |
| ↳ EMAIL_ items | {count} |
| ↳ WHATSAPP_ items | {count} |
| Plans Active | {count} |
| Pending Approval (total) | {count} |
| ↳ Email approvals | {count} |
| ↳ WhatsApp approvals | {count} |
| ↳ LinkedIn drafts | {count} |
| Approved (awaiting dispatch) | {count} |
| Completed (Done) | {count} |
| This Week's Revenue | ${amount or 0} |

## Watcher Status

| Watcher | Status |
|---------|--------|
| Filesystem Watcher | {Active / No activity today} |
| Gmail Watcher | {Active / No activity today} |
| WhatsApp Watcher | {Active / No activity today} |
| Orchestrator | {Active / No activity today} |

## Scheduling Status

| Task | Last Run | Next Run |
|------|----------|----------|
| CEO Briefing (Mon 08:00) | {date of most recent Briefing file or "Never"} | {next Monday 08:00} |
| LinkedIn Post (Weekdays 09:00) | {date of most recent LINKEDIN_ file or "Never"} | {next weekday 09:00} |
| PM2 Health Check (every 5 min) | {from log or "Unknown"} | N/A |

## Recent Activity

{Last 10 log entries formatted as bullet points}
{Or "No recent activity." if none}

## Today's Channel Summary

| Channel | Sent/Posted | Drafted | Errors |
|---------|-------------|---------|--------|
| Email | {count from logs} | {count} | {count} |
| WhatsApp | {count from logs} | — | {count} |
| LinkedIn | {count from logs} | {pending count} | {count} |

## Pending Approvals

{List each file in Pending_Approval/ with type, recipient, and expiry}
{Flag items expiring within 2 hours with ⚠️}
{Or "No approvals pending." if empty}

## Latest Briefing

{Link to most recent briefing file}
{Or "No briefings generated yet."}

## Alerts

{Any triggered alert conditions from Business_Goals.md}
{Any expired approval requests}
{Or "No alerts at this time."}
```

## Rules

- ALWAYS regenerate the entire dashboard (never append/patch)
- Show accurate counts — count actual files, not cached values
- Use the current date/time for "Last Updated"
- Keep the format consistent for Obsidian rendering
- If a folder doesn't exist or is empty, show 0
- Mark expiring approvals clearly — operators need to act on them
- Watcher status based on today's log entries only (UTC date)

## Tools Required

- `Glob` — to count files in folders, find briefings, find LinkedIn posts
- `Read` — to read log files, Business_Goals.md, Company_Handbook.md, approval frontmatter
- `Write` — to overwrite Dashboard.md
