"""Twitter/X poster: publishes approved tweets/replies via Playwright.

Standalone script triggered by orchestrator after HITL approval.
Uses persistent Chromium context to maintain Twitter/X session.
Enforces 280 character limit. Includes login/CAPTCHA detection and DRY_RUN support.
"""

import asyncio
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from playwright.async_api import async_playwright, BrowserContext, Page

repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from watchers.logger import append_log_entry

logger = logging.getLogger(__name__)

TWITTER_HOME_URL = "https://twitter.com/home"
TWITTER_MAX_CHARS = 280

SELECTORS = {
    "login_form": 'input[autocomplete="username"], div[data-testid="LoginForm"]',
    "home_loaded": 'div[data-testid="primaryColumn"]',
    "compose_button": 'a[data-testid="SideNav_NewTweet_Button"], div[aria-label="Tweet"]',
    "tweet_textarea": 'div[data-testid="tweetTextarea_0"], div[aria-label="Tweet text"]',
    "tweet_button": 'div[data-testid="tweetButtonInline"], button[data-testid="tweetButton"]',
    "captcha": 'div[data-testid="ChallengeForm"]',
}


async def _ensure_browser(user_data_dir: str) -> tuple[BrowserContext, Page]:
    pw = await async_playwright().start()
    context = await pw.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
    )
    page = context.pages[0] if context.pages else await context.new_page()
    return context, page


async def _check_session(page: Page) -> bool:
    """Returns True if session is valid (logged in)."""
    try:
        login = await page.query_selector(SELECTORS["login_form"])
        if login:
            logger.error("Twitter/X session expired — login form detected")
            return False
        captcha = await page.query_selector(SELECTORS["captcha"])
        if captcha:
            logger.error("Twitter/X CAPTCHA/challenge detected")
            return False
    except Exception:
        pass
    return True


async def _publish_tweet(page: Page, content: str) -> bool:
    """Compose and publish a tweet."""
    # Enforce Twitter char limit
    if len(content) > TWITTER_MAX_CHARS:
        logger.warning(
            "Tweet content truncated from %d to %d chars", len(content), TWITTER_MAX_CHARS
        )
        content = content[:TWITTER_MAX_CHARS]

    try:
        await page.goto(TWITTER_HOME_URL)
        await page.wait_for_timeout(3000)

        if not await _check_session(page):
            return False

        await page.wait_for_selector(SELECTORS["home_loaded"], timeout=15000)

        # Click compose / Tweet button
        compose_btn = await page.wait_for_selector(SELECTORS["compose_button"], timeout=10000)
        if not compose_btn:
            logger.error("Twitter compose button not found")
            return False
        await compose_btn.click()
        await page.wait_for_timeout(1500)

        # Type tweet content
        textarea = await page.wait_for_selector(SELECTORS["tweet_textarea"], timeout=10000)
        if not textarea:
            logger.error("Twitter tweet textarea not found")
            return False
        await textarea.click()
        await page.keyboard.type(content, delay=15)
        await page.wait_for_timeout(1000)

        # Click Tweet/Post button
        tweet_btn = await page.wait_for_selector(SELECTORS["tweet_button"], timeout=10000)
        if not tweet_btn:
            logger.error("Twitter Tweet button not found")
            return False
        await tweet_btn.click()
        await page.wait_for_timeout(3000)

        logger.info("Tweet published successfully (%d chars)", len(content))
        return True

    except Exception:
        logger.exception("Failed to publish tweet")
        return False


def post_twitter(content: str, user_data_dir: str, vault_path: str | Path, dry_run: bool = True) -> bool:
    """Publish a tweet on Twitter/X.

    Main entry point called by orchestrator dispatch.

    Args:
        content: Tweet text (max 280 chars; truncated if longer).
        user_data_dir: Playwright persistent context directory.
        vault_path: Vault path for logging.
        dry_run: If True, log but skip actual Playwright publish.

    Returns:
        True if tweet was published (or logged in dry run).
    """
    vault_path = Path(vault_path)
    log_dir = vault_path / "Logs"

    # Enforce character limit
    if len(content) > TWITTER_MAX_CHARS:
        content = content[:TWITTER_MAX_CHARS]

    if dry_run:
        logger.info("[DRY_RUN] Would publish tweet (%d chars): %s...", len(content), content[:100])
        append_log_entry(
            log_dir=log_dir,
            action_type="twitter_post",
            actor="twitter_poster",
            target="twitter",
            parameters={"dry_run": True, "content_length": len(content), "preview": content[:100]},
            result="skipped",
        )
        return True

    async def _run() -> bool:
        context, page = await _ensure_browser(user_data_dir)
        try:
            success = await _publish_tweet(page, content)

            if success:
                append_log_entry(
                    log_dir=log_dir,
                    action_type="twitter_post",
                    actor="twitter_poster",
                    target="twitter",
                    parameters={"content_length": len(content), "preview": content[:100]},
                    result="success",
                )
            else:
                dashboard = vault_path / "Dashboard.md"
                if dashboard.exists():
                    dash_content = dashboard.read_text(encoding="utf-8")
                    if "Twitter/X re-authentication" not in dash_content:
                        with open(dashboard, "a", encoding="utf-8") as f:
                            f.write(
                                f"\n\n> **ALERT** ({datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}): "
                                "Twitter/X session issue. Run `python main.py setup twitter` to re-login.\n"
                            )
                append_log_entry(
                    log_dir=log_dir,
                    action_type="auth_failure",
                    actor="twitter_poster",
                    target="twitter",
                    parameters={"event": "post_failed"},
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
