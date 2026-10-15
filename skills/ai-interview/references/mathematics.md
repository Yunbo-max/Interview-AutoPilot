# Mathematical interviews

## Question contract

Record variables, domains, independence assumptions, regularity conditions, requested result, allowed tools, acceptable proof styles, reference derivation, hints and follow-up variants. Distinguish exact answers from approximations. State numeric tolerances and their scale before grading. A quantitative-finance question is an educational exercise, not financial advice.

Check dimensions, boundary cases, division by zero, sign choices, conditional versus unconditional quantities, interchange of limits/integrals/expectations, existence of moments and use of independence. Do not assume Gaussianity, differentiability or invertibility unless supplied or established.

The [sample-variance question](../assets/question-math.example.json) includes a full reference and a changed-assumption follow-up. It is a teaching fixture, not an employer question or experimental benchmark.

## Interaction

Let the candidate finish a reasoning unit before challenging it. Ask one precise question about the disputed step. Accept an alternative valid proof even if it uses different notation. If the problem is underspecified, credit identification of the missing condition and clarify the problem. Do not punish the candidate for a changed assumption introduced by the interviewer.

If the candidate offers a counterexample to the question or reference solution, verify it first. Retract invalid challenges and invalidate dependent findings. During strict mode, hints and reference releases follow the same explicit assistance policy as coding.

## Verification hierarchy

Manual reasoning review checks whether each implication follows under the stated assumptions. Symbolic algebra can support transformations on a specified domain. Numeric substitution can falsify an identity or add limited evidence; it cannot certify a general proof. A proof assistant result, when actually available, covers only its formalized statement and trusted setup.

Use result labels `supported`, `partial`, `contradicted` or `unassessed`, with the method and scope. A solver's `unknown`, timeout or inability to simplify is not proof of falsehood. Explain unresolved proof obligations. Never give a fabricated proof certificate or imply that two models agreeing is formal verification.

## Tool safety

Pass only parsed, whitelisted mathematical structures to a checker. Treat expression parsers that can evaluate arbitrary source as execution surfaces; do not feed untrusted strings through `eval` or an unrestricted parser in the controller. Bound expression size, expansion, precision and solver time. Use an isolated service when evaluation is required. State assumptions in the tool request and preserve them in the result.

If a handwritten symbol or spoken expression is ambiguous, confirm the candidate's intended expression before checking it. Keep the original and corrected forms with answer revisions.

## Review

Provide the reference derivation, assumptions that matter, at least one valid alternative where appropriate, the exact failed or unresolved step, and a changed-condition exercise. Distinguish an arithmetic slip from a structural reasoning gap. No solution is released for an unanswered future question.
