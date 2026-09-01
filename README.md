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

```
main.py                 # entry point (GUI + headless CLI mode)
config/                 # settings (config/settings.py) + user config manager
database/               # SQLite schema, models, repository + optional cloud sync
core/job_search/        # filters, humanizer, API clients, site adapters, orchestrator
core/resume_engine/     # parser, matcher (77%), adaptor (change log), service
core/cover_letter/      # generator (tones), service (approve + schedule follow-up)
core/application/       # submitter (guest/auth), tracker (dashboard/calendar)
core/interview_prep/    # generator (topics/Q&A), flashcards quiz
core/agentic/           # MCP-style agents + orchestrator + CONTINUE protocol
core/self_diagnosis/    # health checks + auto-repair + debug plan
core/voice/             # optional voice assistant
core/notifications/     # desktop + optional Gmail/Calendar/Twilio
security/               # secrets (.env/Credential Manager), AES-GCM, PBKDF2
gui/                    # Tkinter desktop UI
scripts/                # push_to_github, build_exe_local, package_local, continue_handoff
.github/workflows/      # macOS/Windows .exe build (windows-latest)
```

## Quick start (local)

```bash
# Python 3.10+
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt

copy .env.example .env            # then fill in secrets (never commit)
python main.py                    # launch the GUI
```

### Headless / CI smoke test
```bash
python main.py cli search --keywords "Python" --country US
python main.py cli diagnose
```

## Build the `.exe`

- **Automatic:** push to GitHub → `.github/workflows/build-exe.yml` builds on a
  `windows-latest` runner and attaches `JobTrackAI.exe` as an artifact.
- **On your machine:** `python scripts/build_exe_local.py` (PyInstaller; see
  `scripts/build_exe_local.py` for signing guidance).

## Push to GitHub with your PAT

`python scripts/push_to_github.py` (reads `GITHUB_PAT`/`GITHUB_USERNAME` from
`.env` or Credential Manager; never stores the token).

## Package a local zip

`python scripts/package_local.py`

## Documentation

- `docs/ARCHITECTURE.md` — module flow & data model
- `docs/SECURITY.md` — secrets, encryption, legal/ToS on scraping
- `docs/DEPENDENCIES.md` — all external/free dependencies + alternatives
- `docs/FEATURES.md` — feature-by-feature behaviour and flows
- `docs/REBUILD.md` — local rebuild & debugging plan
- `docs/CONTINUATION.md` — resume-from-scratch guide
- `PROMPTS.md` — the full preserved spec (restart without rewriting)

## License

Released under the MIT License (see `LICENSE`).
