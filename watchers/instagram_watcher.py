"""Instagram watcher: monitors Instagram Direct Messages for business keyword messages via Playwright.

Extends BaseWatcher to scan Instagram DM inbox for unread messages containing
business keywords, create INSTAGRAM_ VaultItems in vault/Needs_Action/.

Uses persistent Chromium context to maintain Instagram session.
"""

import argparse
import asyncio
import logging
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from playwright.async_api import async_playwright, BrowserContext, Page

from watchers.base_watcher import BaseWatcher
from watchers.logger import append_log_entry

logger = logging.getLogger(__name__)

# Business keywords from Company_Handbook.md (Nestaro Pilot)
BUSINESS_KEYWORDS: list[str] = [
    "urgent", "invoice", "payment", "pricing",
    "help", "quote", "project", "deadline",
    "collaboration", "hire", "freelance", "proposal", "contract",
]

KEYWORD_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(kw) for kw in BUSINESS_KEYWORDS) + r")\b",
    re.IGNORECASE,
)

INSTAGRAM_INBOX_URL = "https://www.instagram.com/direct/inbox/"
INSTAGRAM_URL = "https://www.instagram.com/"

# Selectors — Instagram DOM (may change with updates; verified 2026)
SELECTORS = {
    # Login detection
    "login_form": 'input[name="username"], form[method="post"]',
    # DM inbox loaded
    "inbox_loaded": 'div[role="main"], nav[aria-label="Primary"], div[class*="x78zum5"]',
    # Thread list items
    "thread_list": 'div[role="listitem"], a[href*="/direct/t/"]',
    # Unread thread indicator
    "unread_dot": 'div[class*="x1lliihq"]',  # unread blue dot
    # Message text in conversation
    "message_text": 'div[role="row"] span, div[dir="auto"]',
    # Sender username
    "sender_name": 'div[class*="x1dm5mii"] span, h1',
    # CAPTCHA / suspicious login
    "captcha": 'div[class*="challenge"], div[id="challenge"]',
    # Suspicious login modal
    "suspicious_login": 'button:has-text("This Was Me"), div[class*="suspicious"]',
}


def _slugify(text: str) -> str:
    """Convert username to a filesystem-safe slug."""
    slug = re.sub(r"[^\w\s-]", "", text.strip())
    slug = re.sub(r"[\s]+", "_", slug)
    return slug[:50]


def _match_keywords(text: str) -> list[str]:
    """Find all business keywords in message text."""
    matches = KEYWORD_PATTERN.findall(text)
    return list(set(kw.lower() for kw in matches))


class InstagramWatcher(BaseWatcher):
    """Watches Instagram DM inbox for business keyword messages via Playwright.

    Uses persistent Chromium context to maintain Instagram session.
    Polls every 60 seconds for unread DMs with keyword content.
    """

    def __init__(
        self,
        vault_path: str | Path,
        check_interval: int = 60,
        user_data_dir: str = "./playwright-data/instagram",
    ):
        super().__init__(vault_path, check_interval)

        self.user_data_dir = str(Path(user_data_dir).resolve())
        self.needs_action_dir = self.vault_path / "Needs_Action"
        self.log_dir = self.vault_path / "Logs"

        self.needs_action_dir.mkdir(exist_ok=True)
        self.log_dir.mkdir(exist_ok=True)

        self._browser_context: BrowserContext | None = None
        self._page: Page | None = None
        self._processed_keys: set[str] = set()
        self._session_valid = True
        self._auth_alert_written = False

        self._load_processed_keys()

    def _load_processed_keys(self) -> None:
        """Scan vault/Needs_Action/ for existing INSTAGRAM_ files to avoid duplicates."""
        for f in self.needs_action_dir.iterdir():
            if f.is_file() and f.name.startswith("INSTAGRAM_") and f.name.endswith(".md"):
                self._processed_keys.add(f.stem)

        if self._processed_keys:
            logger.info("Loaded %d previously processed Instagram message keys", len(self._processed_keys))

    async def _ensure_browser(self) -> None:
        """Launch or reuse persistent Playwright Chromium context."""
        if self._browser_context is not None:
            return

        pw = await async_playwright().start()
        self._browser_context = await pw.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )

        if self._browser_context.pages:
            self._page = self._browser_context.pages[0]
        else:
            self._page = await self._browser_context.new_page()

        await self._page.goto(INSTAGRAM_INBOX_URL)
        logger.info("Instagram browser launched, navigating to DM inbox")

        try:
            await self._page.wait_for_selector(
                f'{SELECTORS["inbox_loaded"]}, {SELECTORS["login_form"]}',
                timeout=30000,
            )
        except Exception:
            logger.warning("Timeout waiting for Instagram to load")

    def _write_auth_failure_alert(self, event: str = "login_form_detected") -> None:
        """Write SYSTEM_AUTH_FAILURE_INSTAGRAM_{timestamp}.md to Needs_Action/."""
        if self._auth_alert_written:
            return
        existing = list(self.needs_action_dir.glob("SYSTEM_AUTH_FAILURE_INSTAGRAM_*.md"))
        if existing:
            self._auth_alert_written = True
            return

        now = datetime.now(timezone.utc)
        ts = now.strftime("%Y%m%d_%H%M%S")
        iso = now.isoformat()
        filename = f"SYSTEM_AUTH_FAILURE_INSTAGRAM_{ts}.md"

        content = f"""---
type: system
priority: high
status: pending
detected_date: {iso}
event: {event}
---

## Instagram Session Expired

The Instagram watcher detected a `{event}` and has paused.

## Resolution Steps

1. Re-authenticate: `python main.py setup instagram`
2. After successful login, move this file to `vault/Done/`
3. Restart the Instagram watcher: `python main.py instagram`

*Alert generated: {iso}*
"""
        target = self.needs_action_dir / filename
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8",
                dir=self.needs_action_dir, suffix=".tmp", delete=False,
            ) as tmp:
                tmp.write(content)
                tmp_path = Path(tmp.name)
            tmp_path.rename(target)
            self._auth_alert_written = True
            logger.warning("Wrote Instagram auth failure alert: %s", filename)
        except Exception:
            logger.exception("Failed to write Instagram auth failure alert")

    async def _check_login(self) -> bool:
        """Check if Instagram session is valid.

        Returns True if session is expired (login form visible).
        """
        if self._page is None:
            return True

        try:
            login = await self._page.query_selector(SELECTORS["login_form"])
            if login:
                logger.warning("Instagram login form detected — session expired!")
                self._session_valid = False

                append_log_entry(
                    log_dir=self.log_dir,
                    action_type="auth_failure",
                    actor="instagram_watcher",
                    target="instagram_session",
                    parameters={"event": "login_form_detected", "action": "paused"},
                    result="failure",
                )

                self._write_auth_failure_alert("login_form_detected")

                dashboard_path = self.vault_path / "Dashboard.md"
                if dashboard_path.exists():
                    content = dashboard_path.read_text(encoding="utf-8")
                    if "Instagram re-authentication needed" not in content:
                        with open(dashboard_path, "a", encoding="utf-8") as f:
                            f.write(
                                f"\n\n> **ALERT** ({datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}): "
                                "Instagram re-authentication needed. Run `python main.py setup instagram` "
                                "to log in.\n"
                            )
                return True

            captcha = await self._page.query_selector(SELECTORS["captcha"])
            if captcha:
                logger.warning("Instagram CAPTCHA/challenge detected!")
                self._session_valid = False
                append_log_entry(
                    log_dir=self.log_dir,
                    action_type="auth_failure",
                    actor="instagram_watcher",
                    target="instagram_session",
                    parameters={"event": "captcha_detected", "action": "paused"},
                    result="failure",
                )
                self._write_auth_failure_alert("captcha_detected")
                return True

        except Exception:
            logger.exception("Error checking Instagram login state")

        return False

    async def _scan_unread_dms(self) -> list[dict]:
        """Scan Instagram DM inbox for unread messages with business keywords.

        Returns list of message dicts with: contact, message_text, keywords_matched.
        """
        if self._page is None:
            return []

        actionable: list[dict] = []

        try:
            # Ensure we're on the DM inbox page
            current_url = self._page.url
            if "direct/inbox" not in current_url:
                await self._page.goto(INSTAGRAM_INBOX_URL)
                await self._page.wait_for_timeout(3000)

            # Find thread items
            thread_items = await self._page.query_selector_all(SELECTORS["thread_list"])

            for thread in thread_items[:20]:  # Check top 20 threads
                try:
                    # Check for unread indicator
                    unread_indicator = await thread.query_selector('[class*="x3r3jxy"]')  # unread dot class
                    aria_label = await thread.get_attribute("aria-label") or ""
                    is_unread = unread_indicator is not None or "unread" in aria_label.lower()

                    if not is_unread:
                        continue

                    # Get contact name
                    name_el = await thread.query_selector("span")
                    contact_name = "Unknown"
                    if name_el:
                        contact_name = (await name_el.inner_text()).strip() or "Unknown"

                    # Click into the conversation
                    await thread.click()
                    await self._page.wait_for_timeout(2000)

                    # Read message content
                    message_els = await self._page.query_selector_all(SELECTORS["message_text"])

                    for msg_el in message_els[-5:]:
                        text = (await msg_el.inner_text()).strip()
                        if not text or len(text) < 3:
                            continue

                        keywords = _match_keywords(text)
                        if keywords:
                            now = datetime.now(timezone.utc)
                            timestamp = now.strftime("%Y%m%d_%H%M%S")
                            slug = _slugify(contact_name)
                            dedup_key = f"INSTAGRAM_{slug}_{timestamp}"

                            if dedup_key not in self._processed_keys:
                                actionable.append({
                                    "contact": contact_name,
                                    "message_text": text,
                                    "keywords_matched": keywords,
                                    "timestamp": timestamp,
                                    "slug": slug,
                                    "dedup_key": dedup_key,
                                    "platform": "instagram",
                                })
                                break

                    # Go back to inbox
                    await self._page.go_back()
                    await self._page.wait_for_timeout(1000)

                except Exception:
                    logger.exception("Error processing Instagram thread")
                    try:
                        await self._page.goto(INSTAGRAM_INBOX_URL)
                        await self._page.wait_for_timeout(2000)
                    except Exception:
                        pass

        except Exception:
            logger.exception("Error scanning Instagram DMs")
            raise

        if actionable:
            logger.info("Found %d Instagram DM(s) with business keywords", len(actionable))

        return actionable

    def check_for_updates(self) -> list[dict]:
        """Synchronous wrapper — runs async scan via event loop."""
        if not self._session_valid:
            logger.warning("Instagram session invalid — skipping scan (run setup)")
            return []

        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(self._ensure_browser())

            if loop.run_until_complete(self._check_login()):
                return []

            return loop.run_until_complete(self._scan_unread_dms())
        finally:
            loop.close()

    def create_action_file(self, source: dict) -> Path | None:
        """Create INSTAGRAM_ VaultItem in vault/Needs_Action/."""
        dedup_key = source["dedup_key"]

        if dedup_key in self._processed_keys:
            logger.debug("Duplicate Instagram message skipped: %s", dedup_key)
            return None

        priority = "high" if any(kw in ("urgent", "deadline", "payment", "invoice") for kw in source["keywords_matched"]) else "medium"

        now = datetime.now(timezone.utc).isoformat()
        keywords_yaml = str(source["keywords_matched"])

        content = f"""---
type: instagram
platform: instagram
contact: "{source['contact']}"
message_text: "{source['message_text'].replace('"', '\\"')}"
keywords_matched: {keywords_yaml}
detected_date: {now}
priority: {priority}
status: pending
---

## Message Details

- **From**: {source['contact']} (Instagram DM)
- **Message**: {source['message_text']}
- **Keywords**: {', '.join(source['keywords_matched'])}

## Suggested Actions

- [ ] Review and respond to this DM (approval required — all Instagram replies need HITL)
"""

        filename = f"{dedup_key}.md"
        target_path = self.needs_action_dir / filename

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.needs_action_dir,
                suffix=".tmp",
                delete=False,
            ) as tmp:
                tmp.write(content)
                tmp_path = Path(tmp.name)

            tmp_path.rename(target_path)
        except Exception:
            if "tmp_path" in locals() and tmp_path.exists():
                tmp_path.unlink()
            raise

        self._processed_keys.add(dedup_key)

        logger.info(
            "Created %s (priority=%s, keywords=%s, from=%s)",
            filename, priority, source["keywords_matched"], source["contact"],
        )

        append_log_entry(
            log_dir=self.log_dir,
            action_type="instagram_triage",
            actor="instagram_watcher",
            target=filename,
            parameters={
                "contact": source["contact"],
                "keywords": source["keywords_matched"],
                "priority": priority,
            },
            result="success",
        )

        return target_path

    def _get_source_name(self, source: dict) -> str:
        return f"{source.get('contact', 'unknown')}:{source.get('keywords_matched', [])}"


# --- CLI entry point ---

async def _setup_session(user_data_dir: str) -> None:
    """Interactive setup — open Instagram for manual login."""
    logger.info("Opening Instagram for login setup...")
    logger.info("Log in manually, then press Ctrl+C to exit after session is saved.")

    pw = await async_playwright().start()
    context = await pw.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
    )

    page = context.pages[0] if context.pages else await context.new_page()
    await page.goto(INSTAGRAM_INBOX_URL)

    logger.info("Waiting for manual login... (Ctrl+C to exit after logging in)")

    try:
        await page.wait_for_selector(SELECTORS["inbox_loaded"], timeout=120000)
        logger.info("Instagram login successful! Session saved to %s", user_data_dir)
    except Exception:
        logger.warning("Timeout waiting for login. Try again with --setup.")
    finally:
        await context.close()
        await pw.stop()


def main() -> None:
    """Run the Instagram watcher from command line."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    parser = argparse.ArgumentParser(description="Instagram Watcher — monitor DMs for business messages")
    parser.add_argument("--setup", action="store_true", help="Open Instagram for first-time login setup")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    load_dotenv(repo_root / ".env")

    vault_path = Path(os.getenv("VAULT_PATH", repo_root / "vault"))
    if not vault_path.is_absolute():
        vault_path = repo_root / vault_path

    user_data_dir = os.getenv("INSTAGRAM_USER_DATA_DIR", str(repo_root / "playwright-data" / "instagram"))
    poll_interval = int(os.getenv("INSTAGRAM_POLL_INTERVAL", "60"))

    if args.setup:
        asyncio.run(_setup_session(user_data_dir))
        return

    logger.info("Vault path: %s", vault_path)

    watcher = InstagramWatcher(
        vault_path=vault_path,
        check_interval=poll_interval,
        user_data_dir=user_data_dir,
    )

    append_log_entry(
        log_dir=vault_path / "Logs",
        action_type="instagram_triage",
        actor="instagram_watcher",
        target="instagram_watcher",
        parameters={"event": "start", "poll_interval": poll_interval},
        result="success",
    )

    try:
        watcher.run()
    except KeyboardInterrupt:
        pass
    finally:
        append_log_entry(
            log_dir=vault_path / "Logs",
            action_type="instagram_triage",
            actor="instagram_watcher",
            target="instagram_watcher",
            parameters={"event": "stop"},
            result="success",
        )


if __name__ == "__main__":
    main()
