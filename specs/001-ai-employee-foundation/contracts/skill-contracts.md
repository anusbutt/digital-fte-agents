# Skill Contracts: AI Employee Foundation

**Branch**: `001-ai-employee-foundation` | **Date**: 2026-02-15

This project does not expose REST APIs. Instead, contracts define the
interface between components via Claude Code Agent Skills and Python scripts.

## Contract 1: File System Watcher → Needs_Action

**Producer**: `watchers/filesystem_watcher.py`
**Consumer**: Orchestrator / Claude Code Skills
**Trigger**: New file detected in /Inbox

**Input**: Any file dropped into /Inbox
**Output**: Metadata `.md` file in /Needs_Action with YAML frontmatter

**Contract**:
- Output filename: `FILE_{original_name_without_ext}.md`
- YAML frontmatter MUST contain: type, original_name, detected_date, priority, status, source_path
- `status` MUST be "pending"
- `type` MUST be one of: invoice, receipt, client_brief, contract, unknown
- File MUST be created atomically (write to temp, then rename)

---

## Contract 2: Orchestrator → Claude Code CLI

**Producer**: `watchers/orchestrator.py`
**Consumer**: Claude Code CLI
**Trigger**: New `.md` file in /Needs_Action or /Approved

**Invocation pattern**:
```
claude --print --skill <skill-path> --context <file-path>
```

**Contract**:
- Orchestrator MUST pass the skill file path and the context file path
- Orchestrator MUST capture stdout for logging
- Orchestrator MUST handle non-zero exit codes as errors
- Orchestrator MUST log the invocation and result to /Logs

---

## Contract 3: Triage Skill

**Skill file**: `skills/triage-inbox.md`
**Input**: VaultItem .md file from /Needs_Action
**Reads**: Company_Handbook.md, Business_Goals.md
**Output**: ActionPlan .md file in /Plans

**Contract**:
- MUST read the VaultItem and Company_Handbook.md
- MUST create a plan file in /Plans with proper YAML frontmatter
- MUST set approval_required=true if Company Handbook rules trigger
- If approval required, MUST create ApprovalRequest in /Pending_Approval
- MUST update Dashboard.md
- MUST move processed VaultItem metadata to indicate processed

---

## Contract 4: Dashboard Update Skill

**Skill file**: `skills/update-dashboard.md`
**Input**: Current state of all vault folders
**Reads**: /Needs_Action, /Plans, /Pending_Approval, /Done, /Logs, Business_Goals.md
**Output**: Regenerated Dashboard.md

**Contract**:
- MUST count items in each folder
- MUST list last 10 activity entries from /Logs
- MUST show pending approval count
- MUST link to latest briefing if exists
- MUST include current date/time of generation

---

## Contract 5: CEO Briefing Skill

**Skill file**: `skills/generate-briefing.md`
**Input**: Trigger (scheduled or manual)
**Reads**: /Done, /Logs, Business_Goals.md, /Briefings (previous)
**Output**: Dated briefing file in /Briefings

**Contract**:
- MUST generate file named `YYYY-MM-DD_Briefing.md`
- MUST include all sections: Executive Summary, Revenue, Completed Tasks, Bottlenecks, Suggestions
- MUST reference Business_Goals.md for target comparison
- MUST update Dashboard.md with link to new briefing

---

## Contract 6: Approval Processing Skill

**Skill file**: `skills/process-approval.md`
**Input**: File detected in /Approved or /Rejected
**Reads**: The approval file, related plan
**Output**: Log entry, files moved to /Done

**Contract**:
- MUST log the approval/rejection with full details
- MUST move related files (approval request, plan, vault item) to /Done
- MUST update Dashboard.md
- In DRY_RUN mode: MUST log "would execute" but not perform external action
