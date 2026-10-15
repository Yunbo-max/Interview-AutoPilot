# Resume and research cross-examination

Use a resume as a source of testable claims, not a writing assignment. Do not invent personal experiences or polish stronger claims on the candidate's behalf. An interview tests the candidate's understanding; it does not certify the historical truth of every project.

## Claim extraction

Attach each important claim to its document and section, then separate ownership, technical mechanism, metric, architecture, novelty and practical result. Record what is stated, what is inferred and what remains unknown. Ask about the actual project, not a keyword-triggered generic quiz.

For each project, build a small coverage map: problem -> personal responsibility -> mechanism -> implementation -> evidence -> limitations. For research add mathematical objects and assumptions, derivation, nearest alternatives, discriminating experiments and failure regimes. Ask the most informative missing point, not every item mechanically.

## Example challenge families

Ownership: identify the candidate's actual module or decision without equating code-line count with contribution.
Mechanism: identify exactly what state, distribution, loss, search rule or information flow changes.
Causality: distinguish an architectural effect from additional compute, data, tuning or evaluation changes.
Statistics: establish denominator, metric definition, split, leakage controls, seeds and uncertainty where relevant.
Novelty: compare the stated contribution with a verified source; do not declare priority from memory.
Failure: ask for a counterexample, failure regime, negative result or trade-off that limits the claim.
Practicality: distinguish a prototype, a delivered artifact and a maintained production system.

A research interviewer can request a small derivation or inspect supplied public code. They cannot demand confidential customer data. Missing confidential evidence is not proof of dishonesty.

## Role profiles

ML/Agent engineering: data flow, retrieval/tool failure, latency, reliability, evaluation and deployment choices.
Research scientist: assumptions, mathematical mechanism, baselines, ablations, uncertainty and reproducibility.
Quant research: probability, statistics, linear algebra, coding, temporal validation and cost/leakage confounders.
General software: algorithms, interfaces, state, testing and system trade-offs.

Use these as emphasis choices, not claims about a particular company's process. Honor the actual JD and user-specified role. Advanced difficulty is separate from pressure style.

## Source discipline

Inspect only user-authorized documents or selected repository paths. Public research lookup requires network permission where the host asks for it; cite current primary sources for time-sensitive claims. Never send private resume text or project identifiers in a web query without consent. A README's claimed result is evidence of a claim, not independent replication.

When a document conflicts with the candidate, quote precise passages and allow a version or scope explanation. When a correction changes the claim, retain the revision without treating every correction as a contradiction. A defensible concession about limitations may demonstrate strong understanding.
