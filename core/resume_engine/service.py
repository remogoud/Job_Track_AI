"""
Job_Track_AI - Resume engine service.

High-level orchestrator for the resume pipeline:
  1. parse resume
  2. compute match score against job description (>=77% -> proceed, else discard)
  3. AI-adapt and build change log
  4. persist optimized resume (pending approval)
  5. approval workflow (GUI calls approve/reject)

The service is the single entry point used by the GUI and the agentic layer.
"""
from __future__ import annotations

import logging
from typing import Any

from config.settings import settings
from database import repository as repo
from database.models import Resume, SystemLog
from core.resume_engine.matcher import match_resume_to_job, passes_threshold
from core.resume_engine.adaptor import ResumeAdaptor, AdaptationResult

log = logging.getLogger(__name__)


class ResumeService:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.adaptor = ResumeAdaptor()

    def parse_and_match(self, resume_text: str, job_description: str,
                        job_id: str | None = None) -> float:
        score = match_resume_to_job(resume_text, job_description)
        if job_id:
            repo.update_job_match(job_id, score)
        repo.log_action("resume_match", {"job_id": job_id, "score": score},
                        user_id=self.user_id)
        return score

    def adapt_for_job(self, resume_text: str, job_title: str, job_description: str,
                      job_id: str | None = None) -> Resume:
        result: AdaptationResult = self.adaptor.adapt(resume_text, job_title, job_description)
        resume = Resume(
            user_id=self.user_id,
            base_resume=resume_text,
            optimized_resume=result.optimized,
            job_id=job_id,
            change_log=result.change_log,
            approved=0,
        )
        repo.create_resume(resume)
        repo.log_action("resume_adapt", {"job_id": job_id, "provider": result.provider,
                                         "changes": len(result.change_log)},
                        user_id=self.user_id)
        return resume

    # --- Approval workflow ---------------------------------------------------
    def approve(self, resume_id: str) -> bool:
        resume = repo.get_resume(resume_id)
        if not resume:
            return False
        resume.approved = 1
        repo.update_resume(resume)
        repo.log_action("resume_approve", {"resume_id": resume_id}, user_id=self.user_id)
        return True

    def reject(self, resume_id: str) -> None:
        resume = repo.get_resume(resume_id)
        if resume:
            resume.approved = -1
            repo.update_resume(resume)
            repo.log_action("resume_reject", {"resume_id": resume_id}, user_id=self.user_id)

    def get_pending(self) -> list[Resume]:
        return [r for r in repo.list_resumes(self.user_id) if r.approved == 0]
