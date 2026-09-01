"""
Job_Track_AI - Application tracker service.

Dashboard aggregation, status management, calendar sync hooks and notification
triggers. Complements ApplicationSubmitter (which handles the act of applying).
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from database import repository as repo
from database.models import Application
from core.application.submitter import STATUSES
from core.notifications.notifier import NotificationService

log = logging.getLogger(__name__)


class ApplicationTracker:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.notifier = NotificationService(user_id)

    # -- dashboard ---------------------------------------------------------------
    def dashboard(self) -> dict:
        apps = repo.list_applications(user_id=self.user_id)
        stats = repo.dashboard_stats(self.user_id)
        total = len(apps)
        return {
            "total": total,
            "stats": stats,
            "recent": apps[:20],
            "due_followups": len(repo.due_followups(
                self.user_id, datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))),
            "interviews": [a for a in apps if a.interview_at],
        }

    # -- calendar sync -----------------------------------------------------------
    def sync_to_calendar(self, application_id: str, start_iso: str) -> bool:
        """Add an interview event to Google Calendar (optional)."""
        app = repo.get_application(application_id)
        if not app:
            return False
        repo.update_application_status(application_id, app.status,
                                       interview_at=start_iso)
        job = repo.get_job(app.job_id)
        title = f"Interview: {job.title if job else 'Role'} @ {job.company if job else 'Company'}"
        self.notifier.interview_invite("", title, start_iso)
        repo.log_action("calendar_sync", {"application_id": application_id,
                                          "start": start_iso}, user_id=self.user_id)
        return True

    # -- notifications -----------------------------------------------------------
    def run_followup_check(self) -> None:
        due = self.notifier.check_followups()
        self.notifier.drain()

    def schedule_followup(self, application_id: str, days: int = 7) -> bool:
        app = repo.get_application(application_id)
        if not app:
            return False
        followup = (datetime.now(timezone.utc) + timedelta(days=days)) \
            .strftime("%Y-%m-%dT%H:%M:%SZ")
        from database import db
        db.execute("UPDATE applications SET followup_date=? WHERE application_id=?",
                   (followup, application_id))
        repo.log_action("follow_up_schedule", {"application_id": application_id,
                                               "days": days}, user_id=self.user_id)
        return True
