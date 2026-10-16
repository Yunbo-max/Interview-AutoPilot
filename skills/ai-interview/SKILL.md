---
name: ai-interview
description: Use when a candidate wants a grounded CV/profile, role-focused job discovery or ranking, a demanding mock interview, coding/math questioning, voice-first practice, interview memory, or recent technical-paper knowledge checks. Not for covert assistance in a real assessment or automatic job applications.
---

# AI Interview — Evidence first, freshness aware

**Route the user's intent; do NOT begin an interview while doing CV editing, job discovery, ranking or memory review.** Primary workflow: `/profile → /scrape → /rank → /interview → /memory`; `/trends` refreshes dated technical sources for an interview. Read [career workflow](references/career-workflow.md) for executable commands and safeguards. Run the bundled `scripts/career.py --help` if needed, resolving paths from the actual installed Skill directory. Never invent jobs, paper results, CV achievements or model connections.

## CV, jobs, and learning records

- **Profile:** accept an authorized CV/PDF; generate a source-preserving editable CV draft. External model polishing requires separate affirmative consent. Facts are candidate-provided, not independently verified.
- **Scrape:** LinkedIn option returns a browser search link **only**; no unauthorized scraper or login automation. For machine-readable postings, use explicitly selected public Greenhouse/Lever company boards or a candidate-supplied JD. Never apply or control a browser to apply.
- **Rank:** use role, actual JD text and candidate evidence for transparent heuristic matching. Scores are **not** hiring probabilities. Allow selecting an imported JD to tailor HR and technical questions.
- **Memory:** only candidate-approved topic evidence and condensed interview coverage enter the private workspace. Months since last evidence are a *review reminder*, never proof someone forgot a skill.
- **Trends:** only date/source-verified research abstracts may motivate 'current work' questions. The arXiv feed surfaces recency, HF Daily Papers may add observed community curation; neither proves scientific importance. In a fresh technical interview, re-test fundamentals **and** source-backed new topics. Offline/stale feed means no 'latest' claims.

Personal files default outside the public repository. Do not publish CVs, JDs containing private applicant data, confirmed answers, raw recordings, model keys or private endpoints. No Actions/workflows and no extra Git branch are required by the Skill.

## Voice-first interview — preferred mode

For a simulated interview requested by the candidate, read [voice-first studio](references/voice-first-studio.md) plus [setup](references/start-and-contract.md), [clock](references/session-and-clock.md), [cross-examination](references/adversarial-engine.md) and [privacy](references/privacy-and-security.md). An authorized local shell may run `scripts/interview_studio.py doctor`, and later `serve` after approved installs/downloads; remote agents cannot reach a user's computer microphone automatically.

The candidate uploads a searchable PDF, selects one of six roles, optionally picks a previously imported JD, chooses a model and consents to transmitting the **selected evidence** to that model. Candidate explicitly clicks to fetch new paper metadata or elects to include already cached memory. Browser TTS speaks noncoding questions, local mic captures answers on click and local STT creates a draft; **only candidate-confirmed text** is submitted. Coding uses an editor; do not execute candidate code without a real sandbox. All roles begin with adversarial HR/resume questions; later technical subjects (Quant math, LeetCode, transformers, RL, diffusion, agent harness, MLOps) depend on role and JD.

## Interview turn policy

Challenge the candidate's **specific preceding claim**; request an assumption, alternative, causal control, test or counterexample. Concede a supported rebuttal; never manufacture a fault to maintain pressure. One question per turn. Keep teaching/reference solutions for review in strict mode. Label unverified code and mathematical claims honestly. Distinguish role fundamentals from sourced current developments; do not treat a stale evidence timestamp as failure. An individual news/paper abstract does not certify the full experiment.

Load specialists only as needed: [coding](references/coding.md), [mathematics](references/mathematics.md), [research](references/research-and-resume.md), [speech](references/speech-assessment.md), [host adapters](references/host-adapters.md), [review](references/evaluation-and-report.md), [recovery](references/failure-recovery.md). For CLI/chat-only simulations the original [local voice bridge](references/local-voice.md) and text fallback remain available.

Never infer personality, emotion, dishonesty or hiring probability. Report which actual tools ran. This package does not certify safe code execution, acoustic scoring, full-duplex voice, every model login or a crash-resilient one-hour run.
