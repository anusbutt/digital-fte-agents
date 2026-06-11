# Research: Nestaro Pilot Nestaro Pilot — Autonomous AI employee

**Branch**: `001-nestaro-pilot` | **Date**: 2026-03-13
**Phase**: 0 — Resolving all unknowns before design

---

## 1. Odoo Version & Installation

**Decision**: Odoo 17 Community Edition via Docker Compose
**Rationale**:
- Odoo 17 CE is the latest stable community release (Oct 2024)
- Odoo 18 CE was just released; ecosystem/Docker images less mature
- Odoo 19 mentioned in product launch doc is not yet released as CE
- Docker avoids manual PostgreSQL setup, dependency conflicts on Windows
- Single `docker compose up -d` starts both Odoo + PostgreSQL
**Alternatives considered**:
- Manual install: rejected — complex on Windows, PostgreSQL config error-prone
- Odoo 18 CE: rejected — Docker image less tested, community modules fewer
- Odoo SaaS: rejected — violates Local-First Privacy principle
**Docker Compose config**:
```yaml
services:
  odoo:
    image: odoo:17.0
    ports: ["8069:8069"]
    depends_on: [db]
    environment:
      HOST: db
      USER: odoo
      PASSWORD: odoo
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: postgres
      POSTGRES_USER: odoo
      POSTGRES_PASSWORD: odoo
```

---

## 2. Odoo Authentication for MCP

**Decision**: Odoo API Key (Bearer token) via `/web/dataset/call_kw`
**Rationale**:
- API keys available since Odoo 14; work with Odoo 17 CE
- Stateless — no session cookie management needed
- odoo-mcp can store key in `.env` and use on every call
- More secure than username/password stored in memory
**Alternatives considered**:
- Session-based (uid + session): rejected — requires login call on every
  restart, session expires, stateful
- OAuth2: not available in Odoo CE (Enterprise only)
**API endpoint pattern**:
```
POST http://localhost:8069/web/dataset/call_kw
Headers: { "Content-Type": "application/json" }
Body: {
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "model": "account.move",
    "method": "search_read",
    "args": [[["state", "=", "posted"]]],
    "kwargs": { "fields": ["name", "partner_id", "amount_total"] }
  }
}
```
**Auth via API key** (Odoo 14+ CE):
```
POST /web/dataset/call_kw
Headers: { "Authorization": "Bearer <API_KEY>" }
```

---

## 3. Facebook Automation via Playwright

**Decision**: Playwright persistent browser context on `facebook.com/messages/`
**Rationale**:
- Same pattern as WhatsApp watcher (proven in earlier prototype)
- Facebook Graph API requires app review (weeks); Playwright is immediate
- Persistent context keeps login session across restarts
- DMs accessible at `/messages/t/<thread_id>`
**Alternatives considered**:
- Graph API: rejected — requires Meta app review, business verification
- Unofficial FB API libraries: rejected — unmaintained, high ban risk
**Selectors approach**:
- Unread DMs: `[aria-label*="unread"]` or badge counts on thread list
- Message text: `.x1ey2m1c` class or `[data-testid="message-text"]`
- Compose reply: `[aria-label="Message"]` textarea
**Keywords to monitor**: urgent, invoice, payment, pricing, project,
deadline, quote, help, collaboration

---

## 4. Instagram Automation via Playwright

**Decision**: Playwright persistent browser context on `instagram.com/direct/inbox/`
**Rationale**:
- Instagram Basic Display API deprecated; Graph API requires business account
- Playwright approach consistent with Facebook and WhatsApp patterns
- Login sessions persist with `userDataDir` option
**Alternatives considered**:
- Meta Graph API: rejected — requires business account, app review
- instagram-private-api (Node): rejected — unofficial, high ban risk
**Selectors approach**:
- Unread DMs: threads with unread indicator in inbox
- Navigate to: `https://www.instagram.com/direct/inbox/`
- Unread count badge: look for notification dots on thread items
**Keywords to monitor**: same as Facebook list above

---

## 5. Twitter/X Automation via Playwright

**Decision**: Playwright persistent browser context on `twitter.com`
**Rationale**:
- Twitter API v2 Free tier: 1 read, 1 write per month — too limited
- Twitter API v2 Basic: $100/month — violates local-first/cost principle
- Playwright approach: zero cost, immediate, consistent with other channels
**Alternatives considered**:
- Twitter API v2 Basic ($100/mo): rejected — cost violates principles
- Tweepy library: rejected — requires API access (paid)
**Selectors approach**:
- Notifications: navigate to `https://twitter.com/notifications`
- DMs: navigate to `https://twitter.com/messages`
- Unread indicator: `[data-testid="badge"]` or notification count
- Post compose: `[data-testid="tweetTextarea_0"]`
**Keywords to monitor**: mentions (@username), DMs with business keywords

---

## 6. Ralph Wiggum Stop Hook

**Decision**: `.claude/hooks/stop.py` — Python script invoked on Claude exit
**Rationale**:
- Claude Code supports hooks in `.claude/hooks/` triggered by lifecycle events
- `stop` event fires when Claude is about to exit
- Hook reads `vault/Needs_Action/` file count
- If items remain and iteration count < 10: exits with code 2 (re-inject)
- If no items remain or max iterations: exits with code 0 (allow exit)
**Hook mechanism**:
```python
# .claude/hooks/stop.py
import sys
import os
from pathlib import Path

vault = Path(os.getenv("VAULT_PATH", "./vault"))
needs_action = vault / "Needs_Action"
iteration = int(os.getenv("RALPH_ITERATION", "0"))
max_iter = int(os.getenv("RALPH_MAX_ITER", "10"))

items = [f for f in needs_action.glob("*.md") if not f.name.startswith("SYSTEM_")]
if items and iteration < max_iter:
    os.environ["RALPH_ITERATION"] = str(iteration + 1)
    sys.exit(2)  # re-inject prompt
sys.exit(0)  # allow exit
```
**Alternatives considered**:
- Orchestrator polling loop (no hook): rejected — Claude exits between items,
  loses context
- Cron-based re-invocation: rejected — latency, no context continuity

---

## 7. PM2 Process Count (Nestaro Pilot vs earlier prototype)

**earlier prototype**: 5 processes (filesystem-watcher, gmail-watcher, whatsapp-watcher,
orchestrator, email-mcp)

**Nestaro Pilot**: 8 processes
1. filesystem-watcher
2. gmail-watcher
3. whatsapp-watcher
4. facebook-watcher (NEW)
5. instagram-watcher (NEW)
6. twitter-watcher (NEW)
7. orchestrator
8. email-mcp
*(odoo-mcp runs on-demand via Claude Code, not as a persistent PM2 process)*

---

## 8. odoo-mcp Architecture

**Decision**: TypeScript MCP server using `@modelcontextprotocol/sdk`,
communicating with Odoo via JSON-RPC over HTTP. Runs as Claude Code MCP
server (invoked on-demand, not PM2).

**7 tools exposed**:
1. `get_invoices(status?, date_from?, date_to?, partner?)` — list invoices
2. `create_invoice(partner_name, amount, description, currency?)` — draft invoice
3. `post_invoice(invoice_id)` — confirm draft → posted
4. `record_payment(invoice_id, amount, payment_date?)` — mark paid
5. `get_partners(search?)` — list clients/vendors
6. `get_financial_summary(date_from?, date_to?)` — MTD revenue, outstanding, overdue
7. `get_transactions(date_from?, date_to?)` — bank/payment transactions

**Error handling**:
- Odoo unreachable: return `{ success: false, error: "ODOO_UNREACHABLE" }`
- Auth failure: return `{ success: false, error: "AUTH_FAILED" }`
- Not found: return `{ success: false, error: "NOT_FOUND", detail: "..." }`

---

## 9. Skill Count (Nestaro Pilot vs earlier prototype)

**earlier prototype**: 7 skills
**Nestaro Pilot**: 9 skills

| Skill | Status |
|-------|--------|
| triage-inbox.md | Expanded (adds facebook, instagram, twitter types) |
| compose-email-reply.md | Copied from earlier prototype |
| compose-whatsapp-reply.md | Copied from earlier prototype |
| generate-linkedin-post.md | Copied from earlier prototype |
| generate-social-post.md | NEW (Facebook, Instagram, Twitter) |
| generate-accounting-briefing.md | NEW (replaces generate-briefing, adds Odoo data) |
| process-approval.md | Expanded (adds odoo actions, social platform actions) |
| process-odoo-action.md | NEW (dedicated Odoo HITL execution) |
| update-dashboard.md | Expanded (adds Odoo summary section) |

---

## 10. .mcp.json (Nestaro Pilot)

Both MCP servers configured:
```json
{
  "mcpServers": {
    "email": {
      "command": "node",
      "args": ["./email-mcp/index.ts"],
      "env": { "EMAIL_MCP_TOKEN_PATH": "./token-mcp.json" }
    },
    "odoo": {
      "command": "node",
      "args": ["./odoo-mcp/index.ts"],
      "env": {
        "ODOO_URL": "http://localhost:8069",
        "ODOO_DB": "odoo_db",
        "ODOO_API_KEY": ""
      }
    }
  }
}
```
