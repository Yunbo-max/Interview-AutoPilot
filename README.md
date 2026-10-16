# AI Interview · Voice-first, evidence-first

**Upload a PDF resume. Choose Quant, ML, AI Research or Agent Engineering. Defend your reasoning in a voice-led interview — coding in the editor.**

Version **0.3.0** brings a runnable local interview studio alongside the established portable Skill. The studio is local HTTP on `127.0.0.1`: browser SpeechSynthesis speaks all non-coding questions; browser microphone records only after user action, then a locally cached faster-whisper model transcribes speech; the candidate corrects text and explicitly submits. Coding questions use a text editor and never run untrusted code. **No raw audio/video is deliberately stored or submitted to model APIs.** The extracted CV and confirmed answers are transmitted to the selected model only after explicit consent; all interactions use a single named interviewer backend.

[简体中文](README.zh-CN.md) · [Skill](skills/ai-interview/SKILL.md) · [Studio guide](skills/ai-interview/references/voice-first-studio.md) · [Design](docs/superpowers/specs/2026-10-16-voice-first-multirole-interview.md)

## Quick start

```bash
git clone https://github.com/Yunbo-max/AI-Interview.git
cd AI-Interview
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r skills/ai-interview/scripts/requirements-studio.txt
python skills/ai-interview/scripts/interview_studio.py doctor
# Without a speech model, typed answers and spoken interviewer output remain available:
python skills/ai-interview/scripts/interview_studio.py serve --without-stt
```

To activate **local** Whisper recognition (explicit network downloads, no speech API key):

```bash
python -m pip install -r skills/ai-interview/scripts/requirements-voice.txt
python skills/ai-interview/scripts/interview_studio.py download-model --allow-download --model base
python skills/ai-interview/scripts/interview_studio.py serve --model base
```

Open the **complete private localhost link** printed in the terminal. PDF extract is previewed first; choose a role, interviewer engine and language; consent before clicking Begin. Use Record → Stop → Correct transcript → Submit, or type. Click Replay to repeat spoken questions. Coding appears as a text editor. Review is downloadable only on explicit click.

## Six role curricula

| Role | One-hour target phases |
|---|---|
| Quant Research | HR 15, Math/Probability 20, Python coding 15, Quant research 10 |
| Quant Developer | HR 15, LeetCode 20, Systems 15, Quant fundamentals 10 |
| ML Engineer | HR 15, Coding 15, ML 20, MLOps 10 |
| AI Researcher | HR 15, Transformer 15, RL/generation 15, Research design 15 |
| LLM/Agent Engineer | HR 15, Coding 15, Transformer 10, Agent harness/MCP 20 |
| Generative AI Researcher | HR 15, Mathematical foundations 10, Diffusion/flow matching 25, Research 10 |

All candidates begin with **HR and adversarial resume questioning**, not a generic keyword quiz. Research roles still need mathematics; Quant is not the only role with math.

## Seven backend choices, two integration families

**CLI hosts (installed and authenticated independently):** Codex CLI (`codex exec`), Claude Code (`claude -p`), and Gemini CLI (`gemini -p`). These are bounded headless inference calls from the local studio; the Skill also works when invoked in their native interactive environments. No extra Hermes agent. CLI versions/permissions and subscriptions vary.

**API model providers (keys in your local environment):** Qwen / Alibaba (`DASHSCOPE_API_KEY`, Singapore endpoint), DeepSeek (`DEEPSEEK_API_KEY`), GLM / Z.ai (`ZAI_API_KEY`), Kimi / Moonshot (`MOONSHOT_API_KEY`). The server uses provider-allowlisted HTTPS endpoints, no arbitrary URL proxy. Configure the relevant key before starting the studio; different providers have different access, quotas and pricing. Default model IDs can be replaced with `AI_INTERVIEW_<PROVIDER>_MODEL` environment variables. Secrets never belong in the browser, a resume or git.

See [multi-host guide](skills/ai-interview/references/voice-first-studio.md) for copy paths and details: Codex `~/.agents/skills/ai-interview`, Claude Code `~/.claude/skills/ai-interview`, Gemini CLI `~/.gemini/skills/ai-interview` or `.agents` alias. Always install the **whole** Skill folder, not just SKILL.md.

## Scope and honest limitations

- Browser TTS depends on installed voices and permitted audio playback; visible text/replay is fallback.
- Local Whisper depends on separately installed dependencies and cached weights. No guarantee of realtime accuracy or device compatibility without live testing.
- Code is *not* executed; mathematical claims/reference solutions and code feedback are model-generated, not proof certificates or sandbox-test results.
- Server clock measures active time (excluding pauses and model waits) only while the in-memory service is alive. No durable post-crash continuity or certified 60-minute endurance.
- The interface is not full-duplex; no autonomous interruption, intonation analysis, webcam or Hermes multi-agent runtime.
- Provider adapters are tested with mocks but not validated on all seven live accounts.

Automated tests (no GitHub Actions or workflow files):

```bash
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
node tests/ui_state_test.cjs
node tests/voice_ui_test.cjs
node tests/voice_failure_ui_test.cjs
node tests/studio_ui_test.cjs
```

Full detail: [acceptance criteria](docs/ACCEPTANCE.md), [legacy design](docs/DESIGN.md), [studio specification](docs/superpowers/specs/2026-10-16-voice-first-multirole-interview.md). No real CVs, audio, transcripts, model keys or user data are committed to the public repository. MIT license.
