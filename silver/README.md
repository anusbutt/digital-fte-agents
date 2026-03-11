# Silver — Digital FTE (Autonomous AI Employee)

> **Hackathon 0 · Personal AI Employee · Silver Tier**

An autonomous AI employee that monitors your Gmail, WhatsApp, and filesystem — reasons about incoming work using Claude — and routes every action through a Human-in-the-Loop approval workflow before executing anything.

---

## What It Does

Silver runs 24/7 as a set of background watchers. When something arrives (an email, a WhatsApp message, a dropped file), it:

1. **Perceives** — Watcher detects the event and creates a structured Markdown item in `vault/Needs_Action/`
2. **Reasons** — Orchestrator invokes a Claude Code skill that reads context, consults the Company Handbook, and writes an ActionPlan to `vault/Plans/`
3. **Awaits approval** — Sensitive actions land in `vault/Pending_Approval/` for human review
4. **Acts** — Once you move the file to `vault/Approved/`, the action executes (send email, reply on WhatsApp, post to LinkedIn)
5. **Logs everything** — Every state change is recorded in `vault/Logs/` as structured JSON audit entries

```
Gmail / WhatsApp / Filesystem
         |
    [Watchers] ──> vault/Needs_Action/
                         |
                  [Orchestrator] ──> Claude Code Skill
                         |
                   vault/Plans/
                         |
              vault/Pending_Approval/  <── YOU REVIEW HERE
                    /         \
             Approved/       Rejected/
                |
           [Execute Action]
                |
            vault/Done/  +  vault/Logs/
```

---

## Architecture

### Core Principle: Perception → Reasoning → Action

Watchers **never act directly**. They only write to the vault. Claude Code skills handle all reasoning. MCP servers handle all execution. The vault is the single source of truth — file movement equals state transition.

### Components

| Component | Tech | Role |
|---|---|---|
| `watchers/filesystem_watcher.py` | Python + watchdog | Monitors `vault/Inbox/` for dropped files |
| `watchers/gmail_watcher.py` | Python + Gmail OAuth2 | Polls Gmail every ~60s, filters noise |
| `watchers/whatsapp_watcher.py` | Python + Playwright | Monitors WhatsApp Web for business keywords |
| `watchers/orchestrator.py` | Python + watchdog | Triggers Claude Code skills on vault events |
| `email-mcp/index.ts` | Node.js MCP server | Sends and drafts emails via Gmail API |
| `skills/*.md` | Agent skill files | All AI reasoning and action logic |
| `vault/` | Obsidian Markdown | State machine — the source of truth |
| PM2 | Process manager | Keeps all 5 processes alive with auto-restart |

### Agent Skills

| Skill | Trigger | Always Requires Approval? |
|---|---|---|
| `triage-inbox` | New item in Needs_Action/ | No (creates plan + approval request if needed) |
| `compose-email-reply` | After triage, email type | Sensitive emails: yes. Non-sensitive: auto-send |
| `compose-whatsapp-reply` | After triage, WhatsApp type | Yes — always |
| `generate-linkedin-post` | Daily scheduler (9 AM) | Yes — always |
| `generate-briefing` | Weekly scheduler (Mon 8 AM) | No — auto-written to vault |
| `process-approval` | File moved to Approved/ or Rejected/ | N/A — this executes the decision |
| `update-dashboard` | After every state change | No — auto-updates Dashboard.md |

---

## Project Structure

```
silver/
├── main.py                        # CLI entry point
├── pyproject.toml                 # Python dependencies (uv)
├── .env.example                   # Environment variable template
├── .mcp.json                      # MCP server config for Claude Code
│
├── watchers/
│   ├── base_watcher.py            # Abstract base (polling loop + exponential backoff)
│   ├── filesystem_watcher.py      # Watches vault/Inbox/
│   ├── gmail_watcher.py           # Polls Gmail API
│   ├── whatsapp_watcher.py        # Playwright-based WhatsApp monitor
│   ├── orchestrator.py            # Master controller, invokes Claude skills
│   └── logger.py                  # Structured JSON audit logging
│
├── skills/
│   ├── triage-inbox.md            # Classify + plan incoming items
│   ├── compose-email-reply.md     # Draft and send/draft email replies
│   ├── compose-whatsapp-reply.md  # Draft WhatsApp replies (approval required)
│   ├── generate-linkedin-post.md  # Generate LinkedIn posts (approval required)
│   ├── generate-briefing.md       # Weekly CEO briefing
│   ├── process-approval.md        # Execute approved actions
│   └── update-dashboard.md        # Regenerate vault/Dashboard.md
│
├── email-mcp/
│   └── index.ts                   # MCP server: send_email + draft_email tools
│
├── scripts/
│   ├── pm2_ecosystem.config.js    # PM2 process definitions (5 processes)
│   ├── linkedin_post.py           # LinkedIn Playwright poster
│   ├── pm2_healthcheck.py         # Restarts failed PM2 processes
│   └── setup_scheduler.py         # Creates Windows Task Scheduler entries
│
├── vault/
│   ├── Inbox/                     # Drop files here to trigger processing
│   ├── Needs_Action/              # Triaged items (FILE_*, EMAIL_*, WHATSAPP_*)
│   ├── Plans/                     # ActionPlans (PLAN_*)
│   ├── Pending_Approval/          # Awaiting human decision (APPROVE_*, LINKEDIN_*)
│   ├── Approved/                  # Move here to execute
│   ├── Rejected/                  # Move here to reject
│   ├── Done/                      # Completed and archived
│   ├── Briefings/                 # Weekly CEO briefings
│   ├── Logs/                      # Structured JSON audit logs (YYYY-MM-DD.md)
│   ├── Dashboard.md               # Live status dashboard
│   ├── Company_Handbook.md        # Business rules, approval thresholds, tone
│   └── Business_Goals.md          # Q1 targets and alert thresholds
│
└── specs/001-digital-fte-silver/
    ├── spec.md                    # Feature requirements
    ├── plan.md                    # Architecture decisions
    ├── tasks.md                   # 51 implementation tasks (all complete)
    └── data-model.md              # Vault entity schemas
```

---

## Setup

### Prerequisites

- Python 3.13+ (`uv` recommended)
- Node.js v24+
- PM2: `npm install -g pm2`
- Playwright browsers: `uv run playwright install chromium`
- Google Cloud project with Gmail API enabled + `credentials.json`

### 1. Install dependencies

```bash
uv sync
cd email-mcp && npm install && cd ..
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — set GOOGLE_CREDENTIALS_PATH at minimum
```

### 3. Authenticate Gmail (one-time)

```bash
uv run python main.py setup gmail
uv run python main.py setup email-mcp    # separate token for sending
```

### 4. Set up WhatsApp session (one-time)

```bash
uv run python main.py setup whatsapp     # scan QR code in browser
```

### 5. Set up LinkedIn session (one-time)

```bash
uv run python main.py setup linkedin     # log in manually in browser
```

### 6. Start all services (safe mode)

```bash
pm2 start scripts/pm2_ecosystem.config.js
pm2 status    # verify all 5 processes are online
pm2 logs      # watch live output
```

### 7. Test with a file drop

```bash
# Drop any file into vault/Inbox/ and watch the pipeline run
cp invoice.pdf vault/Inbox/
```

Check `vault/Needs_Action/`, `vault/Plans/`, and `vault/Pending_Approval/` for results.

### 8. Set up scheduled tasks (run as Admin)

```bash
uv run python scripts/setup_scheduler.py
# LinkedIn post: daily 9 AM weekdays
# CEO briefing: Monday 8 AM
# PM2 healthcheck: every 5 minutes
```

### 9. Go live

```bash
# Edit .env: DRY_RUN=false
pm2 restart all
```

---

## CLI Reference

```
python main.py filesystem       Start filesystem watcher
python main.py gmail            Start Gmail watcher
python main.py whatsapp         Start WhatsApp watcher
python main.py orchestrator     Start orchestrator
python main.py briefing         Generate CEO briefing (one-shot)
python main.py linkedin         Generate LinkedIn post draft (one-shot)
python main.py healthcheck      Run PM2 health check (one-shot)

python main.py setup gmail      OAuth2 setup for Gmail reading
python main.py setup email-mcp  OAuth2 setup for email sending
python main.py setup whatsapp   WhatsApp QR code session setup
python main.py setup linkedin   LinkedIn manual login session
python main.py setup scheduler  Create Windows Task Scheduler entries
python main.py setup pm2        Print PM2 startup instructions
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DRY_RUN` | `true` | Log intentions but never execute real actions |
| `VAULT_PATH` | `./vault` | Path to Obsidian vault |
| `GMAIL_POLL_INTERVAL` | `60` | Gmail polling interval (seconds) |
| `WHATSAPP_POLL_INTERVAL` | `30` | WhatsApp scan interval (seconds) |
| `GOOGLE_CREDENTIALS_PATH` | `./credentials.json` | Google OAuth2 credentials |
| `GMAIL_TOKEN_PATH` | `./token.json` | Gmail watcher OAuth2 token |
| `EMAIL_MCP_TOKEN_PATH` | `./token-mcp.json` | Email MCP OAuth2 token |
| `WHATSAPP_USER_DATA_DIR` | `./playwright-data/whatsapp` | WhatsApp browser session |
| `LINKEDIN_USER_DATA_DIR` | `./playwright-data/linkedin` | LinkedIn browser session |
| `LINKEDIN_POST_TIME` | `09:00` | Daily LinkedIn post time (weekdays) |
| `BRIEFING_DAY` | `MON` | CEO briefing day |
| `BRIEFING_TIME` | `08:00` | CEO briefing time |

---

## How Approval Works

Every sensitive action creates an `APPROVE_*.md` file in `vault/Pending_Approval/`.

**To approve:** move the file to `vault/Approved/`
**To reject:** move the file to `vault/Rejected/`

The orchestrator watches both folders and executes accordingly. No commands needed — just file moves in Obsidian (or File Explorer).

**What always requires approval:**
- Any WhatsApp reply
- Any LinkedIn post
- Emails to new/unknown contacts
- Emails with financial content
- Invoices over $500

**What can auto-execute:**
- Email replies to known contacts with non-sensitive, non-financial content

---

## Vault as a State Machine

```
Inbox/  ──>  Needs_Action/  ──>  Plans/  ──>  Pending_Approval/
                                                  |           |
                                              Approved/   Rejected/
                                                  |           |
                                              Done/  <────────
```

Each folder represents a processing stage. YAML frontmatter in every file carries structured metadata. The Markdown body is human-readable. Logs are structured JSON embedded in Markdown tables.

---

## Tech Stack

- **Python 3.13+** — watchers, orchestrator, CLI
- **Claude Code CLI** — AI reasoning engine (invoked by orchestrator)
- **Node.js + TypeScript** — Email MCP server
- **Gmail API (OAuth2)** — Email reading and sending
- **Playwright** — WhatsApp Web and LinkedIn automation
- **watchdog** — Filesystem event detection
- **PM2** — Process management and auto-restart
- **Windows Task Scheduler** — Cron-style scheduling
- **Obsidian** — Vault viewer (optional but recommended)

---

## Constitution Principles

This project is governed by 8 core principles defined in `.specify/memory/constitution.md`:

1. **Local-First Privacy** — vault is source of truth, secrets stay in `.env`
2. **Perception-Reasoning-Action** — watchers never act, Claude reasons, MCP executes
3. **Human-in-the-Loop** — sensitive actions require explicit approval
4. **Agent Skills First** — all AI logic lives in `.md` skill files
5. **Watcher Resilience** — PM2 auto-restart, exponential backoff
6. **Vault-as-Protocol** — file movement equals state transition
7. **Observability** — structured JSON audit logs for everything
8. **Spec-Driven Development** — constitution → spec → plan → tasks → code

---

## Status

- All 51 implementation tasks complete
- `DRY_RUN=true` by default — safe to run immediately
- Tested: filesystem watcher end-to-end pipeline
- PM2 + Windows Task Scheduler configured for production
