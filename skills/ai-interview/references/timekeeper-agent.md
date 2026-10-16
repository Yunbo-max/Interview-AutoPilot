# Timekeeper Agent — local deterministic pacing supervisor

## Why a separate component?

The interviewer model decides *what to ask* and challenges candidate evidence.
`interview_timekeeper.py` owns *when to remind* and *what time to record*.
It is called an "agent" because it has an independent event policy and timing
ledger. **It is not a second LLM, background Codex call, hosted notification,
or an always-on microphone detector.** Its reminders require no tokens or API key.

The web server invokes `InterviewSession.pulse()` on every service loop even if
no browser `/api/state` poll is received. The session uses `time.monotonic()`
active time. The visible browser polls state for events and can optionally use
system SpeechSynthesis for a brief audio notice. A closed browser cannot play
the reminder, and closing a tab is **not** an automatic pause: press **Pause**
first. A laptop sleep/device restart is not a certified recoverable session.

## Default question policy

| Question category | Gentle nudge | Explain approach | Offer to skip |
| --- | --- | --- | --- |
| HR / resume | 1 min | 2 min | 5 min |
| Transformer / RL / agent / systems / ML / quant | 1m 30s | 3 min | 5 min |
| Probability / math / diffusion / research | 2 min | 4 min | 6 min |
| Coding | 5 min | 10 min | 15 min |

The labels above mean **time since a question became active without a submitted
answer**, not detected silence. Someone thinking, typing, talking into a
microphone, or reviewing a draft is not automatically considered unable to
answer or wrong. For ordinary unanswered voice questions, the browser can speak a brief, natural **interviewer check-in** (not just elapsed-time narration). The scheduled check-in remains visual while recording or coding; no extra model call is used.

**Separate voluntary microphone monitor (0.8.0):** Only after a candidate clicks Record, `studio_web/silence_monitor.js` samples local amplitude through a Web Audio analyser (never connected to output). Two consecutive above-threshold samples indicate activity and reset the approximate silence clock. At roughly 40 seconds of low activity, a once-only interviewer question is shown and, unless muted or unsupported, spoken. The microphone media track is temporarily disabled during this short system-voice prompt to avoid capturing the interviewer, then restored on completion/error/cancellation or a 12-second limit. Microphone silence is *approximate*, not speech content, and noise or quiet speaking can produce false readings; this feature cannot identify whether the candidate is thinking or struggling. The browser provides a replay button and +1 minute controls but never submits or grades a reply automatically. An optional client-observed check-in timestamp (one per active question) is recorded in `timing.turns[].acoustic_checkins` without audio or waveform levels. It is explicitly not independently verified silence. Without Web Audio, only the unanswered-question timer is used; no microphone starts automatically. Pressing **+1 minute** pushes the final
*recommended* question time back by 60 seconds (at most twice). It **does not**
change the entire interview's 60-minute active-time limit, and it does not
silently discard the current answer draft.

At 55 and 59 active minutes the server records a session warning. At 60
verified active minutes it ends the active question without grading an absent
answer, refuses new answers, and offers a review. No model is called simply
because the clock crossed a threshold. If the user explicitly presses **Skip
question**, the interviewer generates the next question, the skipped question
is marked `skipped / unassessed`, and the candidate can still review that
unanswered question after the session. Failed model calls do not consume a
skip or alter the ledger.

## What is measured

The `SessionClock` is authoritative; never derive intervals from chat message
count or system wall time. Active durations include candidates' thinking,
manual typing, recording time, and the question being presented. They exclude
**explicit Pause**, **interviewer model inference**, and **local Whisper /
VoiceStudio transcription/finalization** when bound to the active question.
The HTTP audio endpoint binds via `question_id`; the WebSocket relay pauses
candidate time only after it sends `input_audio.end`, not during microphone
recording. TTS render and laptop sleep effects are not separately certified;
on slow devices they may affect elapsed time. UTC timestamps in exported timing
records are labels, not sources for elapsed seconds.

`GET /api/state` (authenticated, same-origin) returns `timekeeper` with
question elapsed, recommended budget, reminder IDs, session warnings, and
whether STT machine processing is ongoing. `POST /api/extend-question` accepts
`{"question_id":"..."}`; `POST /api/skip` requires that current ID and a
bounded idempotency `submission_id`. Skips do not fabricate a candidate answer.

The exported session review contains `timing.turns` with question ID, phase,
kind, active duration, reminder/check-in events, extensions, UTC start/end, and
`answered/skipped/unfinished/time_limit` outcome. The clock **is not a
competence score**, hiring probability, or emotion/accent estimate. The
private optional `/memory` summary still stores only condensed coverage/counts
rather than raw transcripts or the detailed timing ledger.

## Portable use

The standard local Mac installer automatically includes this Python file in
the self-contained Skill; no Timekeeper software or account is installed
separately. `scripts/career.py interview` starts the same studio. For an
ordinary text-only chat or remote Agent without access to the live local
server, timers cannot autonomously wake or speak; use a user-managed clock
per [session contract](session-and-clock.md). Do not claim a new LLM subagent
ran when only this deterministic monitor was active.

Tests: `tests/test_timekeeper.py`, `tests/test_studio_http.py`,
`tests/test_voicestudio_adapter.py`, and `tests/timekeeper_ui_test.cjs` in the
full repository. See `docs/TIMEKEEPER-VERIFICATION.md` at the repository root.
