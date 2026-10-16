# AI Interview 0.6.0 — macOS one-click installer verification

Date: 2026-10-16. Target: macOS Apple Silicon (especially MacBook Pro M-series); existing Skill and VoiceStudio remain independently licensed. The tests listed here ran in a Linux test container, **not on a physical MacBook**.

## What was executed

- The complete existing Python `unittest` suite plus new installer and controller tests: **157/157 passed** with zero errors and failures in the final full run. See [Python log](verification/mac-one-click-0.6-python.txt).
- All five browser/voice UI simulation suites passed under Node.js; see [UI log](verification/mac-one-click-0.6-ui.txt). These use mocked recording/audio, **not a real microphone**.
- Both Mac launch shell scripts passed `bash -n`. Python scripts passed compilation. `git diff --check` found no whitespace errors.
- **Red/green evidence:** Before the implementation, first tests failed with missing `mac_bootstrap`; the missing detached-session handlers and installer guide produced further failures; the Mac Finder/Bash cross-shell regression failed before the corrected Bash wrapper. MacOS minimum-version and independently copied Skill-directory tests also failed until fixed.
- Real local loopback HTTP tests: a test server and a subprocess-based interview studio were started, health-checked and shut down via the new authenticated `/api/shutdown` route. Sequential reruns reused the same registered process rather than spawning a duplicate.
- Official VoiceStudio installer simulation: a fake, already reviewed 20 MB DMG fixture was checksum-verified using a matching SHA256SUMS string, then mock `hdiutil` read-only mount and `ditto` copy were exercised. The installer did not use sudo or vendor upstream assets.
- SHA256 verification failures, untrusted release metadata/URL, suspicious session URL, stale process metadata, unknown/malformed checksum, unsupported Intel Mac, too-old macOS, and accidental replacement of an existing Skill were tested.
- The pinned temporary uv binary checksums were taken from the public GitHub `astral-sh/uv` release 0.13.1 metadata. The checked-in Bash launcher refuses execution unless the downloaded archive matches the pinned digest.

## What is not tested or automated

- **Not tested on macOS:** actual Apple Silicon system installation, Homebrew/uv-managed Python runtime, native DMG mounting, Gatekeeper dialog, VoiceStudio setup/downloads/licensing, actual voice quality or hardware permission prompts.
- The installer can install the independently licensed VoiceStudio desktop app, but **cannot pre-accept its model licenses, force an unsigned app past macOS Gatekeeper or grant microphone permission**. The user must finish those first-run controls in their own VoiceStudio/browser.
- The installer detects available Codex/Claude/Gemini CLI executables, but **does not install, log into or fund third-party model providers**. Qwen/DeepSeek/GLM/Kimi require their respective API keys. No model backend was authenticated in this test.
- No real continuous hour-long speech interview was executed; subprocess/HTTP tests do not certify model inference, latency or audio hardware. The interview session is in-memory and does not recover after process death. Export the report before stopping.
- A local Codex/Claude/Gemini runner with restricted shell privileges may require the user to approve file writes/browser launching. Cloud agents cannot install on a user's Mac simply by loading a Skill.

## Safety and branch policy

- No GitHub Actions, workflow or extra branches used.
- Public repository contains only our independent MIT scripts and usage docs, **no VoiceStudio AGPL source, weights or installer binary**. Third-party DMG is downloaded on the user's machine from the official GitHub release, with exact URL, size and SHA256 checks before read-only mounting.
- Private session URL, bearer token, PID and application logs are written only under `~/.local/share/ai-interview/runtime/`. `--stop` uses authenticated localhost HTTP and never kills arbitrary PIDs from metadata.
- Downloads must be authorized by the user (interactive prompts or explicit `--yes`); microphone, provider transfer and VoiceStudio remote engine consent remain distinct.
