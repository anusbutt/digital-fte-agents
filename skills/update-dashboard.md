# Skill: Update Dashboard

## Purpose

Regenerate `Dashboard.md` with current status by reading all vault folders, counting items, reading recent logs, and reflecting the current state of business operations.

## Instructions

You are the AI Employee. Follow these steps precisely to regenerate the dashboard.

### Step 1: Count Items in Each Folder

Use `Glob` to count files (excluding `.gitkeep`) in each folder:

| Folder | What to Count |
|--------|--------------|
| `Inbox/` | Unprocessed files (exclude .gitkeep) |
| `Needs_Action/` | Triaged items awaiting processing (*.md, exclude .gitkeep) |
| `Plans/` | Active plans (*.md, exclude .gitkeep) |
| `Pending_Approval/` | Items awaiting human approval (*.md, exclude .gitkeep) |
| `Done/` | Completed items (*.md, exclude .gitkeep) |

### Step 2: Read Recent Activity

Read the most recent log file from `Logs/` (today's date: `Logs/YYYY-MM-DD.json`). Extract the last 10 entries. For each entry, format as:

```
- **{timestamp}** | {action_type} | {target} → {result}
```

If no log file exists for today, check yesterday's. If none exist, show "No recent activity."

### Step 3: Read Business Goals and Handbook

Read `Business_Goals.md` and `Company_Handbook.md` from vault root. Extract from Business_Goals.md:
- Monthly revenue target
- Active project count
- Any alert conditions that are triggered

### Step 4: Find Latest Briefing

Use `Glob` to find the most recent file in `Briefings/` matching `*_Briefing.md`. If found, create a link to it. If none exist, show "No briefings generated yet."

### Step 5: Write Dashboard.md

Overwrite `Dashboard.md` at vault root with this structure:

```markdown
# Dashboard

> **Business**: Freelance Software Development & Consulting
> **Last Updated**: {current date and time}

## Quick Stats

| Metric | Count |
|--------|-------|
| Inbox (unprocessed) | {count} |
| Needs Action | {count} |
| Plans Active | {count} |
| Pending Approval | {count} |
| Completed (Done) | {count} |
| This Week's Revenue | ${amount or 0} |

## Recent Activity

{Last 10 log entries formatted as bullet points}
{Or "No recent activity." if none}

## Pending Approvals

{List each file in Pending_Approval/ with its details}
{Or "No approvals pending." if empty}

## Latest Briefing

{Link to most recent briefing file}
{Or "No briefings generated yet."}

## Alerts

{Any triggered alert conditions from Business_Goals.md}
{Or "No alerts at this time."}
```

## Rules

- ALWAYS regenerate the entire dashboard (never append/patch)
- Show accurate counts -- count actual files, not cached values
- Use the current date/time for "Last Updated"
- Keep the format consistent for Obsidian rendering
- If a folder doesn't exist or is empty, show 0

## Tools Required

- `Glob` -- to count files in folders and find briefings
- `Read` -- to read log files, Business_Goals.md, and Company_Handbook.md
- `Write` -- to overwrite Dashboard.md
