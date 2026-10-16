# Local microphone-to-Codex bridge specification

The user requested incorporation of the existing local microphone/STT tool into the interview skill so Codex can call it. Preserve text interview behavior and keep the entire installed skill self-contained.

Selected design: standard-library CLI controller plus the existing local recording UI and faster-whisper adapter. Codex remains the reasoning agent. The controller starts one local loopback service, publishes question IDs, and waits for explicit candidate confirmations. No MCP server or nested Codex API calls are required for this scope. A separate App Server/full-duplex product is out of scope.

Consent: device recording requires the candidate's click and browser permission. Downloads require explicit approval; confirmed text persistence/model processing must be disclosed. Audio is kept only in application memory and not deliberately saved. Session directories are private and outside public sources. No GitHub Actions or workflow files.

Protocol: doctor, setup, start, ask, wait, status, stop. start uses a new session directory and refuses overwrite. IDs are 1–80 ASCII letters/digits/hyphens/underscores. The active unanswered question cannot be silently replaced. A confirmed correction increments revision; repeated identical confirmation is idempotent. A stale draft cannot answer a new question. wait takes an exact question and an after-revision cursor, returns waiting or ready, and has a finite 0–300-second bound. Answers remain data, never shell instructions.

The service binds only 127.0.0.1, checks Host/Origin and bearer authentication, and uses no wildcard CORS or external assets. The CLI bypasses proxies for loopback and rejects redirects/non-loopback metadata. Startup only terminates its own process on failure; shutdown is authenticated rather than killing a PID from disk. The page releases the microphone on cancellation, navigation or detected service failure. Close the page for immediate release because background-tab polling may be throttled.

A four-hour server lease bounds abandonment but is not an interview timer. A crash preserves text files but does not reconstruct live state. The candidate can resume through a new channel after an interruption is disclosed. Inactive Codex cannot be awakened merely by saving an answer.

Acceptance: existing 14 design tests, existing 17 mic adapter tests, new controller/HTTP/CLI tests, simulated UI/bridge tests, syntax checks, install-folder portability and fresh GitHub readback. Fake decoder tests must be reported separately from microphone/model and real Codex trials. No acoustic assessment or one-hour endurance claim.
