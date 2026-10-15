# Evaluation, answer release and review

## Strict versus coach

Strict mode: maintain the interviewer role, collect concise evidence and defer extended teaching. Coach mode: explain after each attempt, give requested scaffolding and record assistance. Retry mode: use variants of unresolved claims or weaknesses. Switching mode changes future interaction, not the record of earlier assistance.

An explicit answer request terminates the current attempt as assisted and releases its answer. A hint request gives only the next staged hint. Completing a section or ending the session releases the corresponding reference solutions. Do not reveal future variants. Hidden-reference separation in this public, personal-practice skill is not a proctoring or secrecy guarantee.

## Evidence before ratings

First classify each claim: supported, partial, unsupported, contradicted or unassessed. Attach question/rubric version, answer revision, a quote or artifact locator, method and limits. A plausible answer with no external verification can be supported as an explanation, not authenticated as an historical fact.

Optionally rate correctness, reasoning, implementation/verification, trade-off judgment and clarity on an ordinal 0-3 scale:
0: a material error demonstrated by evidence.
1: a useful fragment but a key gap remains.
2: sound within the stated scope with minor omissions.
3: sound, well-defended and aware of relevant limits.
Use N/A for untested dimensions, not zero. Do not average missing scores away or compute an apparently precise hiring probability. Scores are formative, uncalibrated judgments unless validated externally. Pressure style must not change the rubric.

Speech observations have their own evidence table and never change technical scores. No accent, personality, emotion, demographic or health inference. Coding silence, a stutter or an assistive input method is not a reasoning deficit.

## Required final report

1. Session facts: actual/target duration, timing source, role, language, mode changes, available modalities, outages and what was not assessed.
2. Coverage: asked questions and claims, with answered/unattempted/assisted status; do not imply full role coverage from a small sample.
3. Findings: evidence locators, scoped judgments, unresolved conditions and confidence limits.
4. Technical answers: reference solution, assumptions, alternatives, tests/checks actually performed and missing verification.
5. Speech review: measured segment observations and actionable exercises; otherwise explicitly no audio/prosody assessment.
6. Interviewer corrections: withdrawn challenges, corrected transcripts, faulty references and superseded judgments.
7. Practice plan: at most three high-value next drills with a concrete success criterion and variant question.
8. Data summary: what was stored, where, export/deletion options and any external processing already performed.

Provide a readable Markdown report; machine records follow [the contracts](../assets/contracts.schema.json). Do not include private chain-of-thought; concise checkable reasons are enough. Show 'not executed' for unavailable tools, not reassuring green checkmarks.

## Revisions

Do not overwrite an old verdict silently. Record the reason, new evidence and superseded assessment IDs. A correction of ASR or interviewer error removes affected penalties. A candidate changing an already-graded answer is a new attempt, not a retroactive replacement. Resolve the distinction using the captured evidence and candidate clarification.
