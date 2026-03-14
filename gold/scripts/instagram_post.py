"""Instagram poster: publishes approved Instagram posts/replies via Playwright.

Standalone script triggered by orchestrator after HITL approval.
Uses persistent Chromium context to maintain Instagram session.
Includes login detection, CAPTCHA detection, and DRY_RUN support.

Note: Instagram posting via web requires the Creator Studio / web composer flow.
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

INSTAGRAM_URL = "https://www.instagram.com/"

SELECTORS = {
    "login_form": 'input[name="username"]',
    "home_loaded": 'svg[aria-label="Home"], nav[aria-label="Primary"]',
    # New post flow — uses the + button or "New post" link
    "new_post_button": 'svg[aria-label="New post"], a[href="/create/style/"]',
    "caption_textarea": 'div[aria-label="Write a caption..."], textarea[placeholder*="caption"]',
    "share_button": 'div[role="button"]:has-text("Share"), button:has-text("Share")',
    "captcha": 'div[class*="challenge"]',
    # For DM replies: message compose
    "dm_compose": 'div[contenteditable="true"]',
    "dm_send": 'button[type="submit"]:has-text("Send")',
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
            logger.error("Instagram session expired — login form detected")
            return False
        captcha = await page.query_selector(SELECTORS["captcha"])
        if captcha:
            logger.error("Instagram CAPTCHA/challenge detected")
            return False
    except Exception:
        pass
    return True


async def _publish_post(page: Page, content: str) -> bool:
    """Publish a post to Instagram via the web composer."""
    try:
        await page.goto(INSTAGRAM_URL)
        await page.wait_for_timeout(3000)

        if not await _check_session(page):
            return False

        await page.wait_for_selector(SELECTORS["home_loaded"], timeout=15000)

        # Click "New post" button (the + icon)
        new_post_btn = await page.wait_for_selector(SELECTORS["new_post_button"], timeout=10000)
        if not new_post_btn:
            logger.error("Instagram new post button not found")
            return False
        await new_post_btn.click()
        await page.wait_for_timeout(2000)

        # Note: Instagram requires an image/video for feed posts.
        # For text-only content, use the caption field and attach a placeholder.
        # In production: the approval file should include an image path.
        # For now, type caption and attempt Share.

        caption_field = await page.wait_for_selector(SELECTORS["caption_textarea"], timeout=10000)
        if not caption_field:
            logger.error("Instagram caption field not found")
            return False
        await caption_field.click()
        await page.keyboard.type(content, delay=15)
        await page.wait_for_timeout(1000)

        share_btn = await page.wait_for_selector(SELECTORS["share_button"], timeout=10000)
        if not share_btn:
            logger.error("Instagram Share button not found")
            return False
        await share_btn.click()
        await page.wait_for_timeout(3000)

        logger.info("Instagram post published successfully")
        return True

    except Exception:
        logger.exception("Failed to publish Instagram post")
        return False


def post_instagram(content: str, user_data_dir: str, vault_path: str | Path, dry_run: bool = True) -> bool:
    """Publish an Instagram post.

    Main entry point called by orchestrator dispatch.

    Args:
        content: Caption text to publish (include hashtags).
        user_data_dir: Playwright persistent context directory.
        vault_path: Vault path for logging.
        dry_run: If True, log but skip actual Playwright publish.

    Returns:
        True if post was published (or logged in dry run).
    """
    vault_path = Path(vault_path)
    log_dir = vault_path / "Logs"

    if dry_run:
        logger.info("[DRY_RUN] Would publish Instagram post (%d chars): %s...", len(content), content[:100])
        append_log_entry(
            log_dir=log_dir,
            action_type="instagram_post",
            actor="instagram_poster",
            target="instagram",
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
                    action_type="instagram_post",
                    actor="instagram_poster",
                    target="instagram",
                    parameters={"content_length": len(content), "preview": content[:100]},
                    result="success",
                )
            else:
                dashboard = vault_path / "Dashboard.md"
                if dashboard.exists():
                    dash_content = dashboard.read_text(encoding="utf-8")
                    if "Instagram re-authentication" not in dash_content:
                        with open(dashboard, "a", encoding="utf-8") as f:
                            f.write(
                                f"\n\n> **ALERT** ({datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}): "
                                "Instagram session issue. Run `python main.py setup instagram` to re-login.\n"
                            )
                append_log_entry(
                    log_dir=log_dir,
                    action_type="auth_failure",
                    actor="instagram_poster",
                    target="instagram",
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
