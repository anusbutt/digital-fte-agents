# Implementation Plan: Digital FTE Gold — Autonomous AI Employee

**Branch**: `001-digital-fte-gold` | **Date**: 2026-03-13
**Spec**: specs/001-digital-fte-gold/spec.md

## Summary

Build the Gold tier of the Digital FTE system — a fully autonomous AI employee
that extends Silver with: three new social media channels (Facebook, Instagram,
Twitter/X), an Odoo Community accounting MCP server, a Ralph Wiggum stop hook
for multi-step task persistence, an enhanced CEO briefing with live financial
data, comprehensive error recovery, and full JSON audit logging. Gold is
self-contained under `gold/` with no runtime dependencies on bronze or silver.

## Technical Context

**Language/Version**: Python 3.13 (watchers, scripts, stop hook),
TypeScript via tsx / Node.js 24 LTS (MCP servers)
**Primary Dependencies**:
- Python: watchdog, google-api-python-client, google-auth-oauthlib,
  google-auth-httplib2, playwright, python-dotenv
- Node.js: @modelcontextprotocol/sdk, tsx, zod
- Odoo: Docker image `odoo:17.0` + `postgres:15`
**Storage**: Markdown files in `vault/` (state machine), append-only JSON in
`vault/Logs/`, Odoo PostgreSQL for accounting records (Docker-managed)
**Testing**: Manual end-to-end with `DRY_RUN=true`; dry-run validation script;
PM2 health check
**Target Platform**: Windows 11 local machine with Docker Desktop installed
**Project Type**: Single project (self-contained under `gold/`)
**Performance Goals**: Watcher poll interval ≤ 60s; odoo-mcp response ≤ 5s;
CEO briefing generation ≤ 60s; PM2 process restart ≤ 10s
**Constraints**: `DRY_RUN=true` default enforced everywhere; Playwright-only
for social media (no paid APIs); local-first (all data on-machine); Gold
fully self-contained from bronze/silver
**Scale/Scope**: Single user, local machine, 8 PM2-managed processes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Gate Question | Status |
|-----------|--------------|--------|
| I. Local-First Privacy | All secrets in .env? No cloud sync of sessions? | ✅ PASS |
| II. Perception→Reasoning→Action | Watchers never act directly? MCP only after skill? | ✅ PASS |
| III. Skills-First | Zero business logic in Python/TypeScript? All decisions in .md skills? | ✅ PASS |
| IV. HITL | All social, financial, and unknown-contact actions in Pending_Approval/? | ✅ PASS |
| V. Vault-as-State-Machine | 8-stage pipeline enforced? No database substitutes? | ✅ PASS |
| VI. Resilience | Exponential backoff in all watchers? PM2 managing all processes? Ralph Wiggum stop hook present? | ✅ PASS |
| VII. Observability | Every action logged to Logs/ JSON? Dashboard updated after each state change? | ✅ PASS |
| VIII. SDD | Constitution → Spec → Plan → Tasks → Implement order followed? | ✅ PASS |

All gates pass. No violations. No complexity justifications required.

## Project Structure

### Documentation (this feature)

```text
specs/001-digital-fte-gold/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── odoo-mcp-tools.md
│   ├── skill-contracts.md
│   └── vault-schema.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (via /sp.tasks)
```

### Source Code (gold/ root)

```text
gold/
├── watchers/
│   ├── __init__.py
│   ├── base_watcher.py          # Abstract base (exponential backoff, polling loop)
│   ├── logger.py                # Shared JSON audit logger
│   ├── filesystem_watcher.py   # Monitors vault/Inbox/ (from Silver)
│   ├── gmail_watcher.py        # Polls Gmail API (from Silver)
│   ├── whatsapp_watcher.py     # Playwright WhatsApp Web (from Silver)
│   ├── facebook_watcher.py     # Playwright Facebook messages (NEW)
│   ├── instagram_watcher.py    # Playwright Instagram DMs (NEW)
│   ├── twitter_watcher.py      # Playwright Twitter/X mentions+DMs (NEW)
│   └── orchestrator.py         # Master controller — expanded for Gold (from Silver+)
│
├── skills/
│   ├── triage-inbox.md                 # Classify + plan all item types (expanded)
│   ├── compose-email-reply.md          # Draft/send email replies (from Silver)
│   ├── compose-whatsapp-reply.md       # Draft WhatsApp replies (from Silver)
│   ├── generate-linkedin-post.md       # LinkedIn post draft (from Silver)
│   ├── generate-social-post.md         # Facebook/Instagram/Twitter post draft (NEW)
│   ├── generate-accounting-briefing.md # CEO briefing with live Odoo data (NEW)
│   ├── process-approval.md             # HITL post-approval execution (expanded)
│   ├── process-odoo-action.md          # Odoo-specific HITL actions (NEW)
│   └── update-dashboard.md             # Regenerate Dashboard.md (expanded)
│
├── email-mcp/                   # Gmail send/draft MCP server (from Silver)
│   ├── index.ts
│   └── package.json
│
├── odoo-mcp/                    # Odoo JSON-RPC MCP server (NEW)
│   ├── index.ts                 # 7 tools: get_invoices, create_invoice, post_invoice,
│   │                            #   record_payment, get_partners, get_financial_summary,
│   │                            #   get_transactions
│   └── package.json
│
├── scripts/
│   ├── linkedin_post.py         # LinkedIn Playwright post (from Silver)
│   ├── facebook_post.py         # Facebook Playwright post (NEW)
│   ├── instagram_post.py        # Instagram Playwright post (NEW)
│   ├── twitter_post.py          # Twitter/X Playwright post (NEW)
│   ├── pm2_ecosystem.config.js  # 8 PM2 process definitions (expanded)
│   ├── pm2_healthcheck.py       # PM2 process monitor + restart (expanded)
│   ├── setup_scheduler.py       # Windows Task Scheduler setup (expanded)
│   └── validate_dry_run.py      # End-to-end DRY_RUN test (expanded)
│
├── vault/
│   ├── Inbox/                   # Drop zone for files
│   ├── Needs_Action/            # Watcher output
│   ├── Plans/                   # Claude plans
│   ├── Pending_Approval/        # HITL approval queue
│   ├── Approved/                # Human-approved actions
│   ├── Rejected/                # Human-rejected actions
│   ├── Done/                    # Completed items
│   ├── Logs/                    # Daily JSON audit logs (YYYY-MM-DD.json)
│   ├── Briefings/               # CEO briefings
│   ├── Accounting/              # Accounting summaries (Odoo mirror)
│   ├── Dashboard.md
│   ├── Company_Handbook.md
│   └── Business_Goals.md
│
├── .claude/
│   └── hooks/
│       └── stop.py              # Ralph Wiggum stop hook (NEW)
│
├── docker-compose.yml           # Odoo 17 CE + PostgreSQL 15 (NEW)
├── main.py                      # CLI entry point (expanded)
├── pyproject.toml
├── .env.example
├── .mcp.json                    # MCP server config (email-mcp + odoo-mcp)
└── README.md
```

**Structure Decision**: Single project under `gold/`. All watchers, skills,
MCP servers, and scripts co-located. Vault is a sibling directory (not nested
in src) because it is the state machine, not source code. No test directories —
validation is done via `DRY_RUN=true` end-to-end smoke test.

## Complexity Tracking

> No constitution violations requiring justification.

---

## Phase 0: Research

*See `specs/001-digital-fte-gold/research.md` for full findings.*

**Key decisions resolved:**
1. Odoo 17 CE via Docker (not 18 or manual install) — most stable CE image
2. Odoo auth via API key (not session) — stateless, safer for MCP
3. Facebook/Instagram/Twitter via Playwright (not paid APIs) — zero cost, same pattern as WhatsApp
4. Ralph Wiggum as `.claude/hooks/stop.py` — official Claude Code hook mechanism
5. odoo-mcp TypeScript (not Python) — consistency with email-mcp pattern

## Phase 1: Design

*See `data-model.md`, `contracts/`, and `quickstart.md` for full artifacts.*

**Key design outcomes:**
- VaultItem schema extended with 3 new types: facebook, instagram, twitter
- odoo-mcp exposes 7 tools via MCP SDK standard
- Ralph Wiggum stop hook reads `vault/Needs_Action/` file count to decide re-inject
- PM2 ecosystem expanded from 5 (Silver) to 8 processes
- `generate-accounting-briefing` skill replaces `generate-briefing` for Gold
