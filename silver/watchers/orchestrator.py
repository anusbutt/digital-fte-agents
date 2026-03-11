"""Orchestrator: watches vault/Needs_Action, vault/Approved, vault/Rejected, invokes Claude Code skills."""

import argparse
import datetime
import logging
import os
import re
import subprocess
import time
from pathlib import Path

from dotenv import load_dotenv
from watchdog.events import FileCreatedEvent, FileSystemEventHandler
from watchdog.observers import Observer

from watchers.logger import append_log_entry

logger = logging.getLogger(__name__)


# --- T035: Frontmatter parser helper ---

def _parse_frontmatter(path: Path) -> dict[str, str]:
    """Parse YAML frontmatter from a markdown file.

    Returns a flat dict of string key/value pairs. Handles simple key: value
    syntax only (no nested objects or lists). Skips list items and indented lines.
    """
    try:
        content = path.read_text(encoding="utf-8")
        match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if not match:
            return {}
        result: dict[str, str] = {}
        for line in match.group(1).splitlines():
            if ":" in line and not line.startswith(" ") and not line.startswith("-"):
                key, _, val = line.partition(":")
                result[key.strip()] = val.strip().strip("\"'")
        return result
    except Exception:
        return {}


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

    def __init__(self, vault_path: str | Path, repo_root: str | Path | None = None, check_interval: int = 10):
        self.vault_path = Path(vault_path)
        self.repo_root = Path(repo_root) if repo_root else self.vault_path.parent
        self.check_interval = check_interval

        self.needs_action_dir = self.vault_path / "Needs_Action"
        self.approved_dir = self.vault_path / "Approved"
        self.rejected_dir = self.vault_path / "Rejected"
        self.log_dir = self.vault_path / "Logs"
        self.skills_dir = self.repo_root / "skills"

        # Ensure directories exist
        for d in [self.needs_action_dir, self.approved_dir, self.rejected_dir, self.log_dir]:
            d.mkdir(exist_ok=True)

        self._pending_items: list[Path] = []
        self._pending_approvals: list[tuple[Path, str]] = []  # T025: (path, "approved"|"rejected")
        self._running = False

        # Load DRY_RUN from .env (at repo root, not vault)
        load_dotenv(self.repo_root / ".env")
        self.dry_run = os.getenv("DRY_RUN", "true").lower() in ("true", "1", "yes")

        if self.dry_run:
            logger.info("DRY_RUN mode is ON -- Claude will NOT be invoked")
        else:
            logger.info("DRY_RUN mode is OFF -- Claude WILL be invoked")

    def _process_needs_action_item(self, item_path: Path) -> None:
        """Process a single item from /Needs_Action.

        T036: Routes by item prefix (FILE_, EMAIL_, WHATSAPP_) and passes
        appropriate context files to triage-inbox. After triage, checks for
        auto-execute eligibility: EMAIL_ items with sensitivity=non-sensitive
        and approval_required=false in the created plan are executed immediately
        via compose-email-reply without going through the approval folder.
        """
        logger.info("Processing: %s", item_path.name)

        # T036: Read item metadata before triage for type-aware routing
        item_fm = _parse_frontmatter(item_path)
        item_type = item_fm.get("type", "unknown")
        item_sensitivity = item_fm.get("sensitivity", "sensitive")

        # Log triage start
        append_log_entry(
            log_dir=self.log_dir,
            action_type="plan_created",
            actor="orchestrator",
            target=item_path.name,
            parameters={
                "skill": "triage-inbox",
                "item_type": item_type,
                "dry_run": self.dry_run,
            },
            result="success" if not self.dry_run else "skipped",
        )

        # Build triage context: VaultItem + handbook (always) + type-specific extras
        triage_skill = self.skills_dir / "triage-inbox.md"
        handbook = self.vault_path / "Company_Handbook.md"

        context_files: list[Path] = [item_path]
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

        # T036: Auto-execute path for non-sensitive EMAIL_ items
        # If the triage skill set approval_required=false in the plan, send immediately
        if item_type == "email" and item_sensitivity == "non-sensitive":
            plan_name = "PLAN_" + item_path.name
            plan_path = self.vault_path / "Plans" / plan_name
            if plan_path.exists():
                plan_fm = _parse_frontmatter(plan_path)
                approval_required = plan_fm.get("approval_required", "true").lower()
                if approval_required == "false":
                    logger.info(
                        "Auto-executing non-sensitive email reply for %s", item_path.name
                    )
                    append_log_entry(
                        log_dir=self.log_dir,
                        action_type="email_sent",
                        actor="orchestrator",
                        target=item_path.name,
                        parameters={"skill": "compose-email-reply", "auto_execute": True},
                        result="success" if not self.dry_run else "skipped",
                    )
                    compose_skill = self.skills_dir / "compose-email-reply.md"
                    auto_success, auto_output = invoke_claude(
                        skill_path=compose_skill,
                        context_files=[item_path, plan_path],
                        vault_path=self.vault_path,
                        dry_run=self.dry_run,
                    )
                    if not auto_success:
                        logger.error(
                            "Auto-execute compose-email-reply failed for %s: %s",
                            item_path.name,
                            auto_output,
                        )

        # Invoke update-dashboard skill
        dashboard_skill = self.skills_dir / "update-dashboard.md"
        goals = self.vault_path / "Business_Goals.md"

        context_files_dash: list[Path] = []
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
        """T025/T037: Process an approved or rejected file.

        For approved items with a known action type (email_send, email_draft,
        whatsapp_reply, linkedin_post): reads YAML frontmatter and dispatches
        directly to the correct executor via _dispatch_action().
        On dispatch failure the file stays in Approved/ for retry.
        All other cases (rejected, file_process, payment, etc.) delegate to
        the process-approval skill.
        """
        log_action_type = "approval_granted" if decision == "approved" else "approval_rejected"
        logger.info("Processing %s: %s", decision, item_path.name)

        # T037: Read frontmatter for action routing
        fm = _parse_frontmatter(item_path)
        action_type = fm.get("action", "")
        reply_content = fm.get("reply_content", "")
        recipient = fm.get("recipient", "")

        append_log_entry(
            log_dir=self.log_dir,
            action_type=log_action_type,
            actor="orchestrator",
            target=item_path.name,
            parameters={
                "action": action_type,
                "decision": decision,
                "dry_run": self.dry_run,
            },
            result="success" if not self.dry_run else "skipped",
        )

        if decision == "approved" and action_type in (
            "email_send",
            "email_draft",
            "whatsapp_reply",
            "linkedin_post",
        ):
            # T037: Dispatch to the correct executor
            dispatch_success, dispatch_output = self._dispatch_action(
                approval_path=item_path,
                action_type=action_type,
                reply_content=reply_content,
                recipient=recipient,
            )

            if not dispatch_success:
                # Keep file in Approved/ for retry — do NOT move to Done/
                logger.error(
                    "Action dispatch failed for %s (action=%s). "
                    "Kept in Approved/ for retry. Error: %s",
                    item_path.name,
                    action_type,
                    dispatch_output,
                )
                append_log_entry(
                    log_dir=self.log_dir,
                    action_type="error",
                    actor="orchestrator",
                    target=item_path.name,
                    parameters={
                        "action": action_type,
                        "error": dispatch_output[:200],
                        "retry": True,
                    },
                    result="failure",
                )
                # Update dashboard so failure is visible, then return without cleanup
                dashboard_skill = self.skills_dir / "update-dashboard.md"
                invoke_claude(
                    skill_path=dashboard_skill,
                    context_files=[],
                    vault_path=self.vault_path,
                    dry_run=self.dry_run,
                )
                return

            logger.info(
                "Action dispatched successfully for %s (action=%s)",
                item_path.name,
                action_type,
            )
            # After successful dispatch, fall through to process-approval skill
            # for move-to-Done and dashboard update

        # Fallthrough: rejected, file_process, payment, or post-dispatch cleanup
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
        """Scan /Needs_Action for unprocessed items on startup.

        T035: detects FILE_*, EMAIL_*, and WHATSAPP_* prefixes.
        Plan existence check uses the canonical PLAN_{original_name} naming
        from triage-inbox skill (e.g. FILE_x.md → PLAN_FILE_x.md).
        """
        logger.info("Orchestrator startup scan of Needs_Action...")
        count = 0
        plans_dir = self.vault_path / "Plans"

        # T035: all supported VaultItem prefixes
        known_prefixes = ("FILE_", "EMAIL_", "WHATSAPP_")

        for item in sorted(self.needs_action_dir.iterdir()):
            if not item.is_file() or item.suffix != ".md" or item.name.startswith("."):
                continue
            if not any(item.name.startswith(p) for p in known_prefixes):
                continue

            # Canonical plan name: prepend PLAN_ before the original name
            plan_name = "PLAN_" + item.name
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

                # T038: Check for expired approval requests each cycle
                self._check_approval_expiry()

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
        """Run the CEO briefing skill once and exit.

        T043: Ensures vault/Briefings/ exists before invoking. Safe to call
        from Windows Task Scheduler (loads .env, resolves vault path from env).
        """
        logger.info("Generating CEO briefing...")

        # T043: Ensure Briefings/ directory exists
        briefings_dir = self.vault_path / "Briefings"
        briefings_dir.mkdir(parents=True, exist_ok=True)

        briefing_skill = self.skills_dir / "generate-briefing.md"
        goals = self.vault_path / "Business_Goals.md"
        handbook = self.vault_path / "Company_Handbook.md"

        context_files = []
        if goals.exists():
            context_files.append(goals)
        if handbook.exists():
            context_files.append(handbook)

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

    def run_linkedin_post(self) -> None:
        """Run the LinkedIn post generation skill once and exit.

        Invokes generate-linkedin-post skill to create a draft post in
        vault/Pending_Approval/. The post always requires human approval
        before publishing via scripts/linkedin_post.py.
        """
        logger.info("Generating LinkedIn post...")

        linkedin_skill = self.skills_dir / "generate-linkedin-post.md"
        goals = self.vault_path / "Business_Goals.md"
        handbook = self.vault_path / "Company_Handbook.md"

        context_files = []
        if goals.exists():
            context_files.append(goals)
        if handbook.exists():
            context_files.append(handbook)

        append_log_entry(
            log_dir=self.log_dir,
            action_type="linkedin_generated",
            actor="orchestrator",
            target="Pending_Approval/",
            parameters={"skill": "generate-linkedin-post", "dry_run": self.dry_run},
            result="success" if not self.dry_run else "skipped",
        )

        success, output = invoke_claude(
            skill_path=linkedin_skill,
            context_files=context_files,
            vault_path=self.vault_path,
            dry_run=self.dry_run,
        )

        if success:
            logger.info("LinkedIn post generation completed")
        else:
            logger.error("LinkedIn post generation failed: %s", output)

        # T051: Update dashboard after LinkedIn post generation so
        # Pending_Approval/ count reflects the new draft
        dashboard_skill = self.skills_dir / "update-dashboard.md"
        invoke_claude(
            skill_path=dashboard_skill,
            context_files=[],
            vault_path=self.vault_path,
            dry_run=self.dry_run,
        )

    # --- T037: Action dispatcher ---

    def _dispatch_action(
        self,
        approval_path: Path,
        action_type: str,
        reply_content: str,
        recipient: str,
    ) -> tuple[bool, str]:
        """Dispatch an approved action to the correct executor.

        Routes by action_type:
        - email_send / email_draft → compose-email-reply skill (uses email-mcp)
        - whatsapp_reply → WhatsAppWatcher.send_reply()
        - linkedin_post → scripts.linkedin_post.post()
        - all others → process-approval skill via Claude

        Returns (success, output_or_error).
        """
        if action_type in ("email_send", "email_draft"):
            skill = self.skills_dir / "compose-email-reply.md"
            return invoke_claude(
                skill_path=skill,
                context_files=[approval_path],
                vault_path=self.vault_path,
                dry_run=self.dry_run,
            )

        elif action_type == "whatsapp_reply":
            if self.dry_run:
                return True, f"[DRY_RUN] Would WhatsApp reply to {recipient!r}: {reply_content[:60]}..."
            try:
                from watchers.whatsapp_watcher import WhatsAppWatcher  # noqa: PLC0415
                watcher = WhatsAppWatcher(vault_path=self.vault_path)
                watcher.send_reply(recipient, reply_content)
                return True, "WhatsApp reply sent"
            except Exception as exc:
                return False, str(exc)

        elif action_type == "linkedin_post":
            if self.dry_run:
                return True, f"[DRY_RUN] Would post to LinkedIn: {reply_content[:60]}..."
            try:
                from scripts.linkedin_post import post as linkedin_post  # noqa: PLC0415
                user_data_dir = os.getenv("LINKEDIN_USER_DATA_DIR", "playwright-data/linkedin")
                linkedin_post(
                    content=reply_content,
                    user_data_dir=user_data_dir,
                    vault_path=self.vault_path,
                    dry_run=False,
                )
                return True, "LinkedIn post published"
            except Exception as exc:
                return False, str(exc)

        else:
            # file_process / payment / unknown → delegate to process-approval skill
            skill = self.skills_dir / "process-approval.md"
            return invoke_claude(
                skill_path=skill,
                context_files=[approval_path],
                vault_path=self.vault_path,
                dry_run=self.dry_run,
            )

    # --- T038: Approval expiry checker ---

    def _check_approval_expiry(self) -> None:
        """Scan Pending_Approval/ and mark expired approval requests.

        Checks the `expires` ISO timestamp in each APPROVE_*.md frontmatter.
        If the current UTC time is past the expires value, logs the expiry and
        updates the file's status field to 'expired'. Files are NOT moved per
        spec US6 (log-only, no automatic purge).
        """
        pending_dir = self.vault_path / "Pending_Approval"
        if not pending_dir.exists():
            return

        now = datetime.datetime.now(datetime.timezone.utc)

        for item in pending_dir.iterdir():
            if not item.is_file() or item.suffix != ".md" or item.name.startswith("."):
                continue
            if not item.name.startswith("APPROVE_"):
                continue

            fm = _parse_frontmatter(item)
            status = fm.get("status", "pending")
            expires_str = fm.get("expires", "")

            if status in ("approved", "rejected", "expired") or not expires_str:
                continue

            try:
                expires_dt = datetime.datetime.fromisoformat(expires_str.replace("Z", "+00:00"))
            except ValueError:
                continue

            if now > expires_dt:
                logger.warning("Approval expired (no action taken): %s", item.name)
                append_log_entry(
                    log_dir=self.log_dir,
                    action_type="error",
                    actor="orchestrator",
                    target=item.name,
                    parameters={"event": "approval_expired", "expires": expires_str},
                    result="skipped",
                )
                # Update status field in file to 'expired' (in-place edit)
                try:
                    content = item.read_text(encoding="utf-8")
                    updated = re.sub(
                        r"^(status:\s*)pending(\s*)$",
                        r"\1expired\2",
                        content,
                        flags=re.MULTILINE,
                    )
                    item.write_text(updated, encoding="utf-8")
                except Exception:
                    logger.exception("Could not update expired status for %s", item.name)

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
    parser.add_argument(
        "--linkedin",
        action="store_true",
        help="Generate LinkedIn post draft and exit (instead of watching folders)",
    )
    args = parser.parse_args()

    # Load .env from repo root
    repo_root = Path(__file__).resolve().parent.parent
    load_dotenv(repo_root / ".env")

    vault_path = Path(os.getenv("VAULT_PATH", repo_root / "vault"))
    if not vault_path.is_absolute():
        vault_path = repo_root / vault_path

    check_interval = int(os.getenv("CHECK_INTERVAL", "10"))

    logger.info("Vault path: %s", vault_path)
    logger.info("Repo root: %s", repo_root)

    orchestrator = Orchestrator(
        vault_path=vault_path,
        repo_root=repo_root,
        check_interval=check_interval,
    )

    if args.briefing:
        orchestrator.run_briefing()
    elif args.linkedin:
        orchestrator.run_linkedin_post()
    else:
        try:
            orchestrator.run()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
