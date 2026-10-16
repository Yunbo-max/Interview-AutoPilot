# Timekeeper Agent implementation plan

> Native implementation using test-first regression checks. No branches or GitHub Actions.

**Goal:** An independent deterministic timing supervisor for the voice interview.
**Architecture:** `TimekeeperAgent` owns timing ledger/reminders; `InterviewSession` uses monotonic `SessionClock` and its existing lock; `/api/state` exposes snapshots; UI prompts without guessing silence. Read the adjacent design document first.
**Tech Stack:** Python 3.10+ stdlib, existing local HTTP server, browser JavaScript, unittest and Node VM mocks.
**Spec:** `docs/superpowers/specs/2026-10-16-timekeeper-agent.md`.

## Constraints and review focus

Keep candidate data private; skipped answers ungraded; no additional LLM usage for reminders; deterministic time measurement excludes pauses, ASR/model waits; current question id is authoritative; UI never auto-starts a microphone or auto-submits an answer; preserve all old features. Test late polls, pauses, stale actions, duplicate skip, model failure and code-mode no spoken reminders.

- [x] Write failing timekeeper unit and integration tests.
- [x] Implement pure per-question clock, reminders, explicit extension and timing ledger.
- [x] Wire `InterviewSession` transitions and idempotent skip; honor deadline without LLM call.
- [x] Add authenticated HTTP actions and autonomous periodic pulse.
- [x] Add UI timers and gentle reminders; record timing in review.
- [x] Update Skills, bilingual README, changelog and version metadata.
- [x] Run full Python, Node, compile, syntax, package and security checks; publish only to `main` via Pull/Push and verify remote Git tree.
