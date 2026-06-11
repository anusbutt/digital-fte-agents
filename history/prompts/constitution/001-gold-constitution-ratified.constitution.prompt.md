---
id: "001"
title: Nestaro Pilot Constitution Ratified
stage: constitution
date: 2026-03-13
surface: agent
model: claude-sonnet-4-6
feature: none
branch: 001-ai-employee-foundation
user: architect
command: /sp.constitution
labels: [constitution, nestaro-pilot-tier, digital-fte, sdd, principles]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
  - history/prompts/constitution/001-nestaro-pilot-constitution-ratified.constitution.prompt.md
tests:
  - null
---

## Prompt

/sp.constitution ok! write it.

(Architect approved the drafted Nestaro Pilot Constitution covering 8 principles:
Local-First Privacy, Perception→Reasoning→Action, Skills-First, HITL,
Vault-as-State-Machine, Resilience & Graceful Degradation, Observability
& Full Audit Trail, and Spec-Driven Development.)

## Response snapshot

Wrote the completed Nestaro Pilot Constitution to `.specify/memory/constitution.md`
with all 8 principles fully specified, Additional Constraints section
(Python 3.13, Node.js 24, uv, Docker Odoo 17 CE, DRY_RUN default,
Playwright-only social media, Nestaro Pilot self-containment, rate limits),
Development Workflow (8-step SDD order), Governance (amendment procedure
+ semantic versioning rules), and Sync Impact Report as HTML comment.
Version 1.0.0 ratified 2026-03-13.

## Outcome

- ✅ Impact: Nestaro Pilot tier constitution ratified; all 8 principles locked in;
  SDD workflow enforced; HITL gates defined for all sensitive actions;
  Odoo 17 CE via Docker confirmed; Playwright-only for social media confirmed.
- 🧪 Tests: N/A — constitution stage, no code tests.
- 📁 Files: .specify/memory/constitution.md (written, 1.0.0)
- 🔁 Next prompts: /sp.specify — write spec for Nestaro Pilot tier feature 001
- 🧠 Reflection: All 8 principles are declarative, testable, and use
  MUST/MUST NOT language. Ralph Wiggum and PM2 captured under Resilience.
  HITL gates are exhaustive and explicit. Rate limits added as safety guard.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): none
- Next experiment: proceed to /sp.specify for Nestaro Pilot feature 001
