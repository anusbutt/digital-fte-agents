---
id: 011
title: Phase 7 Scheduling PM2 Process Management
stage: green
date: 2026-02-24
surface: agent
model: claude-sonnet-4-6
feature: 001-digital-fte-silver
branch: 001-digital-fte-silver
user: architect
command: /sp.implement
labels: ["implementation", "pm2", "scheduling", "phase-7", "US7", "windows-task-scheduler"]
links:
  spec: specs/001-digital-fte-silver/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - scripts/pm2_ecosystem.config.js
  - scripts/setup_scheduler.py
  - scripts/pm2_healthcheck.py
  - watchers/orchestrator.py
tests:
  - setup_scheduler.py syntax PASS
  - pm2_healthcheck.py syntax PASS
  - orchestrator.py syntax PASS
---

## Prompt

/sp.implement phase 07.

## Response snapshot

Completed Phase 7 Scheduling + PM2: 4 tasks (T040-T043). T040: Created scripts/pm2_ecosystem.config.js with 5 PM2 processes (filesystem-watcher, gmail-watcher, whatsapp-watcher, orchestrator, email-mcp), each with max_restarts:10, restart_delay:5000, autorestart:true, per-process log files in vault/Logs/. T041: Created scripts/setup_scheduler.py using schtasks CLI — creates DigitalFTE-LinkedIn (weekdays 09:00 via --linkedin), DigitalFTE-Briefing (Monday 08:00 via --briefing), DigitalFTE-PM2Health (every 5 min); uses cmd /c wrapper for cwd support; prefers .venv Python. T042: Created scripts/pm2_healthcheck.py — runs pm2 jlist, parses JSON, checks EXPECTED_PROCESSES set, restarts stopped/errored/crashed processes, logs to vault/Logs/ via watchers.logger. T043: Updated run_briefing() in orchestrator.py — ensures vault/Briefings/ exists (mkdir parents), adds Company_Handbook.md to context files.

## Outcome

- Impact: All 5 processes manageable via pm2 start; 3 Task Scheduler entries for automation; health checks every 5 minutes
- Tests: All 3 Python files syntax PASS
- Files: 4 files created/modified
- Next prompts: /sp.implement phase 08 (Agent Skills Update)
- Reflection: schtasks uses cmd /c wrapper to set working directory (schtasks has no native cwd flag); pm2_healthcheck.py uses EXPECTED_PROCESSES set for easy future extension; PM2 process logs go to vault/Logs/ separate from business audit logs per R5

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): syntax checks all PASS
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
