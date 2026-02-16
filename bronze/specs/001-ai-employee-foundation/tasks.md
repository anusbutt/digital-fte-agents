# Tasks: AI Employee Foundation

**Input**: Design documents from `/specs/001-ai-employee-foundation/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested. Manual integration testing per quickstart.md.

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Phase 1: Setup (Project Initialization)

**Purpose**: Create project structure, install dependencies, configure environment

- [x] T001 Initialize uv Python project with pyproject.toml at repository root
- [x] T002 Add dependencies: watchdog, python-dotenv to pyproject.toml
- [x] T003 [P] Create .gitignore with exclusions for .env, .obsidian/, __pycache__/, *.pyc, Logs/, .venv/
- [x] T004 [P] Create .env.example with DRY_RUN=true and placeholder values at repository root
- [x] T005 Create vault folder structure: Inbox/, Needs_Action/, Plans/, Pending_Approval/, Approved/, Rejected/, Done/, Logs/, Briefings/, Accounting/ with .gitkeep files
- [x] T006 [P] Create watchers/__init__.py as empty package init at watchers/__init__.py
- [x] T007 [P] Create skills/ directory with .gitkeep at skills/.gitkeep

**Checkpoint**: Project initializes with `uv sync`, all folders exist, .gitignore works

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core vault documents and base watcher class that ALL user stories depend on

- [x] T008 Create Company_Handbook.md at repository root with freelancer business rules: file classification rules, approval thresholds (invoices > $500 require approval), communication tone, client priority tiers
- [x] T009 Create Business_Goals.md at repository root with sample Q1 2026 goals: monthly revenue target, key metrics table, active projects, subscription audit rules per data-model.md template
- [x] T010 Create Dashboard.md at repository root with initial template: business name, quick stats section (all zeros), recent activity (empty), latest briefing link (none), alerts section
- [x] T011 Implement BaseWatcher abstract class in watchers/base_watcher.py with: __init__(vault_path, check_interval), abstract check_for_updates(), abstract create_action_file(), run() loop with error handling and logging per base_watcher pattern from hackathon doc
- [x] T012 Implement audit logging utility function in watchers/logger.py with: append_log_entry(log_dir, action_type, actor, target, parameters, result, approval_status) that writes JSON Lines to Logs/YYYY-MM-DD.json

**Checkpoint**: Foundation ready. Company_Handbook.md, Business_Goals.md, Dashboard.md exist. BaseWatcher importable. Logger writes structured entries.

---

## Phase 3: User Story 1 - Drop File and Get It Triaged (Priority: P1)

**Goal**: User drops file in /Inbox, metadata .md appears in /Needs_Action within 30 seconds

**Independent Test**: Drop invoice_client_a.pdf into /Inbox → FILE_invoice_client_a.md appears in /Needs_Action with type: invoice, status: pending

### Implementation for User Story 1

- [x] T013 [US1] Implement FilesystemWatcher class in watchers/filesystem_watcher.py: extends BaseWatcher, uses watchdog Observer to monitor Inbox/ folder, on_created event handler copies file and creates metadata .md in Needs_Action/ with YAML frontmatter (type, original_name, detected_date, priority, status, source_path) per data-model.md VaultItem schema
- [x] T014 [US1] Implement file classification logic in watchers/filesystem_watcher.py: classify_file(filename) function that returns invoice|receipt|client_brief|contract|unknown based on filename keywords and file extension patterns
- [x] T015 [US1] Implement duplicate detection in watchers/filesystem_watcher.py: check if FILE_{name}.md already exists in Needs_Action/ before creating, log skip event if duplicate
- [x] T016 [US1] Add startup scan in watchers/filesystem_watcher.py: on watcher start, check Inbox/ for unprocessed files that arrived while watcher was stopped, process each one
- [x] T017 [US1] Add audit log calls to FilesystemWatcher: log file_triage action for each processed file using watchers/logger.py

**Checkpoint**: Drop any file into /Inbox → metadata .md created in /Needs_Action with correct classification. Duplicates skipped. Startup catches missed files.

---

## Phase 4: User Story 2 - Action Plan Creation and Dashboard Update (Priority: P2)

**Goal**: AI processes triaged items, creates plans in /Plans, updates Dashboard.md

**Independent Test**: With item in /Needs_Action, run orchestrator → Plan .md in /Plans, Dashboard.md updated

### Implementation for User Story 2

- [x] T018 [US2] Create triage-inbox.md Agent Skill in skills/triage-inbox.md: instructions for Claude to read a VaultItem from /Needs_Action, consult Company_Handbook.md, classify priority, create ActionPlan in /Plans with YAML frontmatter per data-model.md, set approval_required based on handbook thresholds, move processed item from /Needs_Action
- [x] T019 [US2] Create update-dashboard.md Agent Skill in skills/update-dashboard.md: instructions for Claude to read all vault folders, count items per folder, read last 10 log entries from /Logs, read Business_Goals.md, regenerate Dashboard.md with current stats, recent activity, pending approvals count, latest briefing link
- [x] T020 [US2] Implement Orchestrator class in watchers/orchestrator.py: watches /Needs_Action for new .md files using watchdog, invokes Claude Code CLI with triage-inbox skill via subprocess, then invokes update-dashboard skill, logs orchestration actions
- [x] T021 [US2] Add Claude Code CLI invocation helper in watchers/orchestrator.py: invoke_claude(skill_path, context_files) function that runs `claude --print -p "Follow the skill instructions" --allowedTools Edit,Write,Read,Glob,Grep` with skill content passed as prompt context, captures stdout/stderr, handles errors
- [x] T022 [US2] Add DRY_RUN check in watchers/orchestrator.py: read DRY_RUN from .env via python-dotenv, if true log "would invoke Claude" but skip actual subprocess call

**Checkpoint**: Orchestrator detects items in /Needs_Action, invokes Claude skills, Plans created, Dashboard updated. DRY_RUN mode logs without executing.

---

## Phase 5: User Story 3 - HITL Approval Workflow (Priority: P2)

**Goal**: Sensitive actions create approval files; user approves/rejects by moving files; system responds

**Independent Test**: Trigger sensitive action → approval file in /Pending_Approval → move to /Approved → logged and moved to /Done

### Implementation for User Story 3

- [x] T023 [US3] Add approval request creation to triage-inbox.md skill in skills/triage-inbox.md: when approval_required=true, create ApprovalRequest .md in /Pending_Approval with YAML frontmatter per data-model.md (action, details, amount, recipient, reason, related_plan, created, expires, status)
- [x] T024 [US3] Create process-approval.md Agent Skill in skills/process-approval.md: instructions for Claude to read approved/rejected file, log the decision, move related files (approval request, plan, vault item) to /Done with appropriate status, update Dashboard.md
- [x] T025 [US3] Add /Approved and /Rejected folder watchers to orchestrator.py: detect file_moved events in both folders, invoke process-approval skill with the moved file as context, log the approval/rejection action

**Checkpoint**: Sensitive items trigger approval files. Moving to /Approved → logged + archived to /Done. Moving to /Rejected → logged with rejection status + archived.

---

## Phase 6: User Story 4 - Weekly CEO Briefing (Priority: P3)

**Goal**: Generate comprehensive weekly briefing summarizing business activity

**Independent Test**: With sample data in /Done and /Logs, run briefing → dated file in /Briefings with all sections

### Implementation for User Story 4

- [x] T026 [US4] Create generate-briefing.md Agent Skill in skills/generate-briefing.md: instructions for Claude to read /Done folder (week's items), /Logs (week's entries), Business_Goals.md (targets), generate CEO Briefing with YAML frontmatter per data-model.md, sections for Executive Summary, Revenue, Completed Tasks, Bottlenecks, Proactive Suggestions, write to /Briefings/YYYY-MM-DD_Briefing.md, update Dashboard.md with link
- [x] T027 [US4] Add --briefing CLI flag to orchestrator.py: when passed, invoke generate-briefing skill directly instead of watching folders, exit after completion

**Checkpoint**: Run `uv run python watchers/orchestrator.py --briefing` → dated briefing in /Briefings with all required sections. Dashboard links to it.

---

## Phase 7: User Story 5 - Audit Logging (Priority: P3)

**Goal**: Every AI action captured in structured daily log files

**Independent Test**: Perform several actions → /Logs/YYYY-MM-DD.json has structured entries for each

### Implementation for User Story 5

- [x] T028 [US5] Integrate audit logging into all orchestrator actions in watchers/orchestrator.py: add log calls before and after every Claude invocation, log watcher start/stop events, log errors with full details
- [x] T029 [US5] Integrate audit logging into filesystem_watcher.py: ensure every file detection, classification, duplicate skip, and error is logged with structured fields per data-model.md AuditLog schema
- [x] T030 [US5] Add log reading utility to watchers/logger.py: read_recent_logs(log_dir, days=7) function that reads and parses JSON Lines from last N days of log files, returns list of entries (used by briefing skill)

**Checkpoint**: All actions produce log entries. Log files are valid JSON Lines. read_recent_logs returns structured data.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, final integration, demo readiness

- [x] T031 [P] Create README.md at repository root with: project overview, architecture diagram, setup instructions (reference quickstart.md), demo walkthrough, security disclosure (how credentials handled), tier declaration (Bronze), folder structure explanation
- [x] T032 Perform end-to-end integration test: start watcher + orchestrator, drop 3 test files (invoice, receipt, brief), verify full flow through triage → plan → dashboard, test HITL with one approval and one rejection, generate briefing, verify all logs
- [x] T033 [P] Add sample test files in a test_data/ directory: sample_invoice.txt, sample_receipt.txt, sample_brief.txt with realistic content for demo purposes
- [x] T034 Review all skills for consistency: verify each skill references Company_Handbook.md, uses correct YAML frontmatter schemas from data-model.md, follows constitution principles

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 completion - BLOCKS all user stories
- **Phase 3 (US1 - Triage)**: Depends on Phase 2 - No dependencies on other stories
- **Phase 4 (US2 - Plans/Dashboard)**: Depends on Phase 2 + Phase 3 (needs triaged items to process)
- **Phase 5 (US3 - HITL)**: Depends on Phase 4 (needs plan creation with approval flags)
- **Phase 6 (US4 - Briefing)**: Depends on Phase 2 (can use sample /Done data, independent of US1-3)
- **Phase 7 (US5 - Logging)**: Cross-cutting, integrates into all phases. Best done after US1-4 exist.
- **Phase 8 (Polish)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Independent after Foundation
- **US2 (P2)**: Needs US1 (processes items US1 creates)
- **US3 (P2)**: Needs US2 (approval triggered during plan creation)
- **US4 (P3)**: Independent after Foundation (uses /Done data directly)
- **US5 (P3)**: Cross-cutting, integrates into US1-US4

### Parallel Opportunities

- T003, T004 can run in parallel (both setup, different files)
- T006, T007 can run in parallel (both directory creation)
- T008, T009, T010 could run in parallel (independent vault documents)
- T031, T033 can run in parallel (README and test data)
- US4 (Briefing) can start in parallel with US2/US3 if sample data used

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T007)
2. Complete Phase 2: Foundational (T008-T012)
3. Complete Phase 3: User Story 1 - File Triage (T013-T017)
4. **STOP and VALIDATE**: Drop files, verify triage works
5. Demo-ready MVP: "My AI Employee detects and classifies files"

### Incremental Delivery

1. Setup + Foundation → Project structure ready
2. US1 (Triage) → Files detected and classified (MVP!)
3. US2 (Plans + Dashboard) → AI creates action plans, dashboard live
4. US3 (HITL) → Approval workflow functional
5. US4 (Briefing) → Weekly CEO briefing generates
6. US5 (Logging) → Full audit trail
7. Polish → README, test data, integration verified

---

## Task Summary

| Phase | Story | Tasks | Parallel |
|-------|-------|-------|----------|
| Setup | - | T001-T007 (7) | T003,T004,T006,T007 |
| Foundation | - | T008-T012 (5) | T008,T009,T010 |
| US1 Triage | P1 | T013-T017 (5) | - |
| US2 Plans | P2 | T018-T022 (5) | - |
| US3 HITL | P2 | T023-T025 (3) | - |
| US4 Briefing | P3 | T026-T027 (2) | - |
| US5 Logging | P3 | T028-T030 (3) | - |
| Polish | - | T031-T034 (4) | T031,T033 |
| **Total** | | **34 tasks** | |
