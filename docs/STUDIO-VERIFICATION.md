# AI Interview 0.3.0 — studio verification

Date: 2026-10-16. Scope: local voice-first interview studio, six role curricula, web coding editor, PDF extraction and seven configurable backends.

## Locally executed checks

- `python -m unittest discover -s tests -v`: **82 tests passed**, zero failures; includes 63 pre-existing checks and 19 new session/PDF/provider/HTTP tests. All CLI provider calls in tests use mocks; all audio decoding tests use fake transcription.
- `node tests/studio_ui_test.cjs`: simulated PDF/upload/consent/start/voice output/coding-mode UI flow passed.
- Existing JS suites: `ui_state_test.cjs`, `voice_ui_test.cjs`, `voice_failure_ui_test.cjs` remained passing (8 + 15 assertions and 7 asynchronous scenarios).
- `python -m compileall -q skills/ai-interview/scripts` and `node --check skills/ai-interview/scripts/studio_web/app.js`: passed.
- A real text-based PDF produced with ReportLab was extracted by pypdf, preserving visible candidate text. A blank PDF and invalid file bytes are rejected.
- A new regression test first failed because a completed review was not returned on `/api/state` after reload; server now exposes the previously generated in-memory review in completed state and the page restores it.

## What this does NOT establish

- No real browser microphone or system voice test, local Whisper inference, user-machine host CLI login, or authenticated paid API round trip was performed here.
- No safe execution of arbitrary submitted code. Reference answers, model scoring and mathematics assessments are model-generated and **not independently certified**.
- Browser SpeechSynthesis can be unavailable or blocked; explicit Replay and readable question text remain available.
- The 60-minute timer is an in-memory monotonic local session contract; a host crash loses live session and timing state. The one-hour physical endurance test remains not run.
- No certification for simultaneous speaking/interruptions or raw-audio prosody metrics.

The app is **ready for local compatibility testing**, not guaranteed to run on every laptop, account or provider. Candidate information is not committed to this public GitHub repository. Review downloaded test artifacts and logs only for local fixtures.
