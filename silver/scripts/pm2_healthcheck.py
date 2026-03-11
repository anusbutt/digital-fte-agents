"""pm2_healthcheck.py — Check all Digital FTE PM2 processes and restart stopped ones.

T042: Runs `pm2 jlist` to get JSON process list, checks each process is "online",
restarts any that are "stopped", "errored", or "crashed". Logs results via
watchers.logger.

Called by Task Scheduler every 5 minutes (configured in setup_scheduler.py).

Usage:
    python scripts/pm2_healthcheck.py
    python scripts/pm2_healthcheck.py --dry-run
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from pathlib import Path

# Add repo root to path so watchers.logger is importable
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv

load_dotenv(REPO_ROOT / ".env")

from watchers.logger import append_log_entry  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [pm2-health] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Vault path for audit logs
VAULT_PATH = Path(os.getenv("VAULT_PATH", REPO_ROOT / "vault"))
LOG_DIR = VAULT_PATH / "Logs"

# Expected process names (must match pm2_ecosystem.config.js)
EXPECTED_PROCESSES = {
    "filesystem-watcher",
    "gmail-watcher",
    "whatsapp-watcher",
    "orchestrator",
    "email-mcp",
}

# PM2 statuses considered healthy
HEALTHY_STATUSES = {"online"}

# PM2 statuses that warrant a restart attempt
RESTART_STATUSES = {"stopped", "errored", "crashed"}


def get_pm2_process_list() -> list[dict]:
    """Run `pm2 jlist` and return parsed JSON process list.

    Returns empty list on any failure (PM2 not installed, no processes).
    """
    try:
        result = subprocess.run(
            ["pm2", "jlist"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            logger.error("pm2 jlist failed (exit %d): %s", result.returncode, result.stderr)
            return []
        return json.loads(result.stdout)
    except FileNotFoundError:
        logger.error("pm2 not found. Install with: npm install -g pm2")
        return []
    except json.JSONDecodeError as exc:
        logger.error("Could not parse pm2 jlist output: %s", exc)
        return []
    except subprocess.TimeoutExpired:
        logger.error("pm2 jlist timed out")
        return []


def restart_process(name: str, dry_run: bool) -> bool:
    """Restart a PM2 process by name. Returns True on success."""
    if dry_run:
        logger.info("[DRY_RUN] Would restart PM2 process: %s", name)
        return True

    try:
        result = subprocess.run(
            ["pm2", "restart", name],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            logger.info("Restarted PM2 process: %s", name)
            return True
        else:
            logger.error("Failed to restart %s (exit %d): %s", name, result.returncode, result.stderr)
            return False
    except subprocess.TimeoutExpired:
        logger.error("Timeout restarting PM2 process: %s", name)
        return False


def run_healthcheck(dry_run: bool = False) -> None:
    """Main health check: inspect all PM2 processes and restart unhealthy ones."""
    logger.info("Starting PM2 health check (dry_run=%s)", dry_run)

    processes = get_pm2_process_list()

    if not processes:
        logger.warning("No PM2 processes found or PM2 not running")
        append_log_entry(
            log_dir=LOG_DIR,
            action_type="error",
            actor="pm2_healthcheck",
            target="pm2",
            parameters={"event": "no_processes", "dry_run": dry_run},
            result="failure",
        )
        return

    # Build a name → status map from pm2 jlist
    process_map: dict[str, str] = {}
    for proc in processes:
        name = proc.get("name", "")
        status = proc.get("pm2_env", {}).get("status", "unknown")
        process_map[name] = status

    healthy: list[str] = []
    restarted: list[str] = []
    missing: list[str] = []
    failed_restart: list[str] = []

    for expected in sorted(EXPECTED_PROCESSES):
        if expected not in process_map:
            logger.warning("PM2 process not found: %s", expected)
            missing.append(expected)
            continue

        status = process_map[expected]

        if status in HEALTHY_STATUSES:
            logger.info("OK: %s (%s)", expected, status)
            healthy.append(expected)

        elif status in RESTART_STATUSES:
            logger.warning("Unhealthy process %s (status=%s) — restarting", expected, status)
            success = restart_process(expected, dry_run)
            if success:
                restarted.append(expected)
            else:
                failed_restart.append(expected)

        else:
            logger.info("Process %s has status=%s (not restarting)", expected, status)
            healthy.append(expected)

    # Log summary to audit log
    result_status = "success" if not failed_restart and not missing else "failure"
    append_log_entry(
        log_dir=LOG_DIR,
        action_type="dashboard_updated",
        actor="pm2_healthcheck",
        target="pm2",
        parameters={
            "healthy": healthy,
            "restarted": restarted,
            "missing": missing,
            "failed_restart": failed_restart,
            "dry_run": dry_run,
        },
        result=result_status,
    )

    logger.info(
        "Health check complete — healthy: %d, restarted: %d, missing: %d, failed: %d",
        len(healthy),
        len(restarted),
        len(missing),
        len(failed_restart),
    )

    if missing:
        logger.warning(
            "Missing processes: %s. Start with: pm2 start scripts/pm2_ecosystem.config.js",
            missing,
        )
    if failed_restart:
        logger.error(
            "Failed to restart: %s. Manual intervention required.",
            failed_restart,
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="PM2 health check for Digital FTE Silver processes"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log unhealthy processes but do not restart them",
    )
    args = parser.parse_args()
    run_healthcheck(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
