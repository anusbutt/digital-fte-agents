---
id: "007"
title: "Phase 4: Odoo Accounting MCP Integration Complete"
stage: green
date: "2026-03-14"
surface: agent
model: claude-sonnet-4-6
feature: 001-digital-fte-gold
branch: 001-ai-employee-foundation
user: architect
command: "/sp.implement phase 4"
labels: ["phase-4", "odoo", "mcp", "accounting", "typescript", "HITL", "invoices", "payments"]
links:
  spec: "gold/specs/001-digital-fte-gold/spec.md"
  plan: "gold/specs/001-digital-fte-gold/plan.md"
  tasks: "gold/specs/001-digital-fte-gold/tasks.md"
  contract: "gold/specs/001-digital-fte-gold/contracts/odoo-mcp-tools.md"
  adr: "null"
  pr: "null"
files:
  - gold/odoo-mcp/package.json
  - gold/odoo-mcp/index.ts
  - gold/skills/process-odoo-action.md
  - gold/watchers/orchestrator.py
  - gold/main.py
  - gold/specs/001-digital-fte-gold/tasks.md
tests:
  - "Manual: python main.py setup odoo → prints Docker instructions"
  - "Manual: python main.py odoo-status → hits Odoo JSON-RPC or reports unreachable"
  - "Manual: docker compose up -d, create APPROVE_odoo_create_invoice.md → move to Approved/ → verify DRY_RUN log"
  - "Manual: stop Docker, re-trigger odoo action → verify SYSTEM_ODOO_UNREACHABLE.md in Needs_Action/"
---

## Prompt

```
/sp.implement phase 4
```

## Response Summary

Implemented Phase 4 (T031–T036): Odoo Accounting Integration via MCP.

### T031 — `gold/odoo-mcp/package.json`

Minimal package.json matching email-mcp pattern:
- deps: `@modelcontextprotocol/sdk`, `zod` (for input validation)
- devDeps: `typescript`, `tsx`, `@types/node`
- script: `start: tsx index.ts`
- type: module (ESM)

### T032 — `gold/odoo-mcp/index.ts`

Full TypeScript MCP server implementing all 7 tools per `contracts/odoo-mcp-tools.md`:

| Tool | Odoo model/method | Key behaviour |
|------|------------------|---------------|
| `get_invoices` | `account.move.search_read` | Filters: status, payment_state, date range, partner |
| `create_invoice` | `account.move.create` | Resolves partner by name; creates draft; returns invoice_id + name |
| `post_invoice` | `account.move.action_post` | Validates state; idempotent ALREADY_POSTED; returns new state |
| `record_payment` | `account.payment.create` + `action_post` | Validates INVOICE_NOT_POSTED, AMOUNT_EXCEEDS |
| `get_partners` | `res.partner.search_read` | is_customer from customer_rank, is_vendor from supplier_rank |
| `get_financial_summary` | `account.move.search_read` | Computes MTD revenue, outstanding, overdue list, company currency |
| `get_transactions` | `account.payment.search_read` | Payments in date range |

**Error handling**:
- Network error / connection refused → `{ success: false, error: "ODOO_UNREACHABLE" }`
- HTTP 401 → `{ success: false, error: "AUTH_FAILED" }`
- Odoo RPC fault → `{ success: false, error: <fault message> }`
- Zod validation error → caught and returned as tool error

Auth: Bearer token via `Authorization: Bearer ${ODOO_API_KEY}` on every request.
Transport: stdio (MCP standard); started via `tsx index.ts`.

### T033 — `gold/skills/process-odoo-action.md`

Skill with 4-layer safety gate:
1. DRY_RUN check (log + stop if true)
2. Human approval: `approved_by: human` + file in `vault/Approved/`
3. Expiry: `expires_at` must be in the future
4. Action type: must be `odoo_create_invoice`, `odoo_post_invoice`, or `odoo_record_payment`

For each action type: extract frontmatter params → call odoo-mcp tool → on success move to Done/ + write AuditLogEntry; on failure write `SYSTEM_ODOO_FAILURE_{timestamp}.md` + AuditLogEntry with `result: "failure"`.

`ODOO_UNREACHABLE` special case: writes `SYSTEM_ODOO_UNREACHABLE.md` to Needs_Action/ with retry instructions.

### T034 — Orchestrator expansion

- Added `odoo_create_invoice`, `odoo_post_invoice`, `odoo_record_payment` to recognized action types in `_process_approval()`
- ALL odoo action types (including legacy `odoo_action`) route to `process-odoo-action` skill — never direct dispatch
- Added `_write_odoo_unreachable_alert()` helper: writes `SYSTEM_ODOO_UNREACHABLE.md` (idempotent), appends Dashboard.md alert, logs `system_alert` entry

### T035 — `.mcp.json` (already complete)

`gold/.mcp.json` odoo-mcp entry was written in Phase 2 with correct config:
```json
"odoo-mcp": {
  "command": "node",
  "args": ["--import", "tsx/esm", "odoo-mcp/index.ts"],
  "env": { "ODOO_URL": "...", "ODOO_DB": "...", "ODOO_API_KEY": "..." }
}
```

### T036 — `main.py` additions

- `python main.py setup odoo` — `cmd_setup_odoo()`: prints Docker start instructions, prompts for ODOO_API_KEY, writes/updates it in `.env`
- `python main.py odoo-status` — `cmd_odoo_status()`: direct Python `urllib.request` call to Odoo JSON-RPC; prints MTD revenue, outstanding balance, paid/unpaid counts, unpaid invoice table; no MCP subprocess needed for diagnostics

## Outcome

Phase 4 (T031–T036) **complete**. All 6 tasks marked `[x]` in tasks.md.

**Architecture decisions enforced:**
- HITL for ALL Odoo financial operations: create_invoice, post_invoice, record_payment each require a separate human approval file move
- Never direct-dispatch Odoo actions from orchestrator: always via `process-odoo-action` skill so Claude Code has full context
- Graceful Odoo offline: `ODOO_UNREACHABLE` → SYSTEM_ file in Needs_Action/ + Dashboard alert; never crashes the orchestrator
- Idempotent ALREADY_POSTED: treated as success so retries are safe

**Ready for**: Phase 5 — US3 Enhanced CEO Briefing with Live Accounting Data (T037–T039)
