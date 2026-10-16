# AI Interview · 0.4.0

**Build a defensible CV. Find and rank relevant jobs. Practice demanding voice-first technical interviews. Remember what you demonstrated and what has changed in the field.**

This project focuses on the interview and research-learning lifecycle, **with no automatic applications**. The local model/voice interview and six-role curricula from 0.3.0 remain intact. The new candidate flow is:

`/profile → /scrape → /rank → /interview → /memory` — with optional `/trends` research freshness checks before and during technical interview preparation.

[中文说明](README.zh-CN.md) · [Skill](skills/ai-interview/SKILL.md) · [Career workflow](skills/ai-interview/references/career-workflow.md) · [Evidence/verification](docs/CAREER-VERIFICATION.md)

## Why this differs

**Time since a candidate last demonstrated understanding is not a measurement of memory loss.** The system tracks the age of supporting evidence and optionally challenges recent, sourced technical changes. A strong engineer should be tested on fundamentals *and* developments in their domain. It uses retrieved publication dates/URLs rather than asking an LLM to invent "the latest" papers. A recent arXiv upload is not necessarily a major advance; HF Daily Papers (optional) adds a community-curation signal, not scientific verification.

## Six roles and the five commands

- **`/profile`**: extract a searchable PDF or text CV locally, prepare a candidate-editable Markdown CV draft, and optionally polish it with a chosen model **after explicit external-transfer approval**. The CV is not automatically fact checked or converted to a publication-ready PDF.
- **`/scrape`**: generate a user-facing LinkedIn jobs search URL, import candidate-selected job descriptions, or retrieve public jobs from the documented **Greenhouse** and **Lever** read-only employer boards. **LinkedIn is not scraped**: its rules prohibit unauthorized crawlers/bots, and the software does not log in, bypass restrictions, control the mouse or submit an application.
- **`/rank`**: an explainable role/JD-to-CV relevance heuristic showing matches and unsupported requirements. **Not a hiring probability**. Ranked jobs can be selected in the interview studio.
- **`/interview`**: voice-first local app for Quant Researcher, Quant Developer, ML Engineer, AI Researcher, LLM/Agent Engineer and Generative AI Researcher. Every interview begins with HR/CV claim defense; technical content varies by role. Noncoding questions use browser speech synthesis and candidate microphone answers. Coding prompts use an editor; candidate code is **not executed**.
- **`/memory`**: candidate-triggered private summaries of interview phase coverage and topic evidence, plus transparent study review reminders; raw audio/CV/answers are **not persisted by default**.
- **`/trends` (supporting command)**: retrieve metadata and abstracts from the official **arXiv** Atom API or optional experimental Hugging Face Daily Papers. All entries retain source, publication time and retrieval time; cached material older than 7 days is excluded from claims about current research.

## Quick start on your computer

```bash
git clone https://github.com/Yunbo-max/AI-Interview.git
cd AI-Interview
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -r skills/ai-interview/scripts/requirements-studio.txt

# Start with a private, grounded CV Markdown draft:
python skills/ai-interview/scripts/career.py profile --resume /private/path/to/cv.pdf --role ai_researcher

# LinkedIn search LINK — opens in your browser; not automated scraping:
python skills/ai-interview/scripts/career.py scrape --linkedin "AI Research Scientist" --location London

# Public company ATS listing API (replace with a real board slug):
python skills/ai-interview/scripts/career.py scrape --greenhouse company-slug
# Or: python skills/ai-interview/scripts/career.py scrape --lever company-slug

python skills/ai-interview/scripts/career.py rank --role ai_researcher
python skills/ai-interview/scripts/career.py trends --role ai_researcher --source arxiv
python skills/ai-interview/scripts/career.py memory --show

# Interview studio; typed answers work without local STT:
python skills/ai-interview/scripts/career.py interview --without-stt
```

For microphone answers, install `skills/ai-interview/scripts/requirements-voice.txt`, explicitly download Whisper weights using `interview_studio.py download-model --allow-download --model base`, and start `python skills/ai-interview/scripts/career.py interview`. Real mic permission must be given in the browser. Open only the full private localhost link printed by the program. The research-refresh button in the setup page is opt-in and makes a public-source request based on selected **role**, not CV contents.

Run from a local authenticated **Codex**, **Claude Code** or **Gemini CLI** for their native skill-based workflows. Claude Code additionally exposes `.claude/commands/{profile,scrape,rank,interview,memory,trends}.md` when run in this repository. Other hosts invoke `$ai-interview` / their supported Skill mechanism with these intents. In-browser inference options include **Codex, Claude Code and Gemini CLI** (local installed/login) or provider APIs **Qwen, DeepSeek, GLM and Kimi** (separately configured API keys). A skill install does not log in to a provider or grant microphone access. No Hermes Agent dependency.

## Provenance, privacy, and release scope

Personal files default to `~/.local/share/ai-interview/` (override with `AI_INTERVIEW_WORKSPACE` or `--workspace`). JSON writes are private on POSIX and atomic. The studio only uses cached technical papers and topic evidence if the candidate opts in; refreshing research is an explicit network action. Selecting a saved JD is optional. Selected CV/JD/abstracts/confirmed interview text are sent to the chosen inference provider **only after model-processing consent**. Real world inputs are untrusted data, not executable instructions.

This release is **not** an auto-application robot and does not use a mouse/browser bot on LinkedIn. It lacks a certified code execution sandbox, acoustic speech-style grading, fully duplex audio, durable one-hour crash recovery, and real-account certification for all seven model routes. Source papers are examined at abstract/metadata level only. Offline mocked feed/adapter tests establish local behavior, not external source uptime or scientific novelty.

### Verification (local only, no GitHub Actions)

```bash
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
node tests/ui_state_test.cjs
node tests/voice_ui_test.cjs
node tests/voice_failure_ui_test.cjs
node tests/studio_ui_test.cjs
```

See the exact observed results and remaining gaps in [CAREER-VERIFICATION.md](docs/CAREER-VERIFICATION.md). The source repository has **only `main`**, with no workflow files. MIT licensed.
