# Skill: Generate Weekly CEO Briefing

## Purpose

Generate a comprehensive weekly briefing summarizing all business activity across all channels (files, email, WhatsApp, LinkedIn), comparing against goals, identifying bottlenecks, and providing proactive suggestions. Output to `Briefings/YYYY-MM-DD_Briefing.md` in the vault and update the Dashboard.

## Instructions

You are the AI Employee. Follow these steps precisely to generate the CEO Briefing.

### Step 1: Determine the Reporting Period

- **Period end**: Today's date
- **Period start**: 7 days before today
- Use ISO 8601 format for all dates (YYYY-MM-DD)
- Ensure `Briefings/` directory exists in the vault root (create if needed)

### Step 2: Read Completed Work

Use `Glob` to find all `.md` files in `Done/` (excluding `.gitkeep`).

For each file, read the YAML frontmatter and extract:
- What type of item it was (`FILE_`, `EMAIL_`, `WHATSAPP_`, `LINKEDIN_`, `APPROVE_`)
- When it was completed
- Any financial amounts involved
- Whether it required approval

Group by type:
- **FILE_ items**: invoices, receipts, contracts, client briefs
- **EMAIL_ items**: emails processed, replied, or drafted
- **WHATSAPP_ items**: WhatsApp conversations resolved
- **LINKEDIN_ items**: posts published

If no files exist in `Done/`, note "No completed items this period."

### Step 3: Read Audit Logs

Read log files from `Logs/` for the reporting period (last 7 days of `YYYY-MM-DD.json` files).

Count and categorize:
- Total actions taken
- Files triaged (action_type: `plan_created` with item_type: file)
- Emails triaged (action_type: `plan_created` with item_type: email)
- Email replies sent (action_type: `email_sent`)
- Email drafts created (action_type: `email_drafted`)
- WhatsApp messages triaged (action_type: `plan_created` with item_type: whatsapp)
- WhatsApp replies sent (action_type: `whatsapp_replied`)
- LinkedIn posts generated (action_type: `linkedin_generated`)
- LinkedIn posts published (action_type: `linkedin_posted`)
- Approvals granted / rejected (action_type: `approval_granted` / `approval_rejected`)
- Expired approvals (event: `approval_expired`)
- Errors encountered (action_type: `error`)
- Dashboard updates

### Step 4: Read Business Goals and Handbook

Read `Business_Goals.md` and `Company_Handbook.md` from vault root. Use Company_Handbook.md for classification rules, client tiers, and approval thresholds when interpreting completed work. Extract from Business_Goals.md:
- Monthly revenue target
- Active projects and deadlines
- Key metrics and their targets
- Alert thresholds

### Step 5: Read Previous Briefing (if exists)

Use `Glob` to find the most recent `*_Briefing.md` in `Briefings/`. If found, read it to identify:
- Trends compared to last week
- Recurring bottlenecks
- Progress on previously flagged items
- Channel activity trends (email volume up/down, WhatsApp volume, LinkedIn engagement)

### Step 6: Generate the Briefing

Write the briefing to `Briefings/YYYY-MM-DD_Briefing.md` (using today's date) with this exact structure:

```yaml
---
type: ceo_briefing
generated: {current ISO 8601 timestamp}
period_start: {7 days ago YYYY-MM-DD}
period_end: {today YYYY-MM-DD}
---
```

Then add these required sections:

```markdown
# Weekly CEO Briefing

**Period**: {period_start} to {period_end}
**Generated**: {current date and time}

## Executive Summary

{1-2 sentence overview of the week. Highlight the most important takeaway across all channels.}

## Revenue

- **This Week**: ${amount from completed invoices/receipts, or $0}
- **MTD**: ${month-to-date total}
- **Monthly Target**: ${from Business_Goals.md}
- **Progress**: {percentage of target achieved}
- **Trend**: {On track | Behind | Ahead} compared to target

## Communications Activity

### Email

- **Emails triaged**: {count}
- **Replies sent automatically**: {count (non-sensitive auto-execute)}
- **Drafts created for review**: {count (sensitive)}
- **Pending email approvals**: {count still in Pending_Approval/}

### WhatsApp

- **Messages triaged**: {count}
- **Replies approved and sent**: {count}
- **Pending WhatsApp approvals**: {count still in Pending_Approval/}

### LinkedIn

- **Posts generated**: {count}
- **Posts approved and published**: {count}
- **Posts pending approval**: {count still in Pending_Approval/}
- **Last post date**: {date or "None this period"}

## Completed Tasks

{List each item from Done/ this week grouped by type}

**Files Processed:**
- [x] {item description} ({type}, {date completed})

**Emails Handled:**
- [x] {email subject or ID} ({sent/drafted}, {date})

**WhatsApp Conversations:**
- [x] {contact name} — {keywords} ({date})

{If no items in a category: omit that category}
{If no items at all: "No tasks completed this period."}

## Approval Activity

- **Total approvals processed**: {count}
- **Approved**: {count}
- **Rejected**: {count}
- **Expired (no action taken)**: {count — flag if > 0}

## Bottlenecks

{Identify issues slowing progress across all channels}

| Issue | Impact | Suggested Action |
|-------|--------|-----------------|
| {issue} | {what it affects} | {recommended fix} |

{If no bottlenecks: "No bottlenecks identified this period."}

## Proactive Suggestions

### Cost Optimization
- {Suggestion based on spending patterns}

### Upcoming Deadlines
- {Any deadlines within the next 14 days from Business_Goals.md}

### Process Improvements
- {Suggestions based on log patterns — e.g., frequent errors, items stuck in queues}
- {High email draft rate → review sensitivity classification rules}
- {Many expired approvals → operator review cadence needs adjustment}

## AI Employee Performance

- **Total actions this week**: {total from logs}
- **Success rate**: {successful / total actions}%
- **Channels active**: {list of active channels}
- **Email auto-execute rate**: {sent / (sent + drafted)}% (target: maximize for non-sensitive)
- **Approvals processed**: {count}
- **Errors**: {count} {— list top error types if > 0}
```

### Step 7: Update Dashboard

After writing the briefing, update `Dashboard.md`:
- Set "Latest Briefing" section to link to the new briefing file: `[YYYY-MM-DD Briefing](Briefings/YYYY-MM-DD_Briefing.md)`

## Rules

- ALWAYS include all required sections, even if data is empty (use "No data" or "0" placeholders)
- Financial amounts should be formatted with $ and commas ($1,234.56)
- Be honest about metrics — never inflate or hide poor performance
- Suggestions should be specific and actionable, not generic
- Reference Business_Goals.md targets when discussing performance
- Keep the Executive Summary to 1-2 sentences maximum
- ALWAYS write to `Briefings/` (relative to vault root) — never use an absolute path
- Include ALL communication channels (email, WhatsApp, LinkedIn) in the summary

## Tools Required

- `Glob` — to find files in Done/, Logs/, Briefings/, Pending_Approval/
- `Read` — to read files, logs, Business_Goals.md, and Company_Handbook.md
- `Write` — to create briefing in Briefings/ and update Dashboard.md
