# Contract: Agent Skill Definitions

All skills live in `./skills/`. Each skill is a Markdown file invoked by
the orchestrator via `claude --skill <skill-file>` or via Claude Code
slash commands. Skills are stateless — they read from vault, write to vault,
call MCP tools, and return. No skill stores state between invocations.

---

## Skill 1: triage-inbox.md

**Trigger**: New `.md` file appears in `vault/Needs_Action/`
**Invoked by**: `orchestrator.py` on file creation event

**Inputs** (reads from vault):
- `vault/Needs_Action/{item}.md` — the VaultItem to classify
- `vault/Company_Handbook.md` — classification rules and approval thresholds
- `vault/Business_Goals.md` — context for prioritization

**Outputs** (writes to vault):
- `vault/Plans/PLAN_{item}.md` — ActionPlan with `approval_required` flag
- `vault/Pending_Approval/APPROVAL_{...}.md` — if `approval_required=true`

**Decision matrix**:
| Item type | Sender known | Content | approval_required |
|---|---|---|---|
| email | yes | non-financial, no attachment | false (auto-send) |
| email | no | any | true |
| email | any | financial content | true |
| whatsapp | any | any | true |
| facebook | any | any | true |
| instagram | any | any | true |
| twitter | any | any | true |
| linkedin | any | any | true |
| file | any | invoice > $500 | true |
| file | any | other | false |
| system | any | any | false (auto-alert dashboard) |

---

## Skill 2: generate-social-post.md

**Trigger**: Scheduled daily post time OR manual `python main.py social`
**Invoked by**: `orchestrator.py` on schedule

**Inputs** (reads from vault):
- `vault/Business_Goals.md` — current objectives, revenue targets
- `vault/Company_Handbook.md` — tone, brand voice, content rules
- `vault/Done/` (last 7 days) — recent accomplishments for content ideas

**Outputs** (writes to vault):
- `vault/Pending_Approval/SOCIAL_POST_{platform}_{timestamp}.md` for each
  platform: FACEBOOK, INSTAGRAM, TWITTER
  - Each approval file contains: platform, draft post text (≤ 280 chars for
    Twitter, ≤ 2200 for FB/IG), hashtags, best time to post

**Rules**:
- All social posts MUST route to Pending_Approval (never auto-post)
- Twitter posts MUST be ≤ 280 characters
- Instagram posts MUST include 3–5 hashtags
- Facebook posts MUST include a call-to-action

---

## Skill 3: generate-accounting-briefing.md

**Trigger**: Scheduled weekly briefing day/time OR manual `python main.py briefing`
**Invoked by**: `orchestrator.py` on schedule

**Inputs** (reads from vault + MCP):
- `vault/Business_Goals.md` — revenue targets, KPIs
- `vault/Done/` (last 7 days) — completed work items count + summary
- `vault/Logs/` (last 7 days) — action counts by type
- odoo-mcp `get_financial_summary()` — live revenue and invoice data
- odoo-mcp `get_invoices(payment_state="not_paid")` — unpaid invoice list

**Outputs** (writes to vault):
- `vault/Briefings/YYYY-MM-DD_Briefing.md` — full CEO briefing
- Updates `vault/Dashboard.md` — adds link to latest briefing, updates KPIs

**Required briefing sections**: Executive Summary, Revenue (from Odoo),
Unpaid Invoices (from Odoo), Communications Activity (from Logs/),
Completed Tasks (from Done/), Proactive Suggestions, footer timestamp

**Proactive suggestion triggers**:
- Invoice overdue > 30 days → suggest sending reminder (routes to
  Pending_Approval)
- MTD revenue < 80% of target on day 20+ → flag in briefing
- No social post in 5+ days → suggest content creation

---

## Skill 4: process-approval.md

**Trigger**: File appears in `vault/Approved/` or `vault/Rejected/`
**Invoked by**: `orchestrator.py` on file creation event

**Inputs** (reads from vault):
- `vault/Approved/{file}.md` or `vault/Rejected/{file}.md`
- Referenced `vault/Plans/PLAN_{...}.md`

**Outputs / Actions**:
- For `whatsapp_reply`: calls WhatsApp send directly via orchestrator
- For `linkedin_post`: calls `scripts/linkedin_post.py`
- For `facebook_post`/`facebook_reply`: calls `scripts/facebook_post.py`
- For `instagram_post`/`instagram_reply`: calls `scripts/instagram_post.py`
- For `twitter_post`/`twitter_reply`: calls `scripts/twitter_post.py`
- For `email_send`/`email_draft`: calls email-mcp tool
- For `odoo_*` actions: delegates to `process-odoo-action.md` skill
- Moves processed file to `vault/Done/`
- Appends AuditLogEntry to `vault/Logs/YYYY-MM-DD.json`
- Calls `update-dashboard.md`

---

## Skill 5: process-odoo-action.md

**Trigger**: Called by `process-approval.md` when action_type is `odoo_*`
**Invoked by**: `process-approval.md` (delegation)

**Supported action types**:
- `odoo_create_invoice` → calls odoo-mcp `create_invoice` tool
- `odoo_post_invoice` → calls odoo-mcp `post_invoice` tool
- `odoo_record_payment` → calls odoo-mcp `record_payment` tool

**Safety rules enforced in skill**:
1. Verify `DRY_RUN` flag — if true, log as `dry_run` and stop
2. Verify approval file `approved_by: human` — never auto-approve Odoo actions
3. Verify approval file not expired (`expires_at` check)
4. Call odoo-mcp tool
5. On success: move to Done/, log to Logs/
6. On failure: write `SYSTEM_ODOO_FAILURE_{timestamp}.md` to Needs_Action/,
   log failure to Logs/, do NOT retry

---

## Skill 6: update-dashboard.md

**Trigger**: After any significant vault state change
**Invoked by**: `orchestrator.py` after every orchestration cycle

**Inputs** (reads from vault):
- All vault folder counts (glob each folder)
- `vault/Briefings/` (latest file)
- `vault/Logs/` (today's file for action counts)

**Outputs**:
- Rewrites `vault/Dashboard.md` with:
  - Status table (counts per folder)
  - Latest briefing link
  - Today's action summary (from Logs/)
  - Odoo quick stats (calls odoo-mcp `get_financial_summary` if Odoo available,
    or shows "Odoo: offline" gracefully)
  - Recent activity (last 5 AuditLogEntries)
  - System health (PM2 process status)

---

## Skill 7: compose-email-reply.md (from earlier prototype)

**Trigger**: Auto-execute (approval_required=false) or post-approval email action
**Invoked by**: `orchestrator.py`

**Inputs**: Email VaultItem, ActionPlan
**Outputs**: Calls email-mcp `send_email` or `draft_email` tool
*(Unchanged from earlier prototype)*

---

## Skill 8: compose-whatsapp-reply.md (from earlier prototype)

**Trigger**: Post-approval WhatsApp action
**Invoked by**: `orchestrator.py` after Approved/ detection

**Inputs**: WhatsApp VaultItem, ApprovalRequest
**Outputs**: Sends reply via WhatsApp Playwright automation
*(Unchanged from earlier prototype)*

---

## Skill 9: generate-linkedin-post.md (from earlier prototype)

**Trigger**: Scheduled daily post OR manual invocation
**Invoked by**: `orchestrator.py`

**Inputs**: Business_Goals.md, Done/ (last 7 days)
**Outputs**: Approval file in Pending_Approval/, dispatched via linkedin_post.py
*(Unchanged from earlier prototype)*
