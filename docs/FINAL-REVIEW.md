# Final review — AI Interview 0.2.1

Date: 2026-10-16. Scope: final source/package review of the Codex-callable local voice bridge. This is not real-device, ASR-quality or one-hour interview certification.

## Starting point and branch scope

The GitHub read returned only `main`, at `1491698bc362395342b50b50e0819adc3d7a9062`. The supplied 0.2.0 archive was reconstructed as a Git tree: `5712afe8d662f7bdde199183183bc0eb522b559c`, exactly matching that remote commit's tree. The original full suite passed 55 tests; this did not prevent additional regressions from being found. All changes target main; no new branch or Actions/workflow operation is used.

## Reproduced and fixed

1. A recorder may already be inactive when error/final-data/stop callbacks arrive. Cancellation previously returned too early, allowing partial audio transcription or truncation after the last chunk exceeded the cap. Cancellation now survives these queued callbacks, including question changes and channel loss.
2. A pending microphone permission result could arrive after page departure. The page now releases the stream without starting recording. Reopening the original private link initializes a new page; there is no automatic recording resumption.
3. Replaying an older confirmation could undo a corrected answer. The browser now uses immutable submission IDs plus expected answer revisions. Retries retain their receipt; a new deliberate edit (including returning to earlier wording) has a new ID. Stale new submissions and ID reuse for different text are rejected. Legacy clients without IDs deduplicate by draft/text.
4. A stopped state could still expose a ready answer during shutdown. Stop now holds the state lock; answer reads return stopped without an answer and bounded CLI waits terminate on that state.
5. Corrupted connection metadata and non-ASCII authorization values could produce unhandled errors. They now produce controlled validation/authentication failures.

## Executed evidence

- `python -m unittest discover -s tests -v`: **63 tests passed**, zero failures. Includes all 55 prior checks and 8 new Python regression methods (some include multiple invalid-input subcases).
- `node tests/ui_state_test.cjs`: **8 simulated media-state assertions passed**.
- `node tests/voice_ui_test.cjs`: **15 simulated bridge/UI assertions passed**.
- `node tests/voice_failure_ui_test.cjs`: **7 asynchronous UI regression scenarios passed**. This is a scenario count, not an assertion count.
- Python compilation, JavaScript syntax and whitespace checks passed. Existing package tests include copied-skill execution outside the repository, reference answers, schemas, relative links, version manifests and absence of workflow files.
- The new regression files were also run against the original 0.2.0 source: both commands failed. Python reported 14 failed assertions/subcases across 8 methods; UI reported 6 failed scenarios out of 7. Restoring the patched source made both pass. This is a deterministic code regression control, not an independent model-behavior experiment.

Logs: [Python](verification/final-review-python.txt), [UI](verification/final-review-ui.txt). The complete transcript is not a hardware test; loopback HTTP and subprocess lifecycle checks use a reviewed fake decoder.

## Not tested or implemented

`doctor` found no faster-whisper installation in the review environment. The configured Playwright Chromium executable was absent; no real browser/microphone run was performed. No dependencies/model weights were installed on the candidate's computer. Real Whisper transcription, macOS/Windows microphone permissions, installed Codex behavior, speech latency/accuracy and a full 60-minute interaction remain unverified. The 32 broader behavior/runtime scenarios retain not_run status.

This was an inline source review with automated tests, not an independent reviewer/agent audit. No acoustic-style analyzer, spoken question output, full-duplex interruption, safe candidate-code sandbox or exact one-hour runtime was added. Local speech processing does not make online Codex inference offline. An inactive Codex host still cannot be awakened by a saved answer.
