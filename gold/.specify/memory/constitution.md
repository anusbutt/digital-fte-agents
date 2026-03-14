<!--
SYNC IMPACT REPORT
==================
Version change:   (template) → 1.0.0
Bump type:        MINOR — first ratification; all 8 principles authored from scratch.

Modified principles:
  - None (initial constitution)

Added sections:
  - I.   Local-First Privacy
  - II.  Perception → Reasoning → Action
  - III. Skills-First
  - IV.  Human-in-the-Loop (HITL)
  - V.   Vault-as-State-Machine
  - VI.  Resilience & Graceful Degradation
  - VII. Observability & Full Audit Trail
  - VIII.Spec-Driven Development

Templates reviewed:
  ✅ .specify/templates/plan-template.md   — Constitution Check gate aligns with all 8 principles
  ✅ .specify/templates/spec-template.md   — Scope/requirements sections compatible; no changes needed
  ✅ .specify/templates/tasks-template.md  — Task phases and parallel markers compatible; no changes needed

Follow-up TODOs:
  - None. All placeholders resolved.
-->

# Digital FTE Gold Constitution

## Core Principles

### I. Local-First Privacy

All data — emails, messages, financial records, social media content, and
accounting transactions — MUST remain on the local machine. No sensitive data
may be transmitted to third-party services except through explicitly approved,
audited MCP calls (email-mcp → Gmail API, odoo-mcp → Odoo JSON-RPC). Secrets
MUST be loaded from `.env` only and MUST never be hardcoded in source code or
Markdown skills. Browser sessions for WhatsApp, LinkedIn, Facebook, Instagram,
and Twitter MUST be stored locally in `playwright-data/` and MUST never be
synced to remote systems.

### II. Perception → Reasoning → Action

Every feature MUST follow this three-stage pipeline — no exceptions:

- **Perception**: Python watchers detect external events (filesystem, Gmail,
  WhatsApp, Facebook, Instagram, Twitter) and write structured `.md` files
  to `vault/Needs_Action/`. Watchers MUST NOT act directly on any event.
- **Reasoning**: Claude Code reads vault state and executes Markdown skills
  to classify, plan, and decide. All decisions MUST be written to
  `vault/Plans/` or `vault/Pending_Approval/` before any action is taken.
- **Action**: MCP servers (`email-mcp`, `odoo-mcp`) or approved Playwright
  scripts execute only after a plan exists and (where required) human
  approval is granted.

No watcher may call an MCP server directly. No MCP server may be invoked
without Claude reasoning first. The pipeline is linear and non-negotiable.

### III. Skills-First (NON-NEGOTIABLE)

Every piece of AI logic, classification rule, business reasoning pattern, and
decision heuristic MUST live in a Markdown skill file under `skills/`. Python
watchers and MCP servers MUST contain zero business logic — they handle only:
file I/O, API polling, browser automation, and process management. If Claude
needs to decide, classify, draft, or reason about anything, that logic MUST
be encoded as a skill. Skills MUST be stateless; all state lives in the vault.

### IV. Human-in-the-Loop (HITL) for Sensitive Actions

The following actions MUST ALWAYS route through `vault/Pending_Approval/` and
require explicit human approval before execution — no exceptions, no overrides:

- Any Odoo action: invoice creation, payment recording, or posting
- Emails to contacts not present in `Company_Handbook.md` known contacts list
- All WhatsApp replies (regardless of sender)
- All Facebook posts and direct message replies
- All Instagram posts and direct message replies
- All Twitter/X posts, replies, and direct messages
- All LinkedIn posts
- Any financial action of any amount

Approval workflow: orchestrator writes approval file → human moves file to
`vault/Approved/` or `vault/Rejected/` → orchestrator executes or discards.
The orchestrator MUST check approval file age; files older than 24 hours
MUST be marked `status: expired` and moved to `vault/Done/`.

### V. Vault-as-State-Machine

The vault is the single source of truth for all system state. File movement
equals state transition. No database, no in-memory state, no external queues
may substitute for vault folder structure.

Required state pipeline:
```
Inbox → Needs_Action → Plans → Pending_Approval → Approved/Rejected → Done → Logs
```

Every work item MUST pass through this pipeline in order. Skipping stages is
prohibited. The `vault/Logs/` folder MUST contain one JSON file per day
(`YYYY-MM-DD.json`) accumulating all actions taken that day.

### VI. Resilience & Graceful Degradation

All Python watchers MUST implement exponential backoff on failure:
base delay 1s, multiplier 2x, maximum delay 60s, maximum 3 attempts per
error before escalating to the human-review queue via `vault/Needs_Action/`.

Error recovery MUST follow these strategies by category:
- **Transient** (network timeout, API rate limit): retry with exponential backoff
- **Authentication** (expired OAuth token, revoked session): immediately pause
  the affected watcher, write a `SYSTEM_AUTH_FAILURE_<source>.md` to
  `vault/Needs_Action/`, and do NOT retry until human resolves
- **Logic** (Claude misinterpretation, malformed plan): move item to
  `vault/Needs_Action/` with `status: review_required` and alert Dashboard
- **System** (process crash, disk full): PM2 auto-restarts the process;
  Ralph Wiggum stop hook re-injects the in-progress prompt until the task
  file moves to `vault/Done/` or max iterations (10) is reached

PM2 MUST manage all 6+ background processes. The Ralph Wiggum stop hook
(`.claude/hooks/stop.py`) MUST intercept Claude exits and re-inject the
current prompt if the task file has not reached `vault/Done/`.

### VII. Observability & Full Audit Trail

Every action — approved, rejected, auto-executed, expired, or failed — MUST
be appended to `vault/Logs/YYYY-MM-DD.json` in this exact schema:

```json
{
  "timestamp": "ISO-8601",
  "action_type": "email_send | invoice_create | social_post | whatsapp_reply | ...",
  "actor": "claude_code | orchestrator | human",
  "target": "recipient, platform, or system",
  "parameters": {},
  "approval_status": "auto_approved | human_approved | human_rejected | expired",
  "approved_by": "human | system | null",
  "result": "success | failure | dry_run",
  "error": "null or error message"
}
```

`vault/Dashboard.md` MUST be updated after every significant vault state
change. Logs MUST be retained for a minimum of 90 days. No log file may be
deleted, truncated, or overwritten — only appended.

### VIII. Spec-Driven Development (NON-NEGOTIABLE)

The build order is strictly enforced:
**Constitution → Spec → Plan → Tasks → Implement**

No implementation task may begin without a completed, architect-approved
`tasks.md`. No spec may be written without constitution alignment. No plan
may be written without an approved spec. No vibe coding under any
circumstances.

Every architecturally significant decision MUST be documented as an ADR in
`history/adr/`. Every user prompt and Claude response exchange MUST be
recorded as a PHR in `history/prompts/`. All AI functionality MUST be
implemented as agent skills — not as ad-hoc prompts or inline code.

## Additional Constraints

- **Runtime**: Python 3.13+; Node.js 24+ LTS for all MCP servers (TypeScript
  via `tsx`)
- **Package managers**: `uv` for Python dependencies; `npm` for Node.js
- **Safety default**: `DRY_RUN=true` in all `.env` files; system MUST never
  perform live actions without explicit opt-in (`DRY_RUN=false`)
- **Odoo**: Community Edition 17 via Docker Compose on `localhost:8069`;
  odoo-mcp connects via JSON-RPC only
- **Social media automation**: Playwright persistent browser contexts only;
  no paid APIs for Facebook, Instagram, or Twitter/X
- **Self-containment**: Gold tier MUST be fully self-contained under `gold/`;
  no imports, symlinks, or runtime dependencies on `bronze/` or `silver/`
- **Rate limiting**: Maximum 10 emails/hour, 5 social posts/day, 3 Odoo
  financial actions requiring approval per session

## Development Workflow

1. Architect writes or approves spec (`/sp.specify`) → developer implements
2. Developer produces plan (`/sp.plan`) → architect validates and approves
3. Developer produces tasks (`/sp.tasks`) → architect validates and approves
4. Developer implements task by task → architect validates each phase checkpoint
5. No implementation begins without architect-approved `tasks.md`
6. Every watcher, skill, MCP tool, and script MUST map to a task ID
7. PHR created after every significant prompt exchange
8. ADR created for every architecturally significant decision

## Governance

This constitution supersedes all other practices, conventions, and guidelines
within the Gold tier. In case of conflict, the constitution wins.

Amendment procedure:
1. Architect identifies the required change and its justification
2. Change is documented as an ADR (architectural decision record)
3. Constitution version is incremented per semantic versioning rules:
   - MAJOR: principle removed, redefined, or governance structure changed
   - MINOR: new principle or section added
   - PATCH: clarification, wording, or typo fix
4. `LAST_AMENDED_DATE` is updated to today's date
5. All dependent templates are reviewed for alignment

All implementations must verify compliance with all 8 principles before
marking any task complete. The DRY_RUN flag must be verified before any
live execution. HITL approval gates must never be bypassed.

**Version**: 1.0.0 | **Ratified**: 2026-03-13 | **Last Amended**: 2026-03-13
