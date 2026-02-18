# Bronze Tier - Digital FTE (Full-Time Employee)

> **Panaversity Hackathon 0** | Personal AI Employee | Built with Claude Code Agent Skills + Obsidian

An autonomous AI Employee that lives inside your file system. Drop a file, and it thinks, plans, asks for approval when needed, updates your dashboard, and reports back weekly — all without leaving Obsidian.

---

## What It Does

| Capability | How It Works |
|-----------|--------------|
| **Inbox Monitoring** | Watches a folder for new files in real-time using Python watchdog |
| **Smart Triage** | Classifies documents (invoices, receipts, briefs, contracts) by filename patterns |
| **Action Planning** | Claude AI reads each item + your business rules, then creates step-by-step plans |
| **Human-in-the-Loop** | Sensitive actions (payments > $500, external emails) require your approval first |
| **Live Dashboard** | `Dashboard.md` in Obsidian shows real-time counts, recent activity, and alerts |
| **CEO Briefing** | Weekly summary with revenue tracking, bottleneck analysis, and proactive suggestions |
| **Full Audit Trail** | Every action logged as a Markdown table — visible directly in Obsidian |

---

## Architecture

```
                    +------------------+
                    |   You drop a     |
                    |   file into      |
                    |   /Inbox/        |
                    +--------+---------+
                             |
                             v
               +---------------------------+
               |  filesystem_watcher.py    |
               |  Detects file instantly   |
               |  Classifies by filename   |
               |  Creates metadata .md     |
               +------------+--------------+
                            |
                            v
               +---------------------------+
               |  orchestrator.py          |
               |  Picks up from            |
               |  /Needs_Action/           |
               |  Invokes Claude Code      |
               +------------+--------------+
                            |
              +-------------+-------------+
              |                           |
              v                           v
   +------------------+       +--------------------+
   | triage-inbox.md  |       | Sensitive item?    |
   | Reads handbook   |       | Creates approval   |
   | Creates plan     |       | in /Pending_       |
   | Updates dashboard|       | Approval/          |
   +------------------+       +----------+---------+
                                         |
                              +----------+---------+
                              |                    |
                              v                    v
                     +-------------+      +-------------+
                     | /Approved/  |      | /Rejected/  |
                     | User drags  |      | User drags  |
                     | file here   |      | file here   |
                     +------+------+      +------+------+
                            |                    |
                            v                    v
                     +-----------------------------+
                     |  process-approval.md        |
                     |  Logs decision               |
                     |  Archives to /Done/          |
                     |  Updates Dashboard.md        |
                     +-----------------------------+
```

---

## Tech Stack

| Layer | Technology | Role |
|-------|-----------|------|
| **AI Brain** | [Claude Code CLI](https://claude.ai/code) | Reasoning engine — reads skills, writes plans, updates files |
| **Dashboard & GUI** | [Obsidian](https://obsidian.md/) (free) | Visual interface — browse vault, approve actions, read briefings |
| **File Watchers** | Python 3.13 + [watchdog](https://pypi.org/project/watchdog/) | Real-time file system monitoring with polling fallback |
| **Package Manager** | [uv](https://docs.astral.sh/uv/) | Fast Python dependency management |
| **Agent Skills** | Markdown files (`.md`) | Self-contained AI behavior definitions — no code, just instructions |
| **Audit Logging** | Markdown tables + hidden JSON | Human-readable in Obsidian, machine-parseable for briefings |

---

## Quick Start

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) — `pip install uv` or see docs
- [Claude Code CLI](https://claude.ai/code) — `claude --version` should work
- [Obsidian](https://obsidian.md/) v1.10.6+ (free)

### Installation

```bash
# Clone the repo
git clone https://github.com/anusbutt/digital-fte-agents.git
cd digital-fte-agents/bronze

# Install Python dependencies
uv sync

# Create your environment file
cp .env.example .env
# DRY_RUN=true by default (safe mode — logs only, no Claude invocation)
```

### Open the Vault

1. Launch **Obsidian**
2. Click **"Open folder as vault"**
3. Select the `bronze/` folder
4. You'll see `Dashboard.md` — your command center

### Run the System

Open **3 separate terminals**, all in the `bronze/` directory:

```bash
# Terminal 1: File watcher (monitors Inbox/)
uv run python -c "from watchers.filesystem_watcher import main; main()"

# Terminal 2: Orchestrator (triggers Claude for processing)
uv run python -c "from watchers.orchestrator import main; main()"

# Terminal 3: Drop test files
copy test_data\sample_invoice.txt Inbox\
copy test_data\sample_receipt.txt Inbox\
```

### Generate a CEO Briefing

```bash
uv run python -c "import sys; sys.argv=['o','--briefing']; from watchers.orchestrator import main; main()"
```

---

## How DRY_RUN Works

| Mode | Behavior |
|------|----------|
| `DRY_RUN=true` (default) | Files are detected and classified normally. Logs what Claude *would* do. No Claude invocation. Safe for testing. |
| `DRY_RUN=false` | Full pipeline — Claude reads files, creates plans, updates dashboard, generates briefings. |

Edit `.env` to switch modes. Always start with `true` to verify your setup.

---

## Folder Map

```
bronze/                          # Obsidian vault root
│
├── Dashboard.md                 # Live status — counts, activity feed, alerts
├── Company_Handbook.md          # Business rules the AI follows
├── Business_Goals.md            # Revenue targets, metrics, thresholds
│
├── Inbox/                       # Drop files here
├── Needs_Action/                # Watcher puts classified items here
├── Plans/                       # Claude creates action plans here
├── Pending_Approval/            # Sensitive items wait for your approval
├── Approved/                    # Drag here to approve
├── Rejected/                    # Drag here to reject
├── Done/                        # Completed items archived here
├── Logs/                        # Audit trail (Markdown tables, daily)
├── Briefings/                   # Weekly CEO briefing reports
├── Accounting/                  # Financial tracking
│
├── watchers/                    # Python backend
│   ├── base_watcher.py          # Abstract base class (poll + process loop)
│   ├── filesystem_watcher.py    # Inbox monitor (watchdog + startup scan)
│   ├── orchestrator.py          # Claude invoker (skills + context assembly)
│   └── logger.py                # Audit logging (Markdown + hidden JSON)
│
├── skills/                      # Claude Code Agent Skills
│   ├── triage-inbox.md          # Classify & route inbox items
│   ├── update-dashboard.md      # Regenerate Dashboard.md from vault state
│   ├── generate-briefing.md     # Weekly CEO briefing with revenue analysis
│   └── process-approval.md      # Handle approved/rejected decisions
│
├── test_data/                   # Sample files for demo
│   ├── sample_invoice.txt       # $10,000 invoice (triggers approval)
│   └── sample_receipt.txt       # $49.99 hosting receipt
│
├── pyproject.toml               # Python project (uv)
├── .env.example                 # Environment template
└── .gitignore                   # Excludes .env, .obsidian, Logs/, etc.
```

---

## Agent Skills — The AI's Playbook

Each skill is a plain Markdown file that tells Claude exactly what to do. No code — just structured instructions that Claude follows step by step.

| Skill | When It Fires | What It Does | What It Produces |
|-------|--------------|--------------|-----------------|
| `triage-inbox.md` | New item in `/Needs_Action/` | Reads file + Company Handbook, classifies type & priority, determines if approval needed | Action plan in `/Plans/`, approval request if sensitive |
| `update-dashboard.md` | After every action | Counts all folders, reads logs & goals, regenerates entire dashboard | Fresh `Dashboard.md` with live data |
| `generate-briefing.md` | `--briefing` flag or scheduled | Analyzes week's work, compares to goals, identifies bottlenecks | Dated briefing in `/Briefings/` |
| `process-approval.md` | File moved to `/Approved/` or `/Rejected/` | Reads decision, updates plan status, archives files | Logged decision, files moved to `/Done/` |

---

## Security & Safety

| Layer | What It Does |
|-------|-------------|
| **DRY_RUN Default** | System ships in safe mode — all actions are log-only until you explicitly enable live mode |
| **Human-in-the-Loop** | Invoices > $500, external emails, deletions, and API calls all require your manual approval in Obsidian |
| **Audit Logging** | Every single AI action is recorded with timestamp, actor, target, and result — rendered as a readable table in Obsidian |
| **No Hardcoded Secrets** | All configuration via `.env` (gitignored). Only `.env.example` is committed |
| **File Preservation** | Original files in `/Inbox/` are never modified or deleted — only copied |
| **Gitignore** | `.env`, `.obsidian/`, `Logs/`, `__pycache__/`, `.venv/` all excluded from version control |

---

## Demo Walkthrough

> Estimated time: 5-7 minutes

1. **Open Obsidian** — Show `Dashboard.md` in its clean initial state
2. **Show `Company_Handbook.md`** — The rules your AI follows (classification, approval thresholds, client tiers)
3. **Drop 3 test files into `/Inbox/`** — Invoice, receipt, and client brief
4. **Watch Terminal 1** — Watcher detects each file, classifies it, creates metadata
5. **Watch Terminal 2** — Orchestrator picks up items, invokes Claude skills
6. **Check Obsidian** — Plans appear in `/Plans/`, Dashboard updates with live counts
7. **HITL Approval** — $10,000 invoice triggers approval. Drag from `/Pending_Approval/` to `/Approved/`
8. **Generate CEO Briefing** — Run the briefing command, check `/Briefings/`
9. **Audit Trail** — Open `Logs/` to see every action recorded as a clean table

---

## Business Rules (Company Handbook)

The AI Employee follows rules defined in `Company_Handbook.md`:

- **File Classification**: Invoice, Receipt, Client Brief, Contract, Unknown
- **Approval Required For**: Invoices > $500, external emails, social media posts, file deletions, external API calls
- **Client Priority Tiers**: Tier 1 (same day), Tier 2 (2 business days), Tier 3 (5 business days)
- **General Rules**: Never auto-execute sensitive actions, always log, preserve original files, respect DRY_RUN

All rules are customizable — edit `Company_Handbook.md` to match your business.

---

## Built With

This project was built entirely through **Spec-Driven Development (SDD)**:

```
Constitution → Specification → Plan → Tasks → Implementation
```

- 1 constitution defining project principles
- 1 feature specification with 5 user stories
- 1 implementation plan with data model and contracts
- 34 tasks across 8 phases, all completed
- 35/35 integration test assertions passing
- 12 Prompt History Records documenting every step

All SDD artifacts are preserved in `specs/` and `history/` for full traceability.
