# Data Model: Digital FTE Silver

**Feature**: 001-digital-fte-silver
**Date**: 2026-02-18

## Entities

### 1. VaultItem (Extended from Bronze)

Base entity for all items entering the processing pipeline. Stored as `.md` files with YAML frontmatter in `vault/Needs_Action/`.

**Prefixes**:
- `FILE_{name}.md` — filesystem watcher items (Bronze)
- `EMAIL_{message_id}.md` — Gmail watcher items (Silver)
- `WHATSAPP_{contact}_{timestamp}.md` — WhatsApp watcher items (Silver)

#### FILE_ VaultItem (existing)

```yaml
---
type: invoice | receipt | client_brief | contract | unknown
original_name: "filename.ext"
detected_date: 2026-02-18T10:00:00Z
priority: high | medium | low
status: pending | triaged | done
source_path: "Inbox/filename.ext"
---
```

#### EMAIL_ VaultItem (new)

```yaml
---
type: email
email_id: "message_id_from_gmail"
from: "sender@example.com"
from_name: "Sender Name"
to: "your@gmail.com"
subject: "Email subject line"
snippet: "First 200 chars of email body..."
received_date: 2026-02-18T10:00:00Z
priority: high | medium | low
status: pending | triaged | done
sensitivity: sensitive | non-sensitive
labels: ["INBOX", "UNREAD"]
has_attachments: true | false
---

## Email Content

{Full email body text}

## Suggested Actions

- [ ] Review and respond to this email
```

**Sensitivity Classification**:
- `sensitive`: new/unknown sender, financial content (invoice, payment, amount, $), attachments
- `non-sensitive`: known sender, informational, no financial content

**Priority Classification**:
- `high`: contains "urgent", "asap", "deadline", financial keywords
- `medium`: from known contacts, standard business inquiry
- `low`: general inquiry, no urgency markers

#### WHATSAPP_ VaultItem (new)

```yaml
---
type: whatsapp
contact: "Contact Name"
phone: "+1234567890"
message_text: "Full message text"
keywords_matched: ["invoice", "payment"]
detected_date: 2026-02-18T10:00:00Z
priority: high | medium | low
status: pending | triaged | done
---

## Message Details

- **From**: {contact} ({phone})
- **Message**: {message_text}
- **Keywords**: {keywords_matched}

## Suggested Actions

- [ ] Review and respond to this message (approval required)
```

**Business Keywords**: `urgent, invoice, payment, pricing, help, quote, project, deadline`

### 2. ActionPlan (Extended from Bronze)

Plans created by the triage skill. Stored in `vault/Plans/`.

**Naming**: `PLAN_{prefix}_{identifier}.md`
- `PLAN_FILE_{name}.md`
- `PLAN_EMAIL_{message_id}.md`
- `PLAN_WHATSAPP_{contact}_{timestamp}.md`
- `PLAN_LINKEDIN_{date}.md`

```yaml
---
type: action_plan
related_item: "Needs_Action/{VaultItem filename}"
objective: "Clear one-line summary"
priority: high | medium | low
approval_required: true | false
action_type: file_process | email_reply | whatsapp_reply | linkedin_post
created: 2026-02-18T10:00:00Z
status: pending | in_progress | done | rejected | failed
---

## Objective

{What needs to happen}

## Steps

- [ ] Step 1: {action}
- [ ] Step 2: {action} [REQUIRES APPROVAL]
- [ ] Step 3: {action}

## Context

{Business rules from Company_Handbook.md}

## Reply Draft (if applicable)

{AI-generated reply for email/WhatsApp, or post content for LinkedIn}
```

### 3. ApprovalRequest (Extended from Bronze)

Approval files in `vault/Pending_Approval/`.

**Naming**: `APPROVE_{prefix}_{identifier}.md`

```yaml
---
type: approval_request
action: payment | email_send | email_draft | whatsapp_reply | linkedin_post | file_delete | external_api
details: "Human-readable description"
amount: null | 500.00
recipient: "recipient@email.com" | "Contact Name" | null
reason: "Why this action is needed"
related_plan: "Plans/PLAN_{name}.md"
reply_content: "The actual reply/post text to be sent"
created: 2026-02-18T10:00:00Z
expires: 2026-02-19T10:00:00Z
status: pending | approved | rejected | expired
---

## Action Details

{Full description}

## Content to Send

{The actual email reply, WhatsApp message, or LinkedIn post}

## To Approve

Move this file to the `/Approved/` folder.

## To Reject

Move this file to the `/Rejected/` folder.
```

### 4. LinkedInPost (new)

Generated LinkedIn posts awaiting approval. Created by the `generate-linkedin-post` skill.

**Stored as**: `LINKEDIN_{YYYY-MM-DD}.md` in `vault/Pending_Approval/`

```yaml
---
type: linkedin_post
content: "Full post text"
topic: "AI automation | digital FTEs | industry insights"
generated_date: 2026-02-18T09:00:00Z
status: pending | approved | rejected | posted
posted_date: null | 2026-02-18T09:30:00Z
---

## LinkedIn Post

{Post content}

## To Approve

Move this file to the `/Approved/` folder.

## To Reject

Move this file to the `/Rejected/` folder.
```

### 5. AuditLogEntry (existing, unchanged)

Log entries in `vault/Logs/YYYY-MM-DD.md`.

```json
{
  "timestamp": "2026-02-18T10:00:00Z",
  "action_type": "file_triage | email_triage | whatsapp_triage | plan_created | email_sent | email_drafted | whatsapp_replied | linkedin_posted | approval_requested | approval_granted | approval_rejected | dashboard_updated | briefing_generated | error",
  "actor": "watcher | gmail_watcher | whatsapp_watcher | orchestrator | claude_code | email_mcp | linkedin_poster",
  "target": "filename or entity",
  "parameters": {},
  "result": "success | failure | skipped",
  "approval_status": "not_required | pending | approved | rejected"
}
```

**New action_types for Silver**:
- `email_triage` — Gmail watcher detected actionable email
- `whatsapp_triage` — WhatsApp watcher detected keyword message
- `email_sent` — email-mcp sent an email
- `email_drafted` — email-mcp created a draft
- `whatsapp_replied` — Playwright sent WhatsApp reply
- `linkedin_posted` — Playwright published LinkedIn post

## State Transitions

```
                    ┌─────────────────────────────────────────────┐
                    │                  WATCHERS                    │
                    │  Gmail → EMAIL_*.md                          │
                    │  WhatsApp → WHATSAPP_*.md                   │
                    │  Filesystem → FILE_*.md                      │
                    └────────────────────┬────────────────────────┘
                                         │
                                         ▼
                               vault/Needs_Action/
                                         │
                                         │ (orchestrator → triage skill)
                                         ▼
                                  vault/Plans/
                                    PLAN_*.md
                                         │
                        ┌────────────────┴────────────────┐
                        │                                  │
                  approval_required=true          approval_required=false
                        │                                  │
                        ▼                                  │
              vault/Pending_Approval/                      │
                 APPROVE_*.md                              │
                        │                                  │
                ┌───────┴───────┐                          │
                │               │                          │
                ▼               ▼                          │
          vault/Approved/  vault/Rejected/                 │
                │               │                          │
                │               │                          │
                ▼               ▼                          ▼
           [EXECUTE]      [LOG ONLY]              [AUTO-EXECUTE]
           action via      move to Done           action via
           MCP/Playwright                         MCP/Playwright
                │               │                          │
                └───────┬───────┘                          │
                        │                                  │
                        ▼                                  ▼
                              vault/Done/
                         (all completed items)
```

## Environment Variables

```env
# Safety
DRY_RUN=true

# Vault
VAULT_PATH=./vault

# Watcher intervals
CHECK_INTERVAL=10
GMAIL_POLL_INTERVAL=60
WHATSAPP_POLL_INTERVAL=30

# Gmail API
GOOGLE_CREDENTIALS_PATH=./credentials.json
GMAIL_TOKEN_PATH=./token.json
GMAIL_USER=me

# Email MCP (Node.js/TypeScript)
EMAIL_MCP_TOKEN_PATH=./token-mcp.json

# WhatsApp
WHATSAPP_USER_DATA_DIR=./playwright-data/whatsapp

# LinkedIn
LINKEDIN_USER_DATA_DIR=./playwright-data/linkedin

# Scheduling
LINKEDIN_POST_TIME=09:00
BRIEFING_DAY=MON
BRIEFING_TIME=08:00
```
