"""Audit logging utility for the AI Employee (Gold tier).

Writes structured log entries to Logs/YYYY-MM-DD.md as Markdown tables.
Each entry is appended as a new row, rendering natively in Obsidian.

Gold tier extends Silver with additional action_types for social media
channels (Facebook, Instagram, Twitter) and Odoo accounting operations.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

_MD_HEADER = """---
type: audit_log
date: "{date}"
---

# Audit Log: {date}

| Timestamp | Action | Actor | Target | Result | Details |
|-----------|--------|-------|--------|--------|---------|
"""

# Valid action_types (Silver + Gold extensions)
# Silver: file_triage, email_triage, whatsapp_triage, plan_created,
#         dashboard_updated, approval_requested, approval_granted,
#         approval_rejected, briefing_generated, file_moved, error
# Gold additions:
#   Social: facebook_triage, facebook_reply, facebook_post,
#           instagram_triage, instagram_reply, instagram_post,
#           twitter_triage, twitter_reply, twitter_post
#   Odoo:   odoo_create_invoice, odoo_post_invoice, odoo_record_payment,
#           odoo_get_invoices, odoo_get_summary
#   System: auth_failure, system_alert, ralph_wiggum_loop,
#           linkedin_generated, email_sent, email_drafted


def append_log_entry(
    log_dir: str | Path,
    action_type: str,
    actor: str,
    target: str,
    parameters: dict,
    result: str,
    approval_status: str = "not_required",
) -> Path:
    """Append a structured audit log entry to today's log file.

    Args:
        log_dir: Path to the Logs/ directory.
        action_type: One of the valid action_types listed above.
        actor: Who performed the action (e.g., orchestrator, gmail_watcher,
               facebook_watcher, odoo_mcp, ralph_wiggum).
        target: File or entity acted upon.
        parameters: Action-specific key-value pairs.
        result: One of: success, failure, skipped.
        approval_status: One of: not_required, pending, approved, rejected.

    Returns:
        Path to the log file that was written to.
    """
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    log_file = log_dir / f"{date_str}.md"

    entry = {
        "timestamp": now.isoformat(),
        "action_type": action_type,
        "actor": actor,
        "target": target,
        "parameters": parameters,
        "result": result,
        "approval_status": approval_status,
    }

    # Create file with Markdown header if it doesn't exist
    if not log_file.exists():
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(_MD_HEADER.format(date=date_str))

    # Format parameters as compact string for the table cell
    details = ", ".join(f"{k}: {v}" for k, v in parameters.items())
    # Escape pipe characters so they don't break the Markdown table
    details = details.replace("|", "\\|")
    target_escaped = target.replace("|", "\\|")

    time_str = now.strftime("%H:%M:%S")
    row = f"| {time_str} | {action_type} | {actor} | {target_escaped} | {result} | {details} |\n"

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(row)

    # Also write a hidden JSON block at the end for machine-readable parsing
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"<!-- {json.dumps(entry)} -->\n")

    logger.debug("Logged %s: %s -> %s (%s)", action_type, actor, target, result)
    return log_file


def read_recent_logs(log_dir: str | Path, days: int = 7) -> list[dict]:
    """Read and parse log entries from the last N days.

    Args:
        log_dir: Path to the Logs/ directory.
        days: Number of days to look back (default: 7).

    Returns:
        List of parsed log entry dicts, newest first.
    """
    log_dir = Path(log_dir)
    entries = []

    if not log_dir.exists():
        return entries

    now = datetime.now(timezone.utc)

    for i in range(days):
        day = now.date() - __import__("datetime").timedelta(days=i)
        log_file = log_dir / f"{day.isoformat()}.md"

        if not log_file.exists():
            continue

        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Parse JSON from HTML comments
                if line.startswith("<!-- {") and line.endswith("-->"):
                    json_str = line[5:-4].strip()
                    try:
                        entries.append(json.loads(json_str))
                    except json.JSONDecodeError:
                        logger.warning("Skipping malformed log line in %s", log_file)

    # Sort newest first
    entries.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    return entries
