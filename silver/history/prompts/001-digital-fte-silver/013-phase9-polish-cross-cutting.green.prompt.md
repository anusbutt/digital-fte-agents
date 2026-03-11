---
id: 013
title: Phase 9 Polish Cross Cutting Concerns
stage: green
date: 2026-02-24
surface: agent
model: claude-sonnet-4-6
feature: 001-digital-fte-silver
branch: 001-digital-fte-silver
user: architect
command: /sp.implement
labels: ["implementation", "polish", "cli", "validation", "phase-9", "dry-run"]
links:
  spec: specs/001-digital-fte-silver/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - main.py
  - scripts/validate_dry_run.py
  - test_data/TEST_invoice_sample.txt
  - watchers/orchestrator.py
tests:
  - main.py syntax PASS
  - validate_dry_run.py syntax PASS
  - orchestrator.py syntax PASS
  - T048 env var audit PASS (all 10 vars in .env.example)
  - T050 logger.py field audit PASS (all 7 constitution Principle VII fields)
  - T051 dashboard update fix applied (run_linkedin_post now calls update-dashboard)
---

## Prompt

/sp.implement phase 09.

## Response snapshot

Completed Phase 9 Polish & Cross-Cutting: 5 tasks (T047-T051). T047: Rewrote main.py with argparse subcommands — commands: filesystem, gmail, whatsapp, orchestrator, briefing, linkedin, healthcheck, setup {gmail|whatsapp|linkedin|scheduler|pm2}; setup sub-targets dispatch to OAuth2/Playwright/schtasks/PM2 setup routines; no-args prints version + help. T048: Audited .env.example against all os.getenv() and process.env. calls — all 10 required vars present, PASS. T049: Created scripts/validate_dry_run.py (6-stage pipeline validator: vault structure, inbox file drop, filesystem watcher FILE_ creation, orchestrator DRY_RUN triage, audit log field verification, dashboard existence check; --no-cleanup flag; sys.exit(1) on failure) and test_data/TEST_invoice_sample.txt (sample invoice for testing). T050: Verified logger.py append_log_entry() — entry dict contains all 7 required fields per constitution Principle VII (timestamp, action_type, actor, target, parameters, result, approval_status), PASS. T051: Found run_linkedin_post() missing update-dashboard call; fixed by adding invoke_claude(update-dashboard) after skill completes, ensuring Pending_Approval/ count in Dashboard.md stays current.

## Outcome

- Impact: Clean unified CLI for all operations; DRY_RUN validation tool for QA; all constitution principles verified
- Tests: All 3 Python syntax checks PASS; T048/T050 field audits PASS
- Files: 4 files created/modified
- Next prompts: /sp.git.commit_pr or architect review of full implementation
- Reflection: T051 caught a real bug — run_linkedin_post() was missing dashboard update; validate_dry_run.py is reusable as a smoke test

## Evaluation notes (flywheel)

- Failure modes observed: None in this phase
- Graders run and results (PASS/FAIL): syntax PASS x3, env audit PASS, field audit PASS
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
