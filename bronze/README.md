# AI Employee - Bronze Tier Digital FTE

**Tier**: Bronze | **Hackathon**: Panaversity Hackathon 0 | **Category**: Personal AI Employee

A file-system-based AI Employee that monitors an Inbox folder for dropped files, triages and classifies them, creates action plans, manages a Human-in-the-Loop (HITL) approval workflow, updates an Obsidian dashboard, and generates weekly CEO briefings. All AI functionality is implemented as Claude Code Agent Skills.

## Architecture

```
[File Drop]
    |
    v
filesystem_watcher.py --- Detects new files in /Inbox
    |                      Creates metadata .md in /Needs_Action
    v
orchestrator.py ---------- Detects new .md in /Needs_Action
    |                      Invokes Claude Code with Agent Skills
    v
Claude Code -------------- Reads item + Company_Handbook.md
    |                      Creates plan in /Plans
    |                      If sensitive: creates approval in /Pending_Approval
    |                      Updates Dashboard.md
    v
[User reviews in Obsidian]
    |
    +-- Moves to /Approved --> orchestrator detects
    |                         Invokes process-approval skill
    |                         Logs, moves to /Done
    |
    +-- Moves to /Rejected --> orchestrator detects
                               Logs rejection, moves to /Done

[Manual/Scheduled]
    |
    v
orchestrator.py --briefing --> Generates CEO Briefing in /Briefings
                               Updates Dashboard.md
```

## Tech Stack

| Component | Tool | Purpose |
|-----------|------|---------|
| Brain | Claude Code CLI | Reasoning engine, executes Agent Skills |
| Memory/GUI | Obsidian | Dashboard, vault browsing, HITL approval |
| Watchers | Python + watchdog | File system monitoring |
| Package Manager | uv | Python dependency management |
| Skills | Claude Agent Skills (.md) | AI behavior definitions |

## Setup

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [Claude Code CLI](https://claude.ai/code) (`claude --version` works)
- [Obsidian](https://obsidian.md/) v1.10.6+ (free)

### Installation

```bash
# 1. Clone and install dependencies
cd bronze
uv sync

# 2. Create environment file
cp .env.example .env
# Edit .env -- DRY_RUN=true by default (safe mode)

# 3. Open Obsidian vault
# Open Obsidian -> "Open folder as vault" -> select bronze/
```

### Running

```bash
# Terminal 1: Start file system watcher
uv run python -c "from watchers.filesystem_watcher import main; main()"

# Terminal 2: Start orchestrator
uv run python -c "from watchers.orchestrator import main; main()"

# One-time: Generate CEO briefing
uv run python -c "import sys; sys.argv=['o','--briefing']; from watchers.orchestrator import main; main()"
```

### Testing with DRY_RUN

With `DRY_RUN=true` (default), the system:
- Detects and classifies files normally
- Logs what Claude *would* do, but doesn't invoke Claude
- Produces audit log entries for every action

Set `DRY_RUN=false` in `.env` to enable live Claude Code invocation.

## Demo Walkthrough

1. **Open Obsidian** -- see `Dashboard.md` (clean state)
2. **Show `Company_Handbook.md`** -- the business rules the AI follows
3. **Drop test files into `/Inbox/`**:
   ```bash
   cp test_data/sample_invoice.txt Inbox/
   cp test_data/sample_receipt.txt Inbox/
   cp test_data/sample_brief.txt Inbox/
   ```
4. **Watch the watcher** -- metadata `.md` files appear in `/Needs_Action/`
5. **Orchestrator processes** -- plans created in `/Plans/`, dashboard updated
6. **HITL approval** -- sensitive item creates approval file in `/Pending_Approval/`
   - Drag to `/Approved/` to approve
   - Drag to `/Rejected/` to reject
7. **Generate briefing** -- run with `--briefing` flag
8. **Check audit logs** -- structured JSON Lines in `/Logs/`

## Folder Structure

```
bronze/                          # Obsidian vault root
├── Dashboard.md                 # Real-time status view
├── Company_Handbook.md          # Business rules for the AI
├── Business_Goals.md            # Goals, metrics, thresholds
│
├── Inbox/                       # Drop files here
├── Needs_Action/                # Triaged items awaiting processing
├── Plans/                       # AI-generated action plans
├── Pending_Approval/            # HITL: awaiting human approval
├── Approved/                    # User approved
├── Rejected/                    # User rejected
├── Done/                        # Completed items
├── Logs/                        # Audit logs (JSON Lines, daily)
├── Briefings/                   # Weekly CEO briefings
├── Accounting/                  # Financial tracking
│
├── watchers/                    # Python watcher scripts
│   ├── base_watcher.py          # Abstract base class
│   ├── filesystem_watcher.py    # Watches /Inbox for new files
│   ├── orchestrator.py          # Triggers Claude Code skills
│   └── logger.py                # Structured audit logging
│
├── skills/                      # Claude Code Agent Skills
│   ├── triage-inbox.md          # Classify & route inbox items
│   ├── update-dashboard.md      # Refresh Dashboard.md
│   ├── generate-briefing.md     # Weekly CEO briefing
│   └── process-approval.md      # Handle approved/rejected items
│
├── test_data/                   # Sample files for demo
├── pyproject.toml               # Python project config (uv)
├── .env.example                 # Environment template
└── .gitignore                   # Excludes .env, .obsidian, etc.
```

## Security

| Measure | Implementation |
|---------|---------------|
| No hardcoded secrets | `.env` for configuration, `.env.example` committed |
| DRY_RUN default | All actions log-only until explicitly enabled |
| HITL approval | Sensitive actions require human approval via file movement |
| Audit logging | Every AI action logged to `/Logs/YYYY-MM-DD.json` (JSON Lines) |
| .gitignore | `.env`, `.obsidian/`, `Logs/`, `__pycache__/` excluded from version control |

## Agent Skills

All AI functionality is defined in `.md` files in `/skills/`. Each skill is:
- Self-contained with clear instructions
- References `Company_Handbook.md` for business rules
- Uses YAML frontmatter schemas from the data model
- Can be tested independently

| Skill | Trigger | Output |
|-------|---------|--------|
| triage-inbox.md | New item in /Needs_Action | ActionPlan in /Plans, ApprovalRequest if needed |
| update-dashboard.md | After any action | Regenerated Dashboard.md |
| generate-briefing.md | --briefing flag or scheduled | Dated briefing in /Briefings |
| process-approval.md | File moved to /Approved or /Rejected | Logged decision, files archived to /Done |
