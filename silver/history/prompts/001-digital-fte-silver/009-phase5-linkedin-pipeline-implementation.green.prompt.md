---
id: 009
title: Phase 5 LinkedIn Pipeline Implementation
stage: green
date: 2026-02-23
surface: agent
model: claude-opus-4-6
feature: 001-digital-fte-silver
branch: 001-digital-fte-silver
user: architect
command: /sp.implement
labels: ["implementation", "linkedin-pipeline", "phase-5", "US5", "playwright"]
links:
  spec: specs/001-digital-fte-silver/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - skills/generate-linkedin-post.md
  - scripts/linkedin_post.py
  - watchers/orchestrator.py
tests:
  - linkedin_post.py syntax verification PASS
  - orchestrator.py syntax verification PASS
---

## Prompt

/sp.implement phase 05.

## Response snapshot

Completed Phase 5 LinkedIn Pipeline: 3 tasks (T032-T034). Created skills/generate-linkedin-post.md (Agent Skill for LinkedIn post generation — topics: AI automation, digital FTEs, industry insights, lessons learned, future of work; creates LINKEDIN_{YYYY-MM-DD}.md in vault/Pending_Approval/ per data-model LinkedInPost schema; always requires approval; max 1 post/day; 150-300 words with hook-body-CTA structure). Created scripts/linkedin_post.py (Playwright poster with persistent Chromium context, CAPTCHA detection with Dashboard alert and immediate exit, session expiry detection with Dashboard alert, DRY_RUN support, --setup flag for first-time login, post() function as orchestrator entry point, CLI with --post and --dry-run flags). Updated watchers/orchestrator.py (added run_linkedin_post() method following run_briefing() pattern, --linkedin CLI flag, invokes generate-linkedin-post skill with Business_Goals.md and Company_Handbook.md context).

## Outcome

- Impact: Full LinkedIn pipeline operational — posts generated via skill, published via Playwright, always require human approval
- Tests: Syntax verification PASS for both linkedin_post.py and orchestrator.py
- Files: 3 files created/modified
- Next prompts: /sp.implement phase 06 (Orchestrator Extension + HITL)
- Reflection: LinkedIn pipeline follows same pattern as briefing (skill + orchestrator method + CLI flag); Playwright poster mirrors WhatsApp watcher's async/sync bridge approach

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): Syntax checks PASS, file structure PASS
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
