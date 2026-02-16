<!--
  Sync Impact Report
  ==================
  Version change: 0.0.0 (template) → 1.0.0 (initial ratification)
  Modified principles: N/A (all new)
  Added sections:
    - 6 Core Principles (I–VI)
    - Security & Privacy Requirements
    - Development Workflow (Pure SDD)
    - Governance
  Removed sections: None
  Templates requiring updates:
    - .specify/templates/plan-template.md — ✅ compatible (Constitution Check section exists)
    - .specify/templates/spec-template.md — ✅ compatible (MUST/SHOULD language aligned)
    - .specify/templates/tasks-template.md — ✅ compatible (phased structure supports SDD)
  Follow-up TODOs: None
-->

# Bronze Level Digital Employee Constitution

## Core Principles

### I. Local-First Privacy

All data MUST reside locally in the Obsidian vault by default.
No data leaves the local machine unless explicitly configured
and approved by the user. Sensitive data (banking, credentials,
personal communications) MUST never be stored in markdown files
or committed to version control.

- The Obsidian vault is the single source of truth
- External API calls MUST be documented and justified
- File-based communication between components (markdown-driven)
- No telemetry or data sharing without explicit consent

### II. Human-in-the-Loop (HITL)

The AI MUST never execute sensitive actions autonomously.
All actions with real-world consequences MUST go through
a file-based approval workflow.

- Sensitive actions create approval files in `/Pending_Approval/`
- AI MUST stop and wait until the file is moved to `/Approved/`
- Actions requiring approval: sending emails, payments, social
  media posts, contacting new recipients, deleting files outside
  vault, any action above a defined cost threshold
- Actions NOT requiring approval: reading files, creating/writing
  markdown in vault, classifying items, updating dashboard,
  generating briefings, moving files between vault folders

### III. Agent Skills for All AI Functionality

Every AI capability MUST be implemented as a Claude Code Agent
Skill (`.md` file with clear instructions). No ad-hoc prompting
for repeatable tasks.

- Each skill has a single responsibility
- Skills are versioned alongside the codebase
- Skills reference `Company_Handbook.md` for business rules
- New AI behavior requires a new or updated skill file

### IV. File-Based Communication (Markdown-Driven)

All inter-component communication MUST happen through markdown
files in the Obsidian vault. Components do not call each other
directly.

- Watchers write `.md` files to `/Needs_Action/`
- Claude reads from `/Needs_Action/`, writes to `/Plans/`
- Approval workflow uses `/Pending_Approval/` → `/Approved/`
- Completed items move to `/Done/`
- `Dashboard.md` is the single real-time status view
- Every file MUST have YAML frontmatter with type, date, status

### V. Security by Default

Security MUST be the default state, not an afterthought.
The system MUST be safe even when misconfigured.

- `DRY_RUN=true` is the default; real actions require explicit
  `DRY_RUN=false`
- No hardcoded secrets in code or markdown; use `.env` only
- `.env` MUST be in `.gitignore` before any secrets are added
- `.env.example` with placeholder values MUST be committed
- Audit logging is mandatory: every AI action logged to
  `/Logs/YYYY-MM-DD.json` with timestamp, action, actor,
  target, result, and approval status
- Logs retained minimum 90 days
- On error: stop, log, alert — never retry dangerous actions
- Permission boundaries: AI operates only within the vault

### VI. Simplicity and Smallest Viable Diff

Every change MUST be the smallest possible change that
achieves the goal. No speculative features, no premature
abstractions, no unrelated refactoring.

- YAGNI: do not build what is not explicitly required
- Prefer editing existing files over creating new ones
- No gold-plating: if it works and meets acceptance criteria,
  it is done
- Three similar lines of code are better than a premature
  abstraction

## Security & Privacy Requirements

| Action Category | Auto-Approve | Always Require Approval |
|-----------------|-------------|------------------------|
| Read vault files | Yes | Never |
| Create/edit markdown in vault | Yes | Never |
| Move files between vault folders | Yes | Never |
| Send email | Never | Always |
| Payments/financial | Never | Always |
| Social media posts | Never | Always |
| Delete files outside vault | Never | Always |
| External API calls | Never | Always |

### Credential Management

- API keys, tokens, passwords: `.env` file only (gitignored)
- Banking credentials: OS-level secrets manager preferred
- Credential rotation: monthly or after any suspected breach
- If a secret is accidentally committed: rotate immediately

### Failure Modes

| Error Type | Response |
|------------|----------|
| Transient (network, timeout) | Retry with backoff, max 3 |
| Authentication (expired token) | Stop, alert user |
| Logic (misclassification) | Log, queue for human review |
| Data (corrupted file) | Quarantine file, alert user |
| System (crash, disk full) | Stop, log, wait for restart |

## Development Workflow (Pure SDD)

This project follows Spec-Driven Development strictly.
No implementation occurs without completed artifacts.

### Mandatory Sequence

1. **Constitution** — Project principles (this file)
2. **Specification** (`/sp.specify`) — Feature requirements
3. **Plan** (`/sp.plan`) — Architecture and design
4. **Tasks** (`/sp.tasks`) — Testable task breakdown
5. **Implementation** (`/sp.implement`) — Code

### Rules

- No step may be skipped
- If implementation reveals a missing library, dependency,
  or design gap: STOP implementation, update the relevant
  artifact (spec, plan, or tasks), then resume
- All artifacts MUST stay in sync at all times
- Every artifact change MUST be validated against this
  constitution before proceeding
- User (architect/validator) MUST approve each artifact
  before the next step begins

## Governance

This constitution is the supreme authority for all project
decisions. It overrides all other practices, conventions,
and shortcuts.

### Amendment Procedure

1. Any team member may propose an amendment
2. The architect/validator (user) MUST approve all changes
3. Every amendment MUST include justification
4. Version MUST be bumped per semantic versioning:
   - MAJOR: principle removal or incompatible redefinition
   - MINOR: new principle or materially expanded guidance
   - PATCH: clarification, wording, typo fix
5. All dependent artifacts MUST be checked for consistency
   after any amendment

### Compliance

- Every spec, plan, task, and PR MUST align with this
  constitution
- The plan template's "Constitution Check" gate MUST
  reference these principles
- Non-compliance MUST be flagged and resolved before
  proceeding
- Complexity violations MUST be justified in writing

**Version**: 1.0.0 | **Ratified**: 2026-02-15 | **Last Amended**: 2026-02-15
