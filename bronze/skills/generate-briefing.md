# Skill: Generate Weekly CEO Briefing

## Purpose

Generate a comprehensive weekly briefing summarizing all business activity, comparing against goals, identifying bottlenecks, and providing proactive suggestions. Output to `/Briefings/YYYY-MM-DD_Briefing.md` and update the Dashboard.

## Instructions

You are the AI Employee. Follow these steps precisely to generate the CEO Briefing.

### Step 1: Determine the Reporting Period

- **Period end**: Today's date
- **Period start**: 7 days before today
- Use ISO 8601 format for all dates (YYYY-MM-DD)

### Step 2: Read Completed Work

Use `Glob` to find all `.md` files in `/Done/` (excluding `.gitkeep`).

For each file, read the YAML frontmatter and extract:
- What type of item it was (invoice, receipt, client_brief, contract)
- When it was completed
- Any financial amounts involved
- Whether it required approval

If no files exist in `/Done/`, note "No completed items this period."

### Step 3: Read Audit Logs

Read log files from `/Logs/` for the reporting period (last 7 days of `YYYY-MM-DD.json` files).

Count and categorize:
- Total actions taken
- Files triaged
- Plans created
- Approvals granted / rejected
- Errors encountered
- Dashboard updates

### Step 4: Read Business Goals and Handbook

Read `Business_Goals.md` and `Company_Handbook.md` from vault root. Use Company_Handbook.md for classification rules, client tiers, and approval thresholds when interpreting completed work. Extract from Business_Goals.md:
- Monthly revenue target
- Active projects and deadlines
- Key metrics and their targets
- Alert thresholds

### Step 5: Read Previous Briefing (if exists)

Use `Glob` to find the most recent `*_Briefing.md` in `/Briefings/`. If found, read it to identify:
- Trends compared to last week
- Recurring bottlenecks
- Progress on previously flagged items

### Step 6: Generate the Briefing

Write the briefing to `/Briefings/YYYY-MM-DD_Briefing.md` (using today's date) with this exact structure:

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

{1-2 sentence overview of the week. Highlight the most important takeaway.}

## Revenue

- **This Week**: ${amount from completed invoices/receipts, or $0}
- **MTD**: ${month-to-date total}
- **Monthly Target**: ${from Business_Goals.md}
- **Progress**: {percentage of target achieved}
- **Trend**: {On track | Behind | Ahead} compared to target

## Completed Tasks

{List each item from /Done/ this week}
- [x] {item description} ({type}, {date completed})

{If no items: "No tasks completed this period."}

## Bottlenecks

{Identify issues slowing progress}

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
- {Suggestions based on log patterns -- e.g., frequent errors, items stuck in queues}

## AI Employee Performance

- **Actions this week**: {total from logs}
- **Success rate**: {successful / total actions}%
- **Average processing time**: {if measurable}
- **Approvals processed**: {count}
```

### Step 7: Update Dashboard

After writing the briefing, update `Dashboard.md`:
- Set "Latest Briefing" to link to the new briefing file: `[YYYY-MM-DD Briefing](Briefings/YYYY-MM-DD_Briefing.md)`

## Rules

- ALWAYS include all required sections, even if data is empty (use "No data" placeholders)
- Financial amounts should be formatted with $ and commas ($1,234.56)
- Be honest about metrics -- never inflate or hide poor performance
- Suggestions should be specific and actionable, not generic
- Reference Business_Goals.md targets when discussing performance
- Keep the Executive Summary to 1-2 sentences maximum

## Tools Required

- `Glob` -- to find files in /Done/, /Logs/, /Briefings/
- `Read` -- to read files, logs, Business_Goals.md, and Company_Handbook.md
- `Write` -- to create briefing and update Dashboard.md
