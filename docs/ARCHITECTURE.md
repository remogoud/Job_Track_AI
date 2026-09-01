# Architecture - Job_Track_AI

## Layers
1. **UI layer** - `gui/` (Tkinter). Thin shell; calls services only.
2. **Service layer** - `core/<module>/service.py`. Orchestrates the pipeline,
   owns the business rules (77% gate, approval workflow, follow-up scheduling).
3. **Domain layer** - `database/models.py` dataclasses.
4. **Data layer** - `database/repository.py` (SQLite) with an optional
   `database/cloud_sync.py` facade for Firestore/Cloud SQL.
5. **Security layer** - `security/` (secrets, AES-GCM, PBKDF2).
6. **Config** - `config/settings.py` (immutable dataclass) +
   `config/config_manager.py` (persisted user preferences).

## Data flow (search → apply)
```
SearchFilters -> JobSearchOrchestrator -> [API | Humanizer+Adapter] -> Job[]
   repo.create_job
parse_resume + match (>=0.77?) -> Repo.update_job_match
ResumeAdaptor.adapt -> change_log -> ResumeService -> resume (approved=0)
   -> GUI approve -> approved=1
CoverLetterGenerator -> CoverLetterService -> letter (approved=0)
ApplicationSubmitter.submit -> Application (status=Applied)
ApplicationTracker.dashboard/sync/notify
InterviewPrepGenerator -> flashcard quiz
AgenticOrchestrator routes to agents; CONTINUE handoff
SelfDiagnosis runs health checks + auto-repair + debug plan
```

## Storage (hybrid)
- **SQLite** is the source of truth (offline controlled). DB at
  `data/jobtrack.db` (configurable via `APP_DB_PATH`); WAL + foreign keys on.
- **Cloud SQL / Firestore**: `cloud_sync.py` provides `push`/`pull` and is gated
  behind `enable_cloud_sync`. Migrating = swapping the repository backend.

## Concurrency
- `database/db.py` uses a shared connection with an RLock + `check_same_thread=False`
  so the GUI and worker threads share state safely. Long-running searches/adapts
  run in daemon threads and marshal results back via `root.after`.

## Extensibility
- **AI providers** are pluggable: `local_heuristic` (offline, default) or
  `gemini` (if `GEMINI_API_KEY` set). Resume adaptor, cover letter generator and
  interview prep all follow this pattern.
- **Job sources** are pluggable via `ADAPTER_REGISTRY` and `_API_SOURCES`.

## Testing
- `python main.py cli diagnose` runs the headless health checks (used in CI).
- `scripts/package_local.py` produces a source-only zip.
