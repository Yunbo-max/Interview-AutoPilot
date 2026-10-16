# Voice-first Multi-role Interview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for task-by-task implementation. All modifications target `main` only, no GitHub Actions/workflows.

**Goal:** Candidate can start a local, voice-first role-specific mock interview by PDF resume upload and explicit backend selection, with coding editor and optional local STT.
**Architecture:** local authenticated HTTP controller + pure curriculum/clock core + backend adapters + small browser client; retain old voice.py bridge. Skill directs capable hosts to the new studio while keeping prior modes.
**Tech Stack:** Python standard library, pypdf, optional faster-whisper; browser MediaRecorder, Web Speech Synthesis; CLI adapters/API via urllib; unittest + Node simulated DOM.
**Spec:** [voice-first design](../specs/2026-10-16-voice-first-multirole-interview.md)

## Constraints

No auto-record, credentials in browser, arbitrary shell execution, candidate code execution, uploaded CV in GitHub, extra branches, or workflows. Clear distinctions among implemented, mocked and untested provider capabilities. Only explicit candidate consent for cloud/CLI processing.

## Tasks

1. RED/GREEN: six role curricula, budgets, stage/kind rules, real clock with hold for model latency and pause.
2. RED/GREEN: PDF extraction and consent validation; signed PDF, page and size guards; no disk persistence.
3. RED/GREEN: named provider adapters (Codex/Claude/Gemini CLI, Qwen/DeepSeek/GLM/Kimi HTTPS), error handling, single-question JSON parsing, key isolation.
4. RED/GREEN: authenticated loopback studio HTTP API, start, answer, finish, retry, pause/resume, optional speech; idempotent answers, no code execution, no hidden reference leak.
5. RED/GREEN: UX: PDF upload, role/provider picker, voice-first spoken questions, record/correct/confirm, coding editor and review; simulate browser interaction.
6. Update Skill, README, host refs, portable metadata and version. Run full tests, generate verifiable ZIP, then push directly to main via connector. Report tests and unverified live paths.

## Review focus

Model failure must not lose candidate answer; repeated requests must not bill twice; a stale answer must not count for current question; a missing local STT model must not disable typed submissions; uploaded malicious PDF instructions must be treated as data; unavailable TTS cannot block accessible text presentation.
