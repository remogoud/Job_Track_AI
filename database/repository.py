"""
Job_Track_AI - Repository (data access layer).

Thin mapping from the dataclass models to SQLite. Every method is small and
self-contained so the same operations can be re-implemented for Cloud SQL /
Firestore by swapping the repository backend (see cloud_sync.py).
"""
from __future__ import annotations

import json
import sqlite3

from database import db
from database.models import (
    User, Job, Resume, CoverLetter, Application, InterviewPrep, SystemLog,
)

# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
def create_user(user: User) -> None:
    db.execute(
        "INSERT INTO users(user_id,name,email,password_hash,created_at,updated_at) "
        "VALUES(?,?,?,?,?,?)",
        (user.user_id, user.name, user.email, user.password_hash,
         user.created_at, user.updated_at),
    )


def get_user(user_id: str) -> User | None:
    row = db.fetchone("SELECT * FROM users WHERE user_id=?", (user_id,))
    return User(**dict(row)) if row else None


def update_user(user: User) -> None:
    user.updated_at = __import__("database.models", fromlist=["now_utc"]).now_utc()
    db.execute(
        "UPDATE users SET name=?, email=?, password_hash=?, updated_at=? WHERE user_id=?",
        (user.name, user.email, user.password_hash, user.updated_at, user.user_id),
    )


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------
def create_job(job: Job) -> None:
    db.execute(
        "INSERT INTO jobs(job_id,title,company,location,salary_range,description,"
        "source,match_score,scraped_at) VALUES(?,?,?,?,?,?,?,?,?)",
        (job.job_id, job.title, job.company, job.location, job.salary_range,
         job.description, job.source, job.match_score, job.scraped_at),
    )


def get_job(job_id: str) -> Job | None:
    row = db.fetchone("SELECT * FROM jobs WHERE job_id=?", (job_id,))
    return Job(**dict(row)) if row else None


def list_jobs(source: str | None = None, min_score: float | None = None) -> list[Job]:
    sql, params = "SELECT * FROM jobs WHERE 1=1", []
    if source:
        sql += " AND source=?"
        params.append(source)
    if min_score is not None:
        sql += " AND match_score>=?"
        params.append(min_score)
    sql += " ORDER BY scraped_at DESC"
    return [Job(**dict(r)) for r in db.fetchall(sql, tuple(params))]


def update_job_match(job_id: str, score: float) -> None:
    db.execute("UPDATE jobs SET match_score=? WHERE job_id=?", (score, job_id))


# ---------------------------------------------------------------------------
# Resumes
# ---------------------------------------------------------------------------
def create_resume(resume: Resume) -> None:
    db.execute(
        "INSERT INTO resumes(resume_id,user_id,base_resume,optimized_resume,job_id,"
        "change_log,approved,created_at) VALUES(?,?,?,?,?,?,?,?)",
        (resume.resume_id, resume.user_id, resume.base_resume, resume.optimized_resume,
         resume.job_id, json.dumps(resume.change_log), resume.approved, resume.created_at),
    )


def get_resume(resume_id: str) -> Resume | None:
    row = db.fetchone("SELECT * FROM resumes WHERE resume_id=?", (resume_id,))
    if not row:
        return None
    d = dict(row)
    d["change_log"] = json.loads(d["change_log"] or "[]")
    return Resume(**d)


def update_resume(resume: Resume) -> None:
    db.execute(
        "UPDATE resumes SET base_resume=?, optimized_resume=?, job_id=?, change_log=?,"
        " approved=? WHERE resume_id=?",
        (resume.base_resume, resume.optimized_resume, resume.job_id,
         json.dumps(resume.change_log), resume.approved, resume.resume_id),
    )


def list_resumes(user_id: str) -> list[Resume]:
    rows = db.fetchall("SELECT * FROM resumes WHERE user_id=? ORDER BY created_at DESC",
                       (user_id,))
    out = []
    for r in rows:
        d = dict(r)
        d["change_log"] = json.loads(d["change_log"] or "[]")
        out.append(Resume(**d))
    return out


# ---------------------------------------------------------------------------
# Cover Letters
# ---------------------------------------------------------------------------
def create_cover_letter(cl: CoverLetter) -> None:
    db.execute(
        "INSERT INTO cover_letters(cover_letter_id,user_id,job_id,content,tone,approved,"
        "created_at) VALUES(?,?,?,?,?,?,?)",
        (cl.cover_letter_id, cl.user_id, cl.job_id, cl.content, cl.tone,
         cl.approved, cl.created_at),
    )


def get_cover_letter(cl_id: str) -> CoverLetter | None:
    row = db.fetchone("SELECT * FROM cover_letters WHERE cover_letter_id=?", (cl_id,))
    return CoverLetter(**dict(row)) if row else None


def update_cover_letter(cl: CoverLetter) -> None:
    db.execute(
        "UPDATE cover_letters SET content=?, tone=?, approved=? WHERE cover_letter_id=?",
        (cl.content, cl.tone, cl.approved, cl.cover_letter_id),
    )


def list_cover_letters(user_id: str) -> list[CoverLetter]:
    rows = db.fetchall(
        "SELECT * FROM cover_letters WHERE user_id=? ORDER BY created_at DESC", (user_id,))
    return [CoverLetter(**dict(r)) for r in rows]


# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
def create_application(app: Application) -> None:
    db.execute(
        "INSERT INTO applications(application_id,user_id,job_id,resume_id,cover_letter_id,"
        "status,applied_at,updated_at,followup_date,interview_at,notes)"
        " VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (app.application_id, app.user_id, app.job_id, app.resume_id, app.cover_letter_id,
         app.status, app.applied_at, app.updated_at, app.followup_date,
         app.interview_at, app.notes),
    )


def get_application(app_id: str) -> Application | None:
    row = db.fetchone("SELECT * FROM applications WHERE application_id=?", (app_id,))
    return Application(**dict(row)) if row else None


def update_application_status(app_id: str, status: str, notes: str | None = None,
                              interview_at: str | None = None) -> None:
    from database.models import now_utc
    if status is not None:
        db.execute("UPDATE applications SET status=?, updated_at=? WHERE application_id=?",
                   (status, now_utc(), app_id))
    if notes is not None:
        db.execute("UPDATE applications SET notes=?, updated_at=? WHERE application_id=?",
                   (notes, now_utc(), app_id))
    if interview_at is not None:
        db.execute("UPDATE applications SET interview_at=?, updated_at=? WHERE application_id=?",
                   (interview_at, now_utc(), app_id))


def list_applications(user_id: str | None = None, status: str | None = None) \
        -> list[Application]:
    sql, params = "SELECT * FROM applications WHERE 1=1", []
    if user_id:
        sql += " AND user_id=?"
        params.append(user_id)
    if status:
        sql += " AND status=?"
        params.append(status)
    sql += " ORDER BY updated_at DESC"
    return [Application(**dict(r)) for r in db.fetchall(sql, tuple(params))]


def dashboard_stats(user_id: str) -> dict[str, int]:
    """Counts per status for the dashboard."""
    rows = db.fetchall(
        "SELECT status, COUNT(*) AS n FROM applications WHERE user_id=? GROUP BY status",
        (user_id,))
    stats = {"Applied": 0, "Interview": 0, "Offer": 0, "Rejected": 0, "Withdrawn": 0}
    for r in rows:
        stats[r["status"]] = r["n"]
    return stats


def due_followups(user_id: str, today_date: str) -> list[Application]:
    rows = db.fetchall(
        "SELECT * FROM applications WHERE user_id=? AND followup_date IS NOT NULL "
        "AND followup_date<=? ORDER BY followup_date ASC", (user_id, today_date))
    return [Application(**dict(r)) for r in rows]


# ---------------------------------------------------------------------------
# Interview Prep
# ---------------------------------------------------------------------------
def create_prep(prep: InterviewPrep) -> None:
    db.execute(
        "INSERT INTO interview_prep(prep_id,job_id,topics,mock_questions,flashcards,created_at)"
        " VALUES(?,?,?,?,?,?)",
        (prep.prep_id, prep.job_id, json.dumps(prep.topics),
         json.dumps(prep.mock_questions), json.dumps(prep.flashcards), prep.created_at),
    )


def get_prep(prep_id: str) -> InterviewPrep | None:
    row = db.fetchone("SELECT * FROM interview_prep WHERE prep_id=?", (prep_id,))
    if not row:
        return None
    d = dict(row)
    d["topics"] = json.loads(d["topics"] or "[]")
    d["mock_questions"] = json.loads(d["mock_questions"] or "[]")
    d["flashcards"] = json.loads(d["flashcards"] or "[]")
    return InterviewPrep(**d)


def get_prep_for_job(job_id: str) -> InterviewPrep | None:
    row = db.fetchone("SELECT * FROM interview_prep WHERE job_id=? ORDER BY created_at DESC",
                      (job_id,))
    if not row:
        return None
    d = dict(row)
    d["topics"] = json.loads(d["topics"] or "[]")
    d["mock_questions"] = json.loads(d["mock_questions"] or "[]")
    d["flashcards"] = json.loads(d["flashcards"] or "[]")
    return InterviewPrep(**d)


# ---------------------------------------------------------------------------
# System Logs
# ---------------------------------------------------------------------------
def create_log(log: SystemLog) -> None:
    db.execute(
        "INSERT INTO system_logs(log_id,user_id,action,details,timestamp) VALUES(?,?,?,?,?)",
        (log.log_id, log.user_id, log.action, json.dumps(log.details), log.timestamp),
    )


def log_action(action: str, details: dict | None = None, user_id: str | None = None) -> None:
    create_log(SystemLog(user_id=user_id, action=action, details=details or {}))


def recent_logs(limit: int = 50) -> list[SystemLog]:
    rows = db.fetchall(
        "SELECT * FROM system_logs ORDER BY timestamp DESC LIMIT ?", (limit,))
    out = []
    for r in rows:
        d = dict(r)
        d["details"] = json.loads(d["details"] or "{}")
        out.append(SystemLog(**d))
    return out
