"""Filesystem watcher for the Inbox folder.

Monitors /Inbox for new files using watchdog, creates metadata .md files
in /Needs_Action with YAML frontmatter per data-model.md VaultItem schema.

Implements: T013 (FilesystemWatcher), T014 (classification), T015 (duplicate detection),
            T016 (startup scan), T017 (audit logging).
"""

import logging
import re
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from watchdog.events import FileCreatedEvent, FileSystemEventHandler
from watchdog.observers import Observer

from watchers.base_watcher import BaseWatcher
from watchers.logger import append_log_entry

logger = logging.getLogger(__name__)


# --- T014: File classification logic ---

# Classification rules from Company_Handbook.md
CLASSIFICATION_RULES: list[tuple[re.Pattern, str, str]] = [
    # (compiled regex pattern, file_type, default_priority)
    (re.compile(r"invoice|inv_|bill", re.IGNORECASE), "invoice", "high"),
    (re.compile(r"receipt|rcpt_|payment_confirmation", re.IGNORECASE), "receipt", "medium"),
    (re.compile(r"brief|client_brief|project_brief", re.IGNORECASE), "client_brief", "high"),
    (re.compile(r"contract|agreement|nda|sow", re.IGNORECASE), "contract", "high"),
]


def classify_file(filename: str) -> tuple[str, str]:
    """Classify a file based on filename keywords.

    Args:
        filename: The original filename (e.g., "invoice_client_a.pdf").

    Returns:
        Tuple of (file_type, priority). file_type is one of:
        invoice, receipt, client_brief, contract, unknown.
        priority is one of: high, medium, low.
    """
    for pattern, file_type, priority in CLASSIFICATION_RULES:
        if pattern.search(filename):
            return file_type, priority
    return "unknown", "low"


# --- T013 + T015 + T016 + T017: FilesystemWatcher ---

class _InboxHandler(FileSystemEventHandler):
    """Watchdog event handler that queues new files for processing."""

    def __init__(self, watcher: "FilesystemWatcher"):
        super().__init__()
        self._watcher = watcher

    def on_created(self, event: FileCreatedEvent) -> None:
        if event.is_directory:
            return
        src = Path(event.src_path)
        # Skip hidden files and .gitkeep
        if src.name.startswith("."):
            return
        logger.info("Detected new file in Inbox: %s", src.name)
        self._watcher._pending_files.append(src)


class FilesystemWatcher(BaseWatcher):
    """Watches /Inbox for new files, creates metadata .md in /Needs_Action.

    Uses watchdog Observer for real-time file detection.
    Falls back to polling via BaseWatcher.run() loop.
    """

    def __init__(self, vault_path: str | Path, check_interval: int = 10):
        super().__init__(vault_path, check_interval)

        self.inbox_dir = self.vault_path / "Inbox"
        self.needs_action_dir = self.vault_path / "Needs_Action"
        self.log_dir = self.vault_path / "Logs"

        # Ensure directories exist
        self.inbox_dir.mkdir(exist_ok=True)
        self.needs_action_dir.mkdir(exist_ok=True)
        self.log_dir.mkdir(exist_ok=True)

        # Thread-safe list of files pending processing
        self._pending_files: list[Path] = []
        self._observer: Observer | None = None

    def _metadata_filename(self, original_name: str) -> str:
        """Generate the metadata filename: FILE_{name_without_ext}.md"""
        stem = Path(original_name).stem
        return f"FILE_{stem}.md"

    def _is_duplicate(self, original_name: str) -> bool:
        """T015: Check if metadata file already exists in Needs_Action."""
        md_name = self._metadata_filename(original_name)
        return (self.needs_action_dir / md_name).exists()

    def _create_metadata_file(self, source_path: Path) -> Path | None:
        """Create a VaultItem metadata .md file in Needs_Action.

        Uses atomic write (temp file then rename) per Contract 1.
        Returns the path to the created file, or None if duplicate.
        """
        original_name = source_path.name

        # T015: Duplicate detection
        if self._is_duplicate(original_name):
            logger.info("Duplicate skipped: %s (metadata already exists)", original_name)
            # T017: Log the skip
            append_log_entry(
                log_dir=self.log_dir,
                action_type="file_triage",
                actor="watcher",
                target=original_name,
                parameters={"reason": "duplicate", "source_path": str(source_path)},
                result="skipped",
            )
            return None

        # T014: Classify the file
        file_type, priority = classify_file(original_name)

        # Build YAML frontmatter per data-model.md VaultItem schema
        now = datetime.now(timezone.utc).isoformat()
        relative_source = f"Inbox/{original_name}"

        content = f"""---
type: {file_type}
original_name: "{original_name}"
detected_date: {now}
priority: {priority}
status: pending
source_path: "{relative_source}"
---

## File Details

Automatically triaged file from Inbox.

- **Original Name**: {original_name}
- **Detected Type**: {file_type}
- **Priority**: {priority}
- **Source**: {relative_source}

## Suggested Actions

- [ ] Review and process this {file_type}
"""

        # Atomic write: write to temp, then rename
        md_name = self._metadata_filename(original_name)
        target_path = self.needs_action_dir / md_name

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
            # Clean up temp file on failure
            if tmp_path.exists():
                tmp_path.unlink()
            raise

        logger.info(
            "Created metadata: %s (type=%s, priority=%s)", md_name, file_type, priority
        )

        # T017: Audit log
        append_log_entry(
            log_dir=self.log_dir,
            action_type="file_triage",
            actor="watcher",
            target=original_name,
            parameters={
                "detected_type": file_type,
                "priority": priority,
                "metadata_file": md_name,
                "source_path": relative_source,
            },
            result="success",
        )

        return target_path

    def check_for_updates(self) -> list[Path]:
        """Return pending files detected by watchdog or startup scan."""
        pending = list(self._pending_files)
        self._pending_files.clear()
        return pending

    def create_action_file(self, source_path: Path) -> Path | None:
        """Process a single file from Inbox."""
        return self._create_metadata_file(source_path)

    def _startup_scan(self) -> None:
        """T016: Scan Inbox for unprocessed files on startup.

        Processes any files in Inbox that don't have corresponding
        metadata files in Needs_Action.
        """
        logger.info("Running startup scan of Inbox...")
        count = 0

        for item in sorted(self.inbox_dir.iterdir()):
            if item.is_file() and not item.name.startswith("."):
                if not self._is_duplicate(item.name):
                    self._pending_files.append(item)
                    count += 1

        if count > 0:
            logger.info("Startup scan found %d unprocessed file(s)", count)
        else:
            logger.info("Startup scan: no unprocessed files")

    def run(self) -> None:
        """Start watchdog observer and polling loop.

        Overrides BaseWatcher.run() to add:
        - T016: Startup scan before entering loop
        - Watchdog Observer for real-time file detection
        """
        self._running = True

        # T016: Process files that arrived while watcher was stopped
        self._startup_scan()

        # Start watchdog observer for real-time detection
        handler = _InboxHandler(self)
        self._observer = Observer()
        self._observer.schedule(handler, str(self.inbox_dir), recursive=False)
        self._observer.start()

        # T029: Log watcher start event
        append_log_entry(
            log_dir=self.log_dir,
            action_type="file_moved",
            actor="watcher",
            target="filesystem_watcher",
            parameters={"event": "start", "watching": "Inbox/"},
            result="success",
        )

        logger.info(
            "FilesystemWatcher running (vault=%s, interval=%ds)",
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
                            # T029: Log processing errors
                            append_log_entry(
                                log_dir=self.log_dir,
                                action_type="error",
                                actor="watcher",
                                target=item.name,
                                parameters={"event": "processing_error"},
                                result="failure",
                            )
                except Exception:
                    logger.exception("Error during update check")

                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            logger.info("Watcher stopped by user (Ctrl+C)")
        finally:
            self._running = False
            if self._observer:
                self._observer.stop()
                self._observer.join()
            # T029: Log watcher stop event
            append_log_entry(
                log_dir=self.log_dir,
                action_type="file_moved",
                actor="watcher",
                target="filesystem_watcher",
                parameters={"event": "stop"},
                result="success",
            )
            logger.info("FilesystemWatcher stopped")

    def stop(self) -> None:
        """Stop the watcher and observer."""
        self._running = False
        if self._observer:
            self._observer.stop()


# --- CLI entry point ---

def main() -> None:
    """Run the filesystem watcher from command line."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    vault_path = Path(__file__).resolve().parent.parent
    logger.info("Vault path: %s", vault_path)

    watcher = FilesystemWatcher(vault_path=vault_path, check_interval=10)

    try:
        watcher.run()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
