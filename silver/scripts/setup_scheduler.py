"""setup_scheduler.py — Create Windows Task Scheduler entries for Digital FTE Silver.

R6: Uses `schtasks` CLI to register three scheduled tasks:
  1. LinkedIn post generation — weekdays at 09:00
  2. CEO briefing generation — Mondays at 08:00
  3. PM2 health check        — every 5 minutes

Run once as Administrator:
    python scripts/setup_scheduler.py

To remove all tasks:
    python scripts/setup_scheduler.py --remove
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

# Prefer the venv Python if it exists
if VENV_PYTHON.exists():
    PYTHON_EXE = str(VENV_PYTHON)

TASK_DEFINITIONS = [
    {
        "name": "DigitalFTE-LinkedIn",
        "description": "Generate LinkedIn post draft via Digital FTE orchestrator",
        # Weekdays at 09:00
        "schedule": "/sc daily /d MON,TUE,WED,THU,FRI /st 09:00",
        "command": PYTHON_EXE,
        "args": f'-m watchers.orchestrator --linkedin',
        "run_level": "HIGHEST",
    },
    {
        "name": "DigitalFTE-Briefing",
        "description": "Generate CEO briefing via Digital FTE orchestrator",
        # Mondays at 08:00
        "schedule": "/sc weekly /d MON /st 08:00",
        "command": PYTHON_EXE,
        "args": f'-m watchers.orchestrator --briefing',
        "run_level": "HIGHEST",
    },
    {
        "name": "DigitalFTE-PM2Health",
        "description": "PM2 health check — restart stopped Digital FTE processes",
        # Every 5 minutes
        "schedule": "/sc minute /mo 5",
        "command": PYTHON_EXE,
        "args": f'scripts/pm2_healthcheck.py',
        "run_level": "HIGHEST",
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
            logger.error("FAILED (%d): %s\n%s", result.returncode, description, result.stderr.strip())
            return False
    except FileNotFoundError:
        logger.error("schtasks not found. Run this script on Windows.")
        return False
    except subprocess.TimeoutExpired:
        logger.error("Timeout running: %s", " ".join(cmd))
        return False


def create_tasks() -> None:
    """Register all Task Scheduler entries."""
    logger.info("Creating Windows Task Scheduler entries (repo root: %s)", REPO_ROOT)
    logger.info("Python executable: %s", PYTHON_EXE)

    success_count = 0
    for task in TASK_DEFINITIONS:
        name = task["name"]
        cmd = task["command"]
        args = task["args"]
        schedule_parts = task["schedule"].split()
        run_level = task["run_level"]

        schtasks_cmd = [
            "schtasks",
            "/create",
            "/tn", name,
            "/tr", f'"{cmd}" {args}',
            "/sd", "01/01/2026",  # start date (required by some Windows versions)
            "/rl", run_level,
            "/f",  # force overwrite if exists
            "/ru", "SYSTEM",  # run as SYSTEM to avoid login requirement
        ] + schedule_parts

        # Set working directory via a wrapper approach: schtasks doesn't support /d for cwd
        # so we use the start-in field via /it (interactive) or just rely on SYSTEM profile
        # For cwd, wrap in cmd /c "cd /d <repo> && python ..."
        schtasks_cmd = [
            "schtasks",
            "/create",
            "/tn", name,
            "/tr", f'cmd /c "cd /d {REPO_ROOT} && "{cmd}" {args}"',
            "/rl", run_level,
            "/f",
        ] + schedule_parts

        if _run(schtasks_cmd, f"Create task: {name}"):
            success_count += 1
        else:
            logger.warning(
                "Failed to create task %s. "
                "Ensure you are running as Administrator.",
                name,
            )

    logger.info(
        "Setup complete: %d/%d tasks created",
        success_count,
        len(TASK_DEFINITIONS),
    )

    if success_count == len(TASK_DEFINITIONS):
        logger.info("All tasks registered. Verify with: schtasks /query /tn DigitalFTE*")
    else:
        logger.warning(
            "Some tasks failed. Run as Administrator and check schtasks availability."
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
    logger.info("Done removing tasks.")


def list_tasks() -> None:
    """List Digital FTE Task Scheduler entries."""
    _run(
        ["schtasks", "/query", "/tn", "DigitalFTE*", "/fo", "LIST"],
        "Query DigitalFTE* tasks",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Manage Windows Task Scheduler entries for Digital FTE Silver"
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
