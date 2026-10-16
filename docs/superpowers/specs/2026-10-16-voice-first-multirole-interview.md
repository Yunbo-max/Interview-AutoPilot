# AI Interview 0.3 — voice-first multi-role interview studio

Approved user intent (2026-10-16): extend the existing GitHub `main`-only AI Interview skill into a local, voice-dominant interview simulator. Candidate uploads a PDF CV, selects a Quant/ML/AI role, then has an adversarial HR/CV interview, role-specific math/coding/architecture/research interview, and evidence-based review. Speak questions through browser TTS and receive candidate audio through the existing local Whisper backend. Coding needs an editor and explicit submission; mathematics can be answered by voice or typed text. Keep the installed Skill usable without the web app.

### Distinct integrations

- **CLI hosts:** Codex, Claude Code, and Gemini CLI, all launched as optional bounded *headless model backends* by a local service; separately, the portable `SKILL.md` guides interactive sessions in any capable host. A CLI must already be installed and authenticated. No embedded OAuth or undocumented CLI assumptions.
- **Model APIs:** Qwen, DeepSeek, GLM (Z.ai), and Kimi (Moonshot) through allowlisted HTTPS OpenAI-style chat-completions endpoints, explicit environment API keys and declared model names. API credentials stay server-side; model selection does not imply authentication or entitlement. No user-supplied arbitrary URLs.
- No Hermes dependency. No claim all seven have been exercised against real accounts. Provider calls are externally billed/subject to their own limits.

### Data flow & boundaries

Browser on localhost -> PDF bytes (not stored) -> pypdf text locally -> candidate previews/consents -> chosen model backend -> a single interviewer question -> browser SpeechSynthesis speaks question (candidate may replay/mute) -> candidate records via explicit microphone click -> local Whisper STT -> candidate corrects transcript and confirms -> backend grades and selects next targeted question. Coding phase displays a textarea editor and Submit button. Code is *not executed* in the local service; any correctness discussion is explicitly model-only until sandbox integration. Real-time acoustic scoring remains out of scope.

The model sees only the extracted CV text and confirmed candidate answer, never raw audio; resume text is untrusted evidence, not instructions. Browser transcript retained in memory, no public upload; cloud model submission requires explicit consent. Stop revokes this session; no auto-record, auto-restart or account credential upload.

### Curriculum & session

Six role curricula: Quant Researcher, Quant Developer, ML Engineer, AI Researcher, LLM/Agent Engineer, Generative AI Researcher. All begin with 15-minute HR/resume adversarial segment, then role-specific coverage (math for quant and research; coding for quant dev/ML/agent; transformers, RL, diffusion, systems where fitting). Phase budgets total 60 minutes; model generation wait times are excluded from active clock. Candidates can pause/resume/finish. A real monotonic server clock is used while the local server is running; a crash loses the in-memory session (no false durability guarantee).

Each backend receives a role and stage rubric, a short CV excerpt, current interview exchange and a single-question instruction. First questions are CV specific. Later questions challenge actual candidate claims, can accept a successful rebuttal, and balance subtopics. The backend outputs JSON with a single next question, kind (voice or code), and a brief prior-answer assessment. No premature reference answers. A provider failure must leave the last answer ungraded and permit retry, not silently move on.

### Security & usability

Loopback-only binding, bearer-token auth and origin/host checks for all state-changing HTTP, explicit PDF size/page limits, encrypted/scanned PDF error, allowlisted static routes, no arbitrary path reads or candidate code execution. No GitHub workflows. Return clear errors for missing Python packages, speech weights, model authentication, dead CLI, invalid model JSON and microphone permissions. Browser TTS voices vary by platform and may be unavailable; visible text and replay button are the accessible fallback. Mixed Chinese/English supported.

### Acceptance

Unit tests for curriculum budgets, phase clock/pause/resume, upload validation/consent, replay/duplicate answer idempotence, provider registry and mock transports, model parsing, HTTP auth, code submission/zero execution and generated-question speech fallback. The existing 63 Python checks and simulated browser checks must remain passing. No real-device, live API, or uninterrupted 60-minute certification unless run against that environment and reported.
