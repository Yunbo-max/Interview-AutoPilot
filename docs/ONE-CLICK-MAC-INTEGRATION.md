# MacBook Pro one-click installer — AI Interview v0.6.0

## Scope

The new entry point is `AI-Interview.command` (Finder double-click or `bash AI-Interview.command --yes`). It lives in the project root; its real implementation (`skills/ai-interview/scripts/one-click-mac.sh` and `mac_bootstrap.py`) travels with a standalone Skill installation too. It does **not** invoke GitHub workflows or GitHub Actions and creates no repository branches.

The user requested fully automated local installation and a one-action launch. Agent shell calls must return rather than blocking for an hour. Achieved by spawning **only** the local authenticated interview controller as a detached process; no inference continues when no model API request is actively being made, and microphone capture is never started by the installer. The app's UI is still user-controlled.

## Dependency graph

- Native host: macOS with Python >=3.10. If no suitable Python exists, use existing `uv`/Homebrew, else download a pinned official uv v0.13.1 archive for the current macOS CPU architecture, verify its published SHA256 digest before running it, and let uv install Python 3.11. Nothing uses sudo or `curl | sh`.
- Python runtime: private `~/.local/share/ai-interview/runtime/.venv`; installs in order `requirements-studio.txt`, `requirements-voicestudio.txt` (unless skipped) and `requirements-voice.txt` (unless skipped). Re-running identical package requirements skips redundant pip operations; `--repair` overrides this.
- Speech fallback: multilingual Whisper `base` downloaded only after the user allows downloads or passes `--yes`. A completed marker is written only on successful model download.
- Upstream VoiceStudio: on Apple Silicon only, and only if missing, read official latest-release JSON and select `VoiceStudio-Electron-<version>-mac-arm64.dmg` with an exact GitHub URL. Download `SHA256SUMS.txt` from the same release, verify file size and SHA256, then mount read-only using `hdiutil` and copy the app bundle with `ditto` into `~/Applications` (without overwriting an existing installation). Intel Macs use lightweight fallback. No third-party source or model binaries are committed into the MIT repository.
- Skill discovery: `~/.agents/skills/ai-interview` and `~/.claude/skills/ai-interview` point to the one canonical Skill. User installs at existing paths are backed up to an account-private directory on approval. Never create multiple conflicting copies.
- Model provider: one of the existing authenticated Codex/Claude/Gemini CLIs, or configured Qwen/DeepSeek/GLM/Kimi API key. Installer does not install provider CLIs or perform logins.

## Local process lifecycle

`mac_bootstrap.py launch_interview` checks for an already-running private session using validated `http://127.0.0.1:<port>/#token=<bearer>` metadata and authenticated `GET /api/health`. If live, it reopens the same session. Otherwise it starts `career.py interview --no-browser` as a process with `start_new_session=True` and writes output to an account-private `studio.log`. When the process reports a healthy private URL, the launcher stores the URL and PID in `studio-session.json` mode 0600, opens the browser and **returns to the agent immediately**.

Shutdown via `--stop` sends an authenticated `POST /api/shutdown` only to a validated local address. No PID from saved metadata is ever passed to `kill`. Normal service shutdown closes its existing WebSocket relay. A true process crash resets the in-memory interview state; user should export reviews before stopping. Any automatic app installation may still require a **human** to interact with macOS Gatekeeper, the VoiceStudio setup wizard, VoiceStudio model-license screens, the browser microphone prompt, and the external LLM consent form.

## Security boundaries

The installer only fetches preselected HTTPS GitHub endpoints and follows redirects to known GitHub asset hosts. An ARM64 DMG is mounted only after matching the checksum asset from its exact release; a pinned uv tarball is SHA256 checked by `shasum` before any binary is executed. The launcher never executes downloaded shell scripts. It refuses nonlocal interview URLs, session metadata with invalid structure, and remote redirect attempts. The HTTP server binds `127.0.0.1` and the shutdown endpoint inherits the existing host, origin and bearer-token checks.

The upstream AGPL-3.0 VoiceStudio desktop app is independent. The user's own VoiceStudio configuration can use remote services; the AI Interview installer does not silently allow remote speech. VoiceStudio may need separate model setup/weights from the user. All user CVs and question transcripts remain local to the installed experience except for **explicit user-authorized** submission of CV/JD/answer text to the chosen model. No voice biometrics, code execution sandbox or truly hands-free full-duplex call is claimed.

## Verification

Offline unit tests cover release metadata allowlisting, checksum manifest parsing and tampering, idempotent Skill links/backup behavior, private URL validation, stale and live sessions, actual loopback authenticated shutdown and a detached real local interview server lifecycle using no STT model or physical microphone. Syntax and model-free compatibility tests are additional. Mac-specific `hdiutil`, `ditto`, Gatekeeper, installer network and VoiceStudio's real inference **cannot be executed on this Linux container**. Hardware acceptance must be performed on the candidate's MacBook Pro. The release is useful as an installable implementation, not a claim of a fully field-certified product.
