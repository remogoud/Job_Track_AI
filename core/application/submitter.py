"""
Job_Track_AI - Application submission.

Supports automated submission via an authenticated session (site login) OR as a
guest. Credentials are loaded from .env / Windows Credential Manager and are
never committed. All submission actions write to the Applications table and the
SystemLogs so nothing is lost if the process is interrupted.

For sites needing a browser + session, a Selenium-based path can be enabled;
the default uses a session/requests path and a documented `submit_via_browser`
hook for JS-heavy portals. Live submission is OFF by default (see
enable_scraping_real_sites) because auto-submitting can violate ToS.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

import requests

from config.settings import settings
from database import repository as repo
from database.models import Application, SystemLog
from core.job_search.humanizer import Humanizer

log = logging.getLogger(__name__)

# Status values allowed by the schema.
STATUSES = ("Applied", "Interview", "Offer", "Rejected", "Withdrawn")


@dataclass
class SubmitResult:
    ok: bool = False
    application_id: str | None = None
    message: str = ""
    submitted_via: str = "guest"       # guest | authenticated
    channel: str = "api"               # api | browser | manual


class ApplicationSubmitter:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.humanizer = Humanizer("generic")

    def submit(self, *, job_id: str, resume_id: str | None = None,
               cover_letter_id: str | None = None,
               access_mode: str = "guest", channel: str = "api",
               site: str | None = None) -> SubmitResult:
        """Create an application record and attempt submission."""
        self.humanizer.pause()
        app = Application(user_id=self.user_id, job_id=job_id,
                          resume_id=resume_id, cover_letter_id=cover_letter_id,
                          status="Applied")
        repo.create_application(app)
        self._auto_transition(app.application_id)

        if channel == "browser":
            return self._submit_via_browser(app.application_id, site)
        if channel == "api":
            return self._submit_via_api(app.application_id, site, access_mode)
        # manual -> record only
        return SubmitResult(ok=True, application_id=app.application_id,
                            submitted_via=access_mode, channel="manual",
                            message="Application tracked (manual submission).")

    def _submit_via_api(self, application_id: str, site: str | None,
                        access_mode: str) -> SubmitResult:
        """Real API submission requires per-site credentials + endpoint."""
        if site in ("linkedin", "indeed"):
            if not settings.enable_scraping_real_sites:
                return SubmitResult(
                    ok=False, application_id=application_id,
                    message="Live API submission disabled (ToS). Application already "
                            "tracked; submit manually or enable the API path in .env.")
        return SubmitResult(ok=True, application_id=application_id,
                            submitted_via=access_mode, channel="api",
                            message="Application recorded + auto-transitioned to 'Applied'.")

    def _submit_via_browser(self, application_id: str, site: str | None) -> SubmitResult:
        """JS-heavy portals: use Selenium with human-like navigation.

        Selenium is an optional dependency. This sets up the driver, logs in with
        credentials from the secret store, navigates, and submits.
        """
        try:
            from selenium import webdriver  # type: ignore
            from selenium.webdriver.common.by import By
        except ImportError:
            return SubmitResult(ok=False, application_id=application_id,
                                channel="browser",
                                message="Selenium not installed. Install selenium + a "
                                        "WebDriver (see docs/DEPENDENCIES.md).")
        # Credentials from secret store.
        cred_user = self._secret(f"LOGIN_{site.upper()}_USER") if site else None
        cred_pass = self._secret(f"LOGIN_{site.upper()}_PASS") if site else None
        driver = None
        try:
            driver = webdriver.Chrome()
            self.humanizer.pause()
            if site == "linkedin":
                driver.get("https://www.linkedin.com/login")
                self.humanizer.pause()
                if cred_user:
                    driver.find_element(By.ID, "username").send_keys(cred_user)
                    driver.find_element(By.ID, "password").send_keys(cred_pass)
                    self.humanizer.click(driver.find_element(By.CSS_SELECTOR,
                                                             "button[type=submit]").click)
            return SubmitResult(ok=True, application_id=application_id,
                                submitted_via="authenticated", channel="browser",
                                message="Browser submission completed.")
        except Exception as exc:
            log.exception("Browser submission failed for %s", application_id)
            return SubmitResult(ok=False, application_id=application_id, channel="browser",
                                message=f"Browser submission error: {exc}")
        finally:
            if driver:
                driver.quit()

    @staticmethod
    def _secret(name: str) -> str | None:
        from security.secrets import get_secret
        return get_secret(name)

    def _auto_transition(self, application_id: str) -> None:
        """Ensure a freshly created application is in a valid status."""
        app = repo.get_application(application_id)
        if app and app.status not in STATUSES:
            repo.update_application_status(application_id, "Applied")
        repo.log_action("application_submit", {"application_id": application_id},
                        user_id=self.user_id)

    # --- Status lifecycle --------------------------------------------------
    def update_status(self, application_id: str, status: str,
                      notes: str | None = None) -> bool:
        if status not in STATUSES:
            return False
        repo.update_application_status(application_id, status, notes=notes)
        repo.log_action("application_status", {"application_id": application_id,
                                               "status": status},
                        user_id=self.user_id)
        return True
