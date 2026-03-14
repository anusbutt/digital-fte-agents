# Digital FTE Agent — Gold Tier

An autonomous AI employee that monitors multiple communication channels, drafts
responses for human approval, and executes approved actions — all without
unattended external calls.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        PERCEPTION LAYER                         │
│                                                                 │
│  Gmail Watcher   WhatsApp Watcher   Filesystem Watcher          │
│  Facebook DM     Instagram DM       Twitter Mention/DM          │
│        │               │                   │                    │
│        └───────────────┴───────────────────┘                    │
│                         │ VaultItems                            │
│                    vault/Needs_Action/                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                       REASONING LAYER                           │
│                                                                 │
│              Orchestrator + Claude Code Skills                  │
│                                                                 │
│  triage-inbox → compose-*-reply → generate-*-post              │
│  generate-accounting-briefing → update-dashboard               │
│  process-approval → process-odoo-action                        │
│                         │                                       │
│                    vault/Plans/                                 │
│                    vault/Pending_Approval/                      │
└───────────────────────────┬─────────────────────────────────────┘
                            │  Human reviews & moves files
                            │  Approved/ or Rejected/
┌───────────────────────────▼─────────────────────────────────────┐
│                        ACTION LAYER                             │
│                                                                 │
│  email-mcp (Gmail send/draft)    odoo-mcp (7 accounting tools)  │
│  scripts/facebook_post.py        scripts/instagram_post.py      │
│  scripts/twitter_post.py         scripts/linkedin_post.py       │
│                         │                                       │
│                    vault/Done/ + AuditLog                       │
└─────────────────────────────────────────────────────────────────┘
```

**HITL contract**: every external action (email send, social post, Odoo invoice)
requires a human to physically move a file from `Pending_Approval/` to
`Approved/` before execution.

---

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| AI runtime | Claude Code CLI (`claude`) | Skill invocation, HITL loop |
| Process manager | PM2 | 8 long-running processes |
| Email monitoring | Google Gmail API (Python) | Read business emails |
| Email sending | email-mcp (Node.js MCP) | Send/draft via MCP tool |
| Social DMs | Playwright (Chromium) | Facebook, Instagram, Twitter |
| WhatsApp | Playwright (Web) | WhatsApp Web automation |
| Accounting | odoo-mcp (Node.js MCP) | 7 Odoo JSON-RPC tools |
| Odoo backend | Docker (odoo:17.0 + postgres:15) | Local Odoo instance |
| Scheduler | Windows Task Scheduler | 6 scheduled tasks |
| State machine | Markdown files + folder movement | Vault pipeline |
| Logging | NDJSON (one file per UTC day) | AuditLogEntry trail |

---

## Vault State Machine

```
Inbox/
  └─► Needs_Action/       ← watchers write VaultItems here
        └─► Plans/         ← orchestrator writes ActionPlans
              └─► Pending_Approval/  ← Claude writes approval requests
                    ├─► Approved/    ← human moves here to approve
                    │     └─► Done/  ← orchestrator moves after executing
                    └─► Rejected/    ← human moves here to reject
                          └─► Done/  ← orchestrator moves + logs rejection
```

**Files never deleted** — every item ends in `Done/` with full audit trail.
Expired approvals (>24h) are automatically moved to `Done/` with
`status: expired` by the orchestrator.

---

## Quickstart

See [`specs/001-digital-fte-gold/quickstart.md`](specs/001-digital-fte-gold/quickstart.md)
for the full step-by-step setup guide.

**5-minute summary**:

```bash
# 1. Install dependencies
uv sync
cd email-mcp && npm install && cd ..
cd odoo-mcp && npm install && cd ..

# 2. Configure environment
cp .env.example .env
# Edit .env: set DRY_RUN=true, add API keys

# 3. Start Odoo
docker compose up -d

# 4. Authenticate all channels
python main.py setup gmail
python main.py setup facebook
python main.py setup instagram
python main.py setup twitter
python main.py setup linkedin
python main.py setup whatsapp
python main.py setup odoo

# 5. Start all 8 processes via PM2
python main.py setup pm2

# 6. Register Windows Task Scheduler (run as Admin)
python main.py setup scheduler

# 7. Smoke test (keep DRY_RUN=true)
python scripts/validate_dry_run.py --verbose
```

---

## CLI Reference

### Setup Commands

```
python main.py setup gmail          Gmail OAuth flow (token.json + token-mcp.json)
python main.py setup facebook       Facebook Playwright login (saves browser session)
python main.py setup instagram      Instagram Playwright login
python main.py setup twitter        Twitter/X Playwright login
python main.py setup linkedin       LinkedIn Playwright login
python main.py setup whatsapp       WhatsApp Web QR scan
python main.py setup odoo           Docker instructions + ODOO_API_KEY to .env
python main.py setup email-mcp      email-mcp Node.js setup instructions
python main.py setup pm2            PM2 setup instructions + optional start
python main.py setup scheduler      Register 6 Windows Task Scheduler tasks (Admin)
```

### Watcher Commands (run via PM2 normally)

```
python main.py facebook             Facebook DM watcher (Playwright, poll 60s)
python main.py instagram            Instagram DM watcher (Playwright, poll 60s)
python main.py twitter              Twitter mention+DM watcher (Playwright, poll 60s)
python main.py whatsapp             WhatsApp watcher (Playwright, poll 30s)
python main.py email                Gmail watcher (Gmail API, poll 60s)
python main.py files                Filesystem inbox watcher (poll 10s)
python main.py orchestrator         Master orchestrator (poll 10s)
```

### Content Generation (one-shot)

```
python main.py social-post          Facebook + Instagram + Twitter drafts → Pending_Approval/
python main.py linkedin             LinkedIn post draft → Pending_Approval/
python main.py briefing             CEO accounting briefing → vault/Briefings/
```

### Diagnostics

```
python main.py healthcheck          PM2 health check: inspect 8 processes, restart stopped
python main.py odoo-status          Odoo connection + live financial summary
python scripts/validate_dry_run.py  End-to-end smoke test (9 checks, DRY_RUN=true)
```

---

## PM2 Process Map

| # | PM2 Name | Start Command | Log Files |
|---|----------|---------------|-----------|
| 1 | `filesystem-watcher` | `python main.py files` | `vault/Logs/pm2-filesystem-watcher-*.log` |
| 2 | `gmail-watcher` | `python main.py email` | `vault/Logs/pm2-gmail-watcher-*.log` |
| 3 | `whatsapp-watcher` | `python main.py whatsapp` | `vault/Logs/pm2-whatsapp-watcher-*.log` |
| 4 | `facebook-watcher` | `python main.py facebook` | `vault/Logs/pm2-facebook-watcher-*.log` |
| 5 | `instagram-watcher` | `python main.py instagram` | `vault/Logs/pm2-instagram-watcher-*.log` |
| 6 | `twitter-watcher` | `python main.py twitter` | `vault/Logs/pm2-twitter-watcher-*.log` |
| 7 | `orchestrator` | `python main.py orchestrator` | `vault/Logs/pm2-orchestrator-*.log` |
| 8 | `email-mcp` | `npx tsx email-mcp/index.ts` | `vault/Logs/pm2-email-mcp-*.log` |

> **Note**: `odoo-mcp` is NOT a PM2 process — it runs on-demand as a Claude
> MCP subprocess (stdio transport).

---

## Windows Task Scheduler (6 tasks)

| Task Name | Schedule | Command |
|-----------|----------|---------|
| `DigitalFTE-PM2Startup` | On login | `pm2 start scripts/pm2_ecosystem.config.js` |
| `DigitalFTE-Briefing` | Mon 08:00 | `python main.py briefing` |
| `DigitalFTE-SocialPost` | Weekdays 10:00 | `python main.py social-post` |
| `DigitalFTE-LinkedIn` | Weekdays 09:00 | `python main.py linkedin` |
| `DigitalFTE-PM2Health` | Every 5 min | `python main.py healthcheck` |
| `DigitalFTE-WeeklyHealth` | Sun 07:00 | `python main.py healthcheck` |

Register all: `python main.py setup scheduler` (run as Administrator).

---

## Tier Comparison

| Feature | Bronze | Silver | Gold |
|---------|--------|--------|------|
| Gmail monitoring | ✓ | ✓ | ✓ |
| WhatsApp monitoring | — | ✓ | ✓ |
| LinkedIn post drafts | — | ✓ | ✓ |
| Facebook DM monitoring | — | — | ✓ |
| Instagram DM monitoring | — | — | ✓ |
| Twitter mention/DM | — | — | ✓ |
| Social post dispatch (FB/IG/TW) | — | — | ✓ |
| Odoo accounting MCP | — | — | ✓ |
| CEO accounting briefing | — | — | ✓ |
| Ralph Wiggum loop (auto-process) | — | — | ✓ |
| PM2 processes | 3 | 5 | 8 |
| Windows Task Scheduler tasks | — | 3 | 6 |
| Approval expiry enforcement | — | ✓ | ✓ |
| Auth failure alerting | — | ✓ | ✓ |

---

## Gold-Specific Features

### Ralph Wiggum Stop Hook

Claude Code's Stop hook (``.claude/hooks/stop.py``) intercepts every session
exit. If `vault/Needs_Action/` still has non-SYSTEM_ items, it:

1. Increments an iteration counter (`vault/.ralph_state`)
2. Re-injects a prompt listing remaining items
3. Returns exit code 2 (Claude Code: block exit + re-inject)

Claude loops until all items are processed or `RALPH_MAX_ITER` (default: 10)
is reached. At cap, it writes `SYSTEM_MAX_ITERATIONS_*.md` for operator review.

### Odoo MCP Integration

Seven accounting tools exposed via `odoo-mcp`:

- `get_invoices` — list invoices with filters
- `create_invoice` — draft a new customer invoice
- `post_invoice` — confirm (post) a draft invoice
- `record_payment` — register payment on a posted invoice
- `get_partners` — search Odoo partners/clients
- `get_financial_summary` — MTD revenue, outstanding, overdue invoices
- `get_transactions` — bank/journal transactions

All financial actions require human approval before execution (HITL gate in
`process-odoo-action.md` skill).

### Comprehensive Error Recovery

- **Gmail**: `HttpError` 401/403 → pauses polling, writes `SYSTEM_AUTH_FAILURE_GMAIL_*.md`
- **Facebook/Instagram/Twitter**: login redirect detection → pauses polling, writes `SYSTEM_AUTH_FAILURE_{PLATFORM}_*.md`
- **Odoo offline**: orchestrator detects `ODOO_UNREACHABLE` in skill output → writes `SYSTEM_ODOO_UNREACHABLE.md`
- **Approval expiry**: orchestrator moves items with `expires_at < now` to `Done/` with `status: expired`
- **PM2 restarts**: healthcheck writes `SYSTEM_PM2_RESTART_{process}_*.md` when a process is restarted

All SYSTEM_ files are idempotent (one per outage) and visible on the Dashboard.

---

## Security

- **No secrets in code** — all credentials via `.env` (gitignored)
- **DRY_RUN=true** — set for all testing; prevents all external API calls
- **HITL gate** — zero external actions without human file movement
- **Playwright sessions** — stored in `playwright-data/` (gitignored)
- **Token files** (`token.json`, `token-mcp.json`) — gitignored
- **AuditLog** — every action logged to `vault/Logs/YYYY-MM-DD.json` (NDJSON)

Report security issues: open a GitHub issue with the `security` label.
