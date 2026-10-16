# VoiceStudio optional backend — integration verification (0.5.0)

Date: 2026-10-16. Scope: independent protocol adapter and interview page integration. The VoiceStudio application, model weights and third-party source are **not** bundled; AI-Interview stays MIT and uses VoiceStudio's public REST/WS interoperability endpoints. This report distinguishes mock protocol tests from real hardware/product testing.

## Executed test types

- Python `unittest` full repository suite exercises prior interview/career/voice bridge functionality and new VoiceStudio HTTP, WebSocket relay, upload/size/loopback, session consent, TTS authorization and adapter portability checks. **135/135 passed** on Python 3.13; full output in [`verification/voicestudio-0.5-python.txt`](verification/voicestudio-0.5-python.txt).
- Five Node UI suites **passed**, including the new VoiceStudio streaming/TTS mock and 7 asynchronous microphone fault scenarios. Output: [`verification/voicestudio-0.5-ui.txt`](verification/voicestudio-0.5-ui.txt). They simulate microphone recording, packet streaming, partial/utterance versus final-summary transcript semantics, explicit candidate confirmation, speech generation, playback interruption, coding mode and fallbacks.
- Python `compileall`, Node `--check` and a copied standalone Skill `doctor --voicestudio` also passed. The doctor test confirmed that an unavailable local VoiceStudio reports `available=false` rather than a false connection success.
- The VoiceStudio HTTP service and streaming WebSocket are **fake local services**, not running VoiceStudio. No real speech quality, latency, live microphone, real installed app, per-engine model licenses, Electron platform compatibility or hour-long meeting was verified.

## Explicit security and consent boundaries

- No upstream VoiceStudio AGPL source, voices, models or binaries redistributed. User installs the independent application separately from its official signed/checksummed release as appropriate for the operating system.
- All adapter/relay targets and listeners are 127.0.0.1 only; no proxy or redirected HTTP requests. An authenticated, same-origin relay connects to VoiceStudio as a native loopback client because VoiceStudio rejects the AI-Interview web page's cross-port Origin. Tokens are session data and never intended for public GitHub output.
- A candidate enables VoiceStudio separately in the browser and must click the microphone to record. Text from STT is **not** automatically graded; the user corrects and submits it. The selected VoiceStudio engine may independently use remote inference or download model weights, so its configuration and model-license terms require review before use.
- Browser TTS and the prior Whisper/typed fallbacks remain available if VoiceStudio fails or has no compatible models. The optional `websockets` dependency enables live subtitles; without it, REST batch transcriptions can still work.

## Known limitations and acceptance still needed

- Real device acceptance on macOS/Windows/Linux with installed VoiceStudio v0.5.6+ or a compatible runtime is unverified. VoiceStudio documents that Intel Macs cannot run its local packaged backend. The effect of individual voice engines, resource usage, accessibility settings and delay requires measurement.
- This is turn-taking voice, not certified full-duplex conversation. Microphone errors, transcription failure or a stopped external app cannot be scored as candidate mistakes. No acoustic emotion/voice inference or secure code execution is supplied.
- The complete AI interview session has not been proven stable for a real continuous hour. No upstream AGPL license compatibility determination is asserted for anyone who modifies/embeds that upstream app; contact competent counsel for distribution-specific cases.

## Sources

- [VoiceStudio REST/WS speech contracts](https://github.com/debpalash/VoiceStudio/blob/main/docs/speech-platform.md)
- [VoiceStudio MCP](https://github.com/debpalash/VoiceStudio/blob/main/docs/mcp.md)
- [VoiceStudio download releases](https://github.com/debpalash/VoiceStudio/releases/latest)
- [VoiceStudio source and model notices](https://github.com/debpalash/VoiceStudio/blob/main/LICENSE-NOTICE.md)
