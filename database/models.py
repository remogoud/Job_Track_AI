"""
Job_Track_AI - Domain models (dataclasses mirroring the approved schema).

These are storage-agnostic: the repository layer maps them to SQLite today and
can map them to Cloud SQL / Firestore later without touching business logic.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def new_uuid() -> str:
    return str(uuid.uuid4())


@dataclass
class User:
    user_id: str = field(default_factory=new_uuid)
    name: str = ""
    email: str = ""              # stored encrypted at rest
    password_hash: str = ""
    created_at: str = field(default_factory=now_utc)
    updated_at: str = field(default_factory=now_utc)


@dataclass
class Job:
    job_id: str = field(default_factory=new_uuid)
    title: str = ""
    company: str = ""
    location: str = ""
    salary_range: str = ""
    description: str = ""
    source: str = ""              # linkedin | indeed | naukri | ...
    match_score: float | None = None
    scraped_at: str = field(default_factory=now_utc)

    @property
    def meets_threshold(self, threshold: float = 0.77) -> bool:
        return self.match_score is not None and self.match_score >= threshold


@dataclass
class Resume:
    resume_id: str = field(default_factory=new_uuid)
    user_id: str = ""
    base_resume: str = ""
    optimized_resume: str = ""
    job_id: str | None = None
    change_log: list[dict[str, Any]] = field(default_factory=list)  # JSON
    approved: int = 0
    created_at: str = field(default_factory=now_utc)


@dataclass
class CoverLetter:
    cover_letter_id: str = field(default_factory=new_uuid)
    user_id: str = ""
    job_id: str | None = None
    content: str = ""
    tone: str = "Formal"          # Formal | Enthusiastic | Concise
    approved: int = 0
    created_at: str = field(default_factory=now_utc)


@dataclass
class Application:
    application_id: str = field(default_factory=new_uuid)
    user_id: str = ""
    job_id: str = ""
    resume_id: str | None = None
    cover_letter_id: str | None = None
    status: str = "Applied"       # Applied | Interview | Offer | Rejected | Withdrawn
    applied_at: str = field(default_factory=now_utc)
    updated_at: str = field(default_factory=now_utc)
    followup_date: str | None = None
    interview_at: str | None = None
    notes: str | None = None


@dataclass
class InterviewPrep:
    prep_id: str = field(default_factory=new_uuid)
    job_id: str = ""
    topics: list[str] = field(default_factory=list)          # JSON
    mock_questions: list[dict[str, str]] = field(default_factory=list)  # [{q,a}]
    flashcards: list[dict[str, Any]] = field(default_factory=list)      # [{front,back,repeats}]
    created_at: str = field(default_factory=now_utc)


@dataclass
class SystemLog:
    log_id: str = field(default_factory=new_uuid)
    user_id: str | None = None
    action: str = ""
    details: dict[str, Any] = field(default_factory=dict)   # JSON
    timestamp: str = field(default_factory=now_utc)
