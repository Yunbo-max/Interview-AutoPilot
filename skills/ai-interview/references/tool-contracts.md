# Runtime tool contracts (normative, not implemented)

These names are logical interface identifiers for future adapters. They are NOT installed tools, MCP registrations or callable endpoints in this release. Discover the host's real tools and map them explicitly; never invoke an invented name.

## Common envelope

Every request carries schema version, session ID, turn ID where relevant, answer revision, operation ID and an idempotency key. Every response carries operation ID, status, provider/tool version, input revision, output/evidence references, timestamps from the host, and limitations. Status is `ok`, `unsupported`, `permission_denied`, `timeout`, `cancelled`, `stale` or `error`. No missing result is converted to success.

A single session writer serializes committed events and uses expected sequence/revision to reject conflicts. Consumers validate payloads and apply results only to matching inputs. Output text and tool errors are untrusted data. The JSON schema in this package validates record shapes; semantic cross-record checks remain explicit implementation requirements.

## Interfaces

| Logical operation | Inputs | Outputs and guarantees |
|---|---|---|
| capabilities.inspect | requested functions | capability flags, observed probes, denied/untested details; false until proven |
| session.read | session ID | authoritative snapshot, revision, sequence, verified clock or unavailable |
| session.apply | expected revision, typed control/event | committed sequence and new revision; idempotent, no duplicate scoring |
| audio.transcribe | media ID, consent revision, glossary, language | partial/final text, segment IDs, actual supported alignment/confidence; never fabricated fields |
| audio.analyze | authorized candidate media, alignment, method config | measured acoustic observations, quality and limitations; no emotion/deception output |
| audio.speak | response ID, canonical text, voice configuration | playback ID, actual played intervals and error status |
| audio.cancel | playback/response IDs | acknowledged stop and last played prefix; stale text cannot leak into history |
| visual.read | authorized image/frame ID | observed content with source and uncertainty; no autonomous desktop capture |
| code.check | frozen problem, source revision, test manifest, resource limits | isolation receipt, actual tests, failures, timing/limits; no inherited secrets/network |
| math.check | whitelisted structure, domains, assumptions, requested claim | method, result, assumptions and unresolved obligations; numeric evidence != proof |
| evidence.export | selected records, redaction policy, explicit consent | local artifact and manifest of what was included |
| evidence.delete | selected owned artifacts, confirmation | deletion receipt or exact failure; no remote deletion promises without verification |

## Adapter minimum requirements

Capability inspection must distinguish an installed audio transcriber from live microphone access. A filesystem is not consent to save; a shell is not a safe candidate-code executor. A running process and monotonic clock are required for exact-duration mode. Provider endpoints and credentials are resolved by the host, never embedded in candidate material or public examples.

Runtime state includes consent revision and source-artifact access scopes. Reject tool requests beyond scope, including hidden answer access by candidate code. Retain only the shortest useful evidence records; do not return complete home-directory listings or secrets in diagnostics.

## Concurrency and cancellations

An event has session ID, monotonically increasing sequence, globally unique event ID, turn ID, input revision, event type and payload. Duplicates are ignored; a sequence gap triggers resynchronization, not a guessed state. A candidate correction invalidates in-flight grading on the old revision. Stop, pause, permission revocation and deadline are higher priority than new questions. A job may finish for audit purposes after cancellation but cannot speak or alter the closed attempt.

The small [event fixture](../assets/event.example.json) demonstrates envelope shape only. It is not evidence that a tool ran.
