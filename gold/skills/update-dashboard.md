# Skill: Update Dashboard

## Purpose

Regenerate `Dashboard.md` with current status by reading all vault folders, counting items by type, reading recent logs, reporting watcher health, and reflecting the current state of all business operations including email, WhatsApp, Facebook, Instagram, Twitter, LinkedIn channels, and Odoo financial data.

Gold tier adds: Odoo Financial Snapshot, social media channel summary (Facebook, Instagram, Twitter), and 8-process system health (vs Silver's 5).

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
- `FACEBOOK_*` — Facebook watcher items
- `INSTAGRAM_*` — Instagram watcher items
- `TWITTER_*` — Twitter/X watcher items

Within `Pending_Approval/`, also count by type:
- `APPROVE_EMAIL_*` — email approval requests
- `APPROVE_WHATSAPP_*` — WhatsApp approval requests
- `APPROVE_FACEBOOK_*` — Facebook approval requests
- `APPROVE_INSTAGRAM_*` — Instagram approval requests
- `APPROVE_TWITTER_*` — Twitter/X approval requests
- `LINKEDIN_*` — LinkedIn post drafts awaiting approval
- `APPROVE_FILE_*` — file action approvals

### Step 2: Read Recent Activity from Logs

Read the most recent log file from `Logs/` (today's date: `Logs/YYYY-MM-DD.json`).
Note: log files use `.json` extension (NDJSON format — one JSON object per line).
Extract the **last 5 entries** for the Recent Activity section. For each entry, format as:

```
- **{timestamp}** | {action_type} | {actor} → {target} | {result}
```

If no log file exists for today, check yesterday's. If none exist, show "No recent activity."

Also tally from today's log for the Channel Summary:
- Emails sent / drafted (`email_sent`, `email_drafted`)
- WhatsApp replies dispatched (`whatsapp_reply`)
- Facebook posts/replies published (`facebook_post`, `facebook_reply`)
- Instagram posts/replies published (`instagram_post`, `instagram_reply`)
- Twitter posts/replies published (`twitter_post`, `twitter_reply`)
- LinkedIn posts generated (`linkedin_generated`)
- Odoo actions completed (`odoo_create_invoice`, `odoo_post_invoice`, `odoo_record_payment`)
- Errors encountered (entries with `result: "failure"`)

### Step 3: Read Business Goals and Handbook

Read `Business_Goals.md` and `Company_Handbook.md` from vault root. Extract from Business_Goals.md:
- Monthly revenue target
- Active project count
- Odoo financial targets
- Any alert conditions that are triggered

### Step 4: Find Latest Briefing

Use `Glob` to find the most recent file in `Briefings/` matching `*_Briefing.md`. If found, create a link to it. If none exist, show "No briefings generated yet."

### Step 5: Check Pending Approvals Detail

For each file in `Pending_Approval/`, read the YAML frontmatter and extract:
- `type` (approval_request or linkedin_post)
- `action` (email_send, email_draft, whatsapp_reply, linkedin_post, facebook_reply, etc.)
- `recipient` or contact name
- `expires` timestamp
- `status`

Flag any items where `expires` is within 2 hours as "⚠️ Expiring Soon".

### Step 6: Check Watcher Status (8 Gold PM2 Processes)

Use `Glob` to find the most recent log file in `Logs/` (today's `YYYY-MM-DD.json`
then yesterday's as fallback). Read up to last 100 log entries.

For each of the 8 Gold PM2 processes, check if its `actor` name appears in
today's log entries:

| Process Name | actor value in logs |
|---|---|
| filesystem-watcher | `filesystem_watcher` or `watcher` |
| gmail-watcher | `gmail_watcher` |
| whatsapp-watcher | `whatsapp_watcher` |
| facebook-watcher | `facebook_watcher` |
| instagram-watcher | `instagram_watcher` |
| twitter-watcher | `twitter_watcher` |
| orchestrator | `orchestrator` |
| email-mcp | `email_mcp` (or skip — MCP servers log differently) |

Report each as:
- `✅ Active` — seen in today's logs
- `⚪ No activity today` — not seen in today's logs

Also extract the **last 5 log entries** from today's log file for the
Recent Activity section. Format each as:
```
- **{timestamp}** | {action_type} | {actor} → {target} | {result}
```

### Step 7: Fetch Live Odoo Financial Data

Call the `odoo-mcp` MCP tool `get_financial_summary` with no arguments:

```
Tool: get_financial_summary
Input: {}
```

**If `success: true`**: extract `mtd_revenue`, `total_outstanding`,
`paid_invoice_count`, `unpaid_invoice_count`, `overdue_invoices`, `currency`.
Set Odoo Status = **online**.

**If `success: false` and `error: "ODOO_UNREACHABLE"`**:
- Set all monetary values to `"—"` (unavailable)
- Set Odoo Status = **offline**
- Show: `> Start Odoo: \`docker compose up -d\` then wait ~60s`

**If `success: false` and `error: "AUTH_FAILED"`**:
- Set all monetary values to `"—"` (auth error)
- Set Odoo Status = **auth error — check ODOO_API_KEY**

Extract monthly revenue target from `Business_Goals.md` (look for `$X,XXX/month`
or similar). Compute progress percentage: `(mtd_revenue / target) * 100`.

If `Accounting/` folder has any recent snapshot files, also check them for
any data not covered by the live call.

### Step 8: Check Scheduling Status

Use `Glob` to look for the most recent files:
- `Briefings/*_Briefing.md` — last briefing generation date
- `Pending_Approval/LINKEDIN_*.md` or `Done/LINKEDIN_*.md` — last LinkedIn post date

Report when each scheduled task last ran.

### Step 9: Write Dashboard.md

Overwrite `Dashboard.md` at vault root with this structure:

```markdown
# AI Employee Dashboard — Gold Tier

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
| ↳ FACEBOOK_ items | {count} |
| ↳ INSTAGRAM_ items | {count} |
| ↳ TWITTER_ items | {count} |
| Plans Active | {count} |
| Pending Approval (total) | {count} |
| ↳ Email approvals | {count} |
| ↳ WhatsApp approvals | {count} |
| ↳ Facebook approvals | {count} |
| ↳ Instagram approvals | {count} |
| ↳ Twitter/X approvals | {count} |
| ↳ LinkedIn drafts | {count} |
| Approved (awaiting dispatch) | {count} |
| Completed (Done) | {count} |

## Financial Snapshot (Odoo)

{If Odoo offline:}
> ⚠️ **Odoo offline** — Start with: `docker compose up -d` then wait ~60s

{If Odoo auth error:}
> ⚠️ **Odoo auth error** — Check `ODOO_API_KEY` in `.env`

| Metric | Value |
|--------|-------|
| MTD Revenue | ${mtd_revenue} {currency} |
| Monthly Target | ${target} |
| Progress | {percent}% of target |
| Outstanding | ${total_outstanding} ({unpaid_invoice_count} invoices) |
| Overdue Invoices | {count of overdue_invoices} |
| Odoo Status | **{online \| offline \| auth error}** |

{If overdue_invoices list is not empty:}
**Overdue Invoices:**

| Invoice | Client | Amount | Days Overdue |
|---------|--------|--------|-------------|
| {name} | {partner} | ${amount} | {days_overdue} |

## System Health

| Process | Status |
|---------|--------|
| filesystem-watcher | {✅ Active \| ⚪ No activity today} |
| gmail-watcher | {✅ Active \| ⚪ No activity today} |
| whatsapp-watcher | {✅ Active \| ⚪ No activity today} |
| facebook-watcher | {✅ Active \| ⚪ No activity today} |
| instagram-watcher | {✅ Active \| ⚪ No activity today} |
| twitter-watcher | {✅ Active \| ⚪ No activity today} |
| orchestrator | {✅ Active \| ⚪ No activity today} |
| email-mcp | {✅ Active \| ⚪ No activity today} |

## Scheduling Status

| Task | Last Run | Next Run |
|------|----------|----------|
| CEO Briefing (Mon 08:00) | {date of most recent Briefing file or "Never"} | {next Monday 08:00} |
| LinkedIn Post (Weekdays 09:00) | {date of most recent LINKEDIN_ file or "Never"} | {next weekday 09:00} |

## Recent Activity (Last 5 Actions)

{Last 5 log entries from today's Logs/YYYY-MM-DD.json formatted as bullet points}
{Or "No recent activity." if none}

## Today's Channel Summary

| Channel | Sent/Posted | Drafted | Errors |
|---------|-------------|---------|--------|
| Email | {count from logs} | {count} | {count} |
| WhatsApp | {count from logs} | — | {count} |
| Facebook | {count from logs} | — | {count} |
| Instagram | {count from logs} | — | {count} |
| Twitter/X | {count from logs} | — | {count} |
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

- `odoo-mcp` (MCP) — `get_financial_summary` (with graceful fallback if offline)
- `Glob` — to count files in folders, find briefings, find LinkedIn posts
- `Read` — to read log files (NDJSON), Business_Goals.md, Company_Handbook.md, approval frontmatter
- `Write` — to overwrite Dashboard.md
