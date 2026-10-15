# AI Interview

**Defend your reasoning. Not just your resume.**

An evidence-grounded, adversarial mock-interview skill for coding agents. The interviewer follows your answer, challenges its weakest justified point, accepts a successful rebuttal, and keeps teaching separate from testing.

[中文说明](README.zh-CN.md) · [Skill](skills/ai-interview/SKILL.md) · [Design](docs/DESIGN.md) · [Acceptance](docs/ACCEPTANCE.md) · [Sources](docs/SOURCES.md)

## Release scope

Version **0.1.0** is a **skills-only design release**: a usable instruction package, modular references, data contracts, original sample questions, and offline design checks. It is **not** a completed browser app, microphone service, speech analyzer, code sandbox or one-hour runtime. Those integration contracts are specified; their implementations and live tests are not supplied. Installing a skill does not grant device access.

The package can guide a compatible agent through a text mock interview using the host's real tools. Host behavior has not been independently certified. Full-duplex speech, acoustic measurements, exact timing, crash recovery and safe candidate-code execution each require a verified runtime capability.

## What the skill defines

- **Real cross-examination:** one question per turn; challenge the candidate's actual claim, not a canned list. Concede when the candidate is right.
- **Resume and research depth:** personal contribution, mechanism, assumptions, baselines, causal controls, metrics, negative results and limits.
- **Coding and mathematics:** frozen problem/rubric, reference answers, alternatives, hints, scoped verification and explicit answer release.
- **Speech-aware review:** separate transcript mistakes, acoustic observations, answer structure and technical correctness. No audio means no prosody judgments.
- **A 60-minute session contract:** phase budgets, pause/outage accounting, state revisions, interruption and recovery rules. In plain chat, the clock is user-managed.
- **Privacy by default:** no additional recording, cloud transfer, persistent storage or public export without scoped consent.

These are behavioral instructions and interface requirements, not evidence that every host implements them.

## Install in Codex

Clone the repository, then copy the **whole** skill folder into a supported discovery location. Example for repository-local use:

```bash
git clone https://github.com/Yunbo-max/AI-Interview.git
cd AI-Interview
mkdir -p .agents/skills
target=.agents/skills/ai-interview
if [ -e "$target" ] || [ -L "$target" ]; then
  printf '%s\n' 'Skill already exists; inspect it before replacing it.'
else
  cp -R skills/ai-interview "$target"
fi
```

Open Codex in this repository and invoke:

```text
$ai-interview Start a challenging mock interview using my supplied resume.
Target 60 minutes; match my language. Include research, coding and mathematics.
Verify actual tools first. Keep reference solutions until review or my explicit request.
```

Codex also supports user-local discovery under `~/.agents/skills/`. Restart or refresh discovery if the skill does not appear. See [official skill documentation](https://developers.openai.com/codex/skills/) for current behavior. The supplied plugin manifests are packaging metadata, not proof of installation or publication to a directory.

For another Agent Skills-compatible host, install `skills/ai-interview/` into that host's documented skill directory. Do not rename only `SKILL.md` and lose its references. A generic chat can read the entry file and referenced material, but it still has only its actual host capabilities.

## Controls

Say start, pause, resume, stop, repeat, correct transcript, challenge, hint, show answer, skip, change mode, review or retry. Chinese equivalents work. These are conversational controls, not commands installed on your operating system.

Strict mode defers teaching. Coach mode explains after attempts. Retry uses variants. An explicit request for the answer ends that attempt as assisted. Pressure changes directness, never the standard of correctness.

## Package map

`skills/ai-interview/SKILL.md` is the concise entry. Thirteen references define the operational behavior. `assets/contracts.schema.json` describes eight record variants, with nine JSON examples. The fictional interaction illustrates concessions and transcript repair. `docs/ACCEPTANCE.md` separates static checks, model behavior trials and live integration gates.

## Offline verification

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m unittest discover -s tests -v
```

The suite checks packaging, relative links, schemas, fixtures, default privacy/time budgets, invalid-record rejection and the repository-owned coding reference. It is not a candidate-code execution service. Model pressure scenarios in `tests/scenarios.json` have `execution_status: not_run` until actual isolated trials are recorded. Do not count authored examples as successful evaluations.

## Data and security

Do not put real resumes, recordings, transcripts, scores or credentials in this public repo. A shell or `subprocess` timeout is not an isolation boundary. Without a verified sandbox, the interviewer must label code review static-only. Audio/video cannot establish personality, emotion, honesty or hiring probability.

## License

MIT. See [LICENSE](LICENSE). Sample questions and dialogues are original teaching fixtures, not employer questions, external research benchmarks or real candidate records.
