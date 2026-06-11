"""Orchestrator: watches vault/Needs_Action, vault/Approved, vault/Rejected, invokes Claude Code skills.

Nestaro Pilot tier extends earlier prototype orchestrator with:
- facebook_reply, instagram_reply, twitter_reply dispatch routes (Phase 3)
- odoo_action dispatch route (Phase 4)
- generate-accounting-briefing skill support (Phase 5)
- Social media post generation (Phase 3)
"""

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


# --- Frontmatter parser helper ---

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


# --- Claude Code CLI invocation helper ---

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
    # DRY_RUN check
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

    # Build subprocess environment: inherit current env, inject Ralph Wiggum state.
    # RALPH_ITERATION=0 resets the loop counter for each top-level Claude invocation.
    # The stop hook reads and increments this via the vault/.ralph_state file.
    ralph_env = os.environ.copy()
    ralph_env.setdefault("RALPH_ITERATION", "0")
    ralph_env.setdefault("RALPH_MAX_ITER", "10")
    ralph_env["VAULT_PATH"] = str(vault_path)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            cwd=str(vault_path),
            env=ralph_env,
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


# --- Orchestrator class ---

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
    """Watchdog handler for /Approved and /Rejected folders."""

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

    Nestaro Pilot tier watches:
    - /Needs_Action: FILE_, EMAIL_, WHATSAPP_, FACEBOOK_, INSTAGRAM_, TWITTER_ items
    - /Approved and /Rejected: HITL decisions
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
        self._pending_approvals: list[tuple[Path, str]] = []
        self._running = False

        # Load DRY_RUN from .env (at repo root, not vault)
        load_dotenv(self.repo_root / ".env")
        self.dry_run = os.getenv("DRY_RUN", "true").lower() in ("true", "1", "yes")

        # Scheduling: dates on which scheduled tasks last ran (reset each process start)
        self._last_briefing_date: str | None = None
        self._last_social_post_date: str | None = None
        self._last_linkedin_date: str | None = None

        # Scheduling config from .env
        self.briefing_day = os.getenv("BRIEFING_DAY", "MON").upper()
        self.briefing_time = os.getenv("BRIEFING_TIME", "08:00")
        self.social_post_time = os.getenv("SOCIAL_POST_TIME", "09:00")
        self.linkedin_post_time = os.getenv("LINKEDIN_POST_TIME", "09:00")

        if self.dry_run:
            logger.info("DRY_RUN mode is ON -- Claude will NOT be invoked")
        else:
            logger.info("DRY_RUN mode is OFF -- Claude WILL be invoked")

    def _process_needs_action_item(self, item_path: Path) -> None:
        """Process a single item from /Needs_Action.

        Routes by item prefix (FILE_, EMAIL_, WHATSAPP_, FACEBOOK_, INSTAGRAM_, TWITTER_)
        and passes appropriate context files to triage-inbox.
        """
        logger.info("Processing: %s", item_path.name)

        # Read item metadata before triage for type-aware routing
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

        # Build triage context: VaultItem + handbook (always)
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

        # Auto-execute path for non-sensitive EMAIL_ items
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
        """Process an approved or rejected file.

        For approved items with a known action type: reads YAML frontmatter
        and dispatches directly to the correct executor via _dispatch_action().
        On dispatch failure the file stays in Approved/ for retry.
        All other cases delegate to the process-approval skill.
        """
        log_action_type = "approval_granted" if decision == "approved" else "approval_rejected"
        logger.info("Processing %s: %s", decision, item_path.name)

        # Read frontmatter for action routing
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
            "facebook_reply",
            "facebook_post",
            "instagram_reply",
            "instagram_post",
            "twitter_reply",
            "twitter_post",
            "odoo_action",
            "odoo_create_invoice",
            "odoo_post_invoice",
            "odoo_record_payment",
        ):
            # Dispatch to the correct executor
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

        Nestaro Pilot tier: detects FILE_, EMAIL_, WHATSAPP_, FACEBOOK_, INSTAGRAM_, TWITTER_ prefixes.
        """
        logger.info("Orchestrator startup scan of Needs_Action...")
        count = 0
        plans_dir = self.vault_path / "Plans"

        # All supported VaultItem prefixes (Nestaro Pilot tier)
        known_prefixes = ("FILE_", "EMAIL_", "WHATSAPP_", "FACEBOOK_", "INSTAGRAM_", "TWITTER_")

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

        # Reset Ralph Wiggum state file so stale iteration counts don't persist
        ralph_state = self.vault_path / ".ralph_state"
        try:
            if ralph_state.exists():
                ralph_state.unlink()
        except Exception:
            logger.warning("Could not reset .ralph_state file")

        # Also export RALPH_ITERATION=0 and RALPH_MAX_ITER for the current process
        # so any Claude subprocess started immediately inherits clean state
        os.environ["RALPH_ITERATION"] = "0"
        os.environ.setdefault("RALPH_MAX_ITER", "10")
        os.environ["VAULT_PATH"] = str(self.vault_path)

        # Startup scan
        self._startup_scan()

        # Start watchdog observers
        observer = Observer()

        # Watch /Needs_Action for new triaged items
        needs_handler = _NeedsActionHandler(self)
        observer.schedule(needs_handler, str(self.needs_action_dir), recursive=False)

        # Watch /Approved and /Rejected for HITL decisions
        approved_handler = _ApprovalHandler(self, "approved")
        observer.schedule(approved_handler, str(self.approved_dir), recursive=False)

        rejected_handler = _ApprovalHandler(self, "rejected")
        observer.schedule(rejected_handler, str(self.rejected_dir), recursive=False)

        observer.start()

        # Log watcher start event
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
                        append_log_entry(
                            log_dir=self.log_dir,
                            action_type="error",
                            actor="orchestrator",
                            target=str(item),
                            parameters={"event": "processing_error", "phase": "triage"},
                            result="failure",
                        )

                # Process pending approval decisions
                approvals = list(self._pending_approvals)
                self._pending_approvals.clear()

                for item_path, decision in approvals:
                    try:
                        self._process_approval(item_path, decision)
                    except Exception:
                        logger.exception("Error processing approval %s", item_path)
                        append_log_entry(
                            log_dir=self.log_dir,
                            action_type="error",
                            actor="orchestrator",
                            target=str(item_path),
                            parameters={"event": "approval_error", "decision": decision},
                            result="failure",
                        )

                # Check for expired approval requests each cycle
                self._check_approval_expiry()

                # Check if any scheduled tasks (briefing, social post, LinkedIn) are due
                self._check_schedule()

                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            logger.info("Orchestrator stopped by user (Ctrl+C)")
        finally:
            self._running = False
            observer.stop()
            observer.join()
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
        """Run the CEO/accounting briefing skill once and exit.

        Nestaro Pilot tier uses generate-accounting-briefing.md (Phase 5).
        Falls back to generate-briefing.md if accounting skill not found.
        """
        logger.info("Generating CEO briefing...")

        # Ensure Briefings/ directory exists
        briefings_dir = self.vault_path / "Briefings"
        briefings_dir.mkdir(parents=True, exist_ok=True)

        # Nestaro Pilot tier: prefer generate-accounting-briefing, fallback to generate-briefing
        briefing_skill = self.skills_dir / "generate-accounting-briefing.md"
        if not briefing_skill.exists():
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
            parameters={"skill": briefing_skill.name, "dry_run": self.dry_run},
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

    def run_social_post(self) -> None:
        """Run the social media post generation skill once and exit.

        Generates three platform-specific drafts (Facebook, Instagram, Twitter)
        in vault/Pending_Approval/ for HITL review.
        """
        logger.info("Generating social media post drafts (Facebook, Instagram, Twitter)...")

        social_skill = self.skills_dir / "generate-social-post.md"
        if not social_skill.exists():
            logger.error("Skill not found: %s", social_skill)
            return

        # Ensure Pending_Approval/ exists
        pending_dir = self.vault_path / "Pending_Approval"
        pending_dir.mkdir(parents=True, exist_ok=True)

        goals = self.vault_path / "Business_Goals.md"
        handbook = self.vault_path / "Company_Handbook.md"
        dashboard = self.vault_path / "Dashboard.md"

        context_files: list[Path] = []
        if goals.exists():
            context_files.append(goals)
        if handbook.exists():
            context_files.append(handbook)
        if dashboard.exists():
            context_files.append(dashboard)

        append_log_entry(
            log_dir=self.log_dir,
            action_type="facebook_post",
            actor="orchestrator",
            target="Pending_Approval/",
            parameters={"skill": "generate-social-post", "dry_run": self.dry_run},
            result="success" if not self.dry_run else "skipped",
        )

        success, output = invoke_claude(
            skill_path=social_skill,
            context_files=context_files,
            vault_path=self.vault_path,
            dry_run=self.dry_run,
        )

        if success:
            logger.info("Social post drafts created in Pending_Approval/")
        else:
            logger.error("Social post generation failed: %s", output)

        # Update dashboard after generation
        dashboard_skill = self.skills_dir / "update-dashboard.md"
        invoke_claude(
            skill_path=dashboard_skill,
            context_files=[],
            vault_path=self.vault_path,
            dry_run=self.dry_run,
        )

    def run_linkedin_post(self) -> None:
        """Run the LinkedIn post generation skill once and exit."""
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

        # Update dashboard after LinkedIn post generation
        dashboard_skill = self.skills_dir / "update-dashboard.md"
        invoke_claude(
            skill_path=dashboard_skill,
            context_files=[],
            vault_path=self.vault_path,
            dry_run=self.dry_run,
        )

    # --- Action dispatcher ---

    def _dispatch_action(
        self,
        approval_path: Path,
        action_type: str,
        reply_content: str,
        recipient: str,
    ) -> tuple[bool, str]:
        """Dispatch an approved action to the correct executor.

        earlier prototype routes: email_send, email_draft, whatsapp_reply, linkedin_post
        Nestaro Pilot adds: facebook_reply, facebook_post, instagram_reply, instagram_post,
                   twitter_reply, twitter_post, odoo_action (Phase 3/4)

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

        elif action_type in ("facebook_reply", "facebook_post"):
            # Phase 3: Facebook dispatch via social_post.py
            if self.dry_run:
                return True, f"[DRY_RUN] Would {action_type} to Facebook: {reply_content[:60]}..."
            try:
                from scripts.social_post import post_facebook  # noqa: PLC0415
                user_data_dir = os.getenv("FACEBOOK_USER_DATA_DIR", "playwright-data/facebook")
                post_facebook(
                    content=reply_content,
                    user_data_dir=user_data_dir,
                    vault_path=self.vault_path,
                    dry_run=False,
                )
                return True, f"Facebook {action_type} published"
            except Exception as exc:
                return False, str(exc)

        elif action_type in ("instagram_reply", "instagram_post"):
            # Phase 3: Instagram dispatch via social_post.py
            if self.dry_run:
                return True, f"[DRY_RUN] Would {action_type} to Instagram: {reply_content[:60]}..."
            try:
                from scripts.social_post import post_instagram  # noqa: PLC0415
                user_data_dir = os.getenv("INSTAGRAM_USER_DATA_DIR", "playwright-data/instagram")
                post_instagram(
                    content=reply_content,
                    user_data_dir=user_data_dir,
                    vault_path=self.vault_path,
                    dry_run=False,
                )
                return True, f"Instagram {action_type} published"
            except Exception as exc:
                return False, str(exc)

        elif action_type in ("twitter_reply", "twitter_post"):
            # Phase 3: Twitter/X dispatch via social_post.py
            if self.dry_run:
                return True, f"[DRY_RUN] Would {action_type} to Twitter/X: {reply_content[:60]}..."
            try:
                from scripts.social_post import post_twitter  # noqa: PLC0415
                user_data_dir = os.getenv("TWITTER_USER_DATA_DIR", "playwright-data/twitter")
                post_twitter(
                    content=reply_content,
                    user_data_dir=user_data_dir,
                    vault_path=self.vault_path,
                    dry_run=False,
                )
                return True, f"Twitter {action_type} published"
            except Exception as exc:
                return False, str(exc)

        elif action_type in ("odoo_action", "odoo_create_invoice", "odoo_post_invoice", "odoo_record_payment"):
            # Phase 4: ALL Odoo actions route to process-odoo-action skill (never direct dispatch)
            if self.dry_run:
                return True, f"[DRY_RUN] Would execute {action_type} for {recipient!r}"
            skill = self.skills_dir / "process-odoo-action.md"
            success, output = invoke_claude(
                skill_path=skill,
                context_files=[approval_path],
                vault_path=self.vault_path,
                dry_run=self.dry_run,
            )
            # Check if SYSTEM_ODOO_UNREACHABLE was written (Odoo offline)
            if not success and "ODOO_UNREACHABLE" in output:
                self._write_odoo_unreachable_alert(action_type, approval_path.name)
            return success, output

        else:
            # file_process / payment / unknown → delegate to process-approval skill
            skill = self.skills_dir / "process-approval.md"
            return invoke_claude(
                skill_path=skill,
                context_files=[approval_path],
                vault_path=self.vault_path,
                dry_run=self.dry_run,
            )

    # --- Scheduler ---

    def _check_schedule(self) -> None:
        """Check if any scheduled tasks are due and trigger them.

        Scheduled tasks (configured via .env):
        - CEO Briefing: BRIEFING_DAY (e.g. MON) at BRIEFING_TIME (e.g. 08:00)
        - Social Post: SOCIAL_POST_TIME on weekdays
        - LinkedIn Post: LINKEDIN_POST_TIME on weekdays

        Each task runs at most once per calendar day (UTC).
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        today_str = now.strftime("%Y-%m-%d")
        today_time = now.strftime("%H:%M")

        # Day-of-week map for BRIEFING_DAY env var
        day_map = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4, "SAT": 5, "SUN": 6}
        is_weekday = now.weekday() < 5

        # --- CEO Briefing ---
        briefing_weekday = day_map.get(self.briefing_day, 0)
        if (
            now.weekday() == briefing_weekday
            and today_time >= self.briefing_time
            and self._last_briefing_date != today_str
        ):
            logger.info(
                "Scheduled briefing triggered (day=%s, time=%s)",
                self.briefing_day,
                self.briefing_time,
            )
            self._last_briefing_date = today_str
            try:
                self.run_briefing()
            except Exception:
                logger.exception("Scheduled briefing failed")

        # --- Daily Social Post (weekdays only) ---
        if (
            is_weekday
            and today_time >= self.social_post_time
            and self._last_social_post_date != today_str
        ):
            logger.info(
                "Scheduled social post triggered (time=%s)", self.social_post_time
            )
            self._last_social_post_date = today_str
            try:
                self.run_social_post()
            except Exception:
                logger.exception("Scheduled social post failed")

        # --- Daily LinkedIn Post (weekdays only) ---
        if (
            is_weekday
            and today_time >= self.linkedin_post_time
            and self._last_linkedin_date != today_str
        ):
            logger.info(
                "Scheduled LinkedIn post triggered (time=%s)", self.linkedin_post_time
            )
            self._last_linkedin_date = today_str
            try:
                self.run_linkedin_post()
            except Exception:
                logger.exception("Scheduled LinkedIn post failed")

    # --- Odoo unreachable alert ---

    def _write_odoo_unreachable_alert(self, action_type: str, approval_filename: str) -> None:
        """Write SYSTEM_ODOO_UNREACHABLE.md to Needs_Action/ and Dashboard.md alert.

        Called when odoo-mcp returns ODOO_UNREACHABLE. Idempotent — skips if
        the system file already exists.
        """
        system_file = self.needs_action_dir / "SYSTEM_ODOO_UNREACHABLE.md"
        if system_file.exists():
            return  # Already written; avoid duplicate

        now = datetime.datetime.now(datetime.timezone.utc)
        iso = now.isoformat()
        ts_fmt = now.strftime("%Y-%m-%d %H:%M")

        content = f"""---
type: system
priority: high
status: pending
detected_date: {iso}
action_type: {action_type}
approval_file: {approval_filename}
---

## Odoo Unreachable

The AI employee attempted to execute an Odoo accounting action but could not
connect to Odoo.

**Action attempted**: {action_type}
**Approval file**: {approval_filename} (still in vault/Approved/ for retry)
**Detected**: {ts_fmt} UTC

## Resolution Steps

1. Check Docker: `docker compose ps`
2. Start Odoo if needed: `docker compose up -d`
3. Verify ODOO_URL in `.env` (default: http://localhost:8069)
4. After Odoo is running, move `{approval_filename}` back to `vault/Approved/` to retry.
"""
        try:
            system_file.write_text(content, encoding="utf-8")
            logger.warning("Odoo unreachable — wrote SYSTEM_ODOO_UNREACHABLE.md")
        except Exception:
            logger.exception("Failed to write SYSTEM_ODOO_UNREACHABLE.md")

        # Also append alert to Dashboard.md
        dashboard = self.vault_path / "Dashboard.md"
        if dashboard.exists():
            try:
                dash_content = dashboard.read_text(encoding="utf-8")
                if "Odoo Unreachable" not in dash_content:
                    with open(dashboard, "a", encoding="utf-8") as f:
                        f.write(
                            f"\n\n> **ALERT** ({ts_fmt}): "
                            "Odoo is unreachable. Run `docker compose up -d` to start. "
                            f"Action `{action_type}` is waiting in Approved/ for retry.\n"
                        )
            except Exception:
                logger.exception("Failed to write Odoo alert to Dashboard.md")

        append_log_entry(
            log_dir=self.log_dir,
            action_type="system_alert",
            actor="orchestrator",
            target="SYSTEM_ODOO_UNREACHABLE.md",
            parameters={"action_type": action_type, "approval_file": approval_filename},
            result="failure",
        )

    # --- Approval expiry checker ---

    def _check_approval_expiry(self) -> None:
        """Scan Pending_Approval/ and mark expired approval requests.

        Checks the `expires` ISO timestamp in each APPROVE_*.md frontmatter.
        If the current UTC time is past the expires value, logs the expiry and
        updates the file's status field to 'expired'.
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

                # Update status to expired then move to Done/
                done_dir = self.vault_path / "Done"
                done_dir.mkdir(exist_ok=True)
                done_path = done_dir / item.name

                try:
                    content = item.read_text(encoding="utf-8")
                    updated = re.sub(
                        r"^(status:\s*)pending(\s*)$",
                        r"\1expired\2",
                        content,
                        flags=re.MULTILINE,
                    )
                    item.write_text(updated, encoding="utf-8")
                    item.rename(done_path)
                    logger.info("Moved expired approval to Done/: %s", item.name)
                except Exception:
                    logger.exception("Could not move expired approval %s to Done/", item.name)

                append_log_entry(
                    log_dir=self.log_dir,
                    action_type="approval_expired",
                    actor="orchestrator",
                    target=item.name,
                    parameters={"event": "approval_expired", "expires": expires_str},
                    result="success",
                )

                # Refresh dashboard to reflect the change
                dashboard_skill = self.skills_dir / "update-dashboard.md"
                invoke_claude(
                    skill_path=dashboard_skill,
                    context_files=[],
                    vault_path=self.vault_path,
                    dry_run=self.dry_run,
                )

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

    parser = argparse.ArgumentParser(description="AI employee Orchestrator (Nestaro Pilot tier)")
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
    parser.add_argument(
        "--social-post",
        action="store_true",
        help="Generate Facebook/Instagram/Twitter drafts in Pending_Approval/ and exit",
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
    elif args.social_post:
        orchestrator.run_social_post()
    else:
        try:
            orchestrator.run()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
