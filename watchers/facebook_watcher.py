"""Facebook watcher: monitors Facebook Messenger for business keyword messages via Playwright.

Extends BaseWatcher to scan Facebook messages/notifications for unread messages
containing business keywords, create FACEBOOK_ VaultItems in vault/Needs_Action/.

Uses persistent Chromium context to maintain Facebook session.
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

FACEBOOK_MESSAGES_URL = "https://www.facebook.com/messages/"
FACEBOOK_URL = "https://www.facebook.com/"

# Selectors — Facebook DOM (may change with updates; verified 2026)
SELECTORS = {
    # Login detection
    "login_form": 'input[name="email"], #email, form[action*="login"]',
    # Messenger inbox loaded
    "inbox_loaded": 'div[aria-label="Chats"], div[role="main"]',
    # Chat thread rows with unread indicator
    "unread_thread": 'div[aria-label*="unread"], a[aria-label*="unread"]',
    # Generic thread list items
    "thread_list": 'div[role="listitem"]',
    # Message text in open conversation
    "message_text": 'div[data-scope="messages_table"] span, div[dir="auto"]',
    # Sender name in thread
    "sender_name": 'div[aria-label*="conversation"] h3, span[dir="auto"]',
    # CAPTCHA detection
    "captcha": 'div[id="checkpoint"], div[class*="captcha"]',
}


def _slugify(text: str) -> str:
    """Convert contact name to a filesystem-safe slug."""
    slug = re.sub(r"[^\w\s-]", "", text.strip())
    slug = re.sub(r"[\s]+", "_", slug)
    return slug[:50]


def _match_keywords(text: str) -> list[str]:
    """Find all business keywords in message text."""
    matches = KEYWORD_PATTERN.findall(text)
    return list(set(kw.lower() for kw in matches))


class FacebookWatcher(BaseWatcher):
    """Watches Facebook Messenger for business keyword messages via Playwright.

    Uses persistent Chromium context to maintain Facebook session.
    Polls every 60 seconds for unread messages with keyword content.
    """

    def __init__(
        self,
        vault_path: str | Path,
        check_interval: int = 60,
        user_data_dir: str = "./playwright-data/facebook",
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
        self._auth_alert_written = False  # idempotent SYSTEM_ file guard

        # Load already-processed message keys from existing vault files
        self._load_processed_keys()

    def _load_processed_keys(self) -> None:
        """Scan vault/Needs_Action/ for existing FACEBOOK_ files to avoid duplicates."""
        for f in self.needs_action_dir.iterdir():
            if f.is_file() and f.name.startswith("FACEBOOK_") and f.name.endswith(".md"):
                self._processed_keys.add(f.stem)

        if self._processed_keys:
            logger.info("Loaded %d previously processed Facebook message keys", len(self._processed_keys))

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

        await self._page.goto(FACEBOOK_MESSAGES_URL)
        logger.info("Facebook browser launched, navigating to Messenger")

        # Wait for either inbox or login
        try:
            await self._page.wait_for_selector(
                f'{SELECTORS["inbox_loaded"]}, {SELECTORS["login_form"]}',
                timeout=30000,
            )
        except Exception:
            logger.warning("Timeout waiting for Facebook to load")

    def _write_auth_failure_alert(self, event: str = "login_form_detected") -> None:
        """Write SYSTEM_AUTH_FAILURE_FACEBOOK_{timestamp}.md to Needs_Action/.

        Idempotent — writes only once per watcher session.
        """
        if self._auth_alert_written:
            return

        existing = list(self.needs_action_dir.glob("SYSTEM_AUTH_FAILURE_FACEBOOK_*.md"))
        if existing:
            self._auth_alert_written = True
            return

        now = datetime.now(timezone.utc)
        ts = now.strftime("%Y%m%d_%H%M%S")
        iso = now.isoformat()
        filename = f"SYSTEM_AUTH_FAILURE_FACEBOOK_{ts}.md"

        content = f"""---
type: system
priority: high
status: pending
detected_date: {iso}
event: {event}
---

## Facebook Session Expired

The Facebook watcher detected a `{event}` and has paused.

## Resolution Steps

1. Re-authenticate: `python main.py setup facebook`
2. After successful login, move this file to `vault/Done/`
3. Restart the Facebook watcher: `python main.py facebook`

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
            logger.warning("Wrote Facebook auth failure alert: %s", filename)
        except Exception:
            logger.exception("Failed to write Facebook auth failure alert")

    async def _check_login(self) -> bool:
        """Check if Facebook session is valid.

        Returns True if session is expired (login form visible).
        """
        if self._page is None:
            return True

        try:
            login = await self._page.query_selector(SELECTORS["login_form"])
            if login:
                logger.warning("Facebook login form detected — session expired!")
                self._session_valid = False

                append_log_entry(
                    log_dir=self.log_dir,
                    action_type="auth_failure",
                    actor="facebook_watcher",
                    target="facebook_session",
                    parameters={"event": "login_form_detected", "action": "paused"},
                    result="failure",
                )

                self._write_auth_failure_alert("login_form_detected")

                dashboard_path = self.vault_path / "Dashboard.md"
                if dashboard_path.exists():
                    content = dashboard_path.read_text(encoding="utf-8")
                    if "Facebook re-authentication needed" not in content:
                        with open(dashboard_path, "a", encoding="utf-8") as f:
                            f.write(
                                f"\n\n> **ALERT** ({datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}): "
                                "Facebook re-authentication needed. Run `python main.py setup facebook` "
                                "to log in.\n"
                            )
                return True

            captcha = await self._page.query_selector(SELECTORS["captcha"])
            if captcha:
                logger.warning("Facebook CAPTCHA/checkpoint detected!")
                self._session_valid = False
                append_log_entry(
                    log_dir=self.log_dir,
                    action_type="auth_failure",
                    actor="facebook_watcher",
                    target="facebook_session",
                    parameters={"event": "captcha_detected", "action": "paused"},
                    result="failure",
                )
                self._write_auth_failure_alert("captcha_detected")
                return True

        except Exception:
            logger.exception("Error checking Facebook login state")

        return False

    async def _scan_unread_messages(self) -> list[dict]:
        """Scan Facebook Messenger for unread messages with business keywords.

        Returns list of message dicts with: contact, message_text, keywords_matched.
        """
        if self._page is None:
            return []

        actionable: list[dict] = []

        try:
            # Navigate to Messenger inbox
            current_url = self._page.url
            if "messages" not in current_url:
                await self._page.goto(FACEBOOK_MESSAGES_URL)
                await self._page.wait_for_timeout(3000)

            # Look for unread threads
            thread_items = await self._page.query_selector_all(SELECTORS["thread_list"])

            for thread in thread_items:
                # Check for unread indicator (bold text or aria-label with "unread")
                aria_label = await thread.get_attribute("aria-label") or ""
                is_unread = "unread" in aria_label.lower()

                if not is_unread:
                    # Try to detect bold/unread styling by checking aria labels on child elements
                    unread_el = await thread.query_selector('[aria-label*="unread"]')
                    is_unread = unread_el is not None

                if not is_unread:
                    continue

                # Get contact name
                name_el = await thread.query_selector("span[dir='auto'], h3")
                contact_name = "Unknown"
                if name_el:
                    contact_name = (await name_el.inner_text()).strip() or "Unknown"

                # Click into the thread to read messages
                try:
                    await thread.click()
                    await self._page.wait_for_timeout(2000)
                except Exception:
                    continue

                # Read message content
                message_els = await self._page.query_selector_all(SELECTORS["message_text"])

                for msg_el in message_els[-5:]:
                    try:
                        text = (await msg_el.inner_text()).strip()
                        if not text or len(text) < 3:
                            continue

                        keywords = _match_keywords(text)
                        if keywords:
                            now = datetime.now(timezone.utc)
                            timestamp = now.strftime("%Y%m%d_%H%M%S")
                            slug = _slugify(contact_name)
                            dedup_key = f"FACEBOOK_{slug}_{timestamp}"

                            if dedup_key not in self._processed_keys:
                                actionable.append({
                                    "contact": contact_name,
                                    "message_text": text,
                                    "keywords_matched": keywords,
                                    "timestamp": timestamp,
                                    "slug": slug,
                                    "dedup_key": dedup_key,
                                    "platform": "facebook",
                                })
                                break
                    except Exception:
                        continue

                # Go back to inbox
                try:
                    await self._page.go_back()
                    await self._page.wait_for_timeout(1000)
                except Exception:
                    await self._page.goto(FACEBOOK_MESSAGES_URL)
                    await self._page.wait_for_timeout(2000)

        except Exception:
            logger.exception("Error scanning Facebook messages")
            raise  # Let BaseWatcher handle backoff

        if actionable:
            logger.info("Found %d Facebook message(s) with business keywords", len(actionable))

        return actionable

    def check_for_updates(self) -> list[dict]:
        """Synchronous wrapper — runs async scan via event loop."""
        if not self._session_valid:
            logger.warning("Facebook session invalid — skipping scan (run setup)")
            return []

        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(self._ensure_browser())

            if loop.run_until_complete(self._check_login()):
                return []

            return loop.run_until_complete(self._scan_unread_messages())
        finally:
            loop.close()

    def create_action_file(self, source: dict) -> Path | None:
        """Create FACEBOOK_ VaultItem in vault/Needs_Action/.

        Args:
            source: Message dict from check_for_updates().

        Returns:
            Path to the created .md file, or None if duplicate.
        """
        dedup_key = source["dedup_key"]

        if dedup_key in self._processed_keys:
            logger.debug("Duplicate Facebook message skipped: %s", dedup_key)
            return None

        priority = "high" if any(kw in ("urgent", "deadline", "payment", "invoice") for kw in source["keywords_matched"]) else "medium"

        now = datetime.now(timezone.utc).isoformat()
        keywords_yaml = str(source["keywords_matched"])

        content = f"""---
type: facebook
platform: facebook
contact: "{source['contact']}"
message_text: "{source['message_text'].replace('"', '\\"')}"
keywords_matched: {keywords_yaml}
detected_date: {now}
priority: {priority}
status: pending
---

## Message Details

- **From**: {source['contact']} (Facebook Messenger)
- **Message**: {source['message_text']}
- **Keywords**: {', '.join(source['keywords_matched'])}

## Suggested Actions

- [ ] Review and respond to this message (approval required — all Facebook replies need HITL)
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
            action_type="facebook_triage",
            actor="facebook_watcher",
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
    """Interactive setup — open Facebook for manual login."""
    logger.info("Opening Facebook for login setup...")
    logger.info("Log in manually, then press Ctrl+C to exit after session is saved.")

    pw = await async_playwright().start()
    context = await pw.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
    )

    page = context.pages[0] if context.pages else await context.new_page()
    await page.goto(FACEBOOK_MESSAGES_URL)

    logger.info("Waiting for manual login... (Ctrl+C to exit after logging in)")

    try:
        await page.wait_for_selector(SELECTORS["inbox_loaded"], timeout=120000)
        logger.info("Facebook login successful! Session saved to %s", user_data_dir)
    except Exception:
        logger.warning("Timeout waiting for login. Try again with --setup.")
    finally:
        await context.close()
        await pw.stop()


def main() -> None:
    """Run the Facebook watcher from command line."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    parser = argparse.ArgumentParser(description="Facebook Watcher — monitor Messenger for business messages")
    parser.add_argument("--setup", action="store_true", help="Open Facebook for first-time login setup")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    load_dotenv(repo_root / ".env")

    vault_path = Path(os.getenv("VAULT_PATH", repo_root / "vault"))
    if not vault_path.is_absolute():
        vault_path = repo_root / vault_path

    user_data_dir = os.getenv("FACEBOOK_USER_DATA_DIR", str(repo_root / "playwright-data" / "facebook"))
    poll_interval = int(os.getenv("FACEBOOK_POLL_INTERVAL", "60"))

    if args.setup:
        asyncio.run(_setup_session(user_data_dir))
        return

    logger.info("Vault path: %s", vault_path)
    logger.info("User data dir: %s", user_data_dir)
    logger.info("Poll interval: %ds", poll_interval)

    watcher = FacebookWatcher(
        vault_path=vault_path,
        check_interval=poll_interval,
        user_data_dir=user_data_dir,
    )

    append_log_entry(
        log_dir=vault_path / "Logs",
        action_type="facebook_triage",
        actor="facebook_watcher",
        target="facebook_watcher",
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
            action_type="facebook_triage",
            actor="facebook_watcher",
            target="facebook_watcher",
            parameters={"event": "stop"},
            result="success",
        )


if __name__ == "__main__":
    main()
