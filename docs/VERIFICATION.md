# Verification report — AI Interview 0.1.0

Date: 2026-10-15. Scope: the skills-only design package, not an implemented voice application.

## Executed checks

The complete published design was tested in GitHub Actions at commit
`9740aa70c4e426090d94bd6b4de2be87141619db`.

- [Workflow run 38809514022](https://github.com/Yunbo-max/AI-Interview/actions/runs/38809514022): **success**.
- Job `116678881563`, `verify`: **14 tests passed**, zero failures, 0.150 seconds reported by unittest.
- Runner: Ubuntu 24.04.5; CPython 3.12.15; jsonschema 4.26.0; PyYAML 6.0.3.
- The packaging step produced the full 41-file project archive and a test log. This report is an additional documentation file.

The job logs were retrieved and inspected, and the downloaded artifact hash was checked. Its outer artifact ZIP SHA-256 is
`b285b744da3bc3c20b1eee2381051f92a7414e910847c910db61d43f17cccd34`.
This identifies that particular CI artifact, not every later archive or commit.

The workflow completed successfully but emitted Node.js action deprecation warnings. A successful test run is not a claim that all dependencies are warning-free.

## What the 14 tests cover

The checks cover required files, skill frontmatter/size, local Markdown links, self-contained skill references, aligned versions, schema validity, all nine JSON examples, default privacy flags and 3,600-second phase budgets, invalid-record rejection, no-audio metric restrictions, and maintenance-versus-interview activation boundaries.

The repository-owned coding reference was checked against an independent brute-force oracle on **3,280 strings** over `abc` with lengths 0 through 7, plus **8 listed boundary/Unicode examples**. A deliberately flawed left-boundary implementation was detected on `abba`. This executes reviewed reference code only; it is not a candidate-code sandbox.

The sample-variance reference received **9 exact finite-distribution sanity checks**: three distributions at sample sizes 2, 3 and 4. These examples support a sanity check, not a general proof certificate. The general reference derivation is supplied separately in the question fixture.

Before authoring the package, an empty-package structural baseline ran 12 tests and failed 10 for missing design files. This is a structural baseline, not a fresh-model/no-skill behavioral baseline. The final suite contains two additional checks.

## Explicitly not executed

The **32 scenarios** in `tests/scenarios.json` are specifications with `execution_status: not_run`: 18 agent-behavior scenarios, 12 runtime scenarios and 2 integration scenarios.

No independent fresh-model trials, actual Codex installation smoke test, live microphone capture, acoustic extraction, full-duplex interruption test, candidate-code isolation certification or interactive one-hour endurance test is claimed. Fictional exchanges and format examples are not observed model runs.

## Reproduce

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m unittest discover -s tests -v
```

Use the Actions run for the exact commit being evaluated. A later documentation commit does not retroactively change the cited run. Behavioral and runtime certification require the separate gates in [ACCEPTANCE.md](ACCEPTANCE.md).
