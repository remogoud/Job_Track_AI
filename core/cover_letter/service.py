"""
Job_Track_AI - Cover letter service.

Persists generated cover letters, supports the approval workflow, and schedules
a follow-up on the linked application. Uses the follow-up date field on the
Applications table so the notification engine can pick it up.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from database import repository as repo
from database.models import CoverLetter
from core.cover_letter.generator import CoverLetterGenerator

log = logging.getLogger(__name__)


class CoverLetterService:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.generator = CoverLetterGenerator()

    def generate_and_save(self, resume_text: str, job_title: str, company: str,
                          job_description: str, job_id: str | None,
                          tone: str = "Formal") -> CoverLetter:
        result = self.generator.generate(resume_text, job_title, company,
                                         job_description, tone=tone)
        cl = CoverLetter(user_id=self.user_id, job_id=job_id,
                         content=result.content, tone=result.tone, approved=0)
        repo.create_cover_letter(cl)
        repo.log_action("cover_letter_generate", {"job_id": job_id, "tone": result.tone,
                                                  "provider": result.provider},
                        user_id=self.user_id)
        return cl

    def approve(self, cover_letter_id: str) -> bool:
        cl = repo.get_cover_letter(cover_letter_id)
        if not cl:
            return False
        cl.approved = 1
        repo.update_cover_letter(cl)
        repo.log_action("cover_letter_approve", {"cover_letter_id": cover_letter_id},
                        user_id=self.user_id)
        return True

    def reject(self, cover_letter_id: str) -> None:
        cl = repo.get_cover_letter(cover_letter_id)
        if cl:
            cl.approved = -1
            repo.update_cover_letter(cl)
            repo.log_action("cover_letter_reject", {"cover_letter_id": cover_letter_id},
                            user_id=self.user_id)

    def schedule_follow_up(self, application_id: str, days: int = 7) -> bool:
        """Set a follow-up date N days out on the linked application."""
        app = repo.get_application(application_id)
        if not app:
            return False
        followup = (datetime.now(timezone.utc) + timedelta(days=days)) \
            .strftime("%Y-%m-%dT%H:%M:%SZ")
        repo.update_application_status(application_id, app.status,
                                       interview_at=None)
        # set followup_date directly
        from database import db
        db.execute("UPDATE applications SET followup_date=? WHERE application_id=?",
                   (followup, application_id))
        repo.log_action("follow_up_schedule", {"application_id": application_id,
                                               "days": days}, user_id=self.user_id)
        return True
