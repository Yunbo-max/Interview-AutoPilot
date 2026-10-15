# AI Interview: complete skill design v0.1.0

Design date: 2026-10-15. Status: instructions and interfaces specified; live runtime not implemented.

## Intent and success criteria

A candidate sits at a computer and practices a demanding, interactive mock interview, anchored in their real resume/research, with spoken explanations, code and mathematical work. The session targets one hour and produces an evidence-based review. The differentiator is contingent cross-examination: challenge -> defense -> verification -> concession or deeper question, not resume writing or a static question bank.

The candidate's stated goals are voice input, pace/intonation feedback, detection of content errors, coding/mathematics with answers, and continuous interaction. Defaults chosen here are text fallback, strict mode, challenging pressure, explicit answer release, scoped consent and no mandatory webcam. These can be changed without rewriting the skill.

## Architectural decision

Choose a portable skill plus independent host adapters. A prompts-only design cannot acquire a microphone or enforce a timer. A voice-only black box makes technical verification and transcript repair harder to inspect. The selected design starts with STT -> canonical text -> interviewer -> TTS, plus a separate audio-observation path. Full-duplex is an optional upgrade after cancellation and floor handling work.

The skill owns interview policy. The session controller owns state/time/permissions. A capture client owns microphone, screen and editor input. Verifiers own code/math checks and bounded audio measurements. Provider adapters own transport and model-specific behavior. No particular model or Docker installation is mandatory.

One interviewer speaks to the candidate. 'Evaluator' denotes a responsibility, not a claim that independent agents ran. Actual independent agents may be added later, but agreement is not proof. Technical decisions cite visible evidence, not an opaque confidence score.

## Data flow

Candidate media or editor submission -> scoped capture and revision -> final transcript/structured answer -> frozen question rubric -> permitted checkers -> concise evidence judgment -> one next question -> acknowledged checkpoint. Reference answers remain in the evaluator view until explicit release. No untrusted document is promoted into system instructions.

Eight machine record variants specify session contracts, snapshots, question packages, judgments, event envelopes, speech observations, claims and tool results. JSON schema validates shape and several local invariants. Sequence ordering, elapsed-time arithmetic, consent enforcement, evidence authenticity and event payload semantics require controller checks beyond JSON schema.

## Functional scope

[Setup and consent](../skills/ai-interview/references/start-and-contract.md) avoid repeated onboarding and start safely with missing optional materials. [Clock/state](../skills/ai-interview/references/session-and-clock.md) define one-hour behavior. [Cross-examination](../skills/ai-interview/references/adversarial-engine.md) defines the next-question policy and stopping conditions.

[Multimodal handling](../skills/ai-interview/references/multimodal.md) separates captions from final answers and handles canceled playback. [Speech assessment](../skills/ai-interview/references/speech-assessment.md) defines rates, pauses, pitch limitations and no-audio fallback. [Coding](../skills/ai-interview/references/coding.md) and [mathematics](../skills/ai-interview/references/mathematics.md) define answer/check/review contracts. [Research](../skills/ai-interview/references/research-and-resume.md) covers paper-level assumptions and controls.

[Evaluation](../skills/ai-interview/references/evaluation-and-report.md), [tool interfaces](../skills/ai-interview/references/tool-contracts.md), [privacy](../skills/ai-interview/references/privacy-and-security.md), [host adapters](../skills/ai-interview/references/host-adapters.md) and [recovery](../skills/ai-interview/references/failure-recovery.md) close the operational design.

## Out of scope for this release

No working browser/audio app, avatar, facial analysis, hiring automation, code sandbox, acoustic extractor, installed MCP server or 60-minute unattended process. No claim of a validated acceptance predictor. No paid service is provisioned. No user account is modified. Native speech-to-speech is not required for the first runtime.

## Runtime implementation order

1. Build a text controller with reliable state, question/answer revisions, consent, monotonic timing and deterministic tests.
2. Add isolated code checks and bounded mathematical checking, with unavailable/unknown fallbacks.
3. Add browser microphone capture, turn-final STT, explicit submission and TTS; keep raw-audio analysis separately permissioned.
4. Add measured acoustic review and optional submitted visual artifacts.
5. Only then add full-duplex cancellation, reconnect handling and a real one-hour endurance test.

This is dependency ordering for implementers, not a claim that the implementation was approved, executed or scheduled. A detailed engineering plan should be based on the selected host, operating system and provider when runtime work is requested.

## Release gates

Static checks cover structure and fixtures; behavioral trials test the skill in fresh agent contexts; integration trials test the actual runtime. The [acceptance document](ACCEPTANCE.md) states which evidence is needed and forbids substituting authored examples for measured behavior. This design can be published without pretending the later runtime gates passed.
