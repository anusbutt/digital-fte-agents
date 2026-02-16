# Research: AI Employee Foundation

**Branch**: `001-ai-employee-foundation` | **Date**: 2026-02-15

## R1: File System Monitoring on Windows 11

**Decision**: Use Python `watchdog` library for cross-platform file system monitoring.

**Rationale**: `watchdog` uses native OS events (ReadDirectoryChangesW on Windows) for low-latency detection. It's the most popular Python file monitoring library, well-maintained, and provides a clean event-driven API. Meets the 30-second detection requirement with sub-second latency.

**Alternatives considered**:
- `watchfiles` (Rust-based): Faster but less mature, fewer docs
- `polling` (manual os.stat loop): Simple but high latency, CPU wasteful
- `inotify` (Linux only): Not cross-platform

## R2: Python Project Management

**Decision**: Use `uv` for Python project management with `pyproject.toml`.

**Rationale**: `uv` is the modern standard for Python package management. Fast, handles virtual environments automatically, supports `pyproject.toml` natively. Required Python 3.13+ per hackathon prerequisites.

**Alternatives considered**:
- `pip` + `venv`: Traditional but slower, more manual steps
- `poetry`: Heavier, slower resolution
- `conda`: Overkill for this project size

## R3: Claude Code Agent Skills Pattern

**Decision**: Implement each AI capability as a `.md` skill file in a `/skills/` directory at project root. Skills are invoked by the orchestrator passing the skill content as context to Claude Code CLI.

**Rationale**: Per hackathon requirements, "All AI functionality should be implemented as Agent Skills." Skills are markdown files containing instructions that Claude Code follows. This makes AI behavior version-controlled, reviewable, and modifiable without code changes.

**Alternatives considered**:
- Hardcoded prompts in Python: Not reviewable, not version-friendly
- YAML config: Less expressive than markdown for complex instructions

## R4: Orchestrator Pattern

**Decision**: Python orchestrator script that watches /Needs_Action and /Approved folders, then invokes Claude Code CLI with appropriate skill files using `subprocess`.

**Rationale**: The orchestrator bridges the gap between file watchers (Python) and the AI brain (Claude Code). It uses `subprocess.run()` to call `claude` CLI with `--print` flag for non-interactive execution. This keeps Python simple (just file ops + subprocess) and Claude Code handles all reasoning.

**Alternatives considered**:
- Direct Claude API calls from Python: More complex, requires API key management
- Single monolithic script: Violates separation of concerns, harder to debug

## R5: Audit Log Format

**Decision**: JSON Lines format (one JSON object per line) in daily files at `/Logs/YYYY-MM-DD.json`.

**Rationale**: JSON Lines is appendable (no need to parse full file to add entry), human-readable, and parseable by the CEO Briefing skill. Daily rotation keeps files manageable. Standard structured logging pattern.

**Alternatives considered**:
- Single JSON array: Requires reading/parsing entire file to append
- CSV: Less structured, harder to extend with new fields
- SQLite: Overkill, not readable in Obsidian

## R6: Dashboard Update Strategy

**Decision**: Full regeneration of Dashboard.md on each update, not incremental edits.

**Rationale**: Dashboard.md is a summary view. Regenerating it from current folder state ensures consistency. The AI reads all folders, counts items, and rewrites the dashboard. This avoids state drift from partial updates. File is small enough that regeneration is fast.

**Alternatives considered**:
- Incremental append: Risks state drift, harder to maintain sections
- Template with placeholders: More complex, same result

## R7: HITL File-Based Approval

**Decision**: Approval workflow uses file movement between folders as the approval signal. Orchestrator watches /Approved and /Rejected using the same watchdog mechanism.

**Rationale**: File movement is the simplest possible approval UX in Obsidian -- user just drags a file. No special UI needed. The orchestrator detects the move event and triggers the appropriate action. Aligns with Constitution Principle IV (file-based communication).

**Alternatives considered**:
- Checkbox in markdown: Requires parsing file content, less reliable
- Separate approval CLI: Extra tool for user to learn
- Web UI: Out of scope for Bronze tier
