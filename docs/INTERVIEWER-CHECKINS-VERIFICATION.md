# v0.8.0: Natural interviewer check-ins and microphone activity verification

Date: 2026-10-16. Source: `AI-Interview` on main. Scope: the local deterministic Timekeeper, browser-only speech-amplitude observer, authorized HTTP metadata and mocked interview interaction. **This report does not certify physical macOS microphone behavior, VoiceStudio TTS quality, latency or an uninterrupted hour of interviewing.**

## Executed commands

- `python -m unittest discover -s tests -v` → **182 tests run; 0 failures and 0 errors**. Full log: [checkins-0.8-python.txt](verification/checkins-0.8-python.txt).
- The **8** `tests/*_test.cjs` Node suites → **all exit 0**, including simulated `silence_monitor_test.cjs`, `studio_silence_ui_test.cjs`, earlier 7 asynchronous microphone fault scenarios, and existing UI/voice/Timekeeper tests. Log: [checkins-0.8-ui.txt](verification/checkins-0.8-ui.txt).
- `python -m compileall -q skills/ai-interview/scripts`, `node --check skills/ai-interview/scripts/studio_web/app.js`, and `node --check skills/ai-interview/scripts/studio_web/silence_monitor.js` → all exit 0.
- Test-first evidence: the Python natural-checkin test initially failed because `checkin_prompt` was absent; local amplitude policy test failed because `silence_monitor.js` did not exist; browser mock test failed because no acoustic sampling timer was installed; a server test failed because `/api/acoustic-checkin` returned 404. Each corresponding test passed after its minimum implementation.

## Verified behavior (mocked)

- Timed HR prompts at 1, 2 and 5 minutes now include distinct natural Chinese/English interviewer questions. Coding reminders remain visual-only; a read-only state poll does not trigger a model call, submission or adverse scoring.
- The browser never opens microphone merely to ask for time. The Web Audio monitor starts only after candidate-initiated `getUserMedia`, samples an in-memory amplitude buffer every 500ms and reacts once to ~40s below threshold. A short active audio signal postpones the nudge. No audio or level samples are posted to the server.
- During a spoken check-in, the selected microphone `MediaStreamTrack.enabled` is set false and later restored. Playback end/error/12-second timeout, record cancellation and page lifecycle changes clean up the guard. Question Replay while recording is rejected to prevent feedback into candidate audio.
- The authenticated `/api/acoustic-checkin` endpoint records **only** one bounded, client-reported event for the current spoken question in the timing ledger. Invalid/stale question IDs, unauthenticated requests and pre-interview activity are rejected; neither model grading nor voice consent is bypassed.
- Browser unavailable Web Audio/SpeechSynthesis or intentionally muted speech falls back to visible Timekeeper reminders; the observer does not falsely assert acoustic silence.

## Unverified or intentionally unsupported

Physical microphones; speech recognition accuracy; device echo leakage under genuine VoiceStudio capture; background-tab throttling; Web Audio autoplay restrictions; multilingual TTS model switching for check-ins; native full duplex; wake-word/always-on mic; changing interview questions on nonresponse; and true voice-command navigation. Activity detection uses **approximate amplitude**, not clinical-grade speech recognition, voice identity or proof of silence; quiet candidates and ambient noise can fool the heuristic. Candidate must use on-screen Repeat / +1 minute / Skip controls; speaking "repeat" does not automatically issue those actions. Candidate answers are still submitted only after explicit confirmation. A closed browser tab cannot audibly prompt and doesn't automatically pause the server timer.

License: no third-party voice engine source is imported. GitHub Actions, workflow runs and extra branches are not used.
