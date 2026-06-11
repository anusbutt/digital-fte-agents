---
id: "008"
title: "Phase 5: Enhanced CEO Briefing with Live Accounting Data"
stage: green
date: "2026-03-14"
surface: agent
model: claude-sonnet-4-6
feature: 001-nestaro-pilot
branch: 001-ai-employee-foundation
user: architect
command: "/sp.implement phase 5"
labels: ["phase-5", "briefing", "odoo", "scheduling", "dashboard", "mcp", "ceo"]
links:
  spec: "./specs/001-nestaro-pilot/spec.md"
  tasks: "./specs/001-nestaro-pilot/tasks.md"
  data-model: "./specs/001-nestaro-pilot/data-model.md"
  adr: "null"
  pr: "null"
files:
  - ./skills/generate-accounting-briefing.md
  - ./skills/update-dashboard.md
  - ./watchers/orchestrator.py
  - ./specs/001-nestaro-pilot/tasks.md
tests:
  - "Manual: python main.py briefing → vault/Briefings/YYYY-MM-DD_Briefing.md created"
  - "Manual: with Odoo running, briefing has live revenue/outstanding figures"
  - "Manual: with Odoo offline, briefing uses $0 placeholders, notes 'Odoo offline'"
  - "Manual: invoice > 30 days overdue → APPROVAL_odoo_send_reminder_*.md in Pending_Approval/"
  - "Manual: set BRIEFING_DAY=MON BRIEFING_TIME=08:00, run orchestrator on Monday 08:01 → briefing auto-triggered"
  - "Manual: SOCIAL_POST_TIME=09:00 on weekday → run_social_post() auto-triggered once per day"
---

## Prompt

```
/sp.implement phase 5
```

## Response Summary

Implemented Phase 5 (T037–T039): Enhanced CEO Briefing with Live Accounting Data.

### T037 — `./skills/generate-accounting-briefing.md`

Skill that produces a structured CEO briefing by combining:

**Data sources**:
1. `Business_Goals.md` — revenue target for progress calculation
2. `Company_Handbook.md` — brand/owner name for personalisation
3. `odoo-mcp.get_financial_summary()` — live MTD revenue, outstanding, overdue
4. `odoo-mcp.get_invoices(payment_state="not_paid")` — full unpaid invoice list
5. `vault/Done/` — count of completed tasks in last 7 days
6. `vault/Logs/` — action counts by type for the last 7 days

**Briefing sections** (per data-model.md §7 CEOBriefing schema):
- Executive Summary (2–3 quantitative sentences)
- Revenue table (MTD, target, progress %, outstanding)
- Unpaid Invoices table (sorted by days_overdue desc)
- Communications Activity (7-day tallies per channel)
- Completed Tasks (last 10 Done/ filenames)
- Proactive Suggestions (data-driven, 2–4 bullets)

**Overdue invoice approval requests**: for each invoice with `days_overdue > 30`,
writes `APPROVAL_odoo_send_reminder_{client_slug}_{timestamp}.md` to
`vault/Pending_Approval/` — idempotent (checks for existing files first).

**Odoo offline handling**: all monetary values show `$0.00` with a clear
"Odoo offline" notice. Briefing always generates regardless of Odoo state.

**Final step**: calls `update-dashboard` skill to refresh Dashboard.md.

### T038 — Expanded `./skills/update-dashboard.md`

Three additions to the existing skill:

1. **Step 7 — Live Odoo call via MCP** (replaces passive `Accounting/` folder read):
   - Calls `odoo-mcp.get_financial_summary({})` directly
   - Offline → shows all `—` values + "Start Odoo: `docker compose up -d`" notice
   - Auth error → shows auth error message
   - Online → shows MTD revenue, outstanding, overdue count, overdue table

2. **Step 2 — Recent Activity from NDJSON logs** (updated):
   - Reads `Logs/YYYY-MM-DD.json` (NDJSON format)
   - Extracts last **5** entries (previously 10)
   - Format: `**{timestamp}** | {action_type} | {actor} → {target} | {result}`

3. **Step 6 — 8-process System Health** (expanded from earlier prototype's 5):
   - Explicit table mapping all 8 PM2 processes to their `actor` log names
   - Shows `✅ Active` or `⚪ No activity today` per process

Dashboard template updated to match: Financial Snapshot section now shows live
Odoo table with progress %, overdue invoices sub-table, and Odoo status badge.
System Health table lists all 8 processes explicitly.

### T039 — Orchestrator scheduling (`_check_schedule`)

New `_check_schedule()` method called every loop cycle in `run()`:

Three scheduled tasks, each running at most once per UTC calendar day:

| Task | Env var | Default | Constraint |
|------|---------|---------|-----------|
| CEO Briefing | `BRIEFING_DAY` / `BRIEFING_TIME` | MON / 08:00 | Day-of-week + time check |
| Social Post | `SOCIAL_POST_TIME` | 09:00 | Weekdays only |
| LinkedIn Post | `LINKEDIN_POST_TIME` | 09:00 | Weekdays only |

Guard pattern: `_last_briefing_date`, `_last_social_post_date`, `_last_linkedin_date`
instance variables track the last run date (as `YYYY-MM-DD` string). Compared
against `today_str` each cycle — prevents double-firing.

Schedule check is added just before `time.sleep(check_interval)` in the main
loop, so it runs once every 10 seconds (default interval). At 10s granularity,
the scheduling is accurate to the nearest 10 seconds.

## Outcome

Phase 5 (T037–T039) **complete**. All 3 tasks marked `[x]` in tasks.md.

**Scheduling config summary:**
```env
BRIEFING_DAY=MON        # Monday morning briefing
BRIEFING_TIME=08:00     # Trigger time (UTC)
SOCIAL_POST_TIME=09:00  # Daily social media draft generation (weekdays)
LINKEDIN_POST_TIME=09:00 # Daily LinkedIn draft (weekdays)
```

**Ready for**: Phase 6 — US4 Ralph Wiggum Loop (T040–T041)
