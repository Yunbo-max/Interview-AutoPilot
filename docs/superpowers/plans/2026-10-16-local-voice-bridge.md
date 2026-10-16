# Local Voice Bridge Implementation Plan

> For agentic workers: implement and verify each bounded task before publishing.

**Goal:** let local Codex call the microphone program from its installed ai-interview Skill.
**Architecture:** bundle the existing recorder/backend, add an authenticated question/revision controller and a bounded CLI wait loop, and route the Skill to these real tools.
**Tech Stack:** Python 3.10+ standard library, faster-whisper 1.2.1, browser MediaRecorder, unittest and Node simulated-media tests.
**Spec:** [Local voice bridge](../specs/2026-10-16-local-voice-bridge.md).

## Global constraints

No recording before user action; no hidden speech uploads; no public candidate records; no Actions/workflows. Tool presence is not real-device certification. Existing text mode remains usable.

## Tasks

1. Run existing tests; add failing bridge/packaging tests before implementing the bridge.
2. Bundle mic server/backend/UI; implement doctor/setup/start/ask/wait/status/stop with token, loopback and session protections.
3. Connect the page to the current question; only confirmed matching answers become tool output; stop recording on channel loss.
4. Update skill routing, bilingual installation documentation and version; retire the old automatic workflow.
5. Add round-trip, stale/dedup, correction, malformed input, cancellation and UI regression checks; run complete local suites.
6. Inspect package portability, compare source blobs against uploaded tree, then update main without force. Save ordinary verification logs only.

## Review focus

Pending microphone permission followed by a question change; old draft finishing after a skip; duplicate Confirm requests; model/loopback unavailable; private token accidentally exposed through logs or proxy/redirect. Cover each with tests or an explicit remaining limitation.
