#!/usr/bin/env python3
"""Ralph Wiggum Stop Hook — blocks Claude from exiting while vault/Needs_Action/ has items.

Claude Code Stop hook (transport: stdin JSON payload).

Behaviour:
  - Reads vault/Needs_Action/*.md (excluding SYSTEM_ and .gitkeep)
  - Reads RALPH_ITERATION (env or state file, default 0)
  - Reads RALPH_MAX_ITER (env, default 10)
  - If items remain AND iteration < max_iter:
      - Increments iteration counter in state file
      - Prints orchestrator re-injection prompt to stdout
      - Exits with code 2 (Claude Code: block exit, re-inject stdout as new prompt)
  - If no items remain OR max_iter reached:
      - If max_iter reached with items remaining: writes SYSTEM_MAX_ITERATIONS alert
      - Exits with code 0 (Claude Code: allow exit)

State file: vault/.ralph_state (single integer — current iteration count)
This file approach works regardless of whether the hook inherits RALPH_ITERATION
from the orchestrator environment.

Exit codes:
  0 — allow Claude to exit
  2 — block exit; stdout is re-injected as the next user prompt
"""

import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


# ── Config ─────────────────────────────────────────────────────────────────────

def _resolve_vault_path() -> Path:
    """Resolve vault/ path from VAULT_PATH env var or common defaults."""
    raw = os.environ.get("VAULT_PATH", "")
    if raw:
        vp = Path(raw)
        if vp.is_absolute():
            return vp
        # Relative to the gold/ repo root (parent of .claude/)
        hook_dir = Path(__file__).resolve().parent          # .claude/hooks/
        repo_root = hook_dir.parent.parent                  # gold/
        return (repo_root / vp).resolve()

    # Auto-detect: look for vault/ relative to repo root
    hook_dir = Path(__file__).resolve().parent
    repo_root = hook_dir.parent.parent
    candidate = repo_root / "vault"
    if candidate.is_dir():
        return candidate

    # Fallback: current working directory / vault
    return (Path.cwd() / "vault").resolve()


VAULT_PATH = _resolve_vault_path()
NEEDS_ACTION_DIR = VAULT_PATH / "Needs_Action"
STATE_FILE = VAULT_PATH / ".ralph_state"
RALPH_MAX_ITER = int(os.environ.get("RALPH_MAX_ITER", "10"))


# ── State file helpers ─────────────────────────────────────────────────────────

def _read_iteration() -> int:
    """Read current iteration from env var (priority) or state file."""
    env_val = os.environ.get("RALPH_ITERATION", "")
    if env_val.isdigit():
        return int(env_val)
    try:
        return int(STATE_FILE.read_text(encoding="utf-8").strip())
    except Exception:
        return 0


def _write_iteration(n: int) -> None:
    """Persist iteration counter to state file."""
    try:
        STATE_FILE.write_text(str(n), encoding="utf-8")
    except Exception as e:
        print(f"[ralph] Warning: could not write state file: {e}", file=sys.stderr)


def _reset_iteration() -> None:
    """Reset iteration counter (called on clean exit)."""
    try:
        if STATE_FILE.exists():
            STATE_FILE.unlink()
    except Exception:
        pass


# ── Vault scanner ──────────────────────────────────────────────────────────────

def _count_actionable_items() -> tuple[int, list[str]]:
    """Count items in Needs_Action/ that are not SYSTEM_ files or .gitkeep.

    Returns (count, list_of_filenames).
    """
    if not NEEDS_ACTION_DIR.is_dir():
        return 0, []

    items = []
    for f in NEEDS_ACTION_DIR.iterdir():
        if not f.is_file():
            continue
        if f.suffix != ".md":
            continue
        if f.name == ".gitkeep":
            continue
        if f.name.startswith("SYSTEM_"):
            continue  # System alerts are human-resolved, not Claude items
        items.append(f.name)

    return len(items), sorted(items)


# ── Alert writer ───────────────────────────────────────────────────────────────

def _write_max_iter_alert(remaining_items: list[str]) -> None:
    """Write SYSTEM_MAX_ITERATIONS alert to Needs_Action/ when loop cap is hit."""
    if not NEEDS_ACTION_DIR.is_dir():
        return

    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y%m%d_%H%M%S")
    iso = now.isoformat()

    filename = f"SYSTEM_MAX_ITERATIONS_{ts}.md"
    filepath = NEEDS_ACTION_DIR / filename

    # Idempotent — skip if an alert already exists
    existing = list(NEEDS_ACTION_DIR.glob("SYSTEM_MAX_ITERATIONS_*.md"))
    if existing:
        return

    items_yaml = "\n".join(f"  - {name}" for name in remaining_items[:20])
    overflow = len(remaining_items) - 20 if len(remaining_items) > 20 else 0

    content = f"""---
type: system
priority: high
status: pending
detected_date: {iso}
iteration_cap: {RALPH_MAX_ITER}
unprocessed_count: {len(remaining_items)}
---

## Max Iterations Reached

The Ralph Wiggum loop reached the maximum iteration cap ({RALPH_MAX_ITER}) while
items remained in `vault/Needs_Action/`. Claude has been allowed to exit.

**Unprocessed items ({len(remaining_items)})**:
{items_yaml}
{"  - ...and " + str(overflow) + " more" if overflow else ""}

## Resolution

1. Review the items in `vault/Needs_Action/` manually
2. Check `vault/Logs/` for errors that may have prevented processing
3. Restart the orchestrator: `python main.py orchestrator`
4. If items require human input, process them through the vault pipeline

*Alert generated: {iso}*
"""

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=NEEDS_ACTION_DIR,
            suffix=".tmp",
            delete=False,
        ) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)
        tmp_path.rename(filepath)
    except Exception as e:
        print(f"[ralph] Warning: could not write max-iter alert: {e}", file=sys.stderr)


# ── Orchestrator re-injection prompt ──────────────────────────────────────────

def _build_reinject_prompt(count: int, items: list[str], iteration: int) -> str:
    """Build the re-injection prompt printed to stdout (becomes Claude's next message)."""
    item_list = "\n".join(f"  - {name}" for name in items[:10])
    overflow = count - 10 if count > 10 else 0

    return f"""Continue processing vault/Needs_Action/ items.

There are {count} item(s) remaining to process (iteration {iteration + 1}/{RALPH_MAX_ITER}):

{item_list}
{"  - ...and " + str(overflow) + " more" if overflow else ""}

For each item:
1. Read the frontmatter to determine type and priority
2. Run the triage-inbox skill if no PLAN_ file exists yet
3. If approval_required=true, ensure an APPROVAL_ file exists in Pending_Approval/
4. If approval_required=false, execute the action and move to Done/
5. Write an AuditLogEntry to vault/Logs/

Work through items in priority order (high → medium → low).
Vault path: {VAULT_PATH}
"""


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    # Read stop hook payload from stdin (Claude Code sends JSON)
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        payload = {}

    stop_reason = payload.get("stop_reason", "end_turn")

    # Parse iteration state
    iteration = _read_iteration()

    # Count actionable items
    count, items = _count_actionable_items()

    print(
        f"[ralph] vault={VAULT_PATH} | needs_action={count} | "
        f"iteration={iteration}/{RALPH_MAX_ITER} | stop_reason={stop_reason}",
        file=sys.stderr,
    )

    # ── Decision ──────────────────────────────────────────────────────────────

    if count == 0:
        # No items left — allow clean exit
        print("[ralph] No actionable items remain. Allowing exit.", file=sys.stderr)
        _reset_iteration()
        sys.exit(0)

    if iteration >= RALPH_MAX_ITER:
        # Cap reached — write alert and allow exit
        print(
            f"[ralph] Max iterations ({RALPH_MAX_ITER}) reached with {count} items "
            "remaining. Writing alert and allowing exit.",
            file=sys.stderr,
        )
        _write_max_iter_alert(items)
        _reset_iteration()
        sys.exit(0)

    # Items remain and under cap — block exit and re-inject
    new_iteration = iteration + 1
    _write_iteration(new_iteration)

    print(
        f"[ralph] {count} item(s) remain. Re-injecting (iteration {new_iteration}/{RALPH_MAX_ITER}).",
        file=sys.stderr,
    )

    # Stdout becomes the new user message to Claude
    print(_build_reinject_prompt(count, items, iteration))

    sys.exit(2)


if __name__ == "__main__":
    main()
