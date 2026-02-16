"""Orchestrator: watches /Needs_Action, /Approved, /Rejected, invokes Claude Code skills.

Implements: T020 (Orchestrator class), T021 (Claude CLI helper), T022 (DRY_RUN),
            T025 (Approved/Rejected folder watchers).
"""

import argparse
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from watchdog.events import FileCreatedEvent, FileSystemEventHandler
from watchdog.observers import Observer

from watchers.logger import append_log_entry

logger = logging.getLogger(__name__)


# --- T021: Claude Code CLI invocation helper ---

def invoke_claude(
    skill_path: Path,
    context_files: list[Path],
    vault_path: Path,
    dry_run: bool = True,
) -> tuple[bool, str]:
    """Invoke Claude Code CLI with a skill file and context.

    Args:
        skill_path: Path to the .md skill file.
        context_files: List of file paths to include as context.
        vault_path: Root vault path (working directory for Claude).
        dry_run: If True, log intention but skip actual invocation.

    Returns:
        Tuple of (success: bool, output: str).
    """
    # T022: DRY_RUN check
    if dry_run:
        context_names = [f.name for f in context_files]
        msg = f"[DRY_RUN] Would invoke Claude with skill={skill_path.name}, context={context_names}"
        logger.info(msg)
        return True, msg

    # Build the prompt from skill content + context file references
    skill_content = skill_path.read_text(encoding="utf-8")

    # Build context section
    context_section = ""
    for cf in context_files:
        if cf.exists():
            context_section += f"\n\n--- Context: {cf.name} ---\n"
            context_section += cf.read_text(encoding="utf-8")

    prompt = f"""Follow the skill instructions below precisely.

--- Skill: {skill_path.name} ---
{skill_content}

{context_section}

Execute the skill now. Work within the vault at: {vault_path}
"""

    cmd = [
        "claude",
        "--print",
        "-p",
        prompt,
        "--allowedTools",
        "Edit,Write,Read,Glob,Grep",
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            cwd=str(vault_path),
        )

        if result.returncode != 0:
            logger.error(
                "Claude CLI failed (exit %d): %s", result.returncode, result.stderr
            )
            return False, result.stderr

        logger.info("Claude CLI succeeded for skill: %s", skill_path.name)
        return True, result.stdout

    except subprocess.TimeoutExpired:
        logger.error("Claude CLI timed out for skill: %s", skill_path.name)
        return False, "Timeout after 300 seconds"
    except FileNotFoundError:
        logger.error("Claude CLI not found. Is 'claude' installed and on PATH?")
        return False, "claude command not found"


# --- T020: Orchestrator class ---

class _NeedsActionHandler(FileSystemEventHandler):
    """Watchdog handler for /Needs_Action folder."""

    def __init__(self, orchestrator: "Orchestrator"):
        super().__init__()
        self._orchestrator = orchestrator

    def on_created(self, event: FileCreatedEvent) -> None:
        if event.is_directory:
            return
        src = Path(event.src_path)
        if src.suffix == ".md" and not src.name.startswith("."):
            logger.info("Orchestrator detected new item: %s", src.name)
            self._orchestrator._pending_items.append(src)


class _ApprovalHandler(FileSystemEventHandler):
    """T025: Watchdog handler for /Approved and /Rejected folders."""

    def __init__(self, orchestrator: "Orchestrator", decision: str):
        super().__init__()
        self._orchestrator = orchestrator
        self._decision = decision  # "approved" or "rejected"

    def on_created(self, event: FileCreatedEvent) -> None:
        if event.is_directory:
            return
        src = Path(event.src_path)
        if src.suffix == ".md" and not src.name.startswith("."):
            logger.info(
                "Orchestrator detected %s file: %s", self._decision, src.name
            )
            self._orchestrator._pending_approvals.append((src, self._decision))


class Orchestrator:
    """Master orchestrator that triggers Claude Code skills.

    Watches /Needs_Action for new .md files and invokes:
    1. triage-inbox skill to create plans
    2. update-dashboard skill to refresh Dashboard.md

    Also watches /Approved and /Rejected for HITL decisions (T025).
    """

    def __init__(self, vault_path: str | Path, check_interval: int = 10):
        self.vault_path = Path(vault_path)
        self.check_interval = check_interval

        self.needs_action_dir = self.vault_path / "Needs_Action"
        self.approved_dir = self.vault_path / "Approved"
        self.rejected_dir = self.vault_path / "Rejected"
        self.log_dir = self.vault_path / "Logs"
        self.skills_dir = self.vault_path / "skills"

        # Ensure directories exist
        for d in [self.needs_action_dir, self.approved_dir, self.rejected_dir, self.log_dir]:
            d.mkdir(exist_ok=True)

        self._pending_items: list[Path] = []
        self._pending_approvals: list[tuple[Path, str]] = []  # T025: (path, "approved"|"rejected")
        self._running = False

        # T022: Load DRY_RUN from .env
        load_dotenv(self.vault_path / ".env")
        self.dry_run = os.getenv("DRY_RUN", "true").lower() in ("true", "1", "yes")

        if self.dry_run:
            logger.info("DRY_RUN mode is ON -- Claude will NOT be invoked")
        else:
            logger.info("DRY_RUN mode is OFF -- Claude WILL be invoked")

    def _process_needs_action_item(self, item_path: Path) -> None:
        """Process a single item from /Needs_Action."""
        logger.info("Processing: %s", item_path.name)

        # Log the orchestration start
        append_log_entry(
            log_dir=self.log_dir,
            action_type="plan_created",
            actor="orchestrator",
            target=item_path.name,
            parameters={"skill": "triage-inbox", "dry_run": self.dry_run},
            result="success" if not self.dry_run else "skipped",
        )

        # Invoke triage-inbox skill
        triage_skill = self.skills_dir / "triage-inbox.md"
        handbook = self.vault_path / "Company_Handbook.md"

        context_files = [item_path]
        if handbook.exists():
            context_files.append(handbook)

        success, output = invoke_claude(
            skill_path=triage_skill,
            context_files=context_files,
            vault_path=self.vault_path,
            dry_run=self.dry_run,
        )

        if not success:
            logger.error("Triage skill failed for %s: %s", item_path.name, output)
            append_log_entry(
                log_dir=self.log_dir,
                action_type="error",
                actor="orchestrator",
                target=item_path.name,
                parameters={"skill": "triage-inbox", "error": output[:200]},
                result="failure",
            )
            return

        # Invoke update-dashboard skill
        dashboard_skill = self.skills_dir / "update-dashboard.md"
        goals = self.vault_path / "Business_Goals.md"

        context_files_dash = []
        if goals.exists():
            context_files_dash.append(goals)

        success_dash, output_dash = invoke_claude(
            skill_path=dashboard_skill,
            context_files=context_files_dash,
            vault_path=self.vault_path,
            dry_run=self.dry_run,
        )

        if not success_dash:
            logger.error("Dashboard skill failed: %s", output_dash)
            append_log_entry(
                log_dir=self.log_dir,
                action_type="error",
                actor="orchestrator",
                target="Dashboard.md",
                parameters={"skill": "update-dashboard", "error": output_dash[:200]},
                result="failure",
            )
        else:
            append_log_entry(
                log_dir=self.log_dir,
                action_type="dashboard_updated",
                actor="orchestrator",
                target="Dashboard.md",
                parameters={"trigger": item_path.name, "dry_run": self.dry_run},
                result="success" if not self.dry_run else "skipped",
            )

    def _process_approval(self, item_path: Path, decision: str) -> None:
        """T025: Process an approved or rejected file."""
        action_type = "approval_granted" if decision == "approved" else "approval_rejected"
        logger.info("Processing %s: %s", decision, item_path.name)

        # Log the approval/rejection
        append_log_entry(
            log_dir=self.log_dir,
            action_type=action_type,
            actor="orchestrator",
            target=item_path.name,
            parameters={
                "skill": "process-approval",
                "decision": decision,
                "dry_run": self.dry_run,
            },
            result="success" if not self.dry_run else "skipped",
        )

        # Invoke process-approval skill
        approval_skill = self.skills_dir / "process-approval.md"

        success, output = invoke_claude(
            skill_path=approval_skill,
            context_files=[item_path],
            vault_path=self.vault_path,
            dry_run=self.dry_run,
        )

        if not success:
            logger.error("Process-approval skill failed for %s: %s", item_path.name, output)
            append_log_entry(
                log_dir=self.log_dir,
                action_type="error",
                actor="orchestrator",
                target=item_path.name,
                parameters={"skill": "process-approval", "error": output[:200]},
                result="failure",
            )
            return

        # Update dashboard after approval processing
        dashboard_skill = self.skills_dir / "update-dashboard.md"
        invoke_claude(
            skill_path=dashboard_skill,
            context_files=[],
            vault_path=self.vault_path,
            dry_run=self.dry_run,
        )

        append_log_entry(
            log_dir=self.log_dir,
            action_type="dashboard_updated",
            actor="orchestrator",
            target="Dashboard.md",
            parameters={"trigger": f"{decision}:{item_path.name}", "dry_run": self.dry_run},
            result="success" if not self.dry_run else "skipped",
        )

    def _startup_scan(self) -> None:
        """Scan /Needs_Action for unprocessed items on startup."""
        logger.info("Orchestrator startup scan of Needs_Action...")
        count = 0
        plans_dir = self.vault_path / "Plans"

        for item in sorted(self.needs_action_dir.iterdir()):
            if item.is_file() and item.suffix == ".md" and not item.name.startswith("."):
                # Check if a plan already exists for this item
                plan_name = item.name.replace("FILE_", "PLAN_")
                if not (plans_dir / plan_name).exists():
                    self._pending_items.append(item)
                    count += 1

        if count > 0:
            logger.info("Startup scan found %d unprocessed item(s)", count)
        else:
            logger.info("Startup scan: no unprocessed items")

    def run(self) -> None:
        """Start watching /Needs_Action and process items."""
        self._running = True

        # Startup scan
        self._startup_scan()

        # Start watchdog observers
        observer = Observer()

        # Watch /Needs_Action for new triaged items
        needs_handler = _NeedsActionHandler(self)
        observer.schedule(needs_handler, str(self.needs_action_dir), recursive=False)

        # T025: Watch /Approved and /Rejected for HITL decisions
        approved_handler = _ApprovalHandler(self, "approved")
        observer.schedule(approved_handler, str(self.approved_dir), recursive=False)

        rejected_handler = _ApprovalHandler(self, "rejected")
        observer.schedule(rejected_handler, str(self.rejected_dir), recursive=False)

        observer.start()

        # T028: Log watcher start event
        append_log_entry(
            log_dir=self.log_dir,
            action_type="file_moved",
            actor="orchestrator",
            target="orchestrator",
            parameters={
                "event": "start",
                "dry_run": self.dry_run,
                "watching": ["Needs_Action/", "Approved/", "Rejected/"],
            },
            result="success",
        )

        logger.info(
            "Orchestrator running (vault=%s, interval=%ds, dry_run=%s)",
            self.vault_path,
            self.check_interval,
            self.dry_run,
        )
        logger.info("Watching: Needs_Action/, Approved/, Rejected/")

        try:
            while self._running:
                # Process pending triage items
                pending = list(self._pending_items)
                self._pending_items.clear()

                for item in pending:
                    try:
                        self._process_needs_action_item(item)
                    except Exception:
                        logger.exception("Error processing %s", item)
                        # T028: Log processing errors
                        append_log_entry(
                            log_dir=self.log_dir,
                            action_type="error",
                            actor="orchestrator",
                            target=str(item),
                            parameters={"event": "processing_error", "phase": "triage"},
                            result="failure",
                        )

                # T025: Process pending approval decisions
                approvals = list(self._pending_approvals)
                self._pending_approvals.clear()

                for item_path, decision in approvals:
                    try:
                        self._process_approval(item_path, decision)
                    except Exception:
                        logger.exception("Error processing approval %s", item_path)
                        # T028: Log approval processing errors
                        append_log_entry(
                            log_dir=self.log_dir,
                            action_type="error",
                            actor="orchestrator",
                            target=str(item_path),
                            parameters={"event": "approval_error", "decision": decision},
                            result="failure",
                        )

                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            logger.info("Orchestrator stopped by user (Ctrl+C)")
        finally:
            self._running = False
            observer.stop()
            observer.join()
            # T028: Log watcher stop event
            append_log_entry(
                log_dir=self.log_dir,
                action_type="file_moved",
                actor="orchestrator",
                target="orchestrator",
                parameters={"event": "stop"},
                result="success",
            )
            logger.info("Orchestrator stopped")

    def run_briefing(self) -> None:
        """Run the CEO briefing skill once and exit."""
        logger.info("Generating CEO briefing...")

        briefing_skill = self.skills_dir / "generate-briefing.md"
        goals = self.vault_path / "Business_Goals.md"

        context_files = []
        if goals.exists():
            context_files.append(goals)

        append_log_entry(
            log_dir=self.log_dir,
            action_type="briefing_generated",
            actor="orchestrator",
            target="Briefings/",
            parameters={"skill": "generate-briefing", "dry_run": self.dry_run},
            result="success" if not self.dry_run else "skipped",
        )

        success, output = invoke_claude(
            skill_path=briefing_skill,
            context_files=context_files,
            vault_path=self.vault_path,
            dry_run=self.dry_run,
        )

        if success:
            logger.info("Briefing generation completed")
        else:
            logger.error("Briefing generation failed: %s", output)

    def stop(self) -> None:
        """Signal the orchestrator to stop."""
        self._running = False


# --- CLI entry point ---

def main() -> None:
    """Run the orchestrator from command line."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    parser = argparse.ArgumentParser(description="AI Employee Orchestrator")
    parser.add_argument(
        "--briefing",
        action="store_true",
        help="Generate CEO briefing and exit (instead of watching folders)",
    )
    args = parser.parse_args()

    vault_path = Path(__file__).resolve().parent.parent
    logger.info("Vault path: %s", vault_path)

    orchestrator = Orchestrator(vault_path=vault_path, check_interval=10)

    if args.briefing:
        orchestrator.run_briefing()
    else:
        try:
            orchestrator.run()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
