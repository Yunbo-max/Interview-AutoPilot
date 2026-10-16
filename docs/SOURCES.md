# Primary-source integration notes

Checked 2026-10-15. External APIs and packaging rules can change; runtime adapters must check current documentation and record actual versions. These sources ground compatibility statements, not the effectiveness of the interview design.

| Source | Narrow fact used |
|---|---|
| [Agent Skills specification](https://agentskills.io/specification) | A skill is a directory with SKILL.md metadata/instructions and optional references/assets; format constraints and progressive disclosure. |
| [OpenAI skill documentation](https://developers.openai.com/codex/skills/) | Codex discovery locations, explicit invocation and optional agents/openai.yaml metadata. |
| [OpenAI plugin packaging](https://developers.openai.com/plugins/build/plugins) | Portable root plugin.json and supported .codex-plugin/plugin.json compatibility packaging; packaging does not deploy a service. |
| [OpenAI App Server](https://developers.openai.com/codex/app-server/) | Application integration, initialization, threads, turns, approvals and streaming; recheck protocol version. |
| [OpenAI realtime transcription](https://developers.openai.com/api/docs/guides/realtime-transcription) | Model/transport-specific transcription events and output capabilities; do not assume timestamps or confidence exist. |
| [OpenAI realtime conversations](https://developers.openai.com/api/docs/guides/realtime-conversations) | Provider session lifecycle; the checked documentation states a 60-minute maximum, separate from the product's active clock. |
| [MDN getUserMedia](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia) | Browser audio/video permission and secure-context requirements. |
| [MDN getDisplayMedia](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getDisplayMedia) | Explicit display capture selection and permission constraints. |
| [librosa pYIN](https://librosa.org/doc/latest/generated/librosa.pyin.html) | A method for voiced pitch estimation, not psychological inference. |
| [SymPy assumptions](https://docs.sympy.org/latest/guides/assumptions.html) | Symbolic results depend on assumptions; unknown is distinct from false. |

No existing third-party interview skill was copied into this package. Cross-examination policy, examples, reference tasks and data contracts are original design content. No current model ID, price, subscription entitlement, hiring statistic or employer-specific interview claim is hard-coded.

## Local voice integration (checked 2026-10-16)

- [Codex skills](https://developers.openai.com/codex/skills/): script/resource packaging and local skill discovery.
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper): local CPU model invocation; runtime requirement remains pinned to 1.2.1.
- [getUserMedia](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia): browser permission and secure-context requirements.

## Voice-first multi-role studio (2026-10-16)

- [Codex CLI](https://developers.openai.com/codex/cli/) — headless Codex can be invoked locally with an existing signed-in CLI.
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code/cli-usage) — `claude -p` and structured `--output-format json` are documented; version compatibility requires a live check.
- [Gemini CLI](https://geminicli.com/docs/cli/headless/) — `gemini -p`, JSON mode, and stdin; users require an installed, authenticated CLI.
- [Qwen Model Studio](https://help.aliyun.com/en/model-studio/base-url) — HTTPS OpenAI-compatible endpoint and regional API keys.
- [DeepSeek API](https://api-docs.deepseek.com/zh-cn/) — current chat-completions API and model IDs.
- [Z.ai](https://docs.z.ai/guides/capabilities/mcp-call) — GLM model APIs and separate key/availability.
- [Moonshot AI](https://www.kimi.ai/help/kimi-api/api-overview) — model API and associated account access.
- [MDN Web Speech API](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesis) — browser-dependent question TTS, not guaranteed reliable audio output on every device.
- [pypdf documentation](https://pypdf.readthedocs.io/) — extract text from searchable PDFs; encrypted or scanned inputs require separate handling.

## Career workflow and research recency (2026-10-16)

| Source | Scope of verification / implication |
|---|---|
| [LinkedIn User Agreement](https://www.linkedin.com/legal/user-agreement) and [LinkedIn Help: prohibited software](https://www.linkedin.com/help/linkedin/answer/a1341387/) | LinkedIn disallows unauthorized automated scraping, copying and bot activity. `/scrape --linkedin` is a navigable browser search URL, *not* a bot or a live search API. |
| [Greenhouse Job Board API](https://docs.greenhouse.io/job-board) | Public unauthenticated GET for published company board jobs, including an optional `content=true` argument. The write/apply endpoint is deliberately not used. |
| [Lever Postings API](https://github.com/lever/postings-api) | Company-site public posting GET with JSON mode. No applicant submission endpoint is called. |
| [arXiv API user manual](https://info.arxiv.org/help/api/user-manual.html) | Atom feed query, category/keyword filter and submitted-date sort. Newness alone does not imply scientific importance or reproducibility. |
| [Hugging Face Daily Papers](https://huggingface.co/papers) | Curated research discovery. The optional `/api/daily_papers` endpoint is a public observed interface, not a formally versioned integration contract, and may change; tests use fixtures. |

Publication timestamp and retrieval timestamp are deliberately separate. Prior-review age is merely a signal to *retest*, not a psychological or ability claim. The local career workflow does not send private applicant data to paper sources; the candidate may independently consent to sending selected paper metadata/JD/CV to their model provider.
