---
id: 004
title: Task Breakdown Generation
stage: tasks
date: 2026-02-15
surface: agent
model: claude-opus-4-6
feature: 001-ai-employee-foundation
branch: 001-ai-employee-foundation
user: architect
command: /sp.tasks
labels: ["tasks", "breakdown", "implementation-order", "dependencies"]
links:
  spec: specs/001-ai-employee-foundation/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/001-ai-employee-foundation/tasks.md
tests:
  - N/A
---

## Prompt

/sp.tasks (no additional input -- uses design documents from 001-ai-employee-foundation)

## Response snapshot

Generated tasks.md with 34 tasks across 8 phases: Setup (7), Foundation (5), US1-Triage (5), US2-Plans/Dashboard (5), US3-HITL (3), US4-Briefing (2), US5-Logging (3), Polish (4). Dependencies mapped: US1→US2→US3 chain, US4 independent, US5 cross-cutting. MVP scope: Phases 1-3 (17 tasks). Parallel opportunities identified in Setup, Foundation, and Polish phases.

## Outcome

- Impact: Complete task breakdown ready for implementation
- Tests: N/A (planning artifact)
- Files: specs/001-ai-employee-foundation/tasks.md
- Next prompts: /sp.implement to begin implementation
- Reflection: Tasks map cleanly to user stories; each phase independently testable

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): Format validation PASS - all tasks have checkbox, ID, labels, file paths
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
