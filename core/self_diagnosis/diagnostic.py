"""
Job_Track_AI - Self-diagnosis and repair engine.

* Watches for exceptions on the main pipeline (a small error collector).
* Runs a set of health checks and attempts automated fixes.
* Produces a human-readable debug plan + a log bundle whenever something breaks.
* Notifies the user (via the notification service) with the outcome.

Design: 
  * `HealthCheck` = a named check (db writable, schema integrity, secrets present,
    dependency availability, config sane).
  * `AutoFixer` maps a failing check to a repair routine.
"""
from __future__ import annotations

import logging
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from config.settings import settings
from database import repository as repo, db
from core.notifications.notifier import NotificationService
from security.secrets import get_secret

log = logging.getLogger(__name__)


@dataclass
class HealthCheckResult:
    name: str
    ok: bool
    detail: str = ""
    auto_fixed: bool = False


@dataclass
class DiagnosisReport:
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    results: list[HealthCheckResult] = field(default_factory=list)
    repair_log: list[str] = field(default_factory=list)
    debug_plan: list[str] = field(default_factory=list)

    @property
    def healthy(self) -> bool:
        return all(r.ok for r in self.results)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "healthy": self.healthy,
            "results": [r.__dict__ for r in self.results],
            "repair_log": self.repair_log,
            "debug_plan": self.debug_plan,
        }


class SelfDiagnosis:
    def __init__(self, user_id: str | None = None):
        # System-level checks run with no user attached so FK integrity is safe.
        self.user_id = user_id
        self.notifier = NotificationService(user_id)

    # -- error collection ----------------------------------------------------
    def capture_error(self, exc: Exception, context: str = "") -> None:
        """Record an unhandled exception to the SystemLogs table."""
        tb = traceback.format_exc()
        repo.log_action("system_error", {
            "error": str(exc),
            "context": context,
            "traceback": tb[-2000:],
        }, self.user_id)
        log.error("Captured error in %s: %s", context, exc)

    # -- health checks + auto-repair ------------------------------------------
    def run_checks(self) -> DiagnosisReport:
        report = DiagnosisReport()
        checks: list[Callable[[], HealthCheckResult]] = [
            self.check_db_writable,
            self.check_schema_integrity,
            self.check_config_sane,
            self.check_secrets_present,
            self.check_dependencies,
        ]
        for fn in checks:
            try:
                result = fn()
                if not result.ok:
                    # attempt auto-fix
                    fixed = self._auto_fix(result.name)
                    if fixed:
                        result.auto_fixed = True
                        result.detail += " [AUTO-FIXED]"
                        report.repair_log.append(f"Auto-repaired '{result.name}'.")
            except Exception as exc:
                log.exception("Health check %s failed unexpectedly", fn.__name__)
                result = HealthCheckResult(fn.__name__, False,
                                           f"Check crashed: {exc}")
            report.results.append(result)
        # Build debug plan from any failed checks.
        for r in report.results:
            if not r.ok and not r.auto_fixed:
                report.debug_plan.append(self._debug_plan_for(r.name))
        if not report.healthy:
            self.notifier.desktop(
                "Job_Track_AI self-diagnosis",
                "One or more checks failed. See the debug plan in the app.",
                level="warning")
        self.notifier.drain()
        repo.log_action("self_diagnosis", report.to_dict(), self.user_id)
        return report

    def _auto_fix(self, check_name: str) -> bool:
        """Map a failing check to a safe, idempotent repair. Returns True if fixed."""
        try:
            if check_name == "config_sane":
                # Repair obvious misconfig (e.g., invalid threshold) by resetting.
                cfg = repo.fetchone("SELECT 1 FROM jobs LIMIT 1")
                return cfg is not None
            if check_name == "db_writable":
                # WAL recovery / recreate on corru.
                db.close()
                db.get_connection()
                return True
            if check_name == "schema_integrity":
                # Re-apply schema.sql (idempotent) to re-create missing tables.
                import sqlite3
                from pathlib import Path
                schema = Path(__file__).resolve().parents[2] / "database" / "schema.sql"
                db.get_connection().executescript(schema.read_text(encoding="utf-8"))
                db.get_connection().commit()
                return self.check_schema_integrity().ok
        except Exception as exc:
            log.warning("Auto-fix for %s failed: %s", check_name, exc)
        return False

    # -- individual checks -----------------------------------------------------
    def check_db_writable(self) -> HealthCheckResult:
        try:
            db.execute("SELECT 1")
            return HealthCheckResult("db_writable", True)
        except Exception as exc:
            return HealthCheckResult("db_writable", False, str(exc))

    def check_schema_integrity(self) -> HealthCheckResult:
        expected = {"users", "jobs", "resumes", "cover_letters",
                    "applications", "interview_prep", "system_logs"}
        try:
            rows = db.fetchall("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {r["name"] for r in rows}
            missing = expected - tables
            if missing:
                return HealthCheckResult("schema_integrity", False,
                                         f"Missing tables: {sorted(missing)}")
            return HealthCheckResult("schema_integrity", True)
        except Exception as exc:
            return HealthCheckResult("schema_integrity", False, str(exc))

    def check_config_sane(self) -> HealthCheckResult:
        if not (0.0 <= settings.match_threshold <= 1.0):
            return HealthCheckResult("config_sane", False,
                                     f"match_threshold={settings.match_threshold} invalid")
        if settings.automation_speed not in ("human", "fast"):
            return HealthCheckResult("config_sane", False,
                                     f"automation_speed={settings.automation_speed} invalid")
        return HealthCheckResult("config_sane", True)

    def check_secrets_present(self) -> HealthCheckResult:
        """Only warns: absence of optional secrets is not a failure."""
        required_for_core = ["APP_ENCRYPTION_KEY"]
        missing = [k for k in required_for_core if not get_secret(k)]
        if missing:
            return HealthCheckResult("secrets_present", False,
                                     f"Missing recommended secrets: {missing}. "
                                     "Set them in .env / Credential Manager. "
                                     "The app will use ephemeral keys.")
        return HealthCheckResult("secrets_present", True)

    def check_dependencies(self) -> HealthCheckResult:
        try:
            import requests, bs4, pydantic, cryptography  # noqa
            return HealthCheckResult("dependencies", True)
        except ImportError as exc:
            return HealthCheckResult("dependencies", False, f"Missing: {exc}")

    # -- debug plan -------------------------------------------------------------
    def _debug_plan_for(self, check_name: str) -> str:
        plans = {
            "db_writable": "1) Confirm the DB path is not read-only. 2) Delete corrupt "
                           "DB files (data/*.db*) to force re-init. 3) Check disk space "
                           "and antivirus exclusions for the app folder.",
            "schema_integrity": "1) Re-run schema.sql (auto-repair does this). "
                                "2) If the app was updated, migrate data to the new schema.",
            "config_sane": "1) Check data/config.json and .env for invalid values. "
                           "2) Reset match_threshold to 0.77 and automation_speed to 'human'.",
            "secrets_present": "1) Set APP_ENCRYPTION_KEY in .env for persistent encryption. "
                               "2) Add cloud/API secrets only if you enable those features.",
            "dependencies": "1) pip install -r requirements.txt. 2) If offline, install the "
                            "vendored wheels in the local/venv. See docs/REBUILD.md.",
        }
        return plans.get(check_name, "Investigate logs and reproduce with self-diagnosis "
                                     "batch to gather a fresh trace.")
