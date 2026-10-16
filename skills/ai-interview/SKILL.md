---
name: ai-interview
description: Use when a candidate wants a grounded CV/profile, role-focused job discovery or ranking, a demanding mock interview, coding/math questioning, voice-first practice, interview memory, or recent technical-paper knowledge checks. Not for covert assistance in a real assessment or automatic job applications.
---

# AI Interview — Evidence first, freshness aware

**Route the user's intent; do NOT begin an interview while doing CV editing, job discovery, ranking or memory review.** Primary workflow: `/profile → /scrape → /rank → /interview → /memory`; `/trends` refreshes dated technical sources for an interview. Read [career workflow](references/career-workflow.md) for executable commands and safeguards. Run the bundled `scripts/career.py --help` if needed, resolving paths from the actual installed Skill directory. Never fabricate evidence or connections.

## CV, jobs, and learning records

- **Profile:** accept an authorized CV/PDF; generate a source-preserving editable CV draft. Model polishing needs separate consent; facts remain unverified.
- **Scrape:** LinkedIn option returns a browser search link **only**; no unauthorized scraper or login automation. Use public Greenhouse/Lever boards or supplied JDs; never apply automatically.
- **Rank:** use role, actual JD text and candidate evidence for transparent heuristic matching. Scores are not hiring probabilities; imported JDs inform interviews.
- **Memory:** only candidate-approved topic evidence and condensed interview coverage enter the private workspace. Stale evidence prompts review, not failure.
- **Trends:** only date/source-verified research abstracts may motivate 'current work' questions. Date arXiv/HF sources; never invent freshness or importance.

Keep personal material and keys private. No Actions, workflows, or extra branches.

## First-time local macOS launch

When the candidate explicitly requests one-click installation/launch on their
Mac, read [one-click Mac installer](references/one-click-mac.md). A local agent
may run `bash "$SKILL_DIR/scripts/one-click-mac.sh" --yes` only with the
candidate's explicit install/download approval. The launcher installs the
Skill links, private Python runtime and optionally a **separately licensed**
VoiceStudio app from SHA256-verified official DMG; it never grants mic access,
installs model-provider credentials or suppresses macOS Gatekeeper.

## Voice-first interview — preferred mode

For a simulated interview requested by the candidate, read [voice-first studio](references/voice-first-studio.md) plus [setup](references/start-and-contract.md), [clock](references/session-and-clock.md), [Timekeeper Agent](references/timekeeper-agent.md), [cross-examination](references/adversarial-engine.md) and [privacy](references/privacy-and-security.md). Local shells may run `doctor` then consented `serve`; remote agents cannot access a microphone.

Candidates choose role, PDF, JD and model; uploading to model and paper refresh require consent. Browser TTS and clicked microphone enable voice turns; **only confirmed text** is submitted. Coding uses an editor; never execute untrusted code. All roles begin with HR/resume questioning.

## Optional local VoiceStudio STT/TTS

For a candidate who explicitly wants **VoiceStudio**, first read [VoiceStudio backend — install & use](references/voicestudio-backend.md). This AGPL-3.0 app is **separately installed**, not bundled. `scripts/career.py interview --doctor --voicestudio` checks its fixed loopback protocol; `scripts/career.py interview --voicestudio --without-stt` can use its TTS, real-time streaming partial subtitles (with optional `websockets` relay), and batch STT when available. VoiceStudio requires separate consent and a microphone click. Only summary finals become **editable drafts**. Retain browser/Whisper fallbacks; never expose tokens or automatically install VoiceStudio.

## Natural interviewer check-ins

The [Timekeeper](references/timekeeper-agent.md) may speak a short, local question after unanswered delays, or approximately 40 seconds of low microphone activity during **candidate-initiated** recording. Temporarily mute the mic while prompting; never grade silence, start recording automatically or submit the candidate's answer.

## Interview turn policy

Use the local Timekeeper to track each question, gently remind at role-appropriate milestones, record explicit skips and avoid grading unsubmitted answers. It is a deterministic supervisor, **not** another LLM or speech-silence detector; do not invent elapsed times in chat-only mode.

Challenge the candidate's **specific preceding claim**; request an assumption, alternative, causal control, test or counterexample. Concede a supported rebuttal; never manufacture a fault to maintain pressure. One question per turn. Keep teaching/reference solutions for review in strict mode. Label unverified code and mathematical claims honestly. Distinguish role fundamentals from sourced current developments; do not treat a stale evidence timestamp as failure. An individual news/paper abstract does not certify the full experiment.

Load specialists only as needed: [coding](references/coding.md), [mathematics](references/mathematics.md), [research](references/research-and-resume.md), [speech](references/speech-assessment.md), [host adapters](references/host-adapters.md), [review](references/evaluation-and-report.md), [recovery](references/failure-recovery.md). For CLI/chat-only simulations the original [local voice bridge](references/local-voice.md) and text fallback remain available.

Never infer personality, emotion, dishonesty or hiring probability. Report which actual tools ran. This package does not certify safe code execution, acoustic scoring, full-duplex voice, every model login or a crash-resilient one-hour run.
