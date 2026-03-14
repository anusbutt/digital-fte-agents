# Quickstart: Digital FTE Gold — Autonomous AI Employee

**Prerequisites**: Docker Desktop installed, Claude Code CLI installed,
Node.js 24+ LTS, Python 3.13+, uv package manager

---

## Step 1: Clone & Navigate

```bash
cd digital-fte-agents/gold
```

## Step 2: Install Python Dependencies

```bash
uv sync
```

## Step 3: Install Node.js Dependencies (MCP servers)

```bash
cd email-mcp && npm install && cd ..
cd odoo-mcp && npm install && cd ..
```

## Step 4: Configure Environment

```bash
cp .env.example .env
# Edit .env — at minimum set:
#   DRY_RUN=true          (keep true until fully tested)
#   VAULT_PATH=./vault
#   GOOGLE_CREDENTIALS_PATH=./credentials.json
```

## Step 5: Start Odoo via Docker

```bash
docker compose up -d
# Wait ~60 seconds for Odoo to initialize
# Open http://localhost:8069 in browser
# Create database: name=odoo_db, language=English, demo data=no
# Go to Settings → Technical → API Keys → Create API Key
# Copy the API key to .env: ODOO_API_KEY=<your-key>
# Also set: ODOO_DB=odoo_db
```

## Step 6: Authenticate Gmail (Read)

```bash
python main.py setup gmail
# Follow OAuth2 browser prompt
# Token saved to token.json
```

## Step 7: Authenticate Gmail (Send/Draft MCP)

```bash
python main.py setup email-mcp
# Follow OAuth2 browser prompt
# Token saved to token-mcp.json
```

## Step 8: Authenticate Social Media (Playwright)

```bash
# WhatsApp
python main.py setup whatsapp
# Scan QR code in opened browser window

# LinkedIn
python main.py setup linkedin
# Log in manually in opened browser window

# Facebook
python main.py setup facebook
# Log in manually in opened browser window

# Instagram
python main.py setup instagram
# Log in manually in opened browser window

# Twitter/X
python main.py setup twitter
# Log in manually in opened browser window
```

## Step 9: Configure .mcp.json

```bash
# Update odoo-mcp env in .mcp.json with your ODOO_API_KEY
# Verify email-mcp path is correct
```

## Step 10: Start All Watchers via PM2

```bash
npm install -g pm2
pm2 start scripts/pm2_ecosystem.config.js
pm2 save
pm2 startup   # follow the printed instructions for Windows
```

## Step 11: Verify Everything is Running

```bash
pm2 status
python main.py healthcheck
```

## Step 12: Test with DRY_RUN=true

```bash
# Drop a test file into vault/Inbox/
cp test_data/sample_invoice.txt vault/Inbox/

# Watch the orchestrator logs
pm2 logs orchestrator

# Verify vault/Needs_Action/ gets a FILE_ item
# Verify vault/Plans/ gets a PLAN_ item
# Verify vault/Logs/ gets a JSON entry with "result": "dry_run"
```

## Step 13: Test CEO Briefing

```bash
python main.py briefing
# Check vault/Briefings/ for new briefing file
# Verify Odoo financial data appears (requires Odoo running)
```

## Step 14: Go Live

```bash
# When satisfied with DRY_RUN testing:
# Edit .env: DRY_RUN=false
pm2 restart all
```

---

## Troubleshooting

| Problem | Solution |
|---------|---------|
| Odoo unreachable | Run `docker compose ps` — ensure odoo and db containers are running |
| OAuth token expired | Run `python main.py setup gmail` again |
| Social session expired | Run `python main.py setup {platform}` again |
| PM2 process stopped | Run `pm2 restart {process-name}` |
| Ralph Wiggum loop stuck | Check `vault/Needs_Action/` for SYSTEM_ files; max iterations exceeded |
| Odoo API key invalid | Go to Odoo → Settings → API Keys → regenerate |
