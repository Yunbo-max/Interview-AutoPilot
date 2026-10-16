# Changelog

## 0.7.0 — Per-question Timekeeper Agent, active-time pacing (2026-10-16)

- Added an independent, deterministic local Timekeeper with active per-question timing and phase-specific advisory reminders (HR 1/2/5 minutes, coding 5/10/15, math/research 2/4/6).
- The local server loop records reminder events and 55/59-minute session warnings even without browser polls; at 60 active minutes it stops accepting new answers without a new model call. Closed tabs cannot receive audio alerts and do not automatically pause.
- Added manual extra minute (twice per question) and explicit unassessed skip with question-ID guards, idempotency and reliable retry on model failure. No automatic skipping, silence/acoustic judgment or timing-based skill scoring.
- Pause intervals, interviewer-model execution, and bound Whisper/VoiceStudio transcription waits are excluded from candidate active time. Candidate speech/typing/thinking remain accounted for. Reports contain a timing ledger with skipped/unanswered distinctions; optional long-term Memory still saves condensed coverage rather than transcripts.
- Added a compact Timekeeper display and local browser reminders, coding visual-only policy and tests. No new model provider, always-on microphone, workflows or GitHub Actions.
- Real-device 60-minute endurance, browser/system sleeping, model latency and audio quality remain unverified.

## 0.6.0 — Mac one-click setup and local Agent launch (2026-10-16)

- Added `AI-Interview.command` and a self-contained `one-click-mac.sh` / `mac_bootstrap.py` flow usable by local Codex, Claude Code, Gemini CLI and Finder.
- Automatically prepares an isolated Python environment, installs the voice/studio dependencies, and downloads multilingual Whisper base with explicit installation approval. Modern Python can be bootstrapped with a pinned SHA256-verified uv binary if not installed.
- Added independent VoiceStudio ARM64 DMG installation on Apple Silicon with strict official GitHub release asset URL, version, file size and SHA256 checks. Never vendors AGPL software or accepts third-party model licenses silently.
- Symlinks the complete Skill for local agent discovery, backing up existing installations rather than deleting them.
- Launches a private localhost studio in a detached process so Agent tools return promptly; reuses live sessions and uses a token-authenticated shutdown endpoint instead of killing persisted PIDs.
- Added read-only doctor/dry-run, safe lightweight mode and local tests; Mac hardware, Gatekeeper and speech models remain to be tested on a physical MacBook.


## 0.5.0 — Optional external VoiceStudio STT/TTS integration (2026-10-16)

- Added loopback-only VoiceStudio capability discovery, optional HTTP TTS and batch STT, plus a same-host authenticated WebSocket relay for streaming partial/final transcriptions.
- Added in-browser audio source selection, discovered voice profiles, separate third-party service consent, speaker playback cancellation on recording, final-only editable transcripts and batch/typing fallback.
- Added `--voicestudio` and `--voicestudio-url` to the interview CLI, separately installable `websockets` dependency, portable Skill usage guide and source/license notices.
- No third-party VoiceStudio code, cloned voices or model weights bundled; no automatic installs, new branches or GitHub Actions. Tests use fake local voice servers and simulated browser media, not real audio hardware.

## 0.4.0 — Private career workflow and dated research evidence (2026-10-16)

- Added candidate-first `/profile`, `/scrape`, `/rank`, `/interview`, `/memory` workflow and optional `/trends` refresh. Claude Code gets repository-local command files; portable hosts continue using the canonical Skill.
- Added consent-gated source-preserving CV Markdown drafting and optional AI polish, without automatic applications.
- Added LinkedIn browse/search-link support (**no LinkedIn scraping**), read-only Greenhouse/Lever job-board adapters, JD import/deduplication and transparent role/skill fit ranking.
- Added arXiv and optional HF Daily Papers research metadata adapters with publication/retrieval date gates, bounded source adapters and no fabricated currentness when unavailable.
- Added optional dated research and candidate evidence to technical (not HR) interview prompts, and an optional previously imported JD for job-specific questions.
- Added explicitly saved minimal interview memory and topic-level review reminders that never conflate elapsed time with forgetting.
- Expanded contract/HTTP/CLI/UI tests. No GitHub Actions/workflows, auto-applications, or additional branches.

## 0.3.0 — Voice-first, six-role interview studio (2026-10-16)

- Added role routing, PDF onboarding, spoken interviewer questions, candidate-controlled microphone input, Coding editor and seven model adapters, with clear mock/live test distinctions.

## 0.2.1 — Local voice bridge safety review (2026-10-16)

- Hardened asynchronous recorder cleanup, stale-answer revision handling and local connection-error behavior.

## 0.2.0 — Executable local microphone bridge (2026-10-16)

- Bundled local voice scripts and browser microphone interface into Codex-callable Skill.

## 0.1.0 — Interview skill and contracts (2026-10-15)

- Initial voice/interview policy, coding/math references, contract schemas and offline design checks.
