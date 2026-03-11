"""WhatsApp watcher: monitors WhatsApp Web for business keyword messages via Playwright.

Extends BaseWatcher to scan WhatsApp Web for unread messages containing
business keywords, create WHATSAPP_ VaultItems in vault/Needs_Action/,
and send replies via Playwright after approval.
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

# Business keywords from Company_Handbook.md
BUSINESS_KEYWORDS: list[str] = [
    "urgent", "invoice", "payment", "pricing",
    "help", "quote", "project", "deadline",
]

KEYWORD_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(kw) for kw in BUSINESS_KEYWORDS) + r")\b",
    re.IGNORECASE,
)

WHATSAPP_URL = "https://web.whatsapp.com"

# Selectors — WhatsApp Web DOM (may change with updates)
# These target the 2026 WhatsApp Web layout
SELECTORS = {
    "chat_list": 'div[aria-label="Chat list"]',
    "unread_badge": 'span[data-testid="icon-unread-count"]',
    "chat_row": 'div[data-testid="cell-frame-container"]',
    "message_in": 'div.message-in',
    "message_text": 'span.selectable-text',
    "contact_name": 'span[data-testid="conversation-info-header-chat-title"]',
    "message_input": 'div[data-testid="conversation-compose-box-input"]',
    "send_button": 'button[data-testid="send"]',
    "qr_canvas": 'canvas[aria-label="Scan this QR code to link a device!"]',
    "search_box": 'div[data-testid="chat-list-search"]',
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


class WhatsAppWatcher(BaseWatcher):
    """Watches WhatsApp Web for business keyword messages via Playwright.

    Uses persistent Chromium context to maintain WhatsApp session.
    Polls every 30 seconds for unread chats with keyword messages.
    """

    def __init__(
        self,
        vault_path: str | Path,
        check_interval: int = 30,
        user_data_dir: str = "./playwright-data/whatsapp",
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

        # Load already-processed message keys from existing vault files
        self._load_processed_keys()

    def _load_processed_keys(self) -> None:
        """Scan vault/Needs_Action/ for existing WHATSAPP_ files to avoid duplicates."""
        for f in self.needs_action_dir.iterdir():
            if f.is_file() and f.name.startswith("WHATSAPP_") and f.name.endswith(".md"):
                # Key is the stem: WHATSAPP_{contact}_{timestamp}
                self._processed_keys.add(f.stem)

        if self._processed_keys:
            logger.info("Loaded %d previously processed WhatsApp message keys", len(self._processed_keys))

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

        # Use first page or create one
        if self._browser_context.pages:
            self._page = self._browser_context.pages[0]
        else:
            self._page = await self._browser_context.new_page()

        await self._page.goto(WHATSAPP_URL)
        logger.info("Playwright browser launched, navigating to WhatsApp Web")

        # Wait for either chat list or QR code
        try:
            await self._page.wait_for_selector(
                f'{SELECTORS["chat_list"]}, {SELECTORS["qr_canvas"]}',
                timeout=30000,
            )
        except Exception:
            logger.warning("Timeout waiting for WhatsApp Web to load")

    async def _check_qr_code(self) -> bool:
        """T028: Check if QR code screen is displayed (session expired).

        Returns True if QR code is visible (session invalid).
        """
        if self._page is None:
            return True

        try:
            qr = await self._page.query_selector(SELECTORS["qr_canvas"])
            if qr:
                logger.warning("WhatsApp QR code detected — session expired!")
                self._session_valid = False

                # Log alert
                append_log_entry(
                    log_dir=self.log_dir,
                    action_type="error",
                    actor="whatsapp_watcher",
                    target="whatsapp_session",
                    parameters={"event": "qr_code_detected", "action": "paused"},
                    result="failure",
                )

                # Update Dashboard.md with re-auth message
                dashboard_path = self.vault_path / "Dashboard.md"
                if dashboard_path.exists():
                    content = dashboard_path.read_text(encoding="utf-8")
                    if "WhatsApp re-authentication needed" not in content:
                        with open(dashboard_path, "a", encoding="utf-8") as f:
                            f.write(
                                f"\n\n> **ALERT** ({datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}): "
                                "WhatsApp re-authentication needed. Run `python -m watchers.whatsapp_watcher --setup` "
                                "to scan QR code.\n"
                            )

                return True
        except Exception:
            logger.exception("Error checking for QR code")

        return False

    async def _scan_unread_chats(self) -> list[dict]:
        """Scan WhatsApp Web for unread chats with business keyword messages.

        Returns list of message dicts with: contact, phone, message_text, keywords_matched.
        """
        if self._page is None:
            return []

        actionable: list[dict] = []

        try:
            # Find all chat rows with unread badges
            chat_rows = await self._page.query_selector_all(SELECTORS["chat_row"])

            for row in chat_rows:
                # Check for unread badge
                badge = await row.query_selector(SELECTORS["unread_badge"])
                if not badge:
                    continue

                # Get contact name from the chat row
                name_el = await row.query_selector("span[title]")
                if not name_el:
                    continue
                contact_name = await name_el.get_attribute("title") or "Unknown"

                # Click into the chat to read messages
                await row.click()
                await self._page.wait_for_timeout(1000)  # Wait for chat to load

                # Read the latest incoming messages
                messages = await self._page.query_selector_all(SELECTORS["message_in"])

                # Check the last few messages for keywords
                for msg_el in messages[-5:]:  # Check last 5 messages
                    text_el = await msg_el.query_selector(SELECTORS["message_text"])
                    if not text_el:
                        continue

                    text = await text_el.inner_text()
                    keywords = _match_keywords(text)

                    if keywords:
                        # Extract timestamp from message metadata if available
                        time_el = await msg_el.query_selector("span[data-testid='msg-time']")
                        msg_time = ""
                        if time_el:
                            msg_time = await time_el.inner_text()

                        now = datetime.now(timezone.utc)
                        timestamp = now.strftime("%Y%m%d_%H%M%S")

                        # Build dedup key
                        slug = _slugify(contact_name)
                        dedup_key = f"WHATSAPP_{slug}_{timestamp}"

                        if dedup_key not in self._processed_keys:
                            actionable.append({
                                "contact": contact_name,
                                "phone": "",  # WhatsApp Web doesn't always show phone
                                "message_text": text,
                                "keywords_matched": keywords,
                                "timestamp": timestamp,
                                "slug": slug,
                                "dedup_key": dedup_key,
                            })
                            # Only capture first keyword match per chat per cycle
                            break

        except Exception:
            logger.exception("Error scanning unread chats")
            raise  # Let BaseWatcher handle backoff

        if actionable:
            logger.info("Found %d WhatsApp message(s) with business keywords", len(actionable))

        return actionable

    def check_for_updates(self) -> list[dict]:
        """Synchronous wrapper — runs async scan via event loop."""
        if not self._session_valid:
            logger.warning("WhatsApp session invalid — skipping scan (run --setup)")
            return []

        loop = asyncio.new_event_loop()
        try:
            # Ensure browser is running
            loop.run_until_complete(self._ensure_browser())

            # Check for QR code (session expiry)
            if loop.run_until_complete(self._check_qr_code()):
                return []

            # Scan for unread keyword messages
            return loop.run_until_complete(self._scan_unread_chats())
        finally:
            loop.close()

    def create_action_file(self, source: dict) -> Path | None:
        """Create WHATSAPP_ VaultItem in vault/Needs_Action/.

        Args:
            source: Message dict from check_for_updates().

        Returns:
            Path to the created .md file, or None if duplicate.
        """
        dedup_key = source["dedup_key"]

        # Duplicate detection
        if dedup_key in self._processed_keys:
            logger.debug("Duplicate WhatsApp message skipped: %s", dedup_key)
            return None

        # Determine priority based on keywords
        priority = "high" if any(kw in ("urgent", "deadline", "payment", "invoice") for kw in source["keywords_matched"]) else "medium"

        now = datetime.now(timezone.utc).isoformat()
        keywords_yaml = str(source["keywords_matched"])

        content = f"""---
type: whatsapp
contact: "{source['contact']}"
phone: "{source['phone']}"
message_text: "{source['message_text'].replace('"', '\\"')}"
keywords_matched: {keywords_yaml}
detected_date: {now}
priority: {priority}
status: pending
---

## Message Details

- **From**: {source['contact']} ({source['phone']})
- **Message**: {source['message_text']}
- **Keywords**: {', '.join(source['keywords_matched'])}

## Suggested Actions

- [ ] Review and respond to this message (approval required)
"""

        # Atomic write
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

        # Track as processed
        self._processed_keys.add(dedup_key)

        logger.info(
            "Created %s (priority=%s, keywords=%s, from=%s)",
            filename, priority, source["keywords_matched"], source["contact"],
        )

        # Audit log
        append_log_entry(
            log_dir=self.log_dir,
            action_type="whatsapp_triage",
            actor="whatsapp_watcher",
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
        """Human-readable name for logging."""
        return f"{source.get('contact', 'unknown')}:{source.get('keywords_matched', [])}"

    # --- T030: Reply function ---

    async def _send_reply_async(self, contact: str, message: str) -> bool:
        """Send a WhatsApp reply via Playwright.

        Navigates to the contact's chat and types+sends the message.

        Args:
            contact: Contact name to search for.
            message: Reply text to send.

        Returns:
            True if message was sent successfully.
        """
        if self._page is None:
            await self._ensure_browser()

        if self._page is None:
            logger.error("Cannot send reply — browser not available")
            return False

        try:
            # Click on search to find the contact
            search_box = await self._page.wait_for_selector(
                SELECTORS["search_box"], timeout=5000
            )
            if search_box:
                await search_box.click()
                await self._page.keyboard.type(contact, delay=50)
                await self._page.wait_for_timeout(2000)

                # Click the first matching contact
                first_result = await self._page.query_selector(f'span[title="{contact}"]')
                if first_result:
                    await first_result.click()
                    await self._page.wait_for_timeout(1000)
                else:
                    logger.error("Contact not found in search: %s", contact)
                    return False

            # Type the message
            input_box = await self._page.wait_for_selector(
                SELECTORS["message_input"], timeout=5000
            )
            if not input_box:
                logger.error("Message input box not found")
                return False

            await input_box.click()
            await self._page.keyboard.type(message, delay=20)
            await self._page.wait_for_timeout(500)

            # Click send
            send_btn = await self._page.wait_for_selector(
                SELECTORS["send_button"], timeout=5000
            )
            if send_btn:
                await send_btn.click()
                logger.info("WhatsApp reply sent to %s", contact)

                # Clear search
                await self._page.keyboard.press("Escape")
                await self._page.keyboard.press("Escape")

                return True
            else:
                logger.error("Send button not found")
                return False

        except Exception:
            logger.exception("Failed to send WhatsApp reply to %s", contact)
            return False

    def send_reply(self, contact: str, message: str) -> bool:
        """Synchronous wrapper for sending WhatsApp reply.

        Called by orchestrator after approval.

        Args:
            contact: Contact name to reply to.
            message: Reply text.

        Returns:
            True if sent successfully.
        """
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self._send_reply_async(contact, message))
        finally:
            loop.close()


# --- CLI entry point ---

async def _setup_session(user_data_dir: str) -> None:
    """T028: Interactive setup — open WhatsApp Web for QR code scanning."""
    logger.info("Opening WhatsApp Web for QR code setup...")
    logger.info("Scan the QR code with your phone, then press Ctrl+C to exit.")

    pw = await async_playwright().start()
    context = await pw.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
    )

    page = context.pages[0] if context.pages else await context.new_page()
    await page.goto(WHATSAPP_URL)

    logger.info("Waiting for QR code scan... (Ctrl+C to exit after scanning)")

    try:
        # Wait for chat list to confirm login
        await page.wait_for_selector(SELECTORS["chat_list"], timeout=120000)
        logger.info("WhatsApp login successful! Session saved to %s", user_data_dir)
    except Exception:
        logger.warning("Timeout waiting for login. Try again with --setup.")
    finally:
        await context.close()
        await pw.stop()


def main() -> None:
    """Run the WhatsApp watcher from command line."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    parser = argparse.ArgumentParser(description="WhatsApp Watcher — monitor for business keyword messages")
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Open WhatsApp Web for first-time QR code scan setup",
    )
    args = parser.parse_args()

    # Load .env from repo root
    repo_root = Path(__file__).resolve().parent.parent
    load_dotenv(repo_root / ".env")

    vault_path = Path(os.getenv("VAULT_PATH", repo_root / "vault"))
    if not vault_path.is_absolute():
        vault_path = repo_root / vault_path

    user_data_dir = os.getenv("WHATSAPP_USER_DATA_DIR", str(repo_root / "playwright-data" / "whatsapp"))
    poll_interval = int(os.getenv("WHATSAPP_POLL_INTERVAL", "30"))

    # --setup mode: just open browser for QR scan
    if args.setup:
        asyncio.run(_setup_session(user_data_dir))
        return

    logger.info("Vault path: %s", vault_path)
    logger.info("User data dir: %s", user_data_dir)
    logger.info("Poll interval: %ds", poll_interval)

    watcher = WhatsAppWatcher(
        vault_path=vault_path,
        check_interval=poll_interval,
        user_data_dir=user_data_dir,
    )

    # Log watcher start
    append_log_entry(
        log_dir=vault_path / "Logs",
        action_type="whatsapp_triage",
        actor="whatsapp_watcher",
        target="whatsapp_watcher",
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
            action_type="whatsapp_triage",
            actor="whatsapp_watcher",
            target="whatsapp_watcher",
            parameters={"event": "stop"},
            result="success",
        )


if __name__ == "__main__":
    main()
