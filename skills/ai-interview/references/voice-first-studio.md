# Voice-first studio: role-specific PDF interview

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

`serve` binds an authenticated HTTP interface only to `127.0.0.1`; the full private link is printed locally. Open it on the *same computer* as the server. The browser first requests PDF upload, then role, language, provider and explicit content-transfer consent. The actual voice is emitted by `window.speechSynthesis`: user can replay/mute it. Browser/OS voice availability, autoplay and quality vary. Never claim a cloud or remote agent automatically sees a local microphone.

## 2. Interview architecture

Candidate PDF bytes -> pypdf local text extraction (searchable PDF only; no OCR) -> candidate previews -> selects one of six role curricula -> explicitly consents to selected model processing. The model receives the extracted CV and confirmed text, not microphone audio. Interviewer challenges real resume claims first. A real monotonic local clock counts interaction time; pauses and model response waits are excluded while the server remains running. It is NOT a durable, crash-resumable certified one-hour product.

For ordinary HR/technical/math questions, the interviewer speaks using browser speech synthesis, and the candidate clicks Record, answers aloud, stops, corrects local Whisper text and explicitly submits. If speech recognition fails, typed fallback stays available. Coding questions switch to the in-browser editor and Submit; this program does not run candidate code, so scoring is model-only and marked unverified. Strict mode hides reference answers until finish; `finish` requests model-written corrections/reference examples, not independently verified solutions. The browser keeps session data in the Python process's memory unless the candidate exports a report.

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
