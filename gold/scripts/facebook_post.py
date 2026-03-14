"""Facebook poster: publishes approved Facebook posts/replies via Playwright.

Standalone script triggered by orchestrator after HITL approval.
Uses persistent Chromium context to maintain Facebook session.
Includes login detection, CAPTCHA detection, and DRY_RUN support.
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

FACEBOOK_COMPOSE_URL = "https://www.facebook.com/"

SELECTORS = {
    "login_form": 'input[name="email"], #email',
    "home_loaded": 'div[aria-label="Create post"], div[data-pagelet="FeedUnit_0"]',
    "compose_box": 'div[data-pagelet="FeedComposer"], div[aria-label="Create post"]',
    "compose_textarea": 'div[contenteditable="true"][role="textbox"]',
    "post_button": 'div[aria-label="Post"], button[data-testid="react-composer-post-button"]',
    "captcha": 'div[id="checkpoint"], div[class*="captcha"]',
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
            logger.error("Facebook session expired — login form detected")
            return False
        captcha = await page.query_selector(SELECTORS["captcha"])
        if captcha:
            logger.error("Facebook CAPTCHA/checkpoint detected")
            return False
    except Exception:
        pass
    return True


async def _publish_post(page: Page, content: str) -> bool:
    """Publish a post to Facebook feed."""
    try:
        await page.goto(FACEBOOK_COMPOSE_URL)
        await page.wait_for_timeout(3000)

        if not await _check_session(page):
            return False

        await page.wait_for_selector(SELECTORS["home_loaded"], timeout=15000)

        # Click compose box
        compose = await page.wait_for_selector(SELECTORS["compose_box"], timeout=10000)
        if not compose:
            logger.error("Facebook compose box not found")
            return False
        await compose.click()
        await page.wait_for_timeout(1500)

        # Type content
        textarea = await page.wait_for_selector(SELECTORS["compose_textarea"], timeout=10000)
        if not textarea:
            logger.error("Facebook textarea not found")
            return False
        await textarea.click()
        await page.keyboard.type(content, delay=15)
        await page.wait_for_timeout(1000)

        # Click Post
        post_btn = await page.wait_for_selector(SELECTORS["post_button"], timeout=10000)
        if not post_btn:
            logger.error("Facebook Post button not found")
            return False
        await post_btn.click()
        await page.wait_for_timeout(3000)

        logger.info("Facebook post published successfully")
        return True

    except Exception:
        logger.exception("Failed to publish Facebook post")
        return False


def post_facebook(content: str, user_data_dir: str, vault_path: str | Path, dry_run: bool = True) -> bool:
    """Publish a Facebook post.

    Main entry point called by orchestrator dispatch.

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
        logger.info("[DRY_RUN] Would publish Facebook post (%d chars): %s...", len(content), content[:100])
        append_log_entry(
            log_dir=log_dir,
            action_type="facebook_post",
            actor="facebook_poster",
            target="facebook",
            parameters={"dry_run": True, "content_length": len(content), "preview": content[:100]},
            result="skipped",
        )
        return True

    async def _run() -> bool:
        context, page = await _ensure_browser(user_data_dir)
        try:
            success = await _publish_post(page, content)

            if success:
                append_log_entry(
                    log_dir=log_dir,
                    action_type="facebook_post",
                    actor="facebook_poster",
                    target="facebook",
                    parameters={"content_length": len(content), "preview": content[:100]},
                    result="success",
                )
            else:
                # Write alert to Dashboard
                dashboard = vault_path / "Dashboard.md"
                if dashboard.exists():
                    dash_content = dashboard.read_text(encoding="utf-8")
                    if "Facebook re-authentication" not in dash_content:
                        with open(dashboard, "a", encoding="utf-8") as f:
                            f.write(
                                f"\n\n> **ALERT** ({datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}): "
                                "Facebook session issue. Run `python main.py setup facebook` to re-login.\n"
                            )
                append_log_entry(
                    log_dir=log_dir,
                    action_type="auth_failure",
                    actor="facebook_poster",
                    target="facebook",
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
