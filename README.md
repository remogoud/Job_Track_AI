# Job_Track_AI

Automated job search, application tracking, resume & cover letter adaptation, and
interview preparation — a native **Windows desktop GUI** (`.exe`) with a hybrid
offline/cloud storage model.

> ⚠️ **Security:** Never commit secrets. All keys live in `.env` or Windows
> Credential Manager. Read `docs/SECURITY.md` and `.gitignore`.

---

## What it does (the full pipeline)

1. **Job search** across LinkedIn, Indeed, Naukri, Glassdoor, Monster,
   ZipRecruiter & niche portals. Guest **or** authenticated access. Filter by
   country (US/UK/Germany/Canada/Australia/Singapore/UAE), remote-only, salary,
   role. **API-first** where possible; **human-like navigation** (delays,
   scroll, click simulation) where bot detection exists; **fast mode** where it
   doesn't.
2. **Resume matching** — parses your resume, scores it against the job
   description. **≥ 77% → proceed, else discard.**
3. **Resume adaptation** — AI rewrites the resume for the role, generates a
   change log, and waits for your **approval**. The base resume is never
   mutated; the optimized version becomes active only after approval.
4. **Cover letters** — drafted in Formal / Enthusiastic / Concise tones with a
   follow-up hook and automated follow-up scheduling.
5. **Application submission** — via site login (authenticated) or guest, with
   automatic tracker status.
6. **Tracking dashboard** — applied jobs, status counts, calendar sync for
   interviews, and follow-up notifications.
7. **Interview prep** — role topics, key points, mock Q&A, flashcard quiz mode
   with spaced-repetition tracking.
8. **Agentic flows (MCP-style)** — resume rewriting, cover letter drafting, and
   job-search filtering agents, plus a **`CONTINUE`** handoff protocol.
9. **Self-diagnosis** — watches errors, attempts auto-repair, and emits a debug
   plan + notifications on failure.
10. **Optional voice assistant** — Jarvis-like mode (gracefully degrades to text
    if audio libs are absent).

## Architecture

