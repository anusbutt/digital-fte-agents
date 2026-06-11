"""main.py — Nestaro Pilot tier AI employee entry point.

Unified CLI for the Nestaro Pilot (Nestaro Pilot tier). All social platform setup,
watcher startup, orchestration, and content generation commands live here.

Usage:
    # First-time browser login (saves Playwright session):
    python main.py setup facebook
    python main.py setup instagram
    python main.py setup twitter
    python main.py setup linkedin
    python main.py setup whatsapp

    # Start individual watchers (usually via PM2):
    python main.py facebook            # Start Facebook DM watcher
    python main.py instagram           # Start Instagram DM watcher
    python main.py twitter             # Start Twitter mention+DM watcher
    python main.py whatsapp            # Start WhatsApp watcher
    python main.py email               # Start Gmail watcher
    python main.py files               # Start filesystem watcher

    # Orchestrator (watches vault/Needs_Action + Approved + Rejected):
    python main.py orchestrator

    # One-shot content generation (writes to Pending_Approval/ for HITL):
    python main.py social-post         # Generate Facebook/Instagram/Twitter drafts
    python main.py linkedin            # Generate LinkedIn post draft
    python main.py briefing            # Generate CEO accounting briefing
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# ── Logging setup ──────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Repo/vault resolution ──────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent
load_dotenv(REPO_ROOT / ".env")

VAULT_PATH = Path(os.getenv("VAULT_PATH", REPO_ROOT / "vault"))
if not VAULT_PATH.is_absolute():
    VAULT_PATH = REPO_ROOT / VAULT_PATH

# ── Per-platform user data directories (Playwright session storage) ──────────

PLAYWRIGHT_BASE = REPO_ROOT / "playwright-data"

PLATFORM_DATA_DIRS: dict[str, Path] = {
    "facebook": Path(os.getenv("FACEBOOK_USER_DATA_DIR", str(PLAYWRIGHT_BASE / "facebook"))),
    "instagram": Path(os.getenv("INSTAGRAM_USER_DATA_DIR", str(PLAYWRIGHT_BASE / "instagram"))),
    "twitter": Path(os.getenv("TWITTER_USER_DATA_DIR", str(PLAYWRIGHT_BASE / "twitter"))),
    "linkedin": Path(os.getenv("LINKEDIN_USER_DATA_DIR", str(PLAYWRIGHT_BASE / "linkedin"))),
    "whatsapp": Path(os.getenv("WHATSAPP_USER_DATA_DIR", str(PLAYWRIGHT_BASE / "whatsapp"))),
}


# ── Setup helpers (first-time login) ──────────────────────────────────────────

async def _setup_facebook(user_data_dir: str) -> None:
    """Open Facebook in Playwright for manual login. Saves session cookie."""
    from playwright.async_api import async_playwright  # noqa: PLC0415

    logger.info("Opening Facebook for login setup...")
    logger.info("Log in manually in the browser window, then press Ctrl+C.")

    pw = await async_playwright().start()
    context = await pw.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
    )
    page = context.pages[0] if context.pages else await context.new_page()
    await page.goto("https://www.facebook.com/")

    try:
        await page.wait_for_selector(
            'div[aria-label="Create post"], div[data-pagelet="FeedUnit_0"]',
            timeout=120000,
        )
        logger.info("Facebook login successful! Session saved to %s", user_data_dir)
    except Exception:
        logger.warning("Timeout waiting for Facebook login. Run setup again.")
    finally:
        await context.close()
        await pw.stop()


async def _setup_instagram(user_data_dir: str) -> None:
    """Open Instagram in Playwright for manual login."""
    from playwright.async_api import async_playwright  # noqa: PLC0415

    logger.info("Opening Instagram for login setup...")
    logger.info("Log in manually in the browser window, then press Ctrl+C.")

    pw = await async_playwright().start()
    context = await pw.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
    )
    page = context.pages[0] if context.pages else await context.new_page()
    await page.goto("https://www.instagram.com/")

    try:
        await page.wait_for_selector(
            'svg[aria-label="Home"], nav[aria-label="Primary"]',
            timeout=120000,
        )
        logger.info("Instagram login successful! Session saved to %s", user_data_dir)
    except Exception:
        logger.warning("Timeout waiting for Instagram login. Run setup again.")
    finally:
        await context.close()
        await pw.stop()


async def _setup_twitter(user_data_dir: str) -> None:
    """Open Twitter/X in Playwright for manual login."""
    from playwright.async_api import async_playwright  # noqa: PLC0415

    logger.info("Opening Twitter/X for login setup...")
    logger.info("Log in manually in the browser window, then press Ctrl+C.")

    pw = await async_playwright().start()
    context = await pw.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
    )
    page = context.pages[0] if context.pages else await context.new_page()
    await page.goto("https://twitter.com/home")

    try:
        await page.wait_for_selector(
            'div[data-testid="primaryColumn"]',
            timeout=120000,
        )
        logger.info("Twitter/X login successful! Session saved to %s", user_data_dir)
    except Exception:
        logger.warning("Timeout waiting for Twitter/X login. Run setup again.")
    finally:
        await context.close()
        await pw.stop()


async def _setup_linkedin(user_data_dir: str) -> None:
    """Open LinkedIn in Playwright for manual login."""
    from playwright.async_api import async_playwright  # noqa: PLC0415

    logger.info("Opening LinkedIn for login setup...")
    logger.info("Log in manually in the browser window, then press Ctrl+C.")

    pw = await async_playwright().start()
    context = await pw.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
    )
    page = context.pages[0] if context.pages else await context.new_page()
    await page.goto("https://www.linkedin.com/feed/")

    try:
        await page.wait_for_selector(
            'div[data-test-id="share-box-feed-entry__trigger"], nav[aria-label="Primary"]',
            timeout=120000,
        )
        logger.info("LinkedIn login successful! Session saved to %s", user_data_dir)
    except Exception:
        logger.warning("Timeout waiting for LinkedIn login. Run setup again.")
    finally:
        await context.close()
        await pw.stop()


async def _setup_whatsapp(user_data_dir: str) -> None:
    """Open WhatsApp Web in Playwright for QR code scan."""
    from playwright.async_api import async_playwright  # noqa: PLC0415

    logger.info("Opening WhatsApp Web for QR code scan...")
    logger.info("Scan the QR code with your phone, then press Ctrl+C after login.")

    pw = await async_playwright().start()
    context = await pw.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
    )
    page = context.pages[0] if context.pages else await context.new_page()
    await page.goto("https://web.whatsapp.com/")

    try:
        await page.wait_for_selector(
            'div[data-testid="chat-list"], div[id="side"]',
            timeout=120000,
        )
        logger.info("WhatsApp login successful! Session saved to %s", user_data_dir)
    except Exception:
        logger.warning("Timeout waiting for WhatsApp login. Run setup again.")
    finally:
        await context.close()
        await pw.stop()


SETUP_HANDLERS: dict[str, any] = {
    "facebook": _setup_facebook,
    "instagram": _setup_instagram,
    "twitter": _setup_twitter,
    "linkedin": _setup_linkedin,
    "whatsapp": _setup_whatsapp,
    "odoo": None,       # handled by cmd_setup_odoo (env setup, no browser)
    "gmail": None,      # handled by cmd_setup_gmail (OAuth flow)
    "email-mcp": None,  # handled by cmd_setup_email_mcp (instructions)
    "pm2": None,        # handled by cmd_setup_pm2 (instructions)
    "scheduler": None,  # handled by cmd_setup_scheduler (runs schtasks)
}


def cmd_setup_odoo() -> None:
    """Interactive Odoo setup: print Docker instructions + write ODOO_API_KEY to .env."""
    print("""
=== Odoo Setup ===

Step 1 — Start Odoo with Docker:
  docker compose up -d

  This starts Odoo on http://localhost:8069 and PostgreSQL.
  First run takes ~2 minutes to initialize.

Step 2 — Create Odoo admin user:
  Open http://localhost:8069 in your browser.
  Create a database (any name, remember it).
  Set the admin password.

Step 3 — Generate an API key:
  Settings → Technical → API Keys → New
  Give it a name (e.g. "ai-employee") and copy the key.

Step 4 — Configure .env:
  Edit ./.env and set:
    ODOO_URL=http://localhost:8069
    ODOO_DB=<your database name>
    ODOO_API_KEY=<your API key>

""")
    env_path = REPO_ROOT / ".env"
    api_key = input("Paste your ODOO_API_KEY (or press Enter to skip): ").strip()
    if api_key:
        env_lines: list[str] = []
        if env_path.exists():
            env_lines = env_path.read_text(encoding="utf-8").splitlines()

        # Update or append
        found = False
        for i, line in enumerate(env_lines):
            if line.startswith("ODOO_API_KEY="):
                env_lines[i] = f"ODOO_API_KEY={api_key}"
                found = True
                break
        if not found:
            env_lines.append(f"ODOO_API_KEY={api_key}")

        env_path.write_text("\n".join(env_lines) + "\n", encoding="utf-8")
        logger.info("ODOO_API_KEY written to %s", env_path)
    else:
        logger.info("Skipped — remember to add ODOO_API_KEY to .env manually.")


def cmd_setup_gmail() -> None:
    """Run Gmail OAuth flow to create token.json for the Gmail watcher."""
    print("""
=== Gmail OAuth Setup ===

This will open a browser window to authorize the Gmail watcher.

Prerequisites:
  1. Go to Google Cloud Console → APIs & Services → Credentials
  2. Create an OAuth 2.0 Client ID (Desktop application)
  3. Download credentials.json and place it at: ./credentials.json

Then run this command — it will:
  - Open a browser for Google account authorization
  - Write token.json (for GmailWatcher) and token-mcp.json (for email-mcp)

""")
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        import pickle

        SCOPES = [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.compose",
        ]

        creds_path = REPO_ROOT / "credentials.json"
        if not creds_path.exists():
            logger.error("credentials.json not found at %s", creds_path)
            logger.error("Download it from Google Cloud Console → APIs & Services → Credentials")
            sys.exit(1)

        flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
        creds = flow.run_local_server(port=0)

        token_path = REPO_ROOT / "token.json"
        token_mcp_path = REPO_ROOT / "token-mcp.json"

        import json as _json
        token_data = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": list(creds.scopes or SCOPES),
        }
        token_path.write_text(_json.dumps(token_data, indent=2), encoding="utf-8")
        token_mcp_path.write_text(_json.dumps(token_data, indent=2), encoding="utf-8")

        logger.info("Gmail OAuth complete. Tokens written to:")
        logger.info("  %s  (GmailWatcher)", token_path)
        logger.info("  %s  (email-mcp)", token_mcp_path)

    except ImportError:
        logger.error("google-auth-oauthlib not installed. Run: pip install google-auth-oauthlib")
        sys.exit(1)


def cmd_setup_email_mcp() -> None:
    """Print email-mcp setup instructions."""
    print("""
=== Email MCP Setup ===

The email-mcp server provides Gmail send/draft capabilities to Claude.

Step 1 — Install Node.js dependencies:
  cd email-mcp
  npm install
  cd ..

Step 2 — Ensure Gmail OAuth is complete:
  python main.py setup gmail

Step 3 — Verify .mcp.json has email-mcp configured:
  cat .mcp.json

Step 4 — Start via PM2 (or run standalone for testing):
  pm2 start scripts/pm2_ecosystem.config.js --only email-mcp
  # Or standalone:
  npx tsx email-mcp/index.ts

Step 5 — Verify by checking pm2 status:
  pm2 list

The email-mcp process reads:
  - credentials.json  (Google OAuth client config)
  - token-mcp.json    (OAuth token — created by: python main.py setup gmail)
""")


def cmd_setup_pm2() -> None:
    """Print PM2 setup instructions and optionally start all processes."""
    print("""
=== PM2 Setup ===

PM2 manages all 8 Nestaro Pilot tier processes with auto-restart.

Step 1 — Install PM2 globally (requires Node.js):
  npm install -g pm2

Step 2 — Install Node.js dependencies for email-mcp:
  cd email-mcp && npm install && cd ..

Step 3 — Complete all platform setup first:
  python main.py setup gmail
  python main.py setup facebook
  python main.py setup instagram
  python main.py setup twitter
  python main.py setup linkedin
  python main.py setup whatsapp
  python main.py setup odoo

Step 4 — Start all 8 processes:
  pm2 start scripts/pm2_ecosystem.config.js

Step 5 — Persist PM2 process list (survives reboot):
  pm2 save

Step 6 — Install PM2 as Windows startup service:
  pm2 startup
  # Follow the instructions printed by the command above

Useful PM2 commands:
  pm2 list                   View all process statuses
  pm2 logs                   Tail all process logs
  pm2 logs orchestrator      Tail orchestrator logs only
  pm2 restart all            Rolling restart of all processes
  pm2 stop all               Stop all processes
  pm2 delete all             Remove all processes from PM2
""")
    start = input("Start all processes now? [y/N] ").strip().lower()
    if start == "y":
        import subprocess as _sp
        eco = REPO_ROOT / "scripts" / "pm2_ecosystem.config.js"
        result = _sp.run(["pm2", "start", str(eco)], cwd=str(REPO_ROOT))
        if result.returncode == 0:
            logger.info("All PM2 processes started. Run 'pm2 list' to verify.")
        else:
            logger.error("pm2 start failed. Is PM2 installed? Run: npm install -g pm2")


def cmd_setup_scheduler() -> None:
    """Run setup_scheduler.py to create Windows Task Scheduler entries."""
    import subprocess as _sp
    scheduler_script = REPO_ROOT / "scripts" / "setup_scheduler.py"
    logger.info("Running Windows Task Scheduler setup...")
    result = _sp.run(
        [sys.executable, str(scheduler_script)],
        cwd=str(REPO_ROOT),
    )
    sys.exit(result.returncode)


def cmd_setup(platform: str) -> None:
    """Run first-time setup for a platform."""
    if platform not in SETUP_HANDLERS:
        logger.error(
            "Unknown platform: %r. Choose: %s", platform, ", ".join(SETUP_HANDLERS)
        )
        sys.exit(1)

    # Non-browser setup commands
    if platform == "odoo":
        cmd_setup_odoo()
        return
    if platform == "gmail":
        cmd_setup_gmail()
        return
    if platform == "email-mcp":
        cmd_setup_email_mcp()
        return
    if platform == "pm2":
        cmd_setup_pm2()
        return
    if platform == "scheduler":
        cmd_setup_scheduler()
        return

    # Browser-based Playwright setup
    user_data_dir = str(PLATFORM_DATA_DIRS[platform])
    Path(user_data_dir).mkdir(parents=True, exist_ok=True)

    logger.info("Setup: %s → %s", platform, user_data_dir)
    asyncio.run(SETUP_HANDLERS[platform](user_data_dir))


# ── Watcher start commands ─────────────────────────────────────────────────────

def cmd_facebook() -> None:
    """Start the Facebook DM watcher."""
    from watchers.facebook_watcher import FacebookWatcher  # noqa: PLC0415

    poll_interval = int(os.getenv("FACEBOOK_POLL_INTERVAL", "60"))
    user_data_dir = str(PLATFORM_DATA_DIRS["facebook"])

    logger.info("Starting Facebook watcher (vault=%s, interval=%ds)", VAULT_PATH, poll_interval)
    watcher = FacebookWatcher(
        vault_path=VAULT_PATH,
        check_interval=poll_interval,
        user_data_dir=user_data_dir,
    )
    try:
        watcher.run()
    except KeyboardInterrupt:
        pass


def cmd_instagram() -> None:
    """Start the Instagram DM watcher."""
    from watchers.instagram_watcher import InstagramWatcher  # noqa: PLC0415

    poll_interval = int(os.getenv("INSTAGRAM_POLL_INTERVAL", "60"))
    user_data_dir = str(PLATFORM_DATA_DIRS["instagram"])

    logger.info("Starting Instagram watcher (vault=%s, interval=%ds)", VAULT_PATH, poll_interval)
    watcher = InstagramWatcher(
        vault_path=VAULT_PATH,
        check_interval=poll_interval,
        user_data_dir=user_data_dir,
    )
    try:
        watcher.run()
    except KeyboardInterrupt:
        pass


def cmd_twitter() -> None:
    """Start the Twitter/X mention + DM watcher."""
    from watchers.twitter_watcher import TwitterWatcher  # noqa: PLC0415

    poll_interval = int(os.getenv("TWITTER_POLL_INTERVAL", "60"))
    user_data_dir = str(PLATFORM_DATA_DIRS["twitter"])

    logger.info("Starting Twitter/X watcher (vault=%s, interval=%ds)", VAULT_PATH, poll_interval)
    watcher = TwitterWatcher(
        vault_path=VAULT_PATH,
        check_interval=poll_interval,
        user_data_dir=user_data_dir,
    )
    try:
        watcher.run()
    except KeyboardInterrupt:
        pass


def cmd_whatsapp() -> None:
    """Start the WhatsApp watcher."""
    from watchers.whatsapp_watcher import WhatsAppWatcher  # noqa: PLC0415

    poll_interval = int(os.getenv("WHATSAPP_POLL_INTERVAL", "30"))
    user_data_dir = str(PLATFORM_DATA_DIRS["whatsapp"])

    logger.info("Starting WhatsApp watcher (vault=%s, interval=%ds)", VAULT_PATH, poll_interval)
    watcher = WhatsAppWatcher(
        vault_path=VAULT_PATH,
        check_interval=poll_interval,
        user_data_dir=user_data_dir,
    )
    try:
        watcher.run()
    except KeyboardInterrupt:
        pass


def cmd_email() -> None:
    """Start the Gmail watcher."""
    from watchers.gmail_watcher import GmailWatcher  # noqa: PLC0415

    poll_interval = int(os.getenv("GMAIL_POLL_INTERVAL", "60"))

    logger.info("Starting Gmail watcher (vault=%s, interval=%ds)", VAULT_PATH, poll_interval)
    watcher = GmailWatcher(vault_path=VAULT_PATH, check_interval=poll_interval)
    try:
        watcher.run()
    except KeyboardInterrupt:
        pass


def cmd_files() -> None:
    """Start the filesystem watcher (watches vault/Inbox/)."""
    from watchers.filesystem_watcher import FilesystemWatcher  # noqa: PLC0415

    poll_interval = int(os.getenv("FILE_POLL_INTERVAL", "10"))
    inbox_path = VAULT_PATH / "Inbox"

    logger.info("Starting filesystem watcher (inbox=%s, interval=%ds)", inbox_path, poll_interval)
    watcher = FilesystemWatcher(vault_path=VAULT_PATH, check_interval=poll_interval)
    try:
        watcher.run()
    except KeyboardInterrupt:
        pass


def cmd_orchestrator() -> None:
    """Start the orchestrator (watches Needs_Action/, Approved/, Rejected/)."""
    from watchers.orchestrator import Orchestrator  # noqa: PLC0415

    check_interval = int(os.getenv("CHECK_INTERVAL", "10"))

    logger.info(
        "Starting orchestrator (vault=%s, interval=%ds)", VAULT_PATH, check_interval
    )
    orchestrator = Orchestrator(
        vault_path=VAULT_PATH,
        repo_root=REPO_ROOT,
        check_interval=check_interval,
    )
    try:
        orchestrator.run()
    except KeyboardInterrupt:
        pass


# ── One-shot content generation commands ──────────────────────────────────────

def cmd_social_post() -> None:
    """Generate Facebook/Instagram/Twitter drafts in Pending_Approval/."""
    from watchers.orchestrator import Orchestrator  # noqa: PLC0415

    orchestrator = Orchestrator(vault_path=VAULT_PATH, repo_root=REPO_ROOT)
    orchestrator.run_social_post()


def cmd_linkedin() -> None:
    """Generate a LinkedIn post draft in Pending_Approval/."""
    from watchers.orchestrator import Orchestrator  # noqa: PLC0415

    orchestrator = Orchestrator(vault_path=VAULT_PATH, repo_root=REPO_ROOT)
    orchestrator.run_linkedin_post()


def cmd_briefing() -> None:
    """Generate the CEO accounting briefing in vault/Briefings/."""
    from watchers.orchestrator import Orchestrator  # noqa: PLC0415

    orchestrator = Orchestrator(vault_path=VAULT_PATH, repo_root=REPO_ROOT)
    orchestrator.run_briefing()


def cmd_healthcheck() -> None:
    """Run PM2 health check: inspect all 8 processes; restart stopped ones; print table."""
    import subprocess as _sp
    healthcheck_script = REPO_ROOT / "scripts" / "pm2_healthcheck.py"
    result = _sp.run(
        [sys.executable, str(healthcheck_script)],
        cwd=str(REPO_ROOT),
    )
    sys.exit(result.returncode)


def cmd_odoo_status() -> None:
    """Call odoo-mcp get_financial_summary and print the result.

    Requires ODOO_URL, ODOO_DB, ODOO_API_KEY in .env.
    Uses a direct Python HTTP call (not via MCP subprocess) for quick diagnostics.
    """
    import json
    import urllib.request
    import urllib.error

    odoo_url = os.getenv("ODOO_URL", "http://localhost:8069").rstrip("/")
    odoo_db = os.getenv("ODOO_DB", "odoo")
    api_key = os.getenv("ODOO_API_KEY", "")

    if not api_key:
        logger.error("ODOO_API_KEY is not set. Run: python main.py setup odoo")
        sys.exit(1)

    today = __import__("datetime").date.today()
    first_of_month = today.replace(day=1)

    # Build JSON-RPC request for get_financial_summary (via search_read on account.move)
    payload = json.dumps({
        "jsonrpc": "2.0",
        "method": "call",
        "id": 1,
        "params": {
            "model": "account.move",
            "method": "search_read",
            "args": [[
                ["move_type", "=", "out_invoice"],
                ["state", "=", "posted"],
                ["invoice_date", ">=", str(first_of_month)],
                ["invoice_date", "<=", str(today)],
            ]],
            "kwargs": {
                "fields": ["name", "partner_id", "amount_total", "amount_residual", "payment_state", "invoice_date_due"],
                "limit": 50,
            },
        },
    }).encode("utf-8")

    url = f"{odoo_url}/web/dataset/call_kw"
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    )

    print(f"\n=== Odoo Financial Status ===")
    print(f"URL: {odoo_url}  |  DB: {odoo_db}  |  Period: {first_of_month} → {today}\n")

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        logger.error("Cannot reach Odoo at %s: %s", odoo_url, e)
        logger.error("Run: docker compose up -d")
        sys.exit(1)
    except Exception as e:
        logger.error("Odoo request failed: %s", e)
        sys.exit(1)

    if "error" in data:
        logger.error("Odoo API error: %s", data["error"])
        sys.exit(1)

    invoices = data.get("result", [])
    paid = [i for i in invoices if i["payment_state"] == "paid"]
    unpaid = [i for i in invoices if i["payment_state"] in ("not_paid", "partial")]
    mtd_revenue = sum(i["amount_total"] for i in paid)
    outstanding = sum(i["amount_residual"] for i in unpaid)

    print(f"MTD Revenue:       ${mtd_revenue:,.2f}")
    print(f"Total Outstanding: ${outstanding:,.2f}")
    print(f"Paid Invoices:     {len(paid)}")
    print(f"Unpaid Invoices:   {len(unpaid)}")

    if unpaid:
        print("\nUnpaid Invoices:")
        for inv in unpaid:
            due = inv["invoice_date_due"]
            partner = inv["partner_id"][1] if inv["partner_id"] else "Unknown"
            print(f"  {inv['name']}  {partner:<30}  ${inv['amount_residual']:>10,.2f}  due {due}")

    print(f"\nOdoo is reachable at {odoo_url}")


# ── Help ───────────────────────────────────────────────────────────────────────

HELP_TEXT = """\
Nestaro Pilot — Nestaro Pilot tier

SETUP (first-time login/configuration):
  python main.py setup facebook       Open Facebook for manual login (Playwright)
  python main.py setup instagram      Open Instagram for manual login (Playwright)
  python main.py setup twitter        Open Twitter/X for manual login (Playwright)
  python main.py setup linkedin       Open LinkedIn for manual login (Playwright)
  python main.py setup whatsapp       Open WhatsApp Web for QR scan (Playwright)
  python main.py setup gmail          Run Gmail OAuth flow → token.json + token-mcp.json
  python main.py setup email-mcp      Print email-mcp Node.js setup instructions
  python main.py setup odoo           Print Docker instructions + save ODOO_API_KEY
  python main.py setup pm2            Print PM2 setup instructions (optionally start all)
  python main.py setup scheduler      Register Windows Task Scheduler entries (run as Admin)

WATCHERS (start monitoring — usually via PM2):
  python main.py facebook             Facebook DM watcher
  python main.py instagram            Instagram DM watcher
  python main.py twitter              Twitter mention + DM watcher
  python main.py whatsapp             WhatsApp watcher
  python main.py email                Gmail watcher
  python main.py files                Filesystem inbox watcher
  python main.py orchestrator         Master orchestrator

CONTENT GENERATION (one-shot, writes to Pending_Approval/):
  python main.py social-post          Generate Facebook + Instagram + Twitter drafts
  python main.py linkedin             Generate LinkedIn post draft
  python main.py briefing             Generate CEO accounting briefing

DIAGNOSTICS:
  python main.py healthcheck          PM2 health check — inspect 8 processes, restart stopped
  python main.py odoo-status          Check Odoo connection + print financial summary
"""


# ── Dispatch ───────────────────────────────────────────────────────────────────

COMMANDS: dict[str, any] = {
    "facebook": cmd_facebook,
    "instagram": cmd_instagram,
    "twitter": cmd_twitter,
    "whatsapp": cmd_whatsapp,
    "email": cmd_email,
    "files": cmd_files,
    "orchestrator": cmd_orchestrator,
    "social-post": cmd_social_post,
    "linkedin": cmd_linkedin,
    "briefing": cmd_briefing,
    "healthcheck": cmd_healthcheck,
    "odoo-status": cmd_odoo_status,
}


def main() -> None:
    args = sys.argv[1:]

    if not args or args[0] in ("--help", "-h", "help"):
        print(HELP_TEXT)
        return

    command = args[0]

    # setup <platform>
    if command == "setup":
        if len(args) < 2:
            logger.error("Usage: python main.py setup <platform>")
            logger.error("Platforms: %s", ", ".join(SETUP_HANDLERS))
            sys.exit(1)
        cmd_setup(args[1])
        return

    if command in COMMANDS:
        COMMANDS[command]()
        return

    logger.error("Unknown command: %r", command)
    print(HELP_TEXT)
    sys.exit(1)


if __name__ == "__main__":
    main()
