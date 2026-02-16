"""Base watcher abstract class for all file system watchers."""

import logging
import time
from abc import ABC, abstractmethod
from pathlib import Path

logger = logging.getLogger(__name__)


class BaseWatcher(ABC):
    """Abstract base class for vault folder watchers.

    Subclasses must implement check_for_updates() and create_action_file().
    The run() loop handles scheduling and error recovery.
    """

    def __init__(self, vault_path: str | Path, check_interval: int = 10):
        self.vault_path = Path(vault_path)
        self.check_interval = check_interval
        self._running = False

        if not self.vault_path.exists():
            raise FileNotFoundError(f"Vault path does not exist: {self.vault_path}")

    @abstractmethod
    def check_for_updates(self) -> list[Path]:
        """Check watched folder(s) for new or changed files.

        Returns a list of Paths that need processing.
        """

    @abstractmethod
    def create_action_file(self, source_path: Path) -> Path | None:
        """Process a detected file and create the appropriate action/metadata file.

        Args:
            source_path: Path to the file that triggered the action.

        Returns:
            Path to the created action file, or None if skipped (e.g., duplicate).
        """

    def run(self) -> None:
        """Main loop: poll for updates and process them.

        Runs until self._running is set to False or interrupted.
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
                    for item in updates:
                        try:
                            result = self.create_action_file(item)
                            if result:
                                logger.info("Processed: %s -> %s", item.name, result.name)
                        except Exception:
                            logger.exception("Error processing %s", item)
                except Exception:
                    logger.exception("Error during update check")

                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            logger.info("Watcher stopped by user (Ctrl+C)")
        finally:
            self._running = False
            logger.info("Watcher %s stopped", self.__class__.__name__)

    def stop(self) -> None:
        """Signal the watcher to stop after the current cycle."""
        self._running = False
