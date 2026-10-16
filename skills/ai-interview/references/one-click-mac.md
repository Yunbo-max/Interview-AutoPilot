# One-click macOS installation and launch (v0.6.0)

For a **local** Codex / Claude Code / Gemini CLI agent running on the candidate's
MacBook Pro. Do not attempt local installation from a cloud shell or remote
ChatGPT session. Do not request the candidate's credentials; the interviewer
provider must already be configured or the user logs in separately.

## Single command

From a full cloned AI-Interview repository, run:

```bash
bash AI-Interview.command --yes
```

Or **double-click `AI-Interview.command` in Finder** for a guided interactive
installation. The standalone installed Skill also includes a working installer:

```bash
bash "$SKILL_DIR/scripts/one-click-mac.sh" --yes
```

`--yes` explicitly authorizes Python package downloads, a local multilingual
Whisper base model, and (on Apple Silicon only) the separate official
VoiceStudio installer. No microphone is opened, no personal PDF is read and
no account login occurs during setup. Without `--yes`, a local interactive
terminal asks before networked installations. In agent mode, do not use `--yes`
unless the candidate has expressly requested one-click installation.

The command:

1. Detects macOS and a Python 3.10+ interpreter. If missing, it uses an
   **existing** `uv` or Homebrew with approval. Otherwise, the wrapper
   downloads an official **pinned uv v0.13.1** binary, verifies its published
   SHA256, and asks uv to install Python 3.11. It never installs Homebrew,
   runs an arbitrary remote shell script, or requests sudo.
2. Creates `~/.local/share/ai-interview/runtime/.venv` and installs the studio,
   VoiceStudio stream relay, and local Faster-Whisper requirements. Re-running
   with the same requirement manifest skips redundant package installs.
3. Explicitly downloads the multilingual Whisper `base` model as an offline
   fallback. No audio is uploaded during model download.
4. Registers this **same, complete Skill folder** by symbolic links at
   `~/.agents/skills/ai-interview` for Codex and compatible Agent Skills hosts,
   and `~/.claude/skills/ai-interview` for Claude Code. Old differing folders
   are never silently deleted: an explicitly authorized upgrade moves them to
   `~/.local/share/ai-interview/skill-backups/`. Do not delete or move the
   installed source folder afterward; links point to its location.
5. For **Apple Silicon** (M1/M2/M3/M4 etc.), if VoiceStudio is not already
   installed, obtains release metadata from `debpalash/VoiceStudio`'s official
   GitHub release, selects the exact ARM64 `.dmg`, downloads `SHA256SUMS.txt`,
   checks **SHA256** and file size *before* mounting, then copies the
   independent app into `~/Applications/VoiceStudio.app` without sudo.
   Existing installations are left alone. Intel Mac local backend is unsupported;
   skip VoiceStudio and retain Whisper/browser TTS.
6. Attempts to open VoiceStudio and creates a private authenticated AI-Interview
   localhost server. It opens the browser. A local agent command returns
   promptly while the interview service runs in the background, rather than
   blocking the agent's shell tool for the entire hour.

**First-run human actions remain essential.** VoiceStudio's macOS Gatekeeper
confirmation, its own Python/model setup, model-weight licenses and remote
engine choices are controlled within the upstream app. Do not run `xattr -d`,
turn off Gatekeeper or silently accept licenses. The candidate must click Record
and grant browser microphone access. They separately approve VoiceStudio use
in AI-Interview and sending confirmed answer/CV text to their chosen online LLM.

## Reuse, check, stop

```bash
bash AI-Interview.command --doctor          # read-only diagnosis; no mic
bash AI-Interview.command --dry-run         # print plan; no downloads/changes
bash AI-Interview.command --launch-only     # re-open or launch the existing session
bash AI-Interview.command --stop            # authenticated local shutdown
```

A repeated launch reuses an active session rather than creating a second
interviewer. The launcher stores a **private** localhost URL/token and PID in
`~/.local/share/ai-interview/runtime/studio-session.json`, and diagnostic log
in `studio.log`; these are local, not GitHub files. The private URL must never
be posted in a public issue or a chat transcript. `--stop` uses the authenticated
`POST /api/shutdown` on the same localhost service and never kills arbitrary
PIDs from persisted metadata. A restart after an actual process crash **does
not restore the in-memory interview**; export the report before stopping.

If VoiceStudio is still completing first-run setup, the website starts with a
working multilingual Whisper fallback instead. Re-run `--launch-only` after
VoiceStudio is ready to enable **streaming subtitles** (terminate any previous
session with `--stop` first, after exporting its report). The browser still
requires **Check VoiceStudio → consent → Speech Engine: VoiceStudio** before
using the separate app. Its TTS voice is the current selected VoiceStudio
profile; the browser TTS remains a fallback.

## Alternatives / troubleshooting

- `--no-voicestudio`: only local Whisper plus browser TTS; saves VoiceStudio's
  disk footprint and avoids its separate first-run setup.
- `--skip-whisper`: avoid the extra model; requires VoiceStudio STT or typed
  answers. If VoiceStudio is unavailable, no local microphone transcription.
- `--no-skills`: leave existing agent skill directories untouched.
- `--replace-skills`: make dated backups before replacing another
  installation; `--yes` also explicitly authorizes this safe replacement.
- `--no-launch`: finish installation but do not start a service.
- `--repair`: reinstall Python requirements when a virtual environment is
  corrupted or mismatched.
- If the Mac lacks Python/uv/Homebrew, the installer downloads the pinned SHA256-verified uv binary to a temporary directory and installs Python 3.11. If this step fails because of network restrictions, install Python 3.11 manually from [python.org](https://www.python.org/downloads/macos/) and rerun. No arbitrary remote shell script is executed by our launcher.
- If `VoiceStudio` is not found, start it from `~/Applications`, finish its
  Model Catalogue setup and check the official speech protocol locally:
  `curl http://127.0.0.1:3900/.well-known/voicestudio-speech`.
- Check provider availability and CLI login **in the browser setup**; installing
  this Skill does not buy provider API access or install all model CLIs.
- The local studio requires `127.0.0.1`; remote/cloud agents cannot operate a
  user's microphone through this launcher. Never expose the port via tunnels.

Official VoiceStudio installer and model rules: [macOS installation](https://github.com/debpalash/VoiceStudio/blob/main/docs/install/macos.md),
[official releases](https://github.com/debpalash/VoiceStudio/releases/latest),
[license notice](https://github.com/debpalash/VoiceStudio/blob/main/LICENSE-NOTICE.md).
The application and its installed model weights remain external **AGPL-3.0 / separate-model-license**
artifacts; no upstream source or DMG is bundled in our MIT repository.

All unit and local HTTP checks are simulations of **Mac setup** on Linux. We
cannot assert successful DMG mounting, macOS Gatekeeper, mic model inference,
Mac TTS quality or one-hour stability until tested on an actual candidate Mac.
