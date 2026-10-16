# Local voice integration verification — 0.2.0

Date: 2026-10-16. Scope: bundled microphone-to-text bridge and Skill routing, not a completed one-hour voice interview product.

## Executed

- Full local suite: `python -m unittest discover -s tests -v` — **55 tests passed**, zero failures, 9.747 seconds in the recorded run. Python 3.13.5 on Linux.
- The 55 comprise 14 existing design/reference checks, 17 original microphone-server tests, and 24 new voice/package/portability checks.
- `node tests/ui_state_test.cjs` — **8 simulated media-state assertions passed**.
- `node tests/voice_ui_test.cjs` — **15 simulated bridge/UI assertions passed**.
- Python compilation, JavaScript syntax check, and `git diff --check` passed.
- A clean copy of the entire Skill in a directory with spaces ran its doctor command outside the source repository.
- Real local HTTP requests and CLI subprocesses exercised ask/transcribe/confirm/wait and start/status/stop. The ASR/model backend in these tests was a reviewed **fake**, not Whisper.
- Startup metadata used a private loopback URL; the token was absent from server logs; POSIX metadata mode was 0600.

Ordinary local logs: [Python test output](verification/voice-tests.txt), [simulated UI output](verification/voice-ui-tests.txt). No Actions or workflow run was used. The older automatic workflow file was removed; the 0.1.0 verification report is retained only as historical evidence.

## Regression evidence and limits

Before implementation, all 18 initial new integration/package tests failed for the missing bridge, missing Skill routing or old workflow. Tests were extended as interfaces were implemented. This is a code/structure baseline, not a fresh-model/no-skill behavior experiment.

Earlier full-suite invocations exceeded command time limits and one dependency-probe portability check was intermittent under load. Checks were rerun; most CLI argument tests now invoke the real entry function in-process, while independent subprocess tests retain real start/status/stop and wait coverage. The final complete suite above passed. Timed-out partial logs are not treated as passing runs.

Covered: confirmed-only delivery; exact question binding; answer revisions; idempotent confirmation; refusal of pending-question replacement without explicit skip; stale recording/draft rejection; no automatic audio writes; invalid wait bounds; local metadata validation; download approval gate; private startup and authenticated shutdown; question display and microphone release on simulated channel failure.

Not executed: actual microphone hardware, real browser microphone permission, real faster-whisper inference, real audio accuracy/latency, installed Codex agent behavior, macOS/Windows device validation, full-duplex interruption or one-hour endurance. `doctor` reported faster-whisper was not installed in this test environment. No dependency/model installation on the candidate's computer is claimed. The 32 broader behavior/runtime scenarios remain `not_run`.

A live Codex process must call wait to consume confirmed text; files cannot wake an inactive host. Browser polling may be throttled in inactive tabs: close the tab for immediate microphone release. Session crash recovery remains manual. No acoustic speaking-style analysis or safe candidate-code execution is provided.
