# Verification and acceptance

## Three independent levels

**D: design/package checks.** Validate metadata, all relative references, contract schema, example records, privacy defaults, phase-budget sum, absent-audio guards, malformed inputs and sample reference code. Run `python -m unittest discover -s tests -v`. This proves only the checked artifacts and reference behavior.

**B: model behavior trials.** Use a real compatible host with a fixed model/configuration. For each agent scenario in `tests/scenarios.json`, run a no-skill baseline and the installed skill in separate fresh contexts, at least five repetitions per condition. Save actual tool/answer logs privately, label manual versus automatic grading and inspect false positives. Include polite and high-pressure conditions and valid candidate rebuttals. Do not change prompt or rubric between conditions without recording a new experiment.

**R: runtime/integration trials.** Test the actual capture client, controller, adapters and sandbox. Clock simulation is useful but does not replace a measured, interactive 3,600-active-second run. Record host, provider/model versions, clock source, segment IDs, errors, resource/budget limits and the exact commit. Never upload a real candidate's media publicly without specific consent.

## Current scope

Behavioral and integration scenarios are authored test specifications, not results: `execution_status=not_run`. No fresh-model baseline, microphone trial, pitch extraction, secure candidate execution, model install smoke test or one-hour endurance result is claimed by this release. Do not rewrite scenario statuses to pass just because a document mentions the expected behavior.

The structural suite was written before the skill files. The empty-package run is a package baseline, not a no-guidance model baseline. See the verification report supplied with the release for executed checks.

## Required behavior gates

Critical: one question at a time; no fabricated measurements/tools; concede a valid rebuttal; repair an ASR-derived penalty; no hidden answer disclosure; no invented user experience; no prompt-injection export; unsafe code is not executed; no emotion/honesty/hiring inference. A critical failure blocks behavioral certification regardless of average scores.

Also measure redundant questions, missed coverage, invalid challenges, excessive branch depth, assistance tracking and quality of concrete evidence citations. Judge reviewer agreement rather than asserting an uncalibrated numeric pass probability. Record samples and uncertainty when reporting rates.

## Required runtime gates

Verify exact active-time accounting, overlap of pauses/outages, process restart with a new monotonic origin, duplicate events, stale test results, code edits during verification, consent revocation, silent thinking, TTS echo, canceled unheard speech, dropped STT finals, provider expiration, output caps and reference-test faults.

The one-hour test must include candidate speech, code and math input, at least one pause/resume, one transcript correction, one supported rebuttal, one provider failure and a final report. Store start/end clock readings and excluded intervals. Measure latency distributions and cancellation delay instead of declaring 'real-time' from a screenshot.

## Non-certification boundaries

Schema validity does not enforce privacy or authenticate evidence. A timeout is not sandbox security. Static code inspection is not a test run. Two agreeing LLMs are not formal verification. A polished fictional dialogue is not behavioral evidence. A completed 60-minute timer without interaction is not a one-hour interview test.
