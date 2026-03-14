"""Twitter/X watcher: monitors Twitter/X notifications and DMs for business keyword messages via Playwright.

Extends BaseWatcher to scan Twitter/X notifications and direct messages for
unread messages containing business keywords, create TWITTER_ VaultItems in vault/Needs_Action/.

Uses persistent Chromium context to maintain Twitter/X session.
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

# Business keywords from Company_Handbook.md (Gold)
BUSINESS_KEYWORDS: list[str] = [
    "urgent", "invoice", "payment", "pricing",
    "help", "quote", "project", "deadline",
    "collaboration", "hire", "freelance", "proposal", "contract",
]

KEYWORD_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(kw) for kw in BUSINESS_KEYWORDS) + r")\b",
    re.IGNORECASE,
)

TWITTER_HOME_URL = "https://twitter.com/home"
TWITTER_MESSAGES_URL = "https://twitter.com/messages"
TWITTER_NOTIFICATIONS_URL = "https://twitter.com/notifications/mentions"

# Selectors — Twitter/X DOM (may change with updates; verified 2026)
SELECTORS = {
    # Login detection
    "login_form": 'input[autocomplete="username"], div[data-testid="LoginForm"]',
    # Home/timeline loaded
    "home_loaded": 'div[data-testid="primaryColumn"], div[aria-label="Timeline"]',
    # DM conversation list
    "dm_list": 'div[data-testid="conversation"]',
    # Unread DM indicator
    "dm_unread": 'div[data-testid="conversation"] div[class*="unread"]',
    # Tweet text in notifications or DM
    "tweet_text": 'div[data-testid="tweetText"], div[data-testid="messageEntry"]',
    # Notification tweet content
    "notification_item": 'article[data-testid="tweet"]',
    # Sender name/handle
    "sender_handle": 'div[data-testid="User-Name"] span',
    # CAPTCHA/verification
    "captcha": 'div[data-testid="ChallengeForm"], div[class*="challenge"]',
    # Message compose box
    "compose_box": 'div[data-testid="dmComposerTextInput"]',
    # Send button
    "send_button": 'div[data-testid="dmComposerSendButton"]',
}


def _slugify(text: str) -> str:
    """Convert handle/name to a filesystem-safe slug."""
    slug = re.sub(r"[^\w\s-]", "", text.strip().lstrip("@"))
    slug = re.sub(r"[\s]+", "_", slug)
    return slug[:50]


def _match_keywords(text: str) -> list[str]:
    """Find all business keywords in message text."""
    matches = KEYWORD_PATTERN.findall(text)
    return list(set(kw.lower() for kw in matches))


class TwitterWatcher(BaseWatcher):
    """Watches Twitter/X notifications and DMs for business keyword messages via Playwright.

    Polls:
    1. /notifications/mentions — for @mentions with business keywords
    2. /messages — for DMs with business keywords

    Uses persistent Chromium context to maintain Twitter/X session.
    """

    def __init__(
        self,
        vault_path: str | Path,
        check_interval: int = 60,
        user_data_dir: str = "./playwright-data/twitter",
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
        """Scan vault/Needs_Action/ for existing TWITTER_ files to avoid duplicates."""
        for f in self.needs_action_dir.iterdir():
            if f.is_file() and f.name.startswith("TWITTER_") and f.name.endswith(".md"):
                self._processed_keys.add(f.stem)

        if self._processed_keys:
            logger.info("Loaded %d previously processed Twitter message keys", len(self._processed_keys))

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

        await self._page.goto(TWITTER_HOME_URL)
        logger.info("Twitter/X browser launched")

        try:
            await self._page.wait_for_selector(
                f'{SELECTORS["home_loaded"]}, {SELECTORS["login_form"]}',
                timeout=30000,
            )
        except Exception:
            logger.warning("Timeout waiting for Twitter/X to load")

    def _write_auth_failure_alert(self, event: str = "login_form_detected") -> None:
        """Write SYSTEM_AUTH_FAILURE_TWITTER_{timestamp}.md to Needs_Action/."""
        if self._auth_alert_written:
            return
        existing = list(self.needs_action_dir.glob("SYSTEM_AUTH_FAILURE_TWITTER_*.md"))
        if existing:
            self._auth_alert_written = True
            return

        now = datetime.now(timezone.utc)
        ts = now.strftime("%Y%m%d_%H%M%S")
        iso = now.isoformat()
        filename = f"SYSTEM_AUTH_FAILURE_TWITTER_{ts}.md"

        content = f"""---
type: system
priority: high
status: pending
detected_date: {iso}
event: {event}
---

## Twitter/X Session Expired

The Twitter/X watcher detected a `{event}` and has paused.

## Resolution Steps

1. Re-authenticate: `python main.py setup twitter`
2. After successful login, move this file to `vault/Done/`
3. Restart the Twitter/X watcher: `python main.py twitter`

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
            logger.warning("Wrote Twitter auth failure alert: %s", filename)
        except Exception:
            logger.exception("Failed to write Twitter auth failure alert")

    async def _check_login(self) -> bool:
        """Check if Twitter/X session is valid.

        Returns True if session is expired.
        """
        if self._page is None:
            return True

        try:
            login = await self._page.query_selector(SELECTORS["login_form"])
            if login:
                logger.warning("Twitter/X login form detected — session expired!")
                self._session_valid = False

                append_log_entry(
                    log_dir=self.log_dir,
                    action_type="auth_failure",
                    actor="twitter_watcher",
                    target="twitter_session",
                    parameters={"event": "login_form_detected", "action": "paused"},
                    result="failure",
                )

                self._write_auth_failure_alert("login_form_detected")

                dashboard_path = self.vault_path / "Dashboard.md"
                if dashboard_path.exists():
                    content = dashboard_path.read_text(encoding="utf-8")
                    if "Twitter/X re-authentication needed" not in content:
                        with open(dashboard_path, "a", encoding="utf-8") as f:
                            f.write(
                                f"\n\n> **ALERT** ({datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}): "
                                "Twitter/X re-authentication needed. Run `python main.py setup twitter` "
                                "to log in.\n"
                            )
                return True

            captcha = await self._page.query_selector(SELECTORS["captcha"])
            if captcha:
                logger.warning("Twitter/X CAPTCHA/challenge detected!")
                self._session_valid = False
                append_log_entry(
                    log_dir=self.log_dir,
                    action_type="auth_failure",
                    actor="twitter_watcher",
                    target="twitter_session",
                    parameters={"event": "captcha_detected", "action": "paused"},
                    result="failure",
                )
                self._write_auth_failure_alert("captcha_detected")
                return True

        except Exception:
            logger.exception("Error checking Twitter/X login state")

        return False

    async def _scan_notifications(self) -> list[dict]:
        """Scan @mentions for business keywords."""
        if self._page is None:
            return []

        actionable: list[dict] = []

        try:
            await self._page.goto(TWITTER_NOTIFICATIONS_URL)
            await self._page.wait_for_timeout(3000)

            tweets = await self._page.query_selector_all(SELECTORS["notification_item"])

            for tweet in tweets[:20]:
                try:
                    text_el = await tweet.query_selector(SELECTORS["tweet_text"])
                    if not text_el:
                        continue

                    text = (await text_el.inner_text()).strip()
                    keywords = _match_keywords(text)

                    if not keywords:
                        continue

                    # Get sender handle
                    sender_el = await tweet.query_selector(SELECTORS["sender_handle"])
                    sender = "@unknown"
                    if sender_el:
                        sender = (await sender_el.inner_text()).strip() or "@unknown"

                    now = datetime.now(timezone.utc)
                    timestamp = now.strftime("%Y%m%d_%H%M%S")
                    slug = _slugify(sender)
                    dedup_key = f"TWITTER_{slug}_{timestamp}"

                    if dedup_key not in self._processed_keys:
                        actionable.append({
                            "contact": sender,
                            "message_text": text[:280],  # Twitter char limit
                            "keywords_matched": keywords,
                            "timestamp": timestamp,
                            "slug": slug,
                            "dedup_key": dedup_key,
                            "platform": "twitter",
                            "source_type": "mention",
                        })
                        self._processed_keys.add(dedup_key)  # Pre-mark to avoid DM duplicates

                except Exception:
                    continue

        except Exception:
            logger.exception("Error scanning Twitter notifications")
            raise

        return actionable

    async def _scan_dms(self) -> list[dict]:
        """Scan DMs for business keywords."""
        if self._page is None:
            return []

        actionable: list[dict] = []

        try:
            await self._page.goto(TWITTER_MESSAGES_URL)
            await self._page.wait_for_timeout(3000)

            conversations = await self._page.query_selector_all(SELECTORS["dm_list"])

            for conv in conversations[:20]:
                try:
                    # Check for unread indicator
                    aria_label = await conv.get_attribute("aria-label") or ""
                    # Twitter marks unread conversations differently
                    # Look for unread count or bold styling
                    text_el = await conv.query_selector(SELECTORS["tweet_text"])
                    if not text_el:
                        continue

                    preview_text = (await text_el.inner_text()).strip()
                    keywords = _match_keywords(preview_text)

                    if not keywords:
                        continue

                    # Get sender info
                    sender_el = await conv.query_selector(SELECTORS["sender_handle"])
                    sender = "@unknown"
                    if sender_el:
                        sender = (await sender_el.inner_text()).strip() or "@unknown"

                    now = datetime.now(timezone.utc)
                    timestamp = now.strftime("%Y%m%d_%H%M%S")
                    slug = _slugify(sender)
                    dedup_key = f"TWITTER_{slug}_{timestamp}_dm"

                    if dedup_key not in self._processed_keys:
                        actionable.append({
                            "contact": sender,
                            "message_text": preview_text[:280],
                            "keywords_matched": keywords,
                            "timestamp": timestamp,
                            "slug": slug,
                            "dedup_key": dedup_key,
                            "platform": "twitter",
                            "source_type": "dm",
                        })

                except Exception:
                    continue

        except Exception:
            logger.exception("Error scanning Twitter DMs")
            raise

        return actionable

    def check_for_updates(self) -> list[dict]:
        """Synchronous wrapper — scans mentions then DMs."""
        if not self._session_valid:
            logger.warning("Twitter/X session invalid — skipping scan (run setup)")
            return []

        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(self._ensure_browser())

            if loop.run_until_complete(self._check_login()):
                return []

            mentions = loop.run_until_complete(self._scan_notifications())
            dms = loop.run_until_complete(self._scan_dms())
            return mentions + dms
        finally:
            loop.close()

    def create_action_file(self, source: dict) -> Path | None:
        """Create TWITTER_ VaultItem in vault/Needs_Action/."""
        dedup_key = source["dedup_key"]

        if dedup_key in self._processed_keys:
            logger.debug("Duplicate Twitter message skipped: %s", dedup_key)
            return None

        priority = "high" if any(kw in ("urgent", "deadline", "payment", "invoice") for kw in source["keywords_matched"]) else "medium"

        now = datetime.now(timezone.utc).isoformat()
        keywords_yaml = str(source["keywords_matched"])
        source_type = source.get("source_type", "unknown")

        content = f"""---
type: twitter
platform: twitter
contact: "{source['contact']}"
message_text: "{source['message_text'].replace('"', '\\"')}"
keywords_matched: {keywords_yaml}
source_type: "{source_type}"
detected_date: {now}
priority: {priority}
status: pending
---

## Message Details

- **From**: {source['contact']} (Twitter/X {source_type})
- **Message**: {source['message_text']}
- **Keywords**: {', '.join(source['keywords_matched'])}
- **Type**: {source_type}

## Suggested Actions

- [ ] Review and respond to this {source_type} (approval required — all Twitter/X replies need HITL)
- [ ] Note: Twitter reply must be ≤ 280 characters
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
            "Created %s (priority=%s, keywords=%s, from=%s, type=%s)",
            filename, priority, source["keywords_matched"], source["contact"], source_type,
        )

        append_log_entry(
            log_dir=self.log_dir,
            action_type="twitter_triage",
            actor="twitter_watcher",
            target=filename,
            parameters={
                "contact": source["contact"],
                "keywords": source["keywords_matched"],
                "priority": priority,
                "source_type": source_type,
            },
            result="success",
        )

        return target_path

    def _get_source_name(self, source: dict) -> str:
        return f"{source.get('contact', 'unknown')}:{source.get('source_type', '')}:{source.get('keywords_matched', [])}"


# --- CLI entry point ---

async def _setup_session(user_data_dir: str) -> None:
    """Interactive setup — open Twitter/X for manual login."""
    logger.info("Opening Twitter/X for login setup...")
    logger.info("Log in manually, then press Ctrl+C to exit after session is saved.")

    pw = await async_playwright().start()
    context = await pw.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
    )

    page = context.pages[0] if context.pages else await context.new_page()
    await page.goto(TWITTER_HOME_URL)

    logger.info("Waiting for manual login... (Ctrl+C to exit after logging in)")

    try:
        await page.wait_for_selector(SELECTORS["home_loaded"], timeout=120000)
        logger.info("Twitter/X login successful! Session saved to %s", user_data_dir)
    except Exception:
        logger.warning("Timeout waiting for login. Try again with --setup.")
    finally:
        await context.close()
        await pw.stop()


def main() -> None:
    """Run the Twitter watcher from command line."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    parser = argparse.ArgumentParser(description="Twitter/X Watcher — monitor mentions and DMs for business messages")
    parser.add_argument("--setup", action="store_true", help="Open Twitter/X for first-time login setup")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    load_dotenv(repo_root / ".env")

    vault_path = Path(os.getenv("VAULT_PATH", repo_root / "vault"))
    if not vault_path.is_absolute():
        vault_path = repo_root / vault_path

    user_data_dir = os.getenv("TWITTER_USER_DATA_DIR", str(repo_root / "playwright-data" / "twitter"))
    poll_interval = int(os.getenv("TWITTER_POLL_INTERVAL", "60"))

    if args.setup:
        asyncio.run(_setup_session(user_data_dir))
        return

    logger.info("Vault path: %s", vault_path)

    watcher = TwitterWatcher(
        vault_path=vault_path,
        check_interval=poll_interval,
        user_data_dir=user_data_dir,
    )

    append_log_entry(
        log_dir=vault_path / "Logs",
        action_type="twitter_triage",
        actor="twitter_watcher",
        target="twitter_watcher",
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
            action_type="twitter_triage",
            actor="twitter_watcher",
            target="twitter_watcher",
            parameters={"event": "stop"},
            result="success",
        )


if __name__ == "__main__":
    main()
