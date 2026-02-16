# Quickstart: AI Employee Foundation

**Branch**: `001-ai-employee-foundation` | **Date**: 2026-02-15

## Prerequisites

- Python 3.13+
- uv (Python package manager)
- Claude Code CLI (`claude --version` works)
- Obsidian v1.10.6+ (free)
- Node.js v24+ (for Claude Code)

## Setup

### 1. Install Python dependencies

```bash
cd bronze
uv init --python 3.13
uv add watchdog python-dotenv
```

### 2. Create environment file

```bash
cp .env.example .env
# Edit .env with your settings (DRY_RUN=true by default)
```

### 3. Open Obsidian vault

Open Obsidian → "Open folder as vault" → select the `bronze/` directory.

### 4. Start the file system watcher

```bash
uv run python watchers/filesystem_watcher.py
```

### 5. Start the orchestrator (separate terminal)

```bash
uv run python watchers/orchestrator.py
```

### 6. Test it

Drop a file into the `/Inbox/` folder. Watch:
1. Metadata file appears in `/Needs_Action/` (watcher)
2. Action plan appears in `/Plans/` (orchestrator → Claude)
3. Dashboard.md updates (Claude skill)
4. If sensitive: approval file in `/Pending_Approval/`

### 7. Generate a CEO Briefing (manual)

```bash
uv run python watchers/orchestrator.py --briefing
```

## Folder Structure

```
bronze/                          # Obsidian vault root
├── Dashboard.md                 # Real-time status view
├── Company_Handbook.md          # Business rules
├── Business_Goals.md            # Goals and metrics
├── Inbox/                       # Drop files here
├── Needs_Action/                # Triaged items
├── Plans/                       # AI-generated action plans
├── Pending_Approval/            # Awaiting human approval
├── Approved/                    # User approved
├── Rejected/                    # User rejected
├── Done/                        # Completed items
├── Logs/                        # Audit logs (JSON Lines)
├── Briefings/                   # CEO Briefings
├── watchers/                    # Python scripts
│   ├── base_watcher.py
│   ├── filesystem_watcher.py
│   └── orchestrator.py
└── skills/                      # Claude Code Agent Skills
    ├── triage-inbox.md
    ├── create-plan.md
    ├── update-dashboard.md
    ├── generate-briefing.md
    └── process-approval.md
```

## Verification

| Check | Command / Action | Expected |
|-------|-----------------|----------|
| Watcher running | Drop file in /Inbox | .md appears in /Needs_Action within 30s |
| Triage works | Check /Plans after drop | Plan file with steps created |
| Dashboard updates | Open Dashboard.md | Shows recent activity |
| HITL works | Move approval file to /Approved | Logged and moved to /Done |
| Briefing generates | Run orchestrator --briefing | File in /Briefings |
| Logs captured | Check /Logs/today.json | Structured entries present |
