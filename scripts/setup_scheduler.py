"""setup_scheduler.py — Create Windows Task Scheduler entries for Nestaro Pilot Nestaro Pilot.

Nestaro Pilot tier registers 6 scheduled tasks (vs earlier prototype's 3):
  1. DigitalFTE-PM2Startup    — start all 8 PM2 processes on Windows login
  2. DigitalFTE-Briefing      — CEO accounting briefing (Mon 08:00 by default)
  3. DigitalFTE-SocialPost    — daily social post drafts (weekdays 10:00)
  4. DigitalFTE-LinkedIn      — LinkedIn post draft (weekdays 09:00)
  5. DigitalFTE-PM2Health     — PM2 health check every 5 minutes
  6. DigitalFTE-WeeklyHealth  — verbose weekly health report (Sunday 07:00)

Run once as Administrator:
    python scripts/setup_scheduler.py

To remove all tasks:
    python scripts/setup_scheduler.py --remove

To list current task status:
    python scripts/setup_scheduler.py --list
"""

import argparse
import logging
import shutil
import subprocess
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [setup_scheduler] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent
PYTHON_EXE = shutil.which("python") or shutil.which("python3") or sys.executable
VENV_PYTHON = REPO_ROOT / ".venv" / "Scripts" / "python.exe"

# Prefer venv Python if present
if VENV_PYTHON.exists():
    PYTHON_EXE = str(VENV_PYTHON)

# PM2 executable (resolved at runtime; typically on PATH via npm global)
PM2_EXE = shutil.which("pm2") or "pm2"

TASK_DEFINITIONS = [
    # ── 1. PM2 startup on login ─────────────────────────────────────────────
    {
        "name": "DigitalFTE-PM2Startup",
        "description": "Start all 8 Nestaro Pilot PM2 processes on Windows login",
        # ONLOGON trigger: no /sc needed — uses /sc onlogon
        "schedule": "/sc onlogon",
        "command": PM2_EXE,
        "args": f'start "{REPO_ROOT / "scripts" / "pm2_ecosystem.config.js"}"',
        "run_level": "HIGHEST",
        "cwd": str(REPO_ROOT),
    },

    # ── 2. CEO Briefing (Monday 08:00 by default) ───────────────────────────
    {
        "name": "DigitalFTE-Briefing",
        "description": "Generate CEO accounting briefing via Nestaro Pilot Nestaro Pilot orchestrator",
        "schedule": "/sc weekly /d MON /st 08:00",
        "command": PYTHON_EXE,
        "args": "main.py briefing",
        "run_level": "HIGHEST",
        "cwd": str(REPO_ROOT),
    },

    # ── 3. Daily Social Post generation (weekdays 10:00) ────────────────────
    {
        "name": "DigitalFTE-SocialPost",
        "description": "Generate Facebook/Instagram/Twitter post drafts for HITL approval",
        "schedule": "/sc daily /d MON,TUE,WED,THU,FRI /st 10:00",
        "command": PYTHON_EXE,
        "args": "main.py social-post",
        "run_level": "HIGHEST",
        "cwd": str(REPO_ROOT),
    },

    # ── 4. LinkedIn Post generation (weekdays 09:00) ─────────────────────────
    {
        "name": "DigitalFTE-LinkedIn",
        "description": "Generate LinkedIn post draft via Nestaro Pilot Nestaro Pilot orchestrator",
        "schedule": "/sc daily /d MON,TUE,WED,THU,FRI /st 09:00",
        "command": PYTHON_EXE,
        "args": "main.py linkedin",
        "run_level": "HIGHEST",
        "cwd": str(REPO_ROOT),
    },

    # ── 5. PM2 health check every 5 minutes ─────────────────────────────────
    {
        "name": "DigitalFTE-PM2Health",
        "description": "PM2 health check — restart stopped Nestaro Pilot tier processes",
        "schedule": "/sc minute /mo 5",
        "command": PYTHON_EXE,
        "args": "main.py healthcheck",
        "run_level": "HIGHEST",
        "cwd": str(REPO_ROOT),
    },

    # ── 6. Weekly verbose health report (Sunday 07:00) ──────────────────────
    {
        "name": "DigitalFTE-WeeklyHealth",
        "description": "Weekly verbose PM2 health report for Nestaro Pilot tier",
        "schedule": "/sc weekly /d SUN /st 07:00",
        "command": PYTHON_EXE,
        "args": "main.py healthcheck",
        "run_level": "HIGHEST",
        "cwd": str(REPO_ROOT),
    },
]


def _run(cmd: list[str], description: str) -> bool:
    """Run a subprocess command and log result. Returns True on success."""
    logger.info("%s ...", description)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            logger.info("OK: %s", description)
            if result.stdout.strip():
                logger.debug(result.stdout.strip())
            return True
        else:
            logger.error(
                "FAILED (%d): %s\n%s",
                result.returncode, description, result.stderr.strip(),
            )
            return False
    except FileNotFoundError:
        logger.error("schtasks not found. This script must run on Windows.")
        return False
    except subprocess.TimeoutExpired:
        logger.error("Timeout running: %s", " ".join(cmd))
        return False


def create_tasks() -> None:
    """Register all Task Scheduler entries."""
    logger.info("Creating Windows Task Scheduler entries (repo root: %s)", REPO_ROOT)
    logger.info("Python executable: %s", PYTHON_EXE)
    logger.info("PM2 executable: %s", PM2_EXE)

    success_count = 0
    for task in TASK_DEFINITIONS:
        name = task["name"]
        cmd = task["command"]
        args = task["args"]
        cwd = task.get("cwd", str(REPO_ROOT))
        schedule_parts = task["schedule"].split()
        run_level = task["run_level"]

        # Wrap in cmd /c "cd /d <cwd> && <command> <args>" for working directory
        schtasks_cmd = [
            "schtasks",
            "/create",
            "/tn", name,
            "/tr", f'cmd /c "cd /d {cwd} && "{cmd}" {args}"',
            "/rl", run_level,
            "/f",           # force overwrite if task already exists
        ] + schedule_parts

        if _run(schtasks_cmd, f"Create task: {name}"):
            success_count += 1
        else:
            logger.warning(
                "Failed to create task %s. Ensure you are running as Administrator.",
                name,
            )

    logger.info(
        "Setup complete: %d/%d tasks created",
        success_count,
        len(TASK_DEFINITIONS),
    )

    if success_count == len(TASK_DEFINITIONS):
        logger.info(
            "All tasks registered. Verify with: schtasks /query /tn DigitalFTE* /fo LIST"
        )
    else:
        logger.warning(
            "Some tasks failed (%d/%d). Run as Administrator and retry.",
            len(TASK_DEFINITIONS) - success_count,
            len(TASK_DEFINITIONS),
        )


def remove_tasks() -> None:
    """Delete all registered Task Scheduler entries."""
    logger.info("Removing Windows Task Scheduler entries...")
    for task in TASK_DEFINITIONS:
        name = task["name"]
        _run(
            ["schtasks", "/delete", "/tn", name, "/f"],
            f"Remove task: {name}",
        )
    logger.info("All DigitalFTE tasks removed.")


def list_tasks() -> None:
    """List Nestaro Pilot Task Scheduler entries."""
    _run(
        ["schtasks", "/query", "/tn", "DigitalFTE*", "/fo", "LIST"],
        "Query DigitalFTE* tasks",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Manage Windows Task Scheduler entries for Nestaro Pilot Nestaro Pilot (6 tasks)"
    )
    parser.add_argument(
        "--remove",
        action="store_true",
        help="Remove all DigitalFTE Task Scheduler entries",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all DigitalFTE Task Scheduler entries",
    )
    args = parser.parse_args()

    if args.remove:
        remove_tasks()
    elif args.list:
        list_tasks()
    else:
        create_tasks()


if __name__ == "__main__":
    main()
