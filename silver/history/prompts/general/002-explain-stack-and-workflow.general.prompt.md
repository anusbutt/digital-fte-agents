---
id: 002
title: Explain Complete Stack and Workflow
stage: general
date: 2026-03-06
surface: agent
model: claude-sonnet-4-6
feature: none
branch: 001-digital-fte-silver
user: PC
command: explain the complete stack and workflow of it
labels: ["explanation", "architecture", "stack", "workflow"]
links:
  spec: specs/001-digital-fte-silver/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - none
tests:
  - none
---

## Prompt

explain the complete stack and workflow of it.

## Response snapshot

Provided comprehensive explanation covering:
- Full technology stack (Python 3.13+, Node.js, Playwright, PM2, Windows Task Scheduler)
- Three-layer Perception-Reasoning-Action architecture
- Vault-as-Protocol state machine with all folder transitions
- Five PM2-managed processes and their roles
- Complete end-to-end workflows for: Gmail email pipeline, WhatsApp pipeline, LinkedIn pipeline, CEO Briefing, Filesystem pipeline
- Safety mechanisms: DRY_RUN, HITL approval, 24h expiry, audit logs, backoff, PM2 auto-restart
- Full data flow diagram

## Outcome

- Impact: User has complete understanding of system architecture and workflows
- Tests: none
- Files: none
- Next prompts: Implementation work, debugging, feature additions, or running the system
- Reflection: All 51 tasks already complete. System is production-ready with DRY_RUN=true as safety default.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): none
- Prompt variant (if applicable): none
- Next experiment: none
