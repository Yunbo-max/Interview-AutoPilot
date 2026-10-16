# Timekeeper Agent for voice-first interviews — design

Date: 2026-10-16. Target: AI-Interview 0.7.0.

## Objective

A locally running deterministic **Timekeeper Agent** supervises the existing single interviewer's timing without additional LLM calls. It owns per-question active elapsed time, soft pacing reminders, explicit skips, and an exportable timing ledger. It must never confuse a draft, audible speech, reasoning silence, a model outage or ASR failure with a wrong answer. Browser closure does not create remote notifications; the local server still measures time until paused or stopped.

## Boundaries

- The existing `SessionClock` remains the authority: monotonic active seconds exclude explicit pauses, provider execution, setup and review. UTC wall-clock labels are for audit only; do not compute budgets from wall time.
- `TimekeeperAgent` is **a deterministic local component, not a second LLM process**. The web server calls `pulse()` periodically; it stores each crossed reminder once and returns it through the authenticated `/api/state`. The UI can voice a reminder through local browser speech only if recording, transcription and question speech have stopped.
- Policy by question: HR (60/120/300 seconds); systems, agent, ML, quant, transformer, RL (90/180/300); math, generation and research (120/240/360); coding (300/600/900). Levels: gentle elapsed reminder, request for partial reasoning, offer to skip. No automatic grading, question skipping or scoring penalties.
- A candidate may explicitly request up to two +60-second **recommended question budget** extensions, but this does not extend the 60-minute session clock. A candidate may explicitly skip; skipped questions are **unassessed**, preserved in history and included in reviews.
- At 55 and 59 active minutes, timekeeper records a session warning. At 60 active minutes, it stops accepting new answers without invoking an LLM; the user can finish/review. No extra question is generated after deadline.
- Only server-validated active question IDs can be extended or skipped. Repeat skip IDs are idempotent; retry failures must preserve the active question and clock. No raw audio or new candidate data is persisted.
- Reports contain phase, kind, question ID, active seconds, UTC start/end audit timestamps, reminders, extensions, outcome and summary counts; turn-by-turn time is **not a measure of competence**. No "silence detector" is claimed, since no VAD measurement is available.

## UX

Keep the 60-minute remaining clock, add an independent per-question clock and a calm Timekeeper status panel. Dynamic reminders display without interrupting a recording. Offer **+1 minute** and **Skip question** actions. Voice reminders are optional and local; coding reminders remain visual. Skipping should not generate a fake candidate answer. A completed review includes timing details and skipped/unanswered distinctions.

## Validation

A fake monotonic clock demonstrates threshold crossing, pauses, model delays, deadline and total-time exclusions without sleeping. HTTP tests verify authenticated skip/extension, stale IDs and no extra model grading for inactivity. JavaScript mock tests verify reminders, non-interruption of recordings, actions and review display. Run all existing Python/Node suites; tests alone do not certify a physical microphone or live one-hour interview.
