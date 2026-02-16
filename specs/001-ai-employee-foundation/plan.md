# Implementation Plan: AI Employee Foundation

**Branch**: `001-ai-employee-foundation` | **Date**: 2026-02-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-ai-employee-foundation/spec.md`

## Summary

Build a file-system-based AI Employee (Bronze tier) that monitors an Inbox folder for dropped files, triages them using Claude Code Agent Skills, creates action plans, manages a HITL approval workflow via file movement, updates an Obsidian dashboard, and generates weekly CEO briefings. All AI functionality is implemented as Agent Skills. Python handles file watching and orchestration; Claude Code handles all reasoning.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: watchdog (file monitoring), python-dotenv (env config)
**Storage**: Local filesystem (Obsidian vault = project root, markdown + JSON)
**Testing**: Manual integration testing (drop files, verify outputs)
**Target Platform**: Windows 11 (local machine)
**Project Type**: Single project
**Performance Goals**: File detection within 30 seconds, end-to-end flow within 5 minutes
**Constraints**: Local-first, no external services required, DRY_RUN by default
**Scale/Scope**: Single freelancer user, ~10-50 files per week

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Local-First Privacy | PASS | All data in local Obsidian vault. No external storage. |
| II. HITL | PASS | File-based approval workflow in /Pending_Approval → /Approved. Sensitive actions never auto-execute. |
| III. Agent Skills | PASS | All AI capabilities as .md skill files in /skills/. No hardcoded prompts. |
| IV. File-Based Communication | PASS | All components communicate via .md files in vault folders. YAML frontmatter on all entities. |
| V. Security by Default | PASS | DRY_RUN=true default. .env for secrets. Audit logging to /Logs/. No secrets in code. |
| VI. Simplicity | PASS | Minimal dependencies (watchdog + dotenv). Python for file ops only. Claude for reasoning only. |

**Gate result**: ALL PASS. Proceeding to implementation.

## Project Structure

### Documentation (this feature)

```text
specs/001-ai-employee-foundation/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0: technology decisions
├── data-model.md        # Phase 1: entity schemas
├── quickstart.md        # Phase 1: setup instructions
├── contracts/           # Phase 1: component interfaces
│   └── skill-contracts.md
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (/sp.tasks)
```

### Source Code (repository root)

```text
watchers/
├── __init__.py              # Package init
├── base_watcher.py          # Abstract base class for all watchers
├── filesystem_watcher.py    # Watches /Inbox for new files
└── orchestrator.py          # Watches /Needs_Action + /Approved, invokes Claude

skills/
├── triage-inbox.md          # Classify items, create plans
├── create-plan.md           # Generate action plans
├── update-dashboard.md      # Regenerate Dashboard.md
├── generate-briefing.md     # Weekly CEO Briefing
└── process-approval.md      # Handle approved/rejected items

Inbox/                       # User drops files here
Needs_Action/                # Watcher outputs triaged items
Plans/                       # AI-generated action plans
Pending_Approval/            # HITL approval requests
Approved/                    # User-approved actions
Rejected/                    # User-rejected actions
Done/                        # Completed/archived items
Logs/                        # Audit logs (YYYY-MM-DD.json)
Briefings/                   # Weekly CEO briefings
Accounting/                  # Financial tracking

Dashboard.md                 # Real-time status view
Company_Handbook.md          # Business rules for AI
Business_Goals.md            # Goals, metrics, thresholds

pyproject.toml               # Python project config
.env.example                 # Environment template
.gitignore                   # Excludes .env, .obsidian, etc.
```

**Structure Decision**: Single project layout. Python code in `/watchers/` (not `/src/` because these are background processes, not a library). Skills in `/skills/` as standalone .md files. Vault folders at root level for direct Obsidian access.

## Complexity Tracking

No constitution violations. No complexity justifications needed.

## Component Architecture

```
[File Drop]
    │
    ▼
filesystem_watcher.py ──── Detects new files in /Inbox
    │                       Creates metadata .md in /Needs_Action
    ▼
orchestrator.py ─────────── Detects new .md in /Needs_Action
    │                       Calls: claude --print --skill skills/triage-inbox.md
    ▼
Claude Code ─────────────── Reads item + Company_Handbook.md
    │                       Creates plan in /Plans
    │                       If sensitive: creates approval in /Pending_Approval
    │                       Updates Dashboard.md
    │                       Logs to /Logs
    ▼
[User reviews in Obsidian]
    │
    ├── Moves to /Approved ──► orchestrator detects
    │                          Calls: claude --skill skills/process-approval.md
    │                          Logs, moves to /Done
    │
    └── Moves to /Rejected ──► orchestrator detects
                               Logs rejection, moves to /Done

[Scheduled/Manual]
    │
    ▼
orchestrator.py --briefing ─► Calls: claude --skill skills/generate-briefing.md
                               Reads /Done, /Logs, Business_Goals.md
                               Writes briefing to /Briefings
                               Updates Dashboard.md
```

## Key Design Decisions

1. **Python does file ops only, Claude does reasoning only**: Clean separation. Python never classifies files or makes decisions. Claude never watches folders or manages processes.

2. **Full dashboard regeneration, not incremental**: Ensures consistency. Dashboard is always derived from current folder state.

3. **JSON Lines for logs, not JSON arrays**: Appendable without parsing the entire file. Each line is an independent entry.

4. **File movement as approval signal**: Simplest possible UX in Obsidian. No special tools needed.

5. **Skills as standalone .md files**: Each skill is self-contained with its own instructions. Can be tested independently by running Claude with just that skill.
