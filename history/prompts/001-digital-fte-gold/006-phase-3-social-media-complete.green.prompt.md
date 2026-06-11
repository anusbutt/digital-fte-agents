---
id: "006"
title: "Phase 3: Social Media Monitoring & Posting Complete"
stage: green
date: "2026-03-14"
surface: agent
model: claude-sonnet-4-6
feature: 001-nestaro-pilot
branch: 001-ai-employee-foundation
user: architect
command: "/sp.implement phase 3"
labels: ["phase-3", "social-media", "playwright", "facebook", "instagram", "twitter", "HITL", "watchers", "posting"]
links:
  spec: "./specs/001-nestaro-pilot/spec.md"
  plan: "./specs/001-nestaro-pilot/plan.md"
  tasks: "./specs/001-nestaro-pilot/tasks.md"
  adr: "null"
  pr: "null"
files:
  - ./watchers/facebook_watcher.py
  - ./watchers/instagram_watcher.py
  - ./watchers/twitter_watcher.py
  - ./scripts/facebook_post.py
  - ./scripts/instagram_post.py
  - ./scripts/twitter_post.py
  - ./scripts/social_post.py
  - ./skills/generate-social-post.md
  - ./watchers/orchestrator.py
  - ./main.py
  - ./specs/001-nestaro-pilot/tasks.md
tests:
  - "Manual: drop FACEBOOK_test.md into vault/Needs_Action/ → verify orchestrator triages"
  - "Manual: move APPROVE_*.md to Approved/ → verify facebook_post.py logs DRY_RUN"
  - "Manual: python main.py social-post → verify 3 files in Pending_Approval/"
  - "Manual: python main.py setup facebook → Playwright opens facebook.com"
---

## Prompt

```
please continue limit has reset.
```

(User confirmed to continue Phase 3 implementation after context limit reset.
Prior context: implementing T022–T027 was in progress; resuming from T028.)

## Response Summary

Completed all remaining Phase 3 tasks (T028–T030):

### T028 — `./skills/generate-social-post.md`

New skill that reads Business_Goals.md, Company_Handbook.md, and Done/ (last 7
days) to generate three platform-specific drafts in a single invocation:

- **Facebook**: 100–300 words, CTA required, 2–4 hashtags, warm/community tone
- **Instagram**: 125–200 words, opening hook required, 3–5 hashtags, aspirational tone, emoji woven in
- **Twitter/X**: HARD 280-char limit enforced by character counting step in skill body, 1–2 hashtags, punchy

Output: three files in `vault/Pending_Approval/` with naming convention
`SOCIAL_POST_{PLATFORM}_{YYYYMMDD_HHMMSS}.md`. All share the same timestamp
so they are visually linked as a batch. Files are NEVER auto-published —
each requires individual HITL approval via file move.

### T029 — Orchestrator `run_social_post()` + `--social-post` flag

Added `run_social_post()` method to `./watchers/orchestrator.py`:
- Ensures `vault/Pending_Approval/` exists
- Reads Business_Goals.md, Company_Handbook.md, Dashboard.md as context
- Invokes generate-social-post skill via `invoke_claude()`
- Logs with `facebook_post` action_type (batch log entry)
- Updates dashboard after generation
- Added `--social-post` argparse flag to orchestrator CLI

### T030 — `./main.py`

Unified CLI entry point for the entire Nestaro Pilot tier:
- **Setup**: `python main.py setup {facebook,instagram,twitter,linkedin,whatsapp}`
  — each opens Playwright persistent context browser for manual login and saves session
- **Watchers**: `python main.py {facebook,instagram,twitter,whatsapp,email,files,orchestrator}`
  — loads env vars for poll interval and user_data_dir, starts the appropriate watcher
- **Content generation**: `python main.py {social-post,linkedin,briefing}`
  — delegates to `Orchestrator.run_social_post()`, `run_linkedin_post()`, `run_briefing()`
- All commands load `.env` from repo root and resolve VAULT_PATH absolutely
- `python main.py help` prints full command reference

## Outcome

Phase 3 (T022–T030) is **complete**. All 9 tasks marked `[x]` in tasks.md.

**Phase 3 deliverables:**
| File | Purpose |
|------|---------|
| `watchers/facebook_watcher.py` | Playwright Chromium → facebook.com/messages/ → keyword filter → FACEBOOK_.md |
| `watchers/instagram_watcher.py` | Playwright Chromium → instagram.com/direct/inbox/ → keyword filter → INSTAGRAM_.md |
| `watchers/twitter_watcher.py` | Playwright Chromium → /notifications/mentions + /messages → keyword filter → TWITTER_.md |
| `scripts/facebook_post.py` | `post_facebook()` — HITL-dispatched Facebook posting via Playwright |
| `scripts/instagram_post.py` | `post_instagram()` — HITL-dispatched Instagram posting via Playwright |
| `scripts/twitter_post.py` | `post_twitter()` — 280-char-enforced Twitter posting via Playwright |
| `scripts/social_post.py` | Thin re-export wrapper used by orchestrator |
| `skills/generate-social-post.md` | AI skill: generates 3 platform-specific drafts → Pending_Approval/ |
| `watchers/orchestrator.py` | Added `run_social_post()` + `--social-post` CLI flag |
| `main.py` | Unified CLI: setup, watch, generate |

**Architecture decisions enforced:**
- HITL for ALL social posts: no auto-publishing even for generated content
- Twitter 280-char limit: enforced in both `twitter_post.py` (truncates on dispatch) and `generate-social-post.md` (skill counts before writing)
- Session persistence: each platform uses its own `playwright-data/{platform}/` directory so sessions survive restarts
- DRY_RUN safe: all scripts skip Playwright and log intent when `DRY_RUN=true`

**Ready for**: Phase 4 — US2 Odoo Accounting MCP (T031–T036)
