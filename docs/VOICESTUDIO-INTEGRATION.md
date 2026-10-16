# VoiceStudio integration architecture · AI-Interview 0.5.0

## Boundary

AI-Interview remains an independent MIT project. Optional third-party
VoiceStudio is installed and run by the candidate under its own AGPL-3.0
license. Only our independent protocol client, Python WS relay, browser choice
and technical tests are added to our repository. No vendor source, model
weights, voice clones, or external recordings ship with this package.

## Data flow

```text
Candidate browser (AI-Interview localhost page)
   |-- role / PDF -> local interview controller -> chosen LLM provider (consent)
   |-- interviewer question -> authenticated AI-Interview /api/voicestudio/speak
   |                           -> VoiceStudio localhost:3900 /v1/audio/speech
   |                           <- WAV bytes, capped and checked
   |-- clicked microphone -> private AI-Interview localhost WS relay
   |                         -> VoiceStudio localhost:3900/v1/audio/transcriptions/stream
   |                         <- partial (display only) / final_kind=summary
   |-- Stop -> candidate edits FINAL text -> explicitly submits answer to LLM
   |-- Coding question -> code editor; no TTS/ASR, no untrusted code execution
```

The browser cannot connect directly to VoiceStudio's WS on another localhost
port: VoiceStudio correctly checks the browser Origin. Our relay authenticates
the expected originating studio URL and private user token, and binds the
stream to the current `question_id`. The relay does not expose an admin API,
accept an external target, or install a speech model.

The relay is optional (`websockets>=15,<17`). Its absence disables live captions
without disabling VoiceStudio TTS/HTTP batch transcription. The original
Faster-Whisper speech backend and the browser's SpeechSynthesis remain the
unmodified default. The front end never submits partial STT or final text to
the interview LLM automatically; candidate confirmation is always required.

## Resource and privacy controls

`VoiceStudioAdapter` permits only `http://127.0.0.1:<port>`; no redirection,
user-supplied hostname, proxy, cloud URL or LAN target. HTTP responses and audio
uploads have size limits. TTS is restricted to the active spoken question, and
the question is checked again after generation. The speech relay enforces one
candidate stream, an exact permitted Origin, session token, matching active
question, and total audio/time limits; it never writes WAV/WebM bytes to disk.
A missing or failing service is not represented as a successfully transcribed
answer. The page can fall back to the built-in browser/Whisper path or typing.

VoiceStudio is a separately configured app: it may download model weights when
needed or route to a nonlocal ASR/TTS provider when the candidate configures
one. An opt-in checkbox must be explicitly checked before our UI can invoke
it. A disclosure is not a guarantee that VoiceStudio itself retains no audio:
review that application's own privacy/history and model/source settings.
AI-Interview still sends submitted resume/answers to the selected online LLM
only under separate existing model-processing consent.

## API contracts inspected 2026-10-16

- [VoiceStudio speech protocol](https://github.com/debpalash/VoiceStudio/blob/main/docs/speech-platform.md)
- [VoiceStudio MCP](https://github.com/debpalash/VoiceStudio/blob/main/docs/mcp.md)
- [VoiceStudio licenses](https://github.com/debpalash/VoiceStudio/blob/main/LICENSE-NOTICE.md)
- [VoiceStudio hardware install](https://github.com/debpalash/VoiceStudio/blob/main/docs/install/macos.md)

## Verification policy

Local fake-VoiceStudio HTTP server tests exercise capability discovery, TTS,
multipart STT, active-question checks and proxy/path controls. Local synthetic
WebSocket tests exercise Origin/token isolation, partial-to-final framing,
concurrent-client refusal and raw binary forwarding. Node simulated DOM/Media
Recorder tests exercise consent, speaker interruption, streamed partials,
confirmed-only submission and Coding transition. None of those fixtures
certifies actual ASR/TTS model accuracy, browser microphone permission,
performance on candidate hardware, upstream engine licenses, MCP integration,
or one-hour session reliability. See [verification](VOICESTUDIO-VERIFICATION.md).
