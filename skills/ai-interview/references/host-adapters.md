# Host adapters and installation

## Portable interview rules

Copy the entire `ai-interview/` directory into the host's skill discovery path. In local Codex, use `.agents/skills/` or `~/.agents/skills/`, then explicitly invoke `$ai-interview`. The supplied plugin manifests are distribution metadata; they do not install a service or grant device permission. Text mode remains available without speech dependencies.

Official sources: [Codex skills](https://developers.openai.com/codex/skills/), [plugin packaging](https://developers.openai.com/plugins/build/plugins), [Agent Skills format](https://agentskills.io/specification).

## Implemented local voice adapter (0.2.0)

For microphone requests, read [local voice](local-voice.md) and call [voice.py](../scripts/voice.py). Commands: doctor, setup, start, ask, wait, status and stop. The browser acquires candidate-authorized audio. The local model transcribes; the candidate confirms; the waiting Codex shell call receives corrected text. The same Codex session remains the interviewer. This is a shell tool integration, not an automatically registered MCP tool and not an App Server implementation.

Installation alone does not start recording, install dependencies or download weights. `setup --allow-download` is the explicit network step. Serving uses locally cached weights. No separately billed speech API is required by this adapter. Online Codex model processing is separate from local transcription.

The host must support local process execution, loopback networking and bounded repeated tool calls. A cloud shell is not the user's desktop. Ask for ordinary host permission when required; never bypass a sandbox or tunnel the token-bearing local endpoint. No UI inspection in this environment proves that the candidate's device works.

## Broader runtime still not implemented

The bridge is not a full-duplex interview controller or exact one-hour clock. Codex App Server remains an optional future custom-client integration: initialize, start/resume a thread, stream turns, handle approvals and interruptions. It is not interchangeable with MCP. Recheck [the protocol](https://developers.openai.com/codex/app-server/) before implementing.

Browser device permission comes from [getUserMedia](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia). A future screen adapter must use [getDisplayMedia](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getDisplayMedia) with explicit consent. Neither implies raw media is exposed to the reasoning model.

Cloud STT is not used by the bundled bridge. Future alternatives need separate data-transfer approval and current provider limits. A product session length must not be confused with provider connection lifetime.

Optional future checkers include [librosa pYIN](https://librosa.org/doc/latest/generated/librosa.pyin.html) for acoustic estimates and [SymPy assumptions](https://docs.sympy.org/latest/guides/assumptions.html) for bounded symbolic checks. Neither is a bundled working speech-assessment or proof-certification service.
