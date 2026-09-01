# PROMPTS.md — Job_Track_AI (Preserved Specification)

> **Purpose:** If anything fails, or the build session ends, this file lets you
> restart from scratch **without re-writing the specification**. It contains the
> verbatim prompts you provided, the feasibility clarifications I gave and how
> they were resolved, and the four canonical artifacts (Detailed Prompt,
> Workflow, Database Schema, Git Strategy).
>
> **Resume with:** `python scripts/continue_handoff.py` or paste the
> `CONTINUE` prompt at the bottom of this file into a fresh Arena AI account.

---

## 0. Feasibility Clarifications & Resolutions (from the builder)

1. **GitHub push authentication.** I cannot push to your private `Job_Track_AI`
   repo without your credentials. Resolution: the repo is prepared locally with
   the full branch/commit history; a push script (`scripts/push_to_github.py`)
   uses your Personal Access Token, and a GitHub Actions workflow
   (`.github/workflows/build-exe.yml`) auto-builds on push. **You handle auth.**
2. **Building a native `.exe`.** No cross-compilation in Linux. Resolution:
   (a) a GitHub Actions `windows-latest` workflow builds + scans the `.exe`;
   (b) `scripts/build_exe_local.py` runs PyInstaller on your own Windows machine.
3. **Scraping LinkedIn/Indeed/Glassdoor.** Dual path implemented: API-first
   (LinkedIn Jobs API, Indeed API) preferred; human-like navigation
   (delays/scroll/click simulation) for scraping where bot detection exists.
   **Legal/ToS/account risk documented.** Real-site scraping is OFF by default
   (`ENABLE_SCRAPING_REAL_SITES=false`) in `.env`. **No credentials committed.**
4. **No secrets in the repo.** All keys/credentials live in `.env` (git-ignored)
   or Windows Credential Manager. `.gitignore` excludes `.env`, certs, tokens,
   DB data, build artifacts. `security/secrets.py` reads them securely.
5. **Hybrid storage.** Local SQLite is the offline source of truth; optional
   Google Cloud (Cloud SQL / Firestore) for scale + Gemini/Calendar/Gmail/Drive
   integration, gated behind `ENABLE_CLOUD_SYNC` and lazy-imported GCP libs.
6. **Deliverables & continuation.** Repo-ready code, downloadable files + zipped
   folder (`scripts/package_local.py`), `CONTINUE` prompts
   (`scripts/continue_handoff.py`), and docs + rebuild/debug plan.

---

## 1. Detailed Prompt (verbatim)

> Build me a native Windows desktop GUI application (.exe) for automated job search, application tracking, resume/cover letter adaptation, and interview preparation. The application must include the following features, flows, and safeguards:
>
> ### GitHub Integration
> - Push all generated code, documentation, and project files directly into my GitHub repository: `Job_Track_AI`.
> - Maintain commit history with clear messages (e.g., "Resume adaptation module added", "Interview prep flow updated").
> - If Arena AI session ends or quota is exhausted, provide a continuation prompt `CONTINUE` and a summary of completed work so I can resume in another Arena AI account.
> - Always provide downloadable files and a zipped folder for local use, even if code is pushed to GitHub.
> - Provide either a compiled `.exe` or clear instructions to build `.exe` that passes Windows security checks.
>
> ### Core Features
> - Crawl and scrape jobs across multiple websites (LinkedIn, Naukri, Indeed, Glassdoor, Monster, ZipRecruiter, niche portals).
> - Support both guest access and authenticated login credentials for sites like LinkedIn.
> - Search jobs globally across top high-paying countries (US, UK, Germany, Canada, Australia, Singapore, UAE) and include remote-only filters.
> - Implement human-like navigation for sites with bot detection (simulate clicks, scrolling, delays).
> - Speed up searches where bot monitoring is absent.
> - Prefer API-based integrations (LinkedIn, Indeed APIs) where available to ensure future-proofing.
> - Resume parsing and matching with ≥77% relevance.
> - Resume auto-adaptation with change logs and approval workflow.
> - Tailored cover letter generation with follow-up automation.
> - Application tracker with dashboard, calendar integration, and notifications.
> - Interview prep module (topics, points, mock Q&A, flashcards).
> - Agentic flows with MCP integration (resume rewriting, cover letter drafting, job search filtering).
> - Voice assistant mode (optional Jarvis-like interaction).
> - Self-diagnosis and repair if app breaks, with logs and debugging plan.
>
> ### Database & Storage (Hybrid Model)
> - Local SQLite for resumes, cover letters, and application tracking (offline control).
> - Optional Google Cloud (Cloud SQL, Firestore) for scalability and integration with Google Gemini flows, Calendar, Gmail, Drive.
> - Explicitly list any external dependencies (Ngrok, Twilio, AWS resources) if used.
> - Prefer free/local services; suggest alternatives if not available.
> - Do not commit API keys, credentials, or secrets to GitHub. Use `.env` files or Windows Credential Manager. Add `.gitignore` rules to exclude sensitive files.
>
> ### Deliverables
> - Code pushed to `Job_Track_AI` GitHub repo.
> - Local downloadable project folder (raw + zipped).
> - Documentation of features, flows, and security.
> - Configurable settings for automation speed, human-like navigation, and AI agent integration.
> - Plan document for local rebuild/debugging.
>
> WAIT — do not start building until I provide all artifacts and say **NOW START**.

---

## 2. Workflow — Job Application Automation (verbatim)

> 1. **Job Search** — User sets filters (country, remote, salary, role). System crawls APIs/websites. Human-like navigation if bot detection present.
> 2. **Resume Matching** — Resume parsed → job description analyzed. Match score calculated. If ≥77% → proceed; else → discard.
> 3. **Resume Adaptation** — AI rewrites resume for role. Change log generated. User approves/rejects changes. Optimized resume stored in database.
> 4. **Cover Letter Generation** — AI drafts tailored cover letter. User approves. Stored in database.
> 5. **Application Submission** — Automated submission via site login or guest. Tracker updated with status.
> 6. **Application Tracking** — Dashboard shows applied jobs. Calendar sync for interviews. Notifications for follow-ups.
> 7. **Interview Preparation** — Extract role requirements. Generate topics, points, mock Q&A. Flashcards/quiz mode enabled.
> 8. **Agentic Flows** — MCP agents handle resume, cover letter, search. Arena AI supports `CONTINUE` keyword for broken builds. If quota exhausted → provide summary prompt for next account.
> 9. **Self-Diagnosis** — Monitor errors. Attempt auto-fix. Notify user + provide debug plan.
> 10. **Voice Assistant Mode** — Optional Jarvis-like voice interaction.
>
> WAIT — do not start building until I provide all artifacts and say **NOW START**.

---

## 3. Database Schema (Hybrid Model) (verbatim)

### Users Table
- user_id (UUID, PK)
- name (TEXT)
- email (TEXT, encrypted)
- password_hash (TEXT, securely hashed)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

### Resumes Table
- resume_id (UUID, PK)
- user_id (UUID, FK → Users)
- base_resume (TEXT)
- optimized_resume (TEXT)
- job_id (UUID, FK → Jobs)
- change_log (TEXT, JSON)
- created_at (TIMESTAMP)

### Jobs Table
- job_id (UUID, PK)
- title (TEXT)
- company (TEXT)
- location (TEXT)
- salary_range (TEXT)
- description (TEXT)
- source (TEXT)
- match_score (FLOAT)
- scraped_at (TIMESTAMP)

### Applications Table
- application_id (UUID, PK)
- user_id (UUID, FK → Users)
- job_id (UUID, FK → Jobs)
- resume_id (UUID, FK → Resumes)
- cover_letter_id (UUID, FK → CoverLetters)
- status (TEXT: Applied / Interview / Offer / Rejected)
- applied_at (TIMESTAMP)
- updated_at (TIMESTAMP)

### CoverLetters Table
- cover_letter_id (UUID, PK)
- user_id (UUID, FK → Users)
- job_id (UUID, FK → Jobs)
- content (TEXT)
- tone (TEXT: Formal / Enthusiastic / Concise)
- created_at (TIMESTAMP)

### InterviewPrep Table
- prep_id (UUID, PK)
- job_id (UUID, FK → Jobs)
- topics (TEXT)
- mock_questions (TEXT)
- flashcards (TEXT, JSON)
- created_at (TIMESTAMP)

### SystemLogs Table
- log_id (UUID, PK)
- user_id (UUID, FK → Users)
- action (TEXT)
- details (TEXT, JSON metadata)
- timestamp (TIMESTAMP)

### Storage Strategy
- Local SQLite for offline control.
- Optional Google Cloud SQL/Firestore for scalability and Gemini integration.
- Secrets stored in `.env` files or Windows Credential Manager.
- `.gitignore` excludes sensitive files from GitHub.

**Builder note / non-breaking refinements applied:**
- Timestamps stored in UTC ISO-8601.
- Added indexes on `jobs.match_score`, `applications.status`, `applications.user_id`, `applications.job_id`, `resumes.job_id`, `resumes.user_id`, `logs.action`.
- Added companion columns on Applications: `followup_date`, `interview_at`, `notes` (for follow-up/calendar engines), plus `Withdrawn` status.
- `email` encrypted with AES-256-GCM (key from `APP_ENCRYPTION_KEY`).
- `change_log`, `flashcards`, `topics`, `mock_questions`, `details` stored as JSON as specified.
- Repository layer keeps SQL the source of truth; a `cloud_sync.py` wrapper enables a SQLite → Cloud SQL/Firestore swap later.

---

## 4. Git Commit Strategy (verbatim)

### Branching
- main → stable, production-ready code.
- dev → active development.
- feature/* → one branch per feature (e.g., feature/resume-adaptation).
- hotfix/* → urgent bug fixes.

### Commit Naming Convention
- feat: → new feature (e.g., feat: add resume adaptation module)
- fix: → bug fix (e.g., fix: resolve LinkedIn login error)
- docs: → documentation updates (e.g., docs: add interview prep guide)
- chore: → maintenance tasks (e.g., chore: update dependencies)
- refactor: → code restructuring without new features.

### Commit Frequency
- Small, frequent commits for each logical change.
- Each commit should be self-contained and buildable.

### Pull Requests
- Merge feature branches into dev via PRs.
- Merge dev into main only after testing.

### Releases
- Tag releases (e.g., v1.0.0) when stable.
- Provide zipped folder + release notes for each version.

### Security
- Never commit API keys, credentials, or secrets.
- Use `.env` files or Windows Credential Manager.
- Add `.gitignore` rules to exclude sensitive files.

**Builder note:** Dev is the base branch that receives work; `main` holds
releases. Each feature developed on its own `feature/*` branch and merged to
`dev`; `dev` → `main` only after tests; `v1.0.0` tagged with a zipped folder +
release notes.

---

## 5. Consolidated GitHub / Constraints (verbatim, as re-confirmed)

> 1. **GitHub Push Authentication** — Prepare the repository locally with clean commit history. Do not attempt to push directly. Provide a ready-to-run push script that uses my Personal Access Token (PAT), or a GitHub Actions workflow. I will handle authentication with my own token.
> 2. **Building a Native .exe** — Do not attempt cross-compilation in Linux. Include both a GitHub Actions workflow using `windows-latest` runner to auto-build the `.exe`, and a step-by-step build script (e.g., PyInstaller) for me to run on my own Windows machine.
> 3. **Scraping LinkedIn/Indeed/Glassdoor** — Implement both scraping and API paths. Use human-like navigation safeguards (delays, scrolling, click simulation) for scraping. Prefer API integrations where available (LinkedIn Jobs API, Indeed API). Document clearly that scraping carries legal/account risks. Do not commit any credentials.
> 4. **No Secrets in Repo** — All API keys, credentials, and secrets stored in `.env` files or Windows Credential Manager. Add `.gitignore` rules to exclude sensitive files. Never commit secrets to GitHub.
> 5. **Database & Storage (Hybrid Model)** — Local SQLite for resumes, cover letters, and application tracking (offline control, safe). Optional Google Cloud SQL/Firestore for scalability and integration with Gemini flows, Calendar, Gmail, Drive. Ensure all secrets externalized into `.env` or Credential Manager.
> 6. **Deliverables & Continuation** — Provide code prepared for my GitHub repo (`Job_Track_AI`) via my PAT or workflow. Provide downloadable files and a zipped folder for local use. Provide continuation prompts (`CONTINUE`) if session ends or quota is exhausted. Provide documentation and a local rebuild/debug plan.
> 7. **Prompt Preservation (.md File)** — Create a `PROMPTS.md` file inside the repository that contains the full text of all prompts, the feasibility clarifications and understanding, and the four artifacts (Detailed Prompt, Workflow, Database Schema, Git Strategy).

---

## 6. Build Trigger

The build was authorised with the phrase **NOW START** (given by the user after
confirming yes to committing the complete app structure into the repo).

---

## CONTINUE PROMPT (paste into a fresh Arena AI account)

```
CONTINUE

I am resuming Job_Track_AI from a preserved spec (see PROMPTS.md in the repo).
The repo already has working, committed core modules on the `dev` branch:
config, hybrid SQLite DB layer, job search (API-first + human-like scraping),
resume engine (parse/match/adapt/approve), cover letters, application tracker +
notifications, interview prep + flashcards, agentic MCP flows + CONTINUE protocol,
self-diagnosis, optional voice assistant, and a Tkinter desktop GUI.

Please continue by reviewing the existing code and completing any remaining
tasks, in priority order: add any missing documentation (README, feature/security
docs, rebuild/debug plan), finalise the .exe build workflow and local build
script, run a full end-to-end smoke test, then tag v1.0.0.
Reuse the existing architecture (config/settings.py, database/ hybrid SQLite,
core/* services, security/ secret-only access, feature-branch git convention).
Do NOT rewrite working modules from scratch. Preserve the no-secrets-in-repo rule.
```
