"""
Job_Track_AI - Interview prep service (persistence + access).
"""
from __future__ import annotations

import logging

from database import repository as repo
from database.models import InterviewPrep, SystemLog
from core.interview_prep.generator import InterviewPrepGenerator, InterviewPrepData

log = logging.getLogger(__name__)


class InterviewPrepService:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.generator = InterviewPrepGenerator()

    def generate_for_job(self, job_id: str) -> InterviewPrep:
        job = repo.get_job(job_id)
        if not job:
            raise ValueError(f"No job with id {job_id}")
        data: InterviewPrepData = self.generator.generate(
            job.title, job.description or "")
        prep = InterviewPrep(job_id=job_id, topics=data.topics,
                             mock_questions=data.mock_questions,
                             flashcards=data.flashcards)
        repo.create_prep(prep)
        repo.log_action("interview_prep_generate", {"job_id": job_id,
                                                    "provider": self.generator.provider},
                        user_id=self.user_id)
        return prep

    def get(self, job_id: str) -> InterviewPrep | None:
        return repo.get_prep_for_job(job_id)

    def list_for_user(self) -> list[InterviewPrep]:
        preps: list[InterviewPrep] = []
        apps = repo.list_applications(user_id=self.user_id)
        for app in apps:
            prep = repo.get_prep_for_job(app.job_id)
            if prep:
                preps.append(prep)
        return preps
