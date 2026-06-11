---
id: "009"
title: "Phase 6: Ralph Wiggum Stop Hook Complete"
stage: green
date: "2026-03-14"
surface: agent
model: claude-sonnet-4-6
feature: 001-nestaro-pilot
branch: 001-ai-employee-foundation
user: architect
command: "/sp.implement phase 6"
labels: ["phase-6", "stop-hook", "ralph-wiggum", "loop", "claude-code-hooks", "autonomous"]
links:
  spec: "./specs/001-nestaro-pilot/spec.md"
  tasks: "./specs/001-nestaro-pilot/tasks.md"
  data-model: "./specs/001-nestaro-pilot/data-model.md"
  adr: "null"
  pr: "null"
files:
  - ./.claude/hooks/stop.py
  - ./.claude/settings.json
  - ./watchers/orchestrator.py
  - ./specs/001-nestaro-pilot/tasks.md
tests:
  - "Manual: place 3 .md files in vault/Needs_Action/, run claude -p 'process vault' → verify hook re-injects up to 10 times"
  - "Manual: empty Needs_Action/, run claude → verify hook exits 0 immediately"
  - "Manual: place 1 file, set RALPH_MAX_ITER=1 → verify hook writes SYSTEM_MAX_ITERATIONS alert and exits 0"
  - "Manual: restart orchestrator → verify .ralph_state is deleted and RALPH_ITERATION=0 set in env"
---

## Prompt

```
/sp.implement phase 6.
```

## Response Summary

Implemented Phase 6 (T040–T041): Ralph Wiggum Stop Hook — Claude does not exit
while items remain in vault/Needs_Action/.

### T040 — `./.claude/hooks/stop.py`

Claude Code Stop hook. Executed by the Claude Code runtime just before Claude
would exit.

**Decision logic**:

```
count = glob vault/Needs_Action/*.md (exclude SYSTEM_*, .gitkeep)
iteration = read from RALPH_ITERATION env var OR vault/.ralph_state file

if count == 0:
    _reset_iteration()
    sys.exit(0)          # clean exit

if iteration >= RALPH_MAX_ITER:
    _write_max_iter_alert(items)
    _reset_iteration()
    sys.exit(0)          # cap reached, write alert, exit

# Items remain, under cap → block exit
_write_iteration(iteration + 1)
print(re_inject_prompt)  # stdout → Claude's next user message
sys.exit(2)              # Claude Code: block exit, re-inject
```

**State management**: uses `vault/.ralph_state` (single integer file) as the
durable iteration counter. This works correctly even when the hook process
doesn't inherit `RALPH_ITERATION` from an orchestrator parent — which is the
common case when Claude is run directly from the CLI.

**Re-injection prompt** (stdout → Claude's next message):
- Lists remaining item names (up to 10, with overflow count)
- States current iteration N/MAX
- Reminds Claude of the triage workflow: read frontmatter → run skill → move to Done/
- Includes the vault path explicitly

**SYSTEM_MAX_ITERATIONS alert** (written when cap hit):
- Idempotent: only one alert per session (checks for existing glob match)
- Lists up to 20 unprocessed item names
- Instructions for manual resolution

**Also created**: `./.claude/settings.json` registering the hook:
```json
{
  "hooks": {
    "Stop": [{ "hooks": [{ "type": "command", "command": "python .claude/hooks/stop.py" }] }]
  }
}
```

### T041 — Orchestrator env injection

Two changes to `./watchers/orchestrator.py`:

1. **`invoke_claude()`** — builds `ralph_env = os.environ.copy()` then:
   - `ralph_env.setdefault("RALPH_ITERATION", "0")` — reset for each top-level call
   - `ralph_env.setdefault("RALPH_MAX_ITER", "10")`
   - `ralph_env["VAULT_PATH"] = str(vault_path)` — always override so hook finds vault
   - Passes `env=ralph_env` to `subprocess.run`

2. **`run()`** — at startup before the watchdog observer starts:
   - Deletes `vault/.ralph_state` if present (prevents stale counts from prior session)
   - Sets `os.environ["RALPH_ITERATION"] = "0"` in the current process
   - Sets `os.environ.setdefault("RALPH_MAX_ITER", "10")`
   - Sets `os.environ["VAULT_PATH"] = str(self.vault_path)`

## Outcome

Phase 6 (T040–T041) **complete**. Both tasks marked `[x]` in tasks.md.

**Architecture decisions enforced:**
- File-based state (`vault/.ralph_state`) rather than pure env-var inheritance,
  because env vars cannot propagate from subprocess → parent
- SYSTEM_ prefixed files excluded from actionable item count — these are human-
  resolved alerts, not Claude work items
- Idempotent alert: `SYSTEM_MAX_ITERATIONS_*.md` glob prevents duplicate alerts
  in the same session
- `sys.exit(2)` is the Claude Code hook contract for "block exit and re-inject stdout"

**Ready for**: Phase 7 — US5 Comprehensive Error Recovery (T042–T047)
