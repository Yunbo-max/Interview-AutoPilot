# Optional VoiceStudio audio backend — installation and use

This is the executable VoiceStudio integration for the **independent** AI-Interview
project. It is an external optional speech *backend*, not a replacement for
Codex/Claude/Gemini/Qwen/DeepSeek/GLM/Kimi as interviewer. No VoiceStudio source,
model weights, audio recordings or voice profiles are bundled with this MIT skill.
The integration speaks VoiceStudio's documented local HTTP/WS speech protocol.

## 1. Install VoiceStudio on your own computer

1. Obtain the current installer from the **official**
   [VoiceStudio releases/latest](https://github.com/debpalash/VoiceStudio/releases/latest).
   Verify the published SHA-256 checksum. Use the macOS `.dmg`, Windows `.exe`,
   or Linux `.AppImage` / `.deb` for your OS. You are installing VoiceStudio
   *separately*, not copying its source into AI-Interview.
2. Launch the installed app and complete its normal first-run setup. In its
   **Model Manager / Model Catalogue**, install/configure an ASR model and the
   TTS engine you actually want; accept any model-specific licenses and download
   prompts yourself. **No automatic install or download** of VoiceStudio is
   performed by AI-Interview. VoiceStudio may download missing weights on its
   first TTS/ASR use; our webpage requires an explicit external-backend checkbox
   before invoking it. The user must review those upstream settings.
3. Ensure the backend is running on loopback port **3900** (or another local port).
   Check it locally:

   ```sh
   curl --fail http://127.0.0.1:3900/.well-known/voicestudio-speech
   ```

   It should report `protocol: "voicestudio.speech.v1"`. This is a protocol
   check, **not** proof that a specific voice model has downloaded or warmed.
4. Hardware: VoiceStudio's packaged macOS Python backend requires **Apple
   Silicon**; Intel Macs can use its UI with a separate remote backend but
   this AI-Interview integration intentionally accepts loopback only. For an
   Intel Mac, prefer AI-Interview's bundled Faster-Whisper CPU route instead.
   Some VoiceStudio engines can run CPU-only, slowly; installed models and
   weights vary. See its official
   [macOS guide](https://github.com/debpalash/VoiceStudio/blob/main/docs/install/macos.md),
   [Windows guide](https://github.com/debpalash/VoiceStudio/blob/main/docs/install/windows.md)
   and [Linux guide](https://github.com/debpalash/VoiceStudio/blob/main/docs/install/linux.md).

## 2. Install our optional bridge dependency

In the AI-Interview project (or your installed `ai-interview` skill folder):

```sh
python3 -m pip install -r skills/ai-interview/scripts/requirements-studio.txt
python3 -m pip install -r skills/ai-interview/scripts/requirements-voicestudio.txt
```

On Windows, use `python` instead of `python3` if required. The second line
installs Python `websockets` for the **private loopback stream relay**. It does
not install VoiceStudio, GPU libraries, model weights or a new agent model.
If you omit this package, VoiceStudio **batch STT and TTS** may still work;
streaming subtitles are unavailable. Existing Whisper STT + browser TTS remains
available as a completely separate default.

## 3. Detect and start AI-Interview

```sh
python3 skills/ai-interview/scripts/career.py interview --doctor --voicestudio
python3 skills/ai-interview/scripts/career.py interview --without-stt --voicestudio
```

The first command probes localhost; it does not record audio or install anything.
The second opens the interview studio using VoiceStudio as an *available option*.
`--without-stt` means you do not need to download our built-in Whisper if
VoiceStudio does ASR. To keep both choices, omit `--without-stt` and install
our local model via the separate, existing `download-model --allow-download`
procedure.

For an alternate **local-only** port:

```sh
python3 skills/ai-interview/scripts/career.py interview --without-stt \
  --voicestudio --voicestudio-url http://127.0.0.1:3901
```

Only `http://127.0.0.1:<port>` is allowed. This integration deliberately refuses
public internet, arbitrary HTTP URLs, userinfo credentials, forwarding proxy
settings and LAN addresses. Do not use a public tunnel or weaken VoiceStudio
security to reach another machine. Restart the studio if VoiceStudio is started
after the interview process; the stream relay starts only when the local
service is discovered at startup. Browser access uses the authenticated private
URL printed by AI-Interview, not VoiceStudio's own UI URL.

## 4. Use during an interview

- On the AI-Interview web page, upload/preview your resume and choose your
  target role, optional JD, language, and **interviewer** (Codex, Claude Code,
  Gemini CLI or the supported model APIs). VoiceStudio is independent of
  this LLM selection.
- In the header, click **Check VoiceStudio** and inspect the detected voice
  profiles. Explicitly check the VoiceStudio consent switch after reviewing
  whether the app's selected model needs downloads, carries restrictions or
  routes audio to a remote service. Choose **VoiceStudio** in **Speech Engine**.
- Normal noncoding questions are synthesized with
  `POST /v1/audio/speech` and played only in the user's browser. **Play question**
  repeats them; **Mute**, **Record**, and **Pause** cancel ongoing playback.
  If voice generation fails, browser speech-synthesis is the fallback.
- Click **Record** to allow browser microphone access. The streaming relay uses
  VoiceStudio's documented
  `WS /v1/audio/transcriptions/stream`; **partial** and utterance-final text
  is preview-only. On **Stop**, it sends `{ "type": "input_audio.end" }` and
  accepts the `final_kind: "summary"` transcript for the candidate to edit.
  If streaming fails, it attempts VoiceStudio's `POST /v1/audio/transcriptions`
  batch API. Failed recognition is a tool failure, not a wrong answer.
- Only clicking **SUBMIT ANSWER** after checking terminology, equations,
  negation and names advances the interviewer. VoiceStudio never grades answers
  or auto-submits; Coding questions still show the code editor instead.
- If VoiceStudio is unavailable, leave Speech Engine on the default browser
  TTS / built-in Whisper, or answer by typing. No real-time hardware test is
  implied by the presence of the backend protocol.

## 5. How the relay works and what it does NOT do

Our local authenticated `interview_studio.py` HTTP service binds
`127.0.0.1`. It opens a **second ephemeral loopback WebSocket port** using
`scripts/voicestudio_relay.py`, with an exact browser-Origin allowlist, private
session token, active interview-question binding, no proxy, maximum 20 MiB
per recording, and a single active stream. The intermediary connects to
VoiceStudio as a **native local client without a browser Origin** because
VoiceStudio rejects WS traffic from an unrelated web application's origin.
Both services must reside on the candidate's machine; no microphone can be
opened from a cloud ChatGPT/remote Codex shell by this Skill.

Our code does not intentionally persist raw audio. It **does transmit audio to
VoiceStudio's local process**, whose own recording/history and optional remote
provider behavior are controlled by VoiceStudio's configuration, not by our
application. Read its privacy/security settings before opting in. The text
*you explicitly submit* goes to the selected online interview model under
the original AI-Interview consent. This is not a wholly offline interview if
that model is online or if VoiceStudio has cloud engines enabled.

The backend does **not** provide certified full-duplex interruption, acoustic
speaking-style grades, real-time word alignment, multi-speaker calls, or a
verified one-hour live endurance test. Browser audio, local model speed and
model-language support need real-device testing.

## 6. Optional standalone MCP access for agents

VoiceStudio also exposes a separate `http://127.0.0.1:3900/mcp/` MCP endpoint.
AI-Interview's **web page does not require this MCP connection**; the HTTP/WS
bridge above works with any supported interviewer model. If you want Codex to
call VoiceStudio tools directly, the upstream
[MCP guide](https://github.com/debpalash/VoiceStudio/blob/main/docs/mcp.md)
provides this optional Codex config:

```toml
[mcp_servers.voicestudio]
url = "http://127.0.0.1:3900/mcp/"
http_headers = { "X-OmniVoice-Client-Id" = "codex-cli" }
```

Configure Claude Code or other MCP-compatible hosts according to the same
upstream guide and the host's current MCP documentation. Do not install a
second VoiceStudio backend, assume models exist, or turn on MCP just for the
interview website. MCP `generate_speech` may return base64 audio; our dedicated
HTTP audio route keeps waveform bytes out of the LLM context.

## 7. License and operational limits

[VoiceStudio](https://github.com/debpalash/VoiceStudio) is separately available
under **AGPL-3.0**. Its app, its third-party engines, weights and generated
outputs have distinct terms; some weights are non-commercial. Read its
[license notice](https://github.com/debpalash/VoiceStudio/blob/main/LICENSE-NOTICE.md)
and [model inventory](https://github.com/debpalash/VoiceStudio/blob/main/docs/licensing/model-inventory.md).
This MIT project uses its documented public protocol and does **not** bundle,
modify or distribute VoiceStudio code, audio models or model weights.
Interoperability is not a legal conclusion about derivative works; review
license obligations before creating a redistributed combined product.
