# Quickstart: Digital FTE Silver

**Feature**: 001-digital-fte-silver
**Date**: 2026-02-18

## Prerequisites

- Windows 11
- Python 3.13+ (via `uv`)
- Node.js v24+ (via `npm`)
- PM2 installed globally: `npm install -g pm2`
- Playwright browsers: `playwright install chromium`
- Google Cloud Console project with Gmail API enabled
- OAuth2 credentials (`credentials.json`) downloaded
- WhatsApp Web logged in (first-time: scan QR code)
- LinkedIn logged in via browser (first-time: manual login)

## Setup Steps

### 1. Clone and Install Dependencies

```bash
cd silver/
uv sync                           # Python dependencies
cd email-mcp && npm install && cd ..  # Node.js/TypeScript MCP dependencies
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your paths:

```env
DRY_RUN=true                          # Start in safe mode
VAULT_PATH=./vault
GOOGLE_CREDENTIALS_PATH=./credentials.json
GMAIL_TOKEN_PATH=./token.json
EMAIL_MCP_TOKEN_PATH=./token-mcp.json
WHATSAPP_USER_DATA_DIR=./playwright-data/whatsapp
LINKEDIN_USER_DATA_DIR=./playwright-data/linkedin
```

### 3. Gmail OAuth2 Setup (first time)

```bash
uv run python -m watchers.gmail_watcher --auth
```

This opens a browser for Google OAuth2 consent. Authorize Gmail access. Token saved to `GMAIL_TOKEN_PATH`.

### 4. WhatsApp Session Setup (first time)

```bash
uv run python -m watchers.whatsapp_watcher --setup
```

Opens Chromium with WhatsApp Web. Scan QR code with your phone. Session persists in `WHATSAPP_USER_DATA_DIR`.

### 5. LinkedIn Session Setup (first time)

```bash
uv run python scripts/linkedin_post.py --setup
```

Opens Chromium with LinkedIn. Log in manually. Session persists in `LINKEDIN_USER_DATA_DIR`.

### 6. Register Email MCP Server

Add to Claude Code configuration:

Add to `.mcp.json` in project root:

```json
{
  "mcpServers": {
    "email-mcp": {
      "command": "npx",
      "args": ["tsx", "email-mcp/index.ts"],
      "env": {
        "GOOGLE_CREDENTIALS_PATH": "./credentials.json",
        "EMAIL_MCP_TOKEN_PATH": "./token-mcp.json"
      }
    }
  }
}
```

### 7. Start All Services (DRY_RUN)

```bash
pm2 start scripts/pm2_ecosystem.config.js
pm2 status     # Verify all processes running
pm2 logs       # Watch live logs
```

### 8. Test in DRY_RUN Mode

1. Drop a file in `vault/Inbox/` → filesystem watcher creates `FILE_*.md`
2. Send yourself a test email → gmail watcher creates `EMAIL_*.md`
3. Send a WhatsApp message with "invoice" → whatsapp watcher creates `WHATSAPP_*.md`
4. Check `vault/Needs_Action/` for triage items
5. Check `vault/Plans/` for action plans
6. Check `vault/Pending_Approval/` for approval requests

### 9. Set Up Scheduled Tasks

```bash
uv run python scripts/setup_scheduler.py
```

Creates Windows Task Scheduler entries for:
- LinkedIn post generation (daily 9:00 AM weekdays)
- CEO briefing (Monday 8:00 AM)
- PM2 health check (every 5 minutes)

### 10. Go Live

When ready to process real actions:

```bash
# Edit .env
DRY_RUN=false

# Restart all processes
pm2 restart all
```

## Verification Checklist

- [ ] `vault/` directory opens in Obsidian with only business folders
- [ ] PM2 shows all 5 processes as "online"
- [ ] Filesystem watcher detects files in `vault/Inbox/`
- [ ] Gmail watcher creates `EMAIL_*.md` for actionable emails
- [ ] WhatsApp watcher creates `WHATSAPP_*.md` for keyword messages
- [ ] Orchestrator invokes triage skill on new items
- [ ] Approval files appear in `vault/Pending_Approval/` for sensitive actions
- [ ] Moving file to `vault/Approved/` triggers action execution
- [ ] `vault/Logs/` contains audit entries for all actions
- [ ] `vault/Dashboard.md` updates after each state change

## Common Issues

| Problem | Solution |
|---------|----------|
| Gmail 401 error | Re-run `--auth` to refresh OAuth2 token |
| WhatsApp QR screen | Re-run `--setup` to scan new QR code |
| LinkedIn CAPTCHA | Wait 24h, then re-run `--setup` to login |
| PM2 process keeps restarting | Check `pm2 logs <name>` for error details |
| Email MCP not connecting | Verify path in `.mcp.json`, ensure `tsx` is installed (`npm ls tsx` in email-mcp/) |
