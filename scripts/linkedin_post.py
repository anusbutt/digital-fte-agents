"""LinkedIn poster: publishes approved LinkedIn posts via Playwright.

Standalone script (not a watcher) triggered by orchestrator after approval.
Uses persistent Chromium context to maintain LinkedIn session.
Includes CAPTCHA detection, session expiry handling, and DRY_RUN support.
"""

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from playwright.async_api import async_playwright, BrowserContext, Page

# Add repo root to path for imports
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from watchers.logger import append_log_entry

logger = logging.getLogger(__name__)

LINKEDIN_URL = "https://www.linkedin.com/feed/"

# Selectors — LinkedIn DOM (may change with updates)
SELECTORS = {
    "start_post_button": 'button.share-box-feed-entry__trigger',
    "post_editor": 'div.ql-editor[data-placeholder="What do you want to talk about?"]',
    "post_button": 'button.share-actions__primary-action',
    "captcha": 'iframe[title*="captcha"], iframe[title*="CAPTCHA"], div.captcha, #captcha',
    "login_form": 'form.login__form, input#session_key',
    "feed_loaded": 'div.scaffold-layout__main',
}


async def _ensure_browser(user_data_dir: str) -> tuple[BrowserContext, Page]:
    """Launch persistent Chromium context for LinkedIn."""
    pw = await async_playwright().start()
    context = await pw.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
    )

    page = context.pages[0] if context.pages else await context.new_page()
    return context, page


async def _check_captcha(page: Page) -> bool:
    """Detect CAPTCHA or automation detection.

    Returns True if CAPTCHA is detected — caller must exit immediately.
    """
    try:
        captcha = await page.query_selector(SELECTORS["captcha"])
        if captcha:
            logger.error("CAPTCHA/automation detection triggered — exiting immediately (no retry)")
            return True
    except Exception:
        pass
    return False


async def _check_session(page: Page) -> bool:
    """Check if LinkedIn session is valid (logged in).

    Returns True if logged in, False if login form is visible.
    """
    try:
        login_form = await page.query_selector(SELECTORS["login_form"])
        if login_form:
            logger.error("LinkedIn session expired — login form detected")
            return False
    except Exception:
        pass
    return True


async def _post_content(page: Page, content: str) -> bool:
    """Navigate to LinkedIn feed and publish a post."""
    try:
        # Navigate to feed
        await page.goto(LINKEDIN_URL)
        await page.wait_for_timeout(3000)

        # Check for CAPTCHA
        if await _check_captcha(page):
            return False

        # Check for session expiry
        if not await _check_session(page):
            return False

        # Wait for feed to load
        await page.wait_for_selector(SELECTORS["feed_loaded"], timeout=15000)

        # Click "Start a post" button
        start_btn = await page.wait_for_selector(SELECTORS["start_post_button"], timeout=10000)
        if not start_btn:
            logger.error("'Start a post' button not found")
            return False
        await start_btn.click()
        await page.wait_for_timeout(2000)

        # Type post content into editor
        editor = await page.wait_for_selector(SELECTORS["post_editor"], timeout=10000)
        if not editor:
            logger.error("Post editor not found")
            return False
        await editor.click()
        await page.keyboard.type(content, delay=15)
        await page.wait_for_timeout(1000)

        # Check for CAPTCHA again before posting
        if await _check_captcha(page):
            return False

        # Click "Post" button
        post_btn = await page.wait_for_selector(SELECTORS["post_button"], timeout=10000)
        if not post_btn:
            logger.error("Post button not found")
            return False
        await post_btn.click()
        await page.wait_for_timeout(3000)

        logger.info("LinkedIn post published successfully")
        return True

    except Exception:
        logger.exception("Failed to publish LinkedIn post")
        return False


async def _setup_session(user_data_dir: str) -> None:
    """Interactive setup — open LinkedIn for manual login."""
    logger.info("Opening LinkedIn for login setup...")
    logger.info("Log in manually, then press Ctrl+C to exit.")

    context, page = await _ensure_browser(user_data_dir)

    await page.goto(LINKEDIN_URL)

    logger.info("Waiting for manual login... (Ctrl+C to exit after logging in)")

    try:
        # Wait for feed to confirm login
        await page.wait_for_selector(SELECTORS["feed_loaded"], timeout=120000)
        logger.info("LinkedIn login successful! Session saved to %s", user_data_dir)
    except Exception:
        logger.warning("Timeout waiting for login. Try again with --setup.")
    finally:
        await context.close()


def post(content: str, user_data_dir: str, vault_path: str | Path, dry_run: bool = True) -> bool:
    """Publish a LinkedIn post.

    This is the main entry point called by the orchestrator.

    Args:
        content: Post text to publish.
        user_data_dir: Playwright persistent context directory.
        vault_path: Vault path for logging.
        dry_run: If True, log but skip actual Playwright publish.

    Returns:
        True if post was published (or logged in dry run).
    """
    vault_path = Path(vault_path)
    log_dir = vault_path / "Logs"

    if dry_run:
        logger.info("[DRY_RUN] Would publish LinkedIn post (%d chars): %s...", len(content), content[:100])
        append_log_entry(
            log_dir=log_dir,
            action_type="linkedin_generated",
            actor="linkedin_poster",
            target="linkedin",
            parameters={"dry_run": True, "content_length": len(content), "preview": content[:100]},
            result="skipped",
        )
        return True

    async def _run() -> bool:
        context, page = await _ensure_browser(user_data_dir)
        try:
            # Check for CAPTCHA first
            await page.goto(LINKEDIN_URL)
            await page.wait_for_timeout(3000)

            if await _check_captcha(page):
                # Update Dashboard with alert
                dashboard = vault_path / "Dashboard.md"
                if dashboard.exists():
                    dash_content = dashboard.read_text(encoding="utf-8")
                    if "LinkedIn CAPTCHA" not in dash_content:
                        with open(dashboard, "a", encoding="utf-8") as f:
                            f.write(
                                f"\n\n> **ALERT** ({datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}): "
                                "LinkedIn CAPTCHA/automation detected. Wait 24h, then run "
                                "`python scripts/linkedin_post.py --setup` to re-login.\n"
                            )
                append_log_entry(
                    log_dir=log_dir,
                    action_type="auth_failure",
                    actor="linkedin_poster",
                    target="linkedin",
                    parameters={"event": "captcha_detected"},
                    result="failure",
                )
                return False

            # Check session
            if not await _check_session(page):
                dashboard = vault_path / "Dashboard.md"
                if dashboard.exists():
                    dash_content = dashboard.read_text(encoding="utf-8")
                    if "LinkedIn re-authentication" not in dash_content:
                        with open(dashboard, "a", encoding="utf-8") as f:
                            f.write(
                                f"\n\n> **ALERT** ({datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}): "
                                "LinkedIn session expired. Run `python scripts/linkedin_post.py --setup` to re-login.\n"
                            )
                append_log_entry(
                    log_dir=log_dir,
                    action_type="auth_failure",
                    actor="linkedin_poster",
                    target="linkedin",
                    parameters={"event": "session_expired"},
                    result="failure",
                )
                return False

            success = await _post_content(page, content)

            if success:
                append_log_entry(
                    log_dir=log_dir,
                    action_type="linkedin_generated",
                    actor="linkedin_poster",
                    target="linkedin",
                    parameters={"content_length": len(content), "preview": content[:100]},
                    result="success",
                )
            else:
                append_log_entry(
                    log_dir=log_dir,
                    action_type="error",
                    actor="linkedin_poster",
                    target="linkedin",
                    parameters={"event": "post_failed", "content_length": len(content)},
                    result="failure",
                )

            return success
        finally:
            await context.close()

    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_run())
    finally:
        loop.close()


# --- CLI entry point ---

def main() -> None:
    """Run LinkedIn poster from command line."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    parser = argparse.ArgumentParser(description="LinkedIn Poster — publish posts via Playwright")
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Open LinkedIn for first-time manual login setup",
    )
    parser.add_argument(
        "--post",
        type=str,
        help="Post content to publish (for manual testing)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Log post but skip actual publish",
    )
    args = parser.parse_args()

    # Load .env from repo root
    load_dotenv(repo_root / ".env")

    vault_path = Path(os.getenv("VAULT_PATH", repo_root / "vault"))
    if not vault_path.is_absolute():
        vault_path = repo_root / vault_path

    user_data_dir = os.getenv("LINKEDIN_USER_DATA_DIR", str(repo_root / "playwright-data" / "linkedin"))
    dry_run = args.dry_run or os.getenv("DRY_RUN", "true").lower() in ("true", "1", "yes")

    if args.setup:
        asyncio.run(_setup_session(user_data_dir))
        return

    if args.post:
        success = post(args.post, user_data_dir, vault_path, dry_run=dry_run)
        if success:
            logger.info("Post completed successfully")
        else:
            logger.error("Post failed")
            sys.exit(1)
    else:
        logger.error("No action specified. Use --setup or --post 'content'")
        sys.exit(1)


if __name__ == "__main__":
    main()
