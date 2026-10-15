# Failure handling and recovery

| Failure | Immediate action | Resume condition |
|---|---|---|
| Microphone denied/revoked | Stop capture; offer text; no speech penalty | Candidate accepts text or grants a working device permission |
| STT mistranscribes a technical claim | Suspend affected grading, confirm wording | New answer revision; invalidate dependent findings |
| Audio too noisy or speakers overlap | Mark segment unreliable, ask repeat/text | Candidate-attributed final answer available |
| TTS interrupts or echoes into input | Cancel playback, discard self-audio | Verified floor reset; turn-based fallback if needed |
| Provider timeout/rate limit/budget cap | Freeze host-blocked time and show status | Bounded retry or explicitly selected fallback |
| Candidate code runner unavailable | Do not execute; static/manual assessment | Verified isolated runner or explicit static-only attempt |
| Math solver returns unknown | Keep the proof obligation open | A valid manual argument or scoped tool result |
| Wrong test/reference found | Withdraw challenge, repair grading | Versioned corrected question; candidate not penalized |
| Stale tool result | Record stale result, do not speak or score it | Matching current revision result |
| Checkpoint write failure | Stop claiming durable saves; warn | Verified write or explicitly non-persistent continuation |
| Process restart or disconnect | RECOVERING, then PAUSED | Verified checkpoint, new monotonic origin and candidate resume |
| Two clients edit one session | Reject old expected revision | Resynchronize; one elected writer |
| Storage/privacy permission revoked | Stop further writes/transfers | New scoped consent or in-memory/text mode |
| Deadline or stop while tool runs | Close attempt, cancel generation/playback | Review only; late results cannot silently amend it |

Retries are bounded and idempotent: two retries per operation by default, then pause or degrade. Never run an unlimited hidden retry loop or change a paid provider without authorization. Candidate thinking and tool failures are different clock states.

## Checkpoint design

With storage consent, use a private session directory containing a contract snapshot, event ledger, current state and evidence index; optional recordings have separate consent. Atomically write a new snapshot and index its last committed sequence. On recovery, verify schema version, consistency, artifact ownership and event ordering before replaying. Hashes detect corruption, not the truth of claims. Do not start a new one-hour session if the user asked to continue an old one.

Do not replay side effects while reconstructing state. Reuse acknowledged operation IDs; canceled speech stays canceled. Drop duplicate events and request missing sequences. Expired credentials are refreshed only through the host's authorized mechanism. An absent or corrupt checkpoint is disclosed, never reconstructed as certain from a vague summary.

## Truthful status

State whether the current host is actively running, paused, waiting for candidate input or disconnected. A skill cannot guarantee that a local/cloud process survives a chat turn ending. Exact timing, scheduled warnings and unattended continuation must be verified runtime capabilities. Otherwise explain the limitation once and continue the useful text simulation.
