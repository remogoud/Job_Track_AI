-- ===========================================================================
-- Job_Track_AI - Database Schema (Hybrid Model core: SQLite)
-- Matches the approved "3. Database Schema" artifact exactly, with a few
-- additive indexes/companion fields for calendar sync and follow-ups.
-- All timestamps are stored as ISO-8601 UTC (YYYY-MM-DDTHH:MM:SSZ).
-- ===========================================================================

PRAGMA foreign_keys = ON;

-- --------------------------------------------------------------------------
-- Users
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id         TEXT PRIMARY KEY,                  -- UUID
    name            TEXT NOT NULL,
    email           TEXT NOT NULL,                     -- AES-GCM encrypted at rest
    password_hash   TEXT NOT NULL,                     -- securely hashed (PBKDF2 / bcrypt)
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    updated_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

-- --------------------------------------------------------------------------
-- Jobs
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS jobs (
    job_id          TEXT PRIMARY KEY,                  -- UUID
    title           TEXT NOT NULL,
    company         TEXT,
    location        TEXT,
    salary_range    TEXT,
    description     TEXT,
    source          TEXT,                              -- linkedin | indeed | naukri | etc.
    match_score     REAL,
    scraped_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
CREATE INDEX IF NOT EXISTS idx_jobs_match    ON jobs(match_score);
CREATE INDEX IF NOT EXISTS idx_jobs_source   ON jobs(source);
CREATE INDEX IF NOT EXISTS idx_jobs_title    ON jobs(title);

-- --------------------------------------------------------------------------
-- Resumes
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS resumes (
    resume_id        TEXT PRIMARY KEY,                 -- UUID
    user_id          TEXT NOT NULL REFERENCES users(user_id),
    base_resume      TEXT,                             -- original, never mutated
    optimized_resume TEXT,                             -- AI-adapted version
    job_id           TEXT REFERENCES jobs(job_id),
    change_log       TEXT,                             -- JSON array of changes
    approved         INTEGER NOT NULL DEFAULT 0,       -- approval workflow
    created_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
CREATE INDEX IF NOT EXISTS idx_resumes_user ON resumes(user_id);
CREATE INDEX IF NOT EXISTS idx_resumes_job  ON resumes(job_id);

-- --------------------------------------------------------------------------
-- Cover Letters
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cover_letters (
    cover_letter_id   TEXT PRIMARY KEY,                -- UUID
    user_id           TEXT NOT NULL REFERENCES users(user_id),
    job_id            TEXT REFERENCES jobs(job_id),
    content           TEXT NOT NULL,
    tone              TEXT NOT NULL DEFAULT 'Formal'
                      CHECK (tone IN ('Formal','Enthusiastic','Concise')),
    approved          INTEGER NOT NULL DEFAULT 0,
    created_at        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

-- --------------------------------------------------------------------------
-- Applications
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS applications (
    application_id    TEXT PRIMARY KEY,                -- UUID
    user_id           TEXT NOT NULL REFERENCES users(user_id),
    job_id            TEXT NOT NULL REFERENCES jobs(job_id),
    resume_id         TEXT REFERENCES resumes(resume_id),
    cover_letter_id   TEXT REFERENCES cover_letters(cover_letter_id),
    status            TEXT NOT NULL DEFAULT 'Applied'
                      CHECK (status IN ('Applied','Interview','Offer','Rejected','Withdrawn')),
    applied_at        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    updated_at        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    -- additive: follow-up engine + calendar sync + notes
    followup_date     TEXT,
    interview_at      TEXT,
    notes             TEXT
);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_applications_user  ON applications(user_id);
CREATE INDEX IF NOT EXISTS idx_applications_job   ON applications(job_id);

-- --------------------------------------------------------------------------
-- Interview Prep
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS interview_prep (
    prep_id          TEXT PRIMARY KEY,                 -- UUID
    job_id           TEXT NOT NULL REFERENCES jobs(job_id),
    topics           TEXT,                             -- JSON array of topics/key points
    mock_questions   TEXT,                             -- JSON array of Q&A
    flashcards       TEXT,                             -- JSON: [{front, back, repeats}]
    created_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

-- --------------------------------------------------------------------------
-- System Logs
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS system_logs (
    log_id           TEXT PRIMARY KEY,                 -- UUID
    user_id          TEXT REFERENCES users(user_id),
    action           TEXT NOT NULL,
    details          TEXT,                             -- JSON metadata
    timestamp        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
CREATE INDEX IF NOT EXISTS idx_logs_action ON system_logs(action);
