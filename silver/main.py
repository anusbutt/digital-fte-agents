"""Digital FTE Silver — unified CLI entry point.

T047: Provides subcommands for all watcher, orchestrator, and setup operations.

Usage:
    python main.py <subcommand> [options]

Subcommands:
    filesystem          Start the filesystem watcher (watches vault/Inbox/)
    gmail               Start the Gmail watcher (polls Gmail API)
    whatsapp            Start the WhatsApp watcher (Playwright)
    orchestrator        Start the orchestrator (watches Needs_Action/, Approved/, Rejected/)
    briefing            Generate CEO briefing once and exit
    linkedin            Generate LinkedIn post draft once and exit
    healthcheck         Run PM2 health check once and exit
    setup gmail         Authenticate Gmail OAuth2 for reading emails (first-time setup)
    setup email-mcp     Authenticate Gmail OAuth2 for sending/drafting emails (first-time setup)
    setup whatsapp      Open WhatsApp Web for QR code scan (first-time setup)
    setup linkedin      Open LinkedIn for manual login (first-time setup)
    setup scheduler     Create Windows Task Scheduler entries (requires Administrator)
    setup pm2           Show PM2 startup instructions
"""

import argparse
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env before anything else
REPO_ROOT = Path(__file__).resolve().parent
load_dotenv(REPO_ROOT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def _vault_path() -> Path:
    vault = Path(os.getenv("VAULT_PATH", REPO_ROOT / "vault"))
    if not vault.is_absolute():
        vault = REPO_ROOT / vault
    return vault


def cmd_filesystem(_args: argparse.Namespace) -> None:
    """Start the filesystem watcher."""
    from watchers.filesystem_watcher import main
    main()


def cmd_gmail(_args: argparse.Namespace) -> None:
    """Start the Gmail watcher."""
    from watchers.gmail_watcher import main
    main()


def cmd_whatsapp(_args: argparse.Namespace) -> None:
    """Start the WhatsApp watcher."""
    from watchers.whatsapp_watcher import main
    main()


def cmd_orchestrator(_args: argparse.Namespace) -> None:
    """Start the orchestrator in watch mode."""
    from watchers.orchestrator import Orchestrator
    orch = Orchestrator(vault_path=_vault_path(), repo_root=REPO_ROOT)
    try:
        orch.run()
    except KeyboardInterrupt:
        pass


def cmd_briefing(_args: argparse.Namespace) -> None:
    """Generate CEO briefing once and exit."""
    from watchers.orchestrator import Orchestrator
    orch = Orchestrator(vault_path=_vault_path(), repo_root=REPO_ROOT)
    orch.run_briefing()


def cmd_linkedin(_args: argparse.Namespace) -> None:
    """Generate LinkedIn post draft once and exit."""
    from watchers.orchestrator import Orchestrator
    orch = Orchestrator(vault_path=_vault_path(), repo_root=REPO_ROOT)
    orch.run_linkedin_post()


def cmd_healthcheck(_args: argparse.Namespace) -> None:
    """Run PM2 health check once and exit."""
    from scripts.pm2_healthcheck import run_healthcheck
    run_healthcheck(dry_run=getattr(_args, "dry_run", False))


def cmd_setup(args: argparse.Namespace) -> None:
    """Dispatch to the appropriate setup routine."""
    target = args.setup_target

    if target == "gmail":
        _setup_gmail()
    elif target == "email-mcp":
        _setup_email_mcp()
    elif target == "whatsapp":
        _setup_whatsapp()
    elif target == "linkedin":
        _setup_linkedin()
    elif target == "scheduler":
        _setup_scheduler()
    elif target == "pm2":
        _setup_pm2()
    else:
        print(f"Unknown setup target: {target!r}")
        print("Valid targets: gmail, email-mcp, whatsapp, linkedin, scheduler, pm2")
        sys.exit(1)


def _setup_gmail() -> None:
    """Run Gmail OAuth2 interactive consent flow."""
    print("Starting Gmail OAuth2 setup...")
    print("A browser window will open for Google account authorization.")
    print()
    from watchers.gmail_watcher import _authenticate
    credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH", str(REPO_ROOT / "credentials.json"))
    token_path = os.getenv("GMAIL_TOKEN_PATH", str(REPO_ROOT / "token.json"))
    _authenticate(credentials_path, token_path, interactive=True)
    print(f"Gmail OAuth2 setup complete. Token saved to: {token_path}")


def _setup_email_mcp() -> None:
    """Run OAuth2 consent flow for the Email MCP server (send/draft scopes)."""
    print("Starting Email MCP OAuth2 setup...")
    print("A browser window will open for Google account authorization.")
    print("This grants permission to SEND and DRAFT emails.")
    print()
    from google_auth_oauthlib.flow import InstalledAppFlow

    credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH", str(REPO_ROOT / "credentials.json"))
    token_path = os.getenv("EMAIL_MCP_TOKEN_PATH", str(REPO_ROOT / "token-mcp.json"))

    if not os.path.exists(credentials_path):
        print(f"ERROR: credentials.json not found at: {credentials_path}")
        print("Download it from Google Cloud Console → APIs & Services → Credentials.")
        sys.exit(1)

    scopes = [
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.compose",
    ]

    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, scopes)
    creds = flow.run_local_server(port=0)

    with open(token_path, "w", encoding="utf-8") as f:
        f.write(creds.to_json())

    print(f"Email MCP OAuth2 setup complete. Token saved to: {token_path}")


def _setup_whatsapp() -> None:
    """Open WhatsApp Web for QR code scanning."""
    print("Starting WhatsApp Web setup...")
    print("Chromium will open. Scan the QR code with your WhatsApp mobile app.")
    print()
    from watchers.whatsapp_watcher import WhatsAppWatcher
    vault = _vault_path()
    watcher = WhatsAppWatcher(vault_path=vault)
    watcher._setup_session()


def _setup_linkedin() -> None:
    """Open LinkedIn for manual login."""
    print("Starting LinkedIn session setup...")
    print("Chromium will open. Log in to LinkedIn manually.")
    print()
    from scripts.linkedin_post import setup_session
    user_data_dir = os.getenv("LINKEDIN_USER_DATA_DIR", "./playwright-data/linkedin")
    setup_session(user_data_dir=user_data_dir)


def _setup_scheduler() -> None:
    """Create Windows Task Scheduler entries."""
    print("Creating Windows Task Scheduler entries...")
    print("Note: This requires Administrator privileges.")
    print()
    from scripts.setup_scheduler import create_tasks
    create_tasks()


def _setup_pm2() -> None:
    """Print PM2 startup instructions."""
    print("PM2 Process Management Setup")
    print("=" * 40)
    print()
    print("1. Install PM2 globally:")
    print("   npm install -g pm2")
    print()
    print("2. Start all processes:")
    print(f"   pm2 start {REPO_ROOT / 'scripts' / 'pm2_ecosystem.config.js'}")
    print()
    print("3. Save process list (survives reboot):")
    print("   pm2 save")
    print()
    print("4. Install PM2 as Windows startup service:")
    print("   pm2 startup")
    print()
    print("5. Verify all processes are running:")
    print("   pm2 list")
    print()
    print("Expected processes: filesystem-watcher, gmail-watcher,")
    print("                    whatsapp-watcher, orchestrator, email-mcp")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="digital-fte",
        description="Digital FTE Silver — AI Employee CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py filesystem          # Start filesystem watcher
  python main.py gmail               # Start Gmail watcher
  python main.py whatsapp            # Start WhatsApp watcher
  python main.py orchestrator        # Start orchestrator
  python main.py briefing            # Generate CEO briefing
  python main.py linkedin            # Generate LinkedIn post
  python main.py healthcheck         # Run PM2 health check
  python main.py setup gmail         # Authenticate Gmail (read emails)
  python main.py setup email-mcp     # Authenticate Gmail (send/draft emails)
  python main.py setup whatsapp      # Setup WhatsApp session
  python main.py setup linkedin      # Setup LinkedIn session
  python main.py setup scheduler     # Create Task Scheduler entries
  python main.py setup pm2           # Show PM2 setup instructions
        """,
    )

    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    # Watcher commands
    sub.add_parser("filesystem", help="Start filesystem watcher (watches vault/Inbox/)")
    sub.add_parser("gmail", help="Start Gmail watcher (polls Gmail API every ~60s)")
    sub.add_parser("whatsapp", help="Start WhatsApp watcher (Playwright, polls WhatsApp Web)")
    sub.add_parser("orchestrator", help="Start orchestrator (watches Needs_Action/, Approved/, Rejected/)")

    # One-shot commands
    sub.add_parser("briefing", help="Generate CEO briefing once and exit")
    sub.add_parser("linkedin", help="Generate LinkedIn post draft once and exit")

    hc = sub.add_parser("healthcheck", help="Run PM2 health check once and exit")
    hc.add_argument("--dry-run", action="store_true", help="Log but do not restart processes")

    # Setup command
    setup_p = sub.add_parser("setup", help="First-time setup commands")
    setup_p.add_argument(
        "setup_target",
        choices=["gmail", "email-mcp", "whatsapp", "linkedin", "scheduler", "pm2"],
        metavar="<target>",
        help="Setup target: gmail | email-mcp | whatsapp | linkedin | scheduler | pm2",
    )

    return parser


def main() -> None:
    dry_run = os.getenv("DRY_RUN", "true").lower() in ("true", "1", "yes")
    vault = _vault_path()

    # If called with no args, print status and help
    if len(sys.argv) == 1:
        print(f"Digital FTE Silver v0.2.0")
        print(f"  Vault: {vault}")
        print(f"  DRY_RUN: {dry_run}")
        print()
        _build_parser().print_help()
        sys.exit(0)

    parser = _build_parser()
    args = parser.parse_args()

    dispatch = {
        "filesystem": cmd_filesystem,
        "gmail": cmd_gmail,
        "whatsapp": cmd_whatsapp,
        "orchestrator": cmd_orchestrator,
        "briefing": cmd_briefing,
        "linkedin": cmd_linkedin,
        "healthcheck": cmd_healthcheck,
        "setup": cmd_setup,
    }

    handler = dispatch.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
