# Voice-first studio: role-specific PDF interview and sourced research

The preferred path when the candidate asks for a voice-led mock interview with PDF, role-specific questions and a coding editor. This is an executable *local application* bundled in the Skill, not a remote ChatGPT microphone connector. The entire `skills/ai-interview` directory must be installed with `scripts/` and `studio_web/` intact.

## 1. Host check and setup

Requires Python 3.10+, a browser with `MediaRecorder`, localhost access and a model provider authenticated locally. In the Skill's real installed directory:

```bash
python3 "$SKILL_DIR/scripts/interview_studio.py" doctor
python3 -m pip install -r "$SKILL_DIR/scripts/requirements-studio.txt"
# For offline microphone transcription (requires explicit consent for downloads):
python3 -m pip install -r "$SKILL_DIR/scripts/requirements-voice.txt"
python3 "$SKILL_DIR/scripts/interview_studio.py" download-model --allow-download --model base
python3 "$SKILL_DIR/scripts/interview_studio.py" serve --model base
```

Use `python` rather than `python3` when appropriate for Windows. If local Whisper/model weights are unavailable, use `serve --without-stt` for typed answers; interviewer questions can still be spoken via browser TTS. `download-model` is an explicit external network download. Installing the Skill never opens the mic.

`serve` binds an authenticated HTTP interface only to `127.0.0.1`; the full private link is printed locally. Open it on the *same computer* as the server. The browser first requests PDF upload, then role, language, provider and explicit content-transfer consent. The **default** question voice uses `window.speechSynthesis`; an **optional** VoiceStudio localhost service can synthesize TTS, transcribe WebM via HTTP, or stream partial/final events through our authenticated private WS relay. See [VoiceStudio install and operation](voicestudio-backend.md). Speech selection never changes the separate interviewer model. Browser/OS voice availability, autoplay and quality vary. Never claim a cloud or remote agent automatically sees a local microphone.

## 2. Interview architecture

Candidate PDF bytes -> pypdf local text extraction (searchable PDF only; no OCR) -> candidate previews -> selects one of six role curricula -> explicitly consents to selected model processing. The model receives the extracted CV and confirmed text, not microphone audio. Interviewer challenges real resume claims first. A real monotonic local clock counts interaction time; pauses and model response waits are excluded while the server remains running. It is NOT a durable, crash-resumable certified one-hour product.

For ordinary HR/technical/math questions, the interviewer speaks using browser speech synthesis, and the candidate clicks Record, answers aloud, stops, corrects local Whisper text and explicitly submits. If a spoken question stays unanswered, the separate Timekeeper may ask a natural follow-up rather than merely narrate the elapsed time. After the candidate **deliberately** opens the microphone, a strictly local, approximate amplitude monitor can ask once after around 40 seconds of low activity; interviewer speech momentarily disables the mic track so it is not captured as an answer. See [Timekeeper](timekeeper-agent.md). If speech recognition fails, typed fallback stays available. Coding questions switch to the in-browser editor and Submit; this program does not run candidate code, so scoring is model-only and marked unverified. Strict mode hides reference answers until finish; `finish` requests model-written corrections/reference examples, not independently verified solutions. The browser keeps session data in the Python process's memory unless the candidate exports a report.

## 3. Supported interview engines

Separate **host CLIs** from **model APIs**:

| Choice in browser | Executable backend | Setup | Limitations |
|---|---|---|---|
| Codex | `codex exec` headless | install/login CLI | CLI version must accept restricted flags; live not certified |
| Claude Code | `claude --print` JSON | install/login CLI | no interactive permission prompts in headless mode |
| Gemini CLI | `gemini -p ... --output-format json` | install/login CLI | headless version differences; tool permissions are conservative |
| Qwen | Model Studio chat completions | `DASHSCOPE_API_KEY` | Singapore endpoint by default; keys/regions differ |
| DeepSeek | DeepSeek chat completions | `DEEPSEEK_API_KEY` | selected model/quota required |
| GLM | Z.ai chat completions | `ZAI_API_KEY` | model/quota required |
| Kimi | Moonshot chat completions | `MOONSHOT_API_KEY` | model/quota required |

API model names are defaults, not guarantees of account availability. To override, use only server environment variables `AI_INTERVIEW_QWEN_MODEL`, `AI_INTERVIEW_DEEPSEEK_MODEL`, `AI_INTERVIEW_GLM_MODEL`, `AI_INTERVIEW_KIMI_MODEL`. Real authentication, rates and model access depend on the chosen provider. No Hermes Agent is used. The selected *single* interviewer controls follow-ups; the host CLI is launched in a restricted subprocess rather than as a nested always-on agent.

The installed Skill itself remains compatible with interactive local Codex, Claude Code and Gemini CLI when those hosts can run shell scripts. Copy under a supported discovery location: Codex `~/.agents/skills/ai-interview`, Claude Code `~/.claude/skills/ai-interview`, Gemini CLI `~/.gemini/skills/ai-interview` or its `.agents` alias. The webpage is host-independent. Do not assume a ChatGPT cloud session can run on the candidate's computer.

## 4. Failure and security

Provider failure retains the current question and text for retry. Each answer submission carries question ID and idempotency ID; stale answer cannot become the next answer. If model or internet is not available, do not fabricate a successful answer. The program never directly runs candidate code, accepts arbitrary model URL from the browser, or uploads raw audio to a cloud speech API. The HTTP bridge and localhost token are private; do not expose the port publicly, post the link, or upload candidate PDFs/transcripts to GitHub.

Browser autoplay may refuse speech synthesis; click Replay or read the question. Avoid opening a remote port-forward/tunnel to provide mic input. Realistic speech latency, STT accuracy, interruption and all provider accounts require testing on the candidate's machine. At server restart the in-memory session is lost; export the report explicitly before exiting.


## 5. Career workflow and dated research extension (0.4.0)

The studio stays primarily an interview application. The private, canonical career records are controlled by [the career workflow](career-workflow.md) and the bundled `scripts/career.py`:

- `/profile` creates a private CV source and editable draft separately from uploading a PDF to the interview session. Uploading a PDF to the studio still does **not** automatically persist your full CV.
- `/scrape` stores candidate-selected job descriptions or published Greenhouse/Lever company postings. The setup page queries `/api/jobs`, shows a list of imported JDs, and includes only an explicitly selected JD in interviewer prompts after model-processing consent. It does **not** crawl LinkedIn or make job applications.
- Before beginning the interview, candidates can click **Refresh research for role**. The local server performs an explicit limited HTTPS retrieval from an allowlisted arXiv/HF source using role filters, without transmitting CV or candidate answers. It reports count/source/date, never inventing a successful result. No automatic refresh happens when the page loads.
- Opt-in checkboxes `Use newly retrieved research` and `Use my local memory` gate these contexts separately. Currentness is determined from source publication/retrieval dates; if the feed is stale or unavailable, no 'latest paper' claim is permitted. Research/memory enter only non-HR technical question prompts; candidate memory age is not proof of forgetting.
- At review, **Save private memory summary** explicitly writes a compact record of session role, phase coverage, answer count, elapsed seconds and *unverified-model* evidence label. The raw transcript/CV/recording is not part of that summary. The JSON review export remains separately optional and does include the answered exchanges when the candidate chooses it.

The review-memory API has no effect until the user explicitly clicks the button; it does not repeatedly save on page refresh. An external model still processes the selected context after the candidate consents; private local storage is distinct from online inference provider processing.

## 6. Optional third-party VoiceStudio STT/TTS (0.5.0)

Read the [self-contained installation and operation reference](voicestudio-backend.md). VoiceStudio is independently installed, not embedded, and runs under AGPL-3.0 with separate model/voice asset licenses. Start it locally, review model downloads and remote routing, then run AI-Interview with `--voicestudio` and optionally `--without-stt`. The studio header exposes engine selection, discovered voice profiles and an **explicit separate-service consent** checkbox. For normal spoken questions, the browser plays WAV generated by VoiceStudio's `/v1/audio/speech`, with browser TTS fallback. On candidate-initiated recording, the studio relays WebM over an authenticated local WebSocket to VoiceStudio's `/v1/audio/transcriptions/stream`; partial/utterance-final text is preview-only, and only final summary becomes an editable draft. If the relay is absent or fails, use the explicit local VoiceStudio batch endpoint `/v1/audio/transcriptions`, or typed fallback. Still require candidate **Submit** before involving the interviewer.

The optional third-party service might itself download weights or use a remote engine according to its installed configuration. This integration does not copy VoiceStudio source, autoset model configurations, or claim that all speech is offline. It also does not automatically install the external app or publish the local relay to a network.
