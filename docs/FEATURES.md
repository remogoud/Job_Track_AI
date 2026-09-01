# Feature & Flow Documentation - Job_Track_AI

Implements the full "Job Application Automation" workflow. Each numbered flow
maps to real code below.

## 1. Job Search
- **Files:** `core/job_search/*`
- **Flow:** User sets filters (`SearchFilters`: keywords, country, remote_only,
  salary, sources, access_mode) → `JobSearchOrchestrator` routes each source →
  prefers **API** (`api_clients.py`) → else **scraper adapter**
  (`site_adapters.py`) → results normalized to `Job` and persisted.
- **Human-like navigation:** `humanizer.py` inserts delays, incremental scrolling
  and click simulation for `human` sites (linkedin, indeed, glassdoor, naukri).
  `fast` mode skips waits for low-monitoring sites (monster, ziprecruiter).
- **Countries:** US, UK, Germany, Canada, Australia, Singapore, UAE (+Remote).
- **Guest & authenticated:** `access_mode` supports `guest`/`authenticated`;
  authenticated browser submission uses credentials from the secret store.

## 2. Resume Matching
- **Files:** `core/resume_engine/parser.py`, `matcher.py`
- **Flow:** `parse_resume` extracts sections/skills → `match_resume_to_job`
  computes a 0–1 score (TF-IDF text overlap 0.35 + skill fit 0.65).
- **Gate:** `passes_threshold` (default 0.77). ≥77% → proceed, else **discard**.

## 3. Resume Adaptation
- **Files:** `core/resume_engine/adaptor.py`, `service.py`
- **Flow:** `ResumeAdaptor.adapt` rewrites the summary to match the role,
  injects missing in-demand keywords, and produces a **structured change log**
  (section, action, reason, old/new). `ResumeService` persists the optimized
  resume as `approved=0`; **user approves/rejects** via the GUI
  (`approve`/`reject`). `base_resume` is never mutated.

## 4. Cover Letter Generation
- **Files:** `core/cover_letter/generator.py`, `service.py`
- **Flow:** `CoverLetterGenerator.generate` produces a letter in
  Formal/Enthusiastic/Concise tone using the resume profile + JD skills, with a
  follow-up hook. `CoverLetterService` saves it (approved=0); `schedule_follow_up`
  sets a follow-up date on the linked application.

## 5. Application Submission
- **Files:** `core/application/submitter.py`
- **Flow:** `ApplicationSubmitter.submit` creates an `Application` (status
  Applied) and attempts submission via `api`/`browser`/`manual`, with
  guest/authenticated modes. Validates status transitions; logs everything.

## 6. Application Tracking
- **Files:** `core/application/tracker.py`, `core/notifications/notifier.py`
- **Flow:** `tracker.dashboard` returns totals, per-status counts, due
  follow-ups, interviews. `sync_to_calendar` records an interview time (optional
  GCal event). `notifier.check_followups` raises reminders for due follow-ups.

## 7. Interview Preparation
- **Files:** `core/interview_prep/*`
- **Flow:** `InterviewPrepGenerator.generate` extracts role requirements →
  topics, key points, mock Q&A, flashcards. `FlashcardSession` implements
  spaced-repetition quiz (reveal / answer correct/wrong, score).

## 8. Agentic Flows (MCP-style) + CONTINUE
- **Files:** `core/agentic/*`
- **Flow:** `AgenticOrchestrator` routes intents to `ResumeAgent`,
  `CoverLetterAgent`, `JobSearchAgent` (an MCP-tool-style registry).
- **CONTINUE:** `orchestrator.continuation()`/`save_continuation()` write a
  status JSON to `data/continuation.json`; `scripts/continue_handoff.py` prints a
  ready-to-paste `CONTINUE` prompt for resuming in another Arena account.

## 9. Self-Diagnosis
- **Files:** `core/self_diagnosis/diagnostic.py`
- **Flow:** `SelfDiagnosis.run_checks` runs health checks (db writable, schema
  integrity, config sane, secrets present, deps), attempts auto-repair for
  fixable checks, and emits a **debug plan** + a desktop notification if any
  check fails.

## 10. Voice Assistant (optional)
- **Files:** `core/voice/assistant.py`
- **Flow:** `VoiceAssistant` wraps speech-to-text + text-to-speech and routes
  commands to the agentic orchestrator ("jarvis, find python jobs"). Deals with
  missing audio libs by degrading to text-only (still routes commands).

## Desktop/GUI
- **Files:** `gui/app.py`, `gui/widgets.py`, `main.py`
- Tabs: Search, Resume (parse/match/adapt/approve), Cover Letters, Tracker,
  Interview Prep, AI Assistant (agentic), Settings (speed, self-diagnosis).
  Long operations run in background threads; the CLI (`main.py cli ...`) is for
  automation/CI.
