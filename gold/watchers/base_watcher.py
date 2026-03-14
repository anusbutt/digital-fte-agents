"""Base watcher abstract class for all watchers (filesystem, Gmail, WhatsApp)."""

import logging
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class BaseWatcher(ABC):
    """Abstract base class for vault watchers.

    Subclasses must implement check_for_updates() and create_action_file().
    The run() loop handles scheduling and error recovery.

    Source types are generic (Any) to support:
    - FilesystemWatcher: source is a Path (file in Inbox)
    - GmailWatcher: source is a dict (Gmail message data)
    - WhatsAppWatcher: source is a dict (WhatsApp message data)
    - FacebookWatcher: source is a dict (Facebook message data)
    - InstagramWatcher: source is a dict (Instagram message data)
    - TwitterWatcher: source is a dict (Twitter/X message data)
    """

    def __init__(self, vault_path: str | Path, check_interval: int = 10):
        self.vault_path = Path(vault_path)
        self.check_interval = check_interval
        self._running = False
        self._consecutive_errors = 0
        self._max_backoff = 300  # 5 minutes max backoff

        if not self.vault_path.exists():
            raise FileNotFoundError(f"Vault path does not exist: {self.vault_path}")

    @abstractmethod
    def check_for_updates(self) -> list[Any]:
        """Check for new items to process.

        Returns a list of source items. The type depends on the watcher:
        - FilesystemWatcher: list[Path]
        - GmailWatcher: list[dict] (message metadata)
        - WhatsAppWatcher: list[dict] (message data)
        - FacebookWatcher: list[dict] (message/post data)
        - InstagramWatcher: list[dict] (message/post data)
        - TwitterWatcher: list[dict] (tweet/DM data)
        """

    @abstractmethod
    def create_action_file(self, source: Any) -> Path | None:
        """Process a detected item and create the appropriate .md file in vault/Needs_Action/.

        Args:
            source: The item to process. Type depends on the watcher subclass.

        Returns:
            Path to the created action file, or None if skipped (e.g., duplicate).
        """

    def _get_source_name(self, source: Any) -> str:
        """Get a human-readable name for a source item (for logging).

        Override in subclasses for non-Path sources.
        """
        if isinstance(source, Path):
            return source.name
        if isinstance(source, dict):
            return source.get("id", str(source)[:50])
        return str(source)[:50]

    def _backoff_delay(self) -> float:
        """Calculate exponential backoff delay based on consecutive errors."""
        if self._consecutive_errors <= 0:
            return self.check_interval
        delay = min(
            self.check_interval * (2 ** self._consecutive_errors),
            self._max_backoff,
        )
        return delay

    def run(self) -> None:
        """Main loop: poll for updates and process them.

        Runs until self._running is set to False or interrupted.
        Uses exponential backoff on consecutive errors.
        """
        self._running = True
        logger.info(
            "Starting %s (vault=%s, interval=%ds)",
            self.__class__.__name__,
            self.vault_path,
            self.check_interval,
        )

        try:
            while self._running:
                try:
                    updates = self.check_for_updates()
                    self._consecutive_errors = 0  # Reset on success
                    for item in updates:
                        try:
                            result = self.create_action_file(item)
                            if result:
                                logger.info(
                                    "Processed: %s -> %s",
                                    self._get_source_name(item),
                                    result.name,
                                )
                        except Exception:
                            logger.exception(
                                "Error processing %s", self._get_source_name(item)
                            )
                except Exception:
                    self._consecutive_errors += 1
                    logger.exception(
                        "Error during update check (consecutive: %d)",
                        self._consecutive_errors,
                    )

                delay = self._backoff_delay()
                if delay != self.check_interval:
                    logger.warning(
                        "Backoff: waiting %.1fs (consecutive errors: %d)",
                        delay,
                        self._consecutive_errors,
                    )
                time.sleep(delay)
        except KeyboardInterrupt:
            logger.info("Watcher stopped by user (Ctrl+C)")
        finally:
            self._running = False
            logger.info("Watcher %s stopped", self.__class__.__name__)

    def stop(self) -> None:
        """Signal the watcher to stop after the current cycle."""
        self._running = False
