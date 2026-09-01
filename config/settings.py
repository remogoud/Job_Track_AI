"""
Job_Track_AI — Central configuration.

Loads settings from three sources, in increasing priority order:
  1. Built-in defaults
  2. `.env` file (repo-adjacent, git-ignored)
  3. Environment variables / Windows Credential Manager (not implemented here;
     see security/secrets.py for Credential Manager support)

Secrets are handled ONLY by security/secrets.py and never live in source.
"""
from __future__ import annotations

import os
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Default .env path (project root) + an override via env var.
ENV_PATH = Path(os.environ.get("JOBTRACK_ENV_FILE", PROJECT_ROOT / ".env"))

# Bare-minimum .env parser (no python-dotenv dependency keeps the .exe lean).
# Supports KEY=VALUE, comments (#), quoted values, and ${VAR} interpolation.
def _load_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        # ${VAR} interpolation
        if value.startswith("${") and value.endswith("}"):
            value = os.environ.get(value[2:-1], "")
        env[key] = value
    return env


@dataclass
class Settings:
    """Typed, immutable-by-convention application settings."""

    # --- Paths / storage -------------------------------------------------
    project_root: Path = PROJECT_ROOT
    db_path: Path = PROJECT_ROOT / "data" / "jobtrack.db"
    log_path: Path = PROJECT_ROOT / "logs" / "jobtrack.log"

    # --- Automation behaviour ---------------------------------------------
    automation_speed: str = "human"          # human | fast
    human_delay_min: float = 1.0
    human_delay_max: float = 3.5
    scroll_step: int = 3                     # scroll simulation granularity
    click_delay: float = 0.8

    # --- Matching threshold (spec: >= 77% proceed, else discard) ----------
    match_threshold: float = 0.77

    # --- Feature toggles ---------------------------------------------------
    enable_scraping_real_sites: bool = False  # OFF by default (legal risk)
    enable_voice: bool = False
    enable_cloud_sync: bool = False
    enable_self_diagnosis: bool = True
    enable_notifications: bool = True

    # --- Logging ------------------------------------------------------------
    log_level: str = "INFO"

    # --- Google Cloud (optional) -------------------------------------------
    gcp_project_id: str = ""
    gcp_service_account_key: str = ""
    gemini_api_key: str = ""

    # --- Scraping api keys (never logged) ------------------------------------
    linkedin_client_id: str = ""
    indeed_publisher_id: str = ""

    # --- Overrides loaded from .env -----------------------------------------
    _env: dict[str, str] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        self._env = _load_env(ENV_PATH)
        if not self.db_path.is_absolute():
            self.db_path = PROJECT_ROOT / self.db_path

        # Apply env overrides for behavioural settings.
        self.automation_speed = self._get("AUTOMATION_SPEED", self.automation_speed)
        self.log_level = self._get("LOG_LEVEL", self.log_level).upper()
        self.enable_scraping_real_sites = bool(self._strbool(
            "ENABLE_SCRAPING_REAL_SITES", self.enable_scraping_real_sites))
        self.enable_voice = bool(self._strbool("ENABLE_VOICE", self.enable_voice))
        self.enable_cloud_sync = bool(self._strbool("ENABLE_CLOUD_SYNC", self.enable_cloud_sync))
        self.match_threshold = float(self._get("MATCH_THRESHOLD", str(self.match_threshold)))
        self.gcp_project_id = self._get("GCP_PROJECT_ID", self.gcp_project_id)
        self.gemini_api_key = self._get("GEMINI_API_KEY", self.gemini_api_key)
        self.db_env = self._get("APP_DB_PATH", str(self.db_path))

    def _get(self, key: str, default: Any) -> Any:
        """Precedence: environment variable > .env file > default."""
        return os.environ.get(key, self._env.get(key, default))

    @staticmethod
    def _strbool(value: Any, default: bool) -> bool:
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "on"}

    @property
    def effective_db_path(self) -> Path:
        p = Path(self._get("APP_DB_PATH", str(self.db_path)))
        return p if p.is_absolute() else (PROJECT_ROOT / p)

    @property
    def is_humanlike(self) -> bool:
        return self.automation_speed.lower() == "human"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.pop("_env", None)
        return d

    def summarize(self) -> dict[str, Any]:
        """Safe summary for logging — never includes secret-bearing fields."""
        d = self.to_dict()
        return d


settings = Settings()
