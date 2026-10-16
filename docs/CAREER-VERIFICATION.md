# Candidate workflow and freshness verification — 0.4.0

Date: 2026-10-16. Scope: private candidate CV/job workflow, optional research refresh, evidence-aware interview prompts and topic memory. It is not live platform/provider or one-hour endurance certification.

## Executed local checks

- Re-ran the original 0.3.0 package: 82 Python tests passed, existing studio UI simulation passed before changes.
- Implemented and reran **new unit/HTTP/CLI tests** for the workflow: private source-preserving CV drafting, explicit model-transfer consent, LinkedIn **link-only** behavior, Greenhouse/Lever JSON normalization, imported JD deduplication and heuristic rank, rejected local/private job URLs, source-dated arXiv/HF parsing, 7-day retrieval expiry, memory evidence age, transcript-minimizing session import, optional paper/JD selection in interview prompts, authenticated opt-in research refresh and explicit review-memory saving.
- Verified TDD red/green cases for missing workflow module, missing optional interview context, nonexistent research-refresh and memory HTTP routes, required frontend opt-in flags, JD selection, CLI packaging, malformed research feed failures and model-consent side effects.
- Final `python -m unittest discover -s tests -v` — **117/117 tests passed**, zero failures; 8.913 seconds in the recorded Linux/Python 3.13.5 run ([Python log](verification/career-0.4-tests.txt)). 82 were carried over from 0.3.0, with 35 new workflow/integration/CLI/package cases.
- Four simulated Node suites — **8 recorder-state assertions, 15 bridge/UI assertions, seven asynchronous failure scenarios, and a studio UI scenario** — all passed ([UI log](verification/career-0.4-ui-tests.txt)). These do **not** use a real microphone or browser speaker.
- `python -m compileall` and both JS syntax checks passed. A copied Skill in a separate directory containing spaces ran `career.py scrape --linkedin` without network access or incidental workspace writes; a `career.py interview --doctor` call confirmed pypdf present, but faster-whisper and CLI hosts were not installed in the test environment.
- New `career.py` workflow is self-contained inside the installed Skill; root `.claude/commands` provide repository-scoped commands. Source tree contains no GitHub Actions/workflows; only `main` is an intended remote branch.

## What works at the code/fixture level

- `profile --resume`: reads an authorized PDF (via pypdf) or text CV; builds a local Markdown source-preserving draft; optional model-polished text is consent gated and marked unverified.
- `scrape --linkedin`: constructs a browser-visible LinkedIn job-search URL; **does not fetch or crawl LinkedIn**. `scrape --greenhouse` and `--lever` implement fixed-host published-board GETs and normalized cached jobs. `--import-description` accepts an explicitly provided candidate JD.
- `rank`: computes explainable relative JD-to-CV heuristic scores without presenting scores as hiring probabilities. Mere import time does not make an old posting "new".
- `trends`: arXiv Atom and optional HF Daily Papers parsers capture source, publication and retrieval dates, reject malformed/unsupported sources, and exclude stale cached evidence from model recency claims. Recency is not scientific significance.
- `interview`: browser UI includes imported JD choice, explicit public-paper refresh, per-context opt-ins, voice-led question/confirmed answer and coding editor from prior release. First HR round does not use new paper/memory prompts.
- `memory`: summary is persisted only when the candidate chooses to save it; topic review reminders report age of evidence, not forgetting or lower capability; no full transcript in the saved summary.

## Limitations and claims deliberately not made

**Not tested live:** LinkedIn browsing in a real account, a real Greenhouse or Lever board request, arXiv/HF uptime and response compatibility, all seven model-provider credentials, real microphone/STT/TTS hardware, Cloud/CLI host behaviors, a secure candidate-code sandbox and one-hour interactive endurance. External source XML/JSON/HTTP in tests uses fixtures/mocks.

No request is made to LinkedIn by the scraper: LinkedIn's terms prohibit unauthorized automated scraping. The limited private workspace is user-controlled and local; online model inference still transfers candidate-confirmed content to the selected provider after consent. CV-prompted model outputs have not been factually authenticated; an actual hiring probability is never estimated. A review-due flag marks lack of **recent evidence**, not a diagnosis of skill loss.

Historical verification documents refer to 0.1–0.3 capabilities and should not be read as evidence of 0.4 live integrations.
