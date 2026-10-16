# Timekeeper Agent — local integration verification (v0.7.0)

Date: 2026-10-16. Scope: deterministic local Timekeeper and browser/server/VoiceStudio integration. **This is a simulated local test and source review, not a measured live one-hour interview.**

## What is implemented

- The Python Timekeeper computes per-question active time from the existing monotonic session clock. A periodic local server pulse records reminders even if the browser's three-second polling is delayed. It never calls an LLM, opens a microphone, grades thinking time, assumes the candidate is silent, or wakes a closed browser.
- Default reminder policies: HR 60/120/300s; technical voice 90/180/300s; math, generation and research 120/240/360s; coding 300/600/900s. Notices are advisory, not a forced auto-skip.
- Explicit candidate actions: bounded +60s question-time advisory extension (twice), or idempotent skip with an unassessed record. All requests require the live authenticated question ID; errors and stale submissions cannot silently move the interview forward.
- At 3300 and 3540 active seconds the server records whole-session warnings. At 3600 it expires the question without a new LLM call, and an explicit review can follow.
- Recorded response durations exclude explicit pause, model generation, and active-question audio transcription/finalization on either local Whisper or VoiceStudio. Machine processing has nested hold and manual-pause rules, so completion after a manual pause cannot resume the clock. Speaker playback and machine sleep still require real-device measurement.
- The browser displays two independent clocks, provides a local (no model) spoken reminder only when speech/recording is inactive, offers skip/extension and exports answer times, outcomes and UTC audit labels. No automatic raw-answer/voice persistence was added.

## Executed evidence

The repository contains deterministic tests in `tests/test_timekeeper.py`, HTTP tests in `tests/test_studio_http.py`, VoiceStudio streaming test in `tests/test_voicestudio_adapter.py`, and a separate mocked browser `tests/timekeeper_ui_test.cjs`. The tests exercise late/no browser polls, pause/resume, timed reminders, explicit unassessed skip, idempotency, model failures, overall time cutoff, STT waiting and simulated frontend audio behaviour. Fresh local verification: **177/177 Python unittest methods passed** (0 failures, 0 errors), and **all six Node.js UI simulation suites passed**. Logs: [`Python`](verification/timekeeper-0.7-python.txt) and [`UI`](verification/timekeeper-0.7-ui.txt). Python compileall, JavaScript syntax checks and launcher Bash syntax checks also passed. The tests use mocked microphone/audio hardware and local loopback services rather than real Mac devices.

Regression controls: new Timekeeper tests failed before `interview_timekeeper.py` existed. HTTP tests for authenticated extension/skip and automatic server deadline failed before the routes and service pulse were wired. The batch STT test reproduced 200 simulated seconds of wrongly billed inference, and VoiceStudio WS test reproduced the same for final-summary processing; both now have scoped model-wait exclusion. The browser test initially failed without a per-question display and independent actions. A concurrency ordering regression was found and fixed so the streaming ASR hold is released **before** the final text becomes available to the candidate.

## Not established by these checks

- No real MacBook Pro microphone, speech model, audio player, model-provider login, or continuous physical one-hour test was run.
- No speech-activity detector exists: “not submitted” is not “silent.” A voice prompt may be suppressed while the microphone is active. The current system is turn-taking, not full-duplex.
- Closing the browser does not pause the service; press Pause before leaving. The effect of actual macOS sleep, microphone permission dialogs, TTS rendering, and host resource pressure has not been verified.
- Skipped questions and slow answers are **not** correctness evidence. No hiring-probability, personality, voice-tone, or deception score is produced. VoiceStudio is a separately installed third-party app, not bundled into this repository.
