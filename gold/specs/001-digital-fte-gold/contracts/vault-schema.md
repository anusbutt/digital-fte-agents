# Contract: Vault Schema & File Naming Conventions

## Folder Purpose Map

| Folder | Purpose | Written by | Read by |
|--------|---------|-----------|---------|
| `vault/Inbox/` | Human/external file drops | Human | Filesystem watcher |
| `vault/Needs_Action/` | All watcher output | Watchers | Orchestrator |
| `vault/Plans/` | Claude action plans | triage-inbox skill | Orchestrator |
| `vault/Pending_Approval/` | HITL queue | Skills | Human + Orchestrator |
| `vault/Approved/` | Human-approved | Human | Orchestrator |
| `vault/Rejected/` | Human-rejected | Human | Orchestrator |
| `vault/Done/` | Completed items | Orchestrator | generate-accounting-briefing |
| `vault/Logs/` | JSON audit trail | logger.py | generate-accounting-briefing |
| `vault/Briefings/` | CEO briefings | generate-accounting-briefing | Human |
| `vault/Accounting/` | Odoo mirrors | generate-accounting-briefing | Human |

## File Naming Conventions

### Needs_Action items (from watchers)
```
EMAIL_{message_id}.md
WHATSAPP_{chat_id}_{timestamp}.md
FACEBOOK_{thread_id}_{timestamp}.md
INSTAGRAM_{thread_id}_{timestamp}.md
TWITTER_{tweet_or_dm_id}_{timestamp}.md
FILE_{original_filename}.md
SYSTEM_{error_type}_{timestamp}.md
```

### Plans
```
PLAN_EMAIL_{message_id}.md
PLAN_FACEBOOK_{thread_id}_{timestamp}.md
(mirrors the Needs_Action filename with PLAN_ prefix)
```

### Approval Requests
```
APPROVAL_{action_type}_{source}_{YYYYMMDD_HHMMSS}.md
Example: APPROVAL_facebook_post_businesspage_20260313_091500.md
Example: APPROVAL_odoo_create_invoice_clienta_20260313_120000.md
```

### Social Post Approvals
```
SOCIAL_POST_FACEBOOK_{YYYYMMDD_HHMMSS}.md
SOCIAL_POST_INSTAGRAM_{YYYYMMDD_HHMMSS}.md
SOCIAL_POST_TWITTER_{YYYYMMDD_HHMMSS}.md
```

### Briefings
```
YYYY-MM-DD_Briefing.md
Example: 2026-03-16_Briefing.md
```

### Audit Logs
```
vault/Logs/YYYY-MM-DD.json   (NDJSON — one JSON object per line)
```

## Deduplication Rules

- **Watchers** store processed IDs in memory (set) during runtime
- **On restart**, watchers re-read `vault/Needs_Action/` and `vault/Done/`
  filenames to rebuild the processed set from the `raw_id` frontmatter field
- **Orchestrator** skips any Needs_Action file that already has a corresponding
  PLAN_ file in `vault/Plans/`

## Expiry Rules

- ApprovalRequests: expire 24 hours after `created` timestamp
- Orchestrator checks expiry on every cycle; moves expired files to Done/
  with `status: expired` in frontmatter

## Dashboard.md Required Sections

```markdown
# AI Employee Dashboard — Gold Tier

*Last updated: {ISO-8601}*

## Status
| Folder | Count |
|--------|-------|
| Needs Action | {n} |
| Pending Approval | {n} |
| Done (today) | {n} |

## Financial Snapshot (Odoo)
- MTD Revenue: ${amount} / ${target} ({pct}%)
- Outstanding: ${amount} ({count} invoices)
- Overdue: {count} invoices

## Recent Activity (last 5 actions)
| Time | Action | Result |
|------|--------|--------|
...

## Latest Briefing
[{date} CEO Briefing](Briefings/{date}_Briefing.md)

## System Health
| Process | Status |
|---------|--------|
| filesystem-watcher | {running/stopped} |
| gmail-watcher | {running/stopped} |
| whatsapp-watcher | {running/stopped} |
| facebook-watcher | {running/stopped} |
| instagram-watcher | {running/stopped} |
| twitter-watcher | {running/stopped} |
| orchestrator | {running/stopped} |
| email-mcp | {running/stopped} |
```
