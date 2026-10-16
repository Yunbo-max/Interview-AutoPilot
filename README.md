# AI Interview

**Defend your reasoning. Not just your resume.**

An evidence-grounded, adversarial interview skill for agents. The interviewer follows your answer, challenges a justified weak point, accepts a successful rebuttal and separates testing from teaching.

[中文说明](README.zh-CN.md) · [Skill](skills/ai-interview/SKILL.md) · [Local voice](skills/ai-interview/references/local-voice.md) · [Voice verification](docs/VOICE-VERIFICATION.md)

## 0.2.0: microphone input is inside the skill

The package now includes Python scripts and a local recording page. Local Codex can start the page, display a question and receive your **confirmed** spoken answer through a shell tool result. You do not need to manually copy each answer into chat while Codex's tool loop is active.

Flow: **Codex asks → browser records with your permission → local Whisper transcribes → you correct and confirm → Codex's `wait` returns text → Codex follows up.**

This is turn-based microphone input, not a complete real-time voice product. No speech-style analyzer, spoken interviewer output, full-duplex interruption, safe coding sandbox, automatic one-hour clock or always-on Codex service is claimed. Local interface tests are not real microphone/model tests; see the verification report.

## Install

Install/copy the whole `skills/ai-interview` folder to `~/.agents/skills/ai-interview` (or a supported repository-local `.agents/skills/` directory). Back up an old copy outside skill discovery paths first; do not leave two same-named active skills. Restart Codex if needed. [Official skill documentation](https://developers.openai.com/codex/skills/).

The skill can be copied without the repository and still contains its runtime scripts. Put real resumes and session data in a separate private workspace, not this public source repository.

Example invocation:

```text
$ai-interview Start a challenging mock interview using my supplied resume.
Use the bundled local microphone input and match my language.
Check voice.py doctor first. Ask before downloading dependencies/model weights.
Start the local page, display one question at a time, and use wait to read my
confirmed answers. Keep reference answers until review. Do not upload recordings,
transcripts or session files to GitHub. Target 60 minutes with an external timer.
```

## Voice commands Codex can call

Resolve `SKILL_DIR` from the loaded skill; choose a new private `SESSION` directory.

```bash
python3 "$SKILL_DIR/scripts/voice.py" doctor
# Only after download approval:
python3 "$SKILL_DIR/scripts/voice.py" setup --allow-download --model base
python3 "$SKILL_DIR/scripts/voice.py" start --session-dir "$SESSION"
python3 "$SKILL_DIR/scripts/voice.py" ask --session-dir "$SESSION" --question-id q001 --text "Why this algorithm?"
python3 "$SKILL_DIR/scripts/voice.py" wait --session-dir "$SESSION" --question-id q001 --after-revision 0 --timeout 20
python3 "$SKILL_DIR/scripts/voice.py" stop --session-dir "$SESSION"
```

Use `python` on Windows when appropriate. Python 3.10+ is required; speech dependencies must support your Python/platform. `setup` creates a separate virtual environment and downloads weights; `start` loads cached weights only. Browser permission remains required and recording starts only on a click. No speech API key is needed. CPU int8 is the default, with float32 fallback. Each clip is limited to three minutes.

`wait` returns JSON: `waiting` means no confirmed answer; `ready.answer.confirmed_text` contains the confirmed answer. Question IDs and revisions prevent stale answers and duplicate grading. Only an active Codex process making tool calls will consume it. Saving a file cannot wake a stopped Codex conversation. Say "continue voice interview" if the host has stopped waiting.

## Other interview content

The concise entry loads fourteen references on demand: setup, clock contract, adversarial questioning, research/resume depth, coding, mathematics, multimodal input, speech-assessment boundaries, evaluation, recovery, security, tool contracts, host adapters and executable local voice. Structured fixtures include reference coding/math answers. Strict mode defers teaching; explicit answer requests mark an attempt assisted. Challenging style never licenses personal attacks or false objections.

## Verification and privacy

Run checks locally:

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m unittest discover -s tests -v
node tests/ui_state_test.cjs
node tests/voice_ui_test.cjs
```

The Python suite includes real loopback HTTP and CLI tests using a **fake decoder**, plus the original design checks. Simulated media tests do not verify a real microphone. The broader 32 behavior/runtime scenarios remain `not_run`; do not count authored examples as successful evaluations.

No GitHub Actions/workflows are used. The old automatic design-check workflow was removed; source changes and ordinary verification logs are the only GitHub artifacts for this change. Historical verification reports remain historical.

Do not publish candidate resumes, recorded media, transcripts, scores, bearer tokens or credentials. `connection.json` and the private browser link contain a local access token. Audio is not deliberately saved by the app; raw/corrected **text** is saved only on confirmation. Online Codex may send that text to its model provider. A local speech recognizer does not make the whole interview offline.

## License

MIT. [LICENSE](LICENSE). Original sample questions and fictional dialogues are teaching fixtures, not employer questions or an external benchmark.
