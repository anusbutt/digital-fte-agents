# Contract: Vault Item Schemas

**Date**: 2026-02-18

## Contract 1: Watcher → Vault (File Creation)

Each watcher creates `.md` files in `vault/Needs_Action/` with YAML frontmatter.

**Invariants**:
- File MUST have YAML frontmatter with at minimum: `type`, `status`, `created` (or `detected_date`)
- Filename MUST use the correct prefix: `FILE_`, `EMAIL_`, `WHATSAPP_`
- File creation MUST be atomic (write to temp, rename)
- Watcher MUST NOT create duplicate files (check before write)
- `status` MUST be `pending` on creation

**Filesystem Watcher Contract** (unchanged from Bronze):
- Prefix: `FILE_{stem}.md`
- Required fields: `type, original_name, detected_date, priority, status, source_path`

**Gmail Watcher Contract** (new):
- Prefix: `EMAIL_{message_id}.md`
- Required fields: `type: email, email_id, from, from_name, to, subject, snippet, received_date, priority, status, sensitivity, labels, has_attachments`
- MUST include full email body in `## Email Content` section
- MUST classify sensitivity: `sensitive` if new sender, financial content, or attachments; `non-sensitive` otherwise

**WhatsApp Watcher Contract** (new):
- Prefix: `WHATSAPP_{contact_slug}_{YYYYMMDD_HHMMSS}.md`
- Required fields: `type: whatsapp, contact, phone, message_text, keywords_matched, detected_date, priority, status`
- `contact_slug`: contact name lowercased, spaces replaced with underscores
- Timestamp format in filename: `YYYYMMDD_HHMMSS`

## Contract 2: Triage Skill → Plan

**Input**: VaultItem `.md` file from `vault/Needs_Action/` + `vault/Company_Handbook.md`
**Output**: ActionPlan in `vault/Plans/` + optional ApprovalRequest in `vault/Pending_Approval/`

**Invariants**:
- Plan filename: `PLAN_{original_vault_item_name_without_extension}.md`
- Plan MUST include: `type: action_plan, related_item, objective, priority, approval_required, action_type, created, status: pending`
- `action_type` MUST be one of: `file_process, email_reply, whatsapp_reply, linkedin_post`
- If `approval_required: true`, an APPROVE_ file MUST be created in `vault/Pending_Approval/`
- Reply/post content MUST be included in the plan under `## Reply Draft`

## Contract 3: Approval → Action Execution

**Input**: Approval file moved to `vault/Approved/` or `vault/Rejected/`
**Output**: Action execution (or rejection logging) + files moved to `vault/Done/`

**Invariants**:
- Approved files trigger action execution based on `action` field
- `email_send` → email-mcp `send_email` tool
- `email_draft` → email-mcp `draft_email` tool
- `whatsapp_reply` → Playwright WhatsApp reply
- `linkedin_post` → Playwright LinkedIn post
- Rejected files → log rejection, move to Done
- ALL actions MUST be logged via `logger.py`
- Failed actions MUST keep file in `vault/Approved/` for retry (not moved to Done)

## Contract 4: Orchestrator → Claude CLI

**Input**: Skill `.md` file + context files
**Output**: Claude-generated vault files (plans, approvals, dashboard updates)

**Invariants**:
- Invoke via: `claude --print -p "{prompt}" --allowedTools "Edit,Write,Read,Glob,Grep"`
- Timeout: 300 seconds (5 minutes)
- DRY_RUN mode: log intent, skip invocation
- Skills directory: `skills/` (repo root, NOT inside vault)
- Context files: vault items + Company_Handbook.md
