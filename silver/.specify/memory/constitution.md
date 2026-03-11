<!--
  SYNC IMPACT REPORT
  Version change: 0.0.0 (template) → 1.0.0
  Modified principles: N/A (initial ratification)
  Added sections:
    - 8 Core Principles (I–VIII)
    - Technology Stack & Constraints
    - Development Workflow
    - Governance
  Removed sections: None
  Templates requiring updates:
    - .specify/templates/plan-template.md ⚠ pending (Constitution Check needs Silver gates)
    - .specify/templates/spec-template.md ✅ no changes needed
    - .specify/templates/tasks-template.md ✅ no changes needed
  Follow-up TODOs: None
-->
# Digital FTE Silver Constitution

## Core Principles

### I. Local-First Privacy

All persistent state, plans, logs, and business data MUST reside in the local
Obsidian vault (`vault/` directory). Secrets (API keys, OAuth tokens, session
data, credentials) MUST use environment variables (`.env`) or the OS credential
manager. Secrets MUST NEVER be committed to version control. The vault is the
single source of truth for all agent state.

- `.env` MUST be listed in `.gitignore` before any secret is stored.
- Code repository and Obsidian vault MUST be separated (`silver/` vs `silver/vault/`).
- Watchers and MCP servers read secrets only from environment variables at runtime.

### II. Perception-Reasoning-Action Architecture

The system follows a strict three-layer pipeline that MUST NOT be bypassed:

1. **Perception (Watchers)**: Python sentinel scripts detect external events
   (Gmail, WhatsApp, filesystem) and write `.md` files to `vault/Needs_Action/`.
   Watchers MUST NOT invoke Claude or execute actions directly.
2. **Reasoning (Claude Code)**: The orchestrator invokes Claude with Agent Skills
   to read items, consult `Company_Handbook.md`, and create plans in `vault/Plans/`.
3. **Action (MCP + Skills)**: After human approval (when required), MCP servers
   and skills execute external actions (send email, post to LinkedIn).

No layer may bypass another. Watchers never act. Claude never sends without approval
where required. MCP servers only execute what has been planned and approved.

### III. Human-in-the-Loop (NON-NEGOTIABLE)

All sensitive actions MUST create an approval request file in
`vault/Pending_Approval/` before execution. The agent MUST NOT execute
sensitive actions until the human moves the file to `vault/Approved/`.

**Always require approval:**
- Emails to new/unknown contacts
- Emails with financial content (invoices, payments)
- LinkedIn posts
- Any action involving money
- File deletions

**Auto-approve (no approval file needed):**
- Replies to known contacts for non-sensitive topics
- Dashboard updates
- Log entries
- Internal vault file creation (plans, metadata)

Approval thresholds are defined in `vault/Company_Handbook.md` and MUST be
consulted by the triage skill before every action decision.

### IV. Agent Skills First

All AI functionality MUST be implemented as Claude Code Agent Skills (`.md`
files in `skills/`). Skills are the unit of capability — reusable, testable,
and composable.

- No inline prompt logic in Python code; every AI capability gets a skill file.
- Each skill MUST declare: Purpose, Instructions (numbered steps), Rules, and
  Tools Required.
- The orchestrator invokes skills via `claude --print -p` with skill content
  and context files.

### V. Watcher Resilience

Watcher scripts MUST run continuously and survive failures:

- All watchers MUST be managed by a process manager (PM2) for auto-restart.
- All watchers MUST implement retry with exponential backoff for transient errors.
- All watchers MUST use structured logging via the `logger.py` module.
- When external APIs are unavailable, watchers MUST degrade gracefully (log the
  error, skip the cycle, retry next interval) — never crash permanently.
- Watchers write `.md` files to `vault/Needs_Action/` — they MUST NOT call
  Claude or execute actions directly.

### VI. Vault-as-Protocol

All inter-component communication happens through the Obsidian vault folder
structure. File movement between folders represents state transitions:

```
vault/Inbox → vault/Needs_Action → vault/Plans
  → vault/Pending_Approval → vault/Approved → vault/Done
                            → vault/Rejected → vault/Done
```

- `vault/Dashboard.md` is the single real-time status summary, regenerated
  after every state change.
- Each `.md` file in the vault MUST have YAML frontmatter with at minimum:
  `type`, `status`, and `created` fields.
- Folder names are fixed and MUST NOT be renamed or reorganized without a
  constitution amendment.

### VII. Observability and Audit

Every action the AI takes MUST be logged:

- Log format: structured JSON embedded in Markdown tables at
  `vault/Logs/YYYY-MM-DD.md`.
- Required fields: `timestamp`, `action_type`, `actor`, `target`,
  `parameters`, `result`, `approval_status`.
- Retain logs for a minimum of 90 days.
- The `logger.py` module is the single entry point for all audit logging.
  No component may write to Logs/ directly.

### VIII. Spec-Driven Development

All features follow the SDD lifecycle:

```
Constitution → Spec → Plan → Tasks → Implementation
```

- No feature is implemented without a spec.
- If something is missed in the spec phase, all artifacts (spec, plan, tasks)
  MUST be updated before implementation proceeds.
- Every user prompt interaction is recorded as a PHR (Prompt History Record).
- Architecturally significant decisions are captured as ADRs upon user consent.

## Technology Stack and Constraints

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Knowledge Base | Obsidian (local Markdown vault) | GUI + long-term memory |
| Logic Engine | Claude Code CLI | Reasoning, planning, execution |
| Gmail Watcher | Python 3.13+ / Google OAuth2 API | Poll unread emails, write to vault |
| WhatsApp Watcher | Python 3.13+ / Playwright | Monitor messages via WhatsApp Web |
| LinkedIn Poster | Python 3.13+ / Playwright | Daily business post generation |
| Filesystem Watcher | Python 3.13+ / watchdog | Monitor vault/Inbox for file drops |
| Email MCP | Node.js MCP server / Gmail API | Send and draft emails |
| Orchestrator | Python 3.13+ / watchdog | Trigger Claude skills on vault events |
| Process Manager | PM2 | Keep watchers alive, auto-restart |
| Scheduling | Windows Task Scheduler | Timed triggers (briefings, posts) |
| Package Manager | uv (Python), npm (Node.js) | Dependency management |

**Platform**: Windows 11

**Silver Tier Scope:**
- In scope: All Bronze functionality + Gmail watcher + WhatsApp watcher +
  LinkedIn auto-posting + email-mcp server + HITL approval workflow +
  Claude reasoning loop (Plan.md) + basic scheduling + Agent Skills
- Out of scope: Odoo integration, Facebook/Instagram/Twitter, cloud deployment,
  Ralph Wiggum autonomous loop, weekly CEO briefing automation (Gold/Platinum)

## Development Workflow

1. **Pure SDD**: Constitution → Spec → Plan → Tasks → Implementation.
   No exceptions.
2. **Artifact-first**: If a requirement is discovered during implementation that
   is not in the spec, STOP. Update spec → plan → tasks, then resume.
3. **Smallest viable diff**: Each change MUST be the minimum needed to satisfy
   the current task. No unrelated refactoring.
4. **No invented APIs**: Do not fabricate data contracts or external APIs.
   If information is missing, ask the architect (human).
5. **Secrets handling**: Use `.env` files for local development. Document
   required environment variables in `.env.example`. Never hardcode tokens.
6. **Vault separation**: Code lives in repo root. Obsidian vault lives in
   `vault/`. Watchers and orchestrator reference `vault/` as their working
   directory.

## Governance

- This constitution supersedes all other project documents and practices.
- Amendments require: documented rationale, semantic version bump, and
  architect (human) approval.
- All code changes MUST verify compliance with these principles.
- Complexity beyond what is specified MUST be justified with a rationale
  referencing a specific principle or hackathon requirement.
- Versioning policy: MAJOR for principle removal/redefinition, MINOR for
  new principles or sections, PATCH for clarifications.

**Version**: 1.0.0 | **Ratified**: 2026-02-18 | **Last Amended**: 2026-02-18
