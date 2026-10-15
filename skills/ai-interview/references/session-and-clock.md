# One-hour state machine and clock

## States

`SETUP -> READY -> ACTIVE -> REVIEW -> COMPLETED`.
`ACTIVE -> PAUSED -> ACTIVE`; `ACTIVE -> RECOVERING -> PAUSED`.
A stop request from ACTIVE, PAUSED or RECOVERING enters REVIEW. Permission loss moves to PAUSED. An invalid checkpoint enters RECOVERING, never a guessed continuation.

Within ACTIVE, floor states are `ASKING`, `LISTENING`, `THINKING`, `EVALUATING`. Only a final candidate answer or explicit submission starts grading. Thinking silence is a valid part of answering.

## Timing contract

A runtime owns the clock; an LLM never estimates elapsed minutes from tokens or number of messages. With a running monotonic clock, active elapsed is the measured duration in ACTIVE, excluding the union of explicit pause, outage and host-blocked intervals. The union prevents double subtraction when an outage and pause overlap. Count candidate thinking, writing and agreed interviewer speech. Exclude setup, device repair, provider waiting when the candidate cannot proceed, and detailed review. Attribute each interval a reason and source.

Persist accumulated active seconds at checkpoints. After a process restart, discard the old monotonic origin; establish a new origin and resume from the accumulated total. Do not bill the disconnected interval to the candidate. UTC timestamps are audit aids, not the elapsed-time clock. A system clock change must not change the time budget.

At 3,600 verified active seconds, stop accepting new answers, finalize any in-flight answer as incomplete and enter REVIEW. Warn at five and one minute remaining when the host supports scheduled UI events. No new long question after its phase budget is exhausted; report missing coverage instead. Extensions require an explicit change in the contract and remain visible in the report.

In chat-only mode, set `clock_mode=user_managed` and say the 60 minutes are a target, not an enforced continuous session. A candidate may use an external timer and send stop. An inactive chat cannot send a deadline alert by itself. Never schedule an hourly automation as a substitute for a live interview process.

## Authoritative state

Keep a contract revision, phase, active seconds, current question/rubric version, claim ledger, transcript revisions, assistance history, provider bindings, capability/consent revisions and last acknowledged event sequence. Store evidence locators, not speculative inner monologue.

Use one writer per session. Every operation carries session ID, turn ID, input revision and idempotency key. An old transcript result must not overwrite a new correction. A tool finishing after a stop, deadline or new answer revision is recorded as stale; it cannot change the final verdict silently.

## Fair continuity

One candidate-facing interviewer at a time even when specialist tools run concurrently. Review work may run concurrently only within a live capable runtime, with bounded timeouts and no overlapping speech. Do not claim independent multi-agent validation when only one agent performed the checks.

A checkpoint saves continuity, not proof that an answer is true. Local hashes can detect accidental changes but cannot prove experiments were genuine. Resume the current question rather than restarting an hour or repeating resolved challenges.
