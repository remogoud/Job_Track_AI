"""
Job_Track_AI — Notifications (follow-ups, interviews, updates).

Provides desktop notifications (stdlib-friendly) and an optional Gmail /
Google Calendar / SMS path. All endpoints are OPTIONAL and configured via .env
or Windows Credential Manager. The local engine always queues notifications so
nothing is lost when an external channel is unavailable.

External dependence summary (see docs/DEPENDENCIES.md):
  * Twilio (optional, free tier) — SMS. Not used unless configured.
  * Google Calendar API — interview invites. Optional.
  * Gmail API — follow-up email drafting. Optional.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from database import repository as repo
from core.job_search.humanizer import Humanizer
from security.secrets import get_secret

log = logging.getLogger(__name__)


@dataclass
class Notification:
    title: str
    body: str
    level: str = "info"      # info | warning | critical


class NotificationService:
    def __init__(self, user_id: str | None = None):
        # user_id may be None for system-level notifications (nullable FK on logs).
        self.user_id = user_id
        self._queue: list[Notification] = []

    # -- desktop -----------------------------------------------------------------
    def desktop(self, title: str, body: str, level: str = "info") -> None:
        self._queue.append(Notification(title=title, body=body, level=level))
        try:
            from plyer import notification  # type: ignore  # optional
            notification.notify(title=title, message=body, timeout=8)
        except Exception:
            # Fallback: log only (GUI will read the queue).
            log.info("Notification: %s — %s", title, body)
        self._log_alert(title, body, level)

    def _log_alert(self, title: str, body: str, level: str) -> None:
        repo.log_action("notification", {"title": title, "body": body, "level": level},
                        user_id=self.user_id)

    # -- follow-up reminder ------------------------------------------------------
    def check_followups(self) -> list[Application]:
        """Return + raise notifications for applications with a due follow-up."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        due = repo.due_followups(self.user_id, today)
        for app in due:
            self.desktop(
                "Follow-up due",
                f"You applied to a role on {app.applied_at}. Time to follow up.",
                level="info")
        return due

    # -- external channels (optional) ---------------------------------------------
    def email_follow_up(self, to_email: str, subject: str, body: str) -> bool:
        """Gmail follow-up — requires GOOGLE credentials via secret store."""
        cred = get_secret("GOOGLE_APPLICATION_CREDENTIALS") or get_secret("GOOGLE_CLIENT_ID")
        if not cred:
            log.warning("Gmail follow-up skipped: no Google credentials configured.")
            return False
        # Draft-and-send via Gmail API (google-api-python-client) — lazily wired.
        raise NotImplementedError("Wire Gmail API send using your credentials here.")

    def interview_invite(self, email: str, title: str, start_iso: str) -> bool:
        """Google Calendar event. Optional; requires Calendar API credentials."""
        if not get_secret("GOOGLE_CALENDAR_ID"):
            log.warning("Calendar invite skipped: no Google Calendar configured.")
            return False
        raise NotImplementedError("Wire Google Calendar API create-event here.")

    def sms(self, phone: str, body: str) -> bool:
        """Twilio SMS. Optional; requires Twilio credentials."""
        if not get_secret("TWILIO_ACCOUNT_SID"):
            log.warning("SMS skipped: no Twilio credentials configured.")
            return False
        raise NotImplementedError("Wire Twilio send (twilio python SDK) here.")

    def drain(self) -> list[Notification]:
        q, self._queue = self._queue, []
        return q
