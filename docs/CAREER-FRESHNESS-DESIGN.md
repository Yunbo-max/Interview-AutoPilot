# Candidate career workflow and research freshness — design (2026-10-16)

Status: executable v0.4 scope, not a claim of real-provider certification.

## Product intent

Keep AI-Interview focused on better interviews rather than automatic applications. Offer five user-facing intents: `/profile`, `/scrape`, `/rank`, `/interview`, `/memory`. `/trends` is a supporting refresh command for volatile topics; it is also used by `/interview`. No `/apply` command is created and no click/submit automation is provided. The pre-existing voice-first interview application remains the interview UI.

## Interfaces and provenance

- `profile`: import user-selected PDF or UTF-8 CV, extract text locally, create an editable, **unverified** CV Markdown draft, and maintain a private source profile. Optional provider-assisted polishing is explicit and consent-gated; never invent jobs, metrics or publications.
- `scrape`: generate a navigable LinkedIn job search URL (not a scraper); retrieve postings from companies' publicly documented Greenhouse or Lever job board GET APIs; import a user-provided LinkedIn or other job description by explicitly supplying title, company, URL and description file. No login-wall bypass, headless LinkedIn crawling, fabricated jobs or applications.
- `rank`: deterministic and explainable job-to-profile fit heuristic, including uncovered role skills, and a clear 'not hiring probability' disclosure. Ground in cached imported board/JD text; missing description reduces evidence, not candidate worth. No automatic applications.
- `interview`: voice-first studio stays authoritative, optionally adds *recent sourced abstracts* and *last-demonstrated topic evidence* to non-HR interviewer prompts only. Stale feeds are not called fresh. Recent paper ≠ important paper; popularity is an independent signal, only when observed.
- `memory`: only persists after a user's explicit CLI action. Importing an interview report records phase coverage and unverified model-feedback status; candidates can explicitly mark a topic demonstrated or needing practice. No raw transcripts by default. A 'review due' marker flags **age of evidence**, not a decline in intelligence or competence.
- `trends`: retrieves dated research metadata from arXiv's official Atom API and optionally HF Daily Papers' public community curation endpoint. HTTPS fixed-host, bounded response, limited results, no fabricated fetch results. Store provenance, publication and retrieval timestamps; annotate partial failures. A local cache requires a recent retrieval timestamp (default 7 days) to enter a new interview; no source means no recency claims.

The private workspace defaults outside the public Git repository, under the user's home directory, and is configurable. The CV is personal data. Models and sources may have their own permissions and network disclosure. External paper abstracts and JDs are untrusted data, not instructions. The interview's model can critique a paper from its abstract but may not claim it read full experiments without actual full paper retrieval.

## Architecture

- New independent, bundled Python CLI `skills/ai-interview/scripts/career.py` owns workspace state, job ingestion/rank, public research refresh, and memory. Standard library except installed pypdf and existing optional router.
- Original `interview_core.InterviewSession` accepts optional bounded briefing after explicit candidate choice, no state persistence implied.
- `interview_studio.StudioHandler` reads *only already cached* curated research and topic records when explicit checkboxes are ticked. An HTTP interview start never silently fetches the internet or writes a persistent CV.
- Cross-host guidance: one canonical Skill; `.claude/commands` afford slash command entry in Claude Code when run from repository; Codex/Gemini invoke the Skill and CLI intents. Unknown CLI host compatibility is not certified.

## Privacy/failure acceptance

- JSON state writes are atomic; data paths cannot be controlled by imported URLs; report import keeps only coverage and short notes, not the raw question-answer history.
- Feed URLs are constructed from allowlisted hosts and validated company slugs/role IDs. LinkedIn requests are not made by the scraper.
- Model-generated CV drafts are clearly labeled, must be human-reviewed, and require explicit disclosure before passing CV/JD externally.
- Network failure is returned as failure, not an empty successful 'up to date' result. A stale cache is rejected for current-paper claims. Prompt-time relevance checks must be deterministic and testable.
- Existing voice, question IDs, coding mode and original 82 regression tests remain intact.

## Measured evidence needed before certification

Pure parsing/ranking/memory tests use fixtures, not external site responses. Real fetches, LinkedIn browsing, actual Codex/Claude/Gemini interaction, OCR, stable ATS response shapes, real speech and one-hour endurance remain separate integration trials. The `docs/CAREER-VERIFICATION.md` report must state what was and was not tested.
