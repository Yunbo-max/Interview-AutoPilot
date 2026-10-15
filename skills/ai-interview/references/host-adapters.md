# Host adapters and installation

## Skills-only mode available from this package

The entire `ai-interview/` directory must travel together. In Codex, place it under a supported `.agents/skills/` location, then explicitly invoke `$ai-interview`. This release also includes portable root `plugin.json` and a Codex compatibility manifest. It does not register a remote server, deploy a service or install into an account automatically. Host discovery and behavior still require a smoke test in the chosen host.

Plain chat can apply the interview rules through available text/file tools. No mounted microphone, persistent storage or clock is assumed. A resume supplied in that chat is not permission to search unrelated connected files.

Official sources: [Codex skill discovery](https://developers.openai.com/codex/skills/), [plugin packaging](https://developers.openai.com/plugins/build/plugins), [Agent Skills format](https://agentskills.io/specification). Consult them again before changing installation metadata.

## Future local runtime: recommended adapter

A browser handles the candidate's input and an explicit submission control. A local controller owns the session clock, state and tool permissions. Speech-to-text feeds a canonical text turn to the interviewer; TTS speaks only the approved interviewer reply. Acoustic analysis reads authorized raw audio independently. Start turn-based; full-duplex is a separate acceptance gate.

Codex App Server is an integration option for a custom interactive client: initialize the connection, start/resume a thread, stream turns and handle approvals/interruptions. App Server has its own protocol; it is not interchangeable with an MCP server. Map a session ID to the actual returned thread ID, and persist it only with consent. Recheck the installed protocol version rather than copying sample fields forever. [Official App Server documentation](https://developers.openai.com/codex/app-server/).

An alternative agent API can implement the same logical contracts. No specific paid provider or model is required by this skill. Do not promise a subscription covers separate speech/model API usage. Set explicit cost/rate/concurrency budgets during runtime setup, fail clearly when they are exhausted, and never invent pricing.

## Media integration

Browser microphone access requires consent and a secure context; screen capture needs explicit user selection. See [getUserMedia](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia) and [getDisplayMedia](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getDisplayMedia). These APIs do not implement the interview engine or guarantee compatibility in every browser.

STT outputs differ by model. Probe transcript finalization, alignment, timestamps and supported confidence outputs; unavailable metadata remains unavailable. [Realtime transcription](https://developers.openai.com/api/docs/guides/realtime-transcription).

A one-hour product session is independent of any provider connection lifetime. The Realtime conversation documentation checked on 2026-10-15 specifies a 60-minute session maximum: reserve reconnection margin and carry the controller state across a fresh connection rather than resetting the interview. Treat that limit as provider-specific, not universal. [Realtime conversations](https://developers.openai.com/api/docs/guides/realtime-conversations).

## Optional checkers

An audio adapter may use [librosa pYIN](https://librosa.org/doc/latest/generated/librosa.pyin.html) for voiced pitch estimates; estimates are not emotion labels. A math adapter may use [SymPy assumptions](https://docs.sympy.org/latest/guides/assumptions.html) for bounded symbolic checks; no simplification does not mean false. Neither dependency nor adapter is bundled as a working runtime here.
