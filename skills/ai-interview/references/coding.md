# Coding interviews and answer verification

## Build the question before asking it

Specify task, signature, input/output, constraints, examples, accepted variants, reference solution, hints, test oracle, boundary cases and complexity expectations. Verify the reference on the stated domain before treating it as an authority. State how Unicode, mutation, ordering, numeric overflow and invalid inputs are handled where relevant. Problem authorship and validation status belong in the question record.

The bundled [coding question](../assets/question-coding.example.json) is an original functional fixture, not a research benchmark or a claim about employer interviews. Its reference is available publicly in this repository; separation during a session is a UI/process rule, not cryptographic secrecy.

## Interaction

Ask the candidate to clarify requirements, explain an approach, implement, test and defend complexity. Do not force all stages into one message. During strict mode, do not auto-complete their code or give the reference solution. A request for a hint creates an assistance event; a request for the answer ends this attempt as assisted and releases the solution. Never penalize use of an allowed language or library.

Maintain code version, content hash and answer revision. An old test run cannot judge a later edit. Do not substitute a sample input for the full test scope.

## Checks

Distinguish syntax/runtime behavior, observed test correctness, algorithmic argument, complexity and communication. Accept any valid implementation, not only reference-like code. Test with an independent oracle or useful metamorphic properties when feasible; random checks alone are not a proof. Save seed, test manifest, code hash, tool version, pass/fail counts, failures, timeouts and limits. A finite passing suite supports only that tested scope.

Counterexamples must satisfy the original specification. A timeout caused by infrastructure is not an algorithmic timeout. Complexity arguments are examined separately from wall-clock measurements. A wrong reference or faulty test invalidates that challenge and triggers correction, not a candidate failure.

## Isolation boundary

Candidate code is untrusted, even in a personal practice session. Run it only through a verified isolated runner with no inherited credentials, network denied, bounded CPU/memory/time/output, no access to unrelated files and descendant-process termination. A plain subprocess timeout, Python `exec`, prompt instruction or generic agent workspace permission is not a security sandbox. Do not require Docker specifically; an appropriately isolated alternative is acceptable.

If no such runner exists, perform static/manual analysis, mark `execution=unavailable` and never claim tests passed. Never run candidate code inside the trusted controller, reference checker or Agent process. Review only selected workspace files; do not ingest the home directory.

## Reference release

After a section is complete, the session ends or an explicit answer request terminates the attempt, provide a correct solution, why it works, complexity, edge cases and alternatives. Separate observed bugs from conjectured ones. Retry uses a related variant rather than the identical exposed problem.
