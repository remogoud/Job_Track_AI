"""
Job_Track_AI - Secret retrieval.

Priority order:
  1. Windows Credential Manager (if available) - most secure on Windows.
  2. Environment variables.
  3. `.env` file (git-ignored).

NEVER hard-code secrets. This module deliberately refuses to log or expose
secret *values* - only presence/absence booleans.
"""
from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Optional

from config.settings import settings

log = logging.getLogger(__name__)

# Cache so we don't re-read files repeatedly.
_env_cache: dict[str, str] | None = None


def _load_env_file() -> dict[str, str]:
    global _env_cache
    if _env_cache is None:
        path = settings.project_root / ".env"
        env: dict[str, str] = {}
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip().strip('"').strip("'")
        _env_cache = env
    return _env_cache


def _credential_manager_get(service: str, key: str) -> Optional[str]:
    """Best-effort Windows Credential Manager lookup. Returns None if unavailable."""
    try:
        import win32cred  # type: ignore
        blob = win32cred.CredRead(
            f"{service}/{key}", win32cred.CRED_TYPE_GENERIC, 0)
        if blob and blob["CredentialBlob"]:
            return blob["CredentialBlob"].decode("utf-8").strip("\x00").strip()
    except Exception:
        return None
    return None


def get_secret(name: str, service: str = "JobTrackAI") -> Optional[str]:
    """Retrieve a secret by name across all sources. Never logs the value."""
    # 1) Windows Credential Manager
    try:
        value = _credential_manager_get(service, name)
        if value:
            return value
    except Exception:
        pass
    # 2) Environment variable
    value = os.environ.get(name)
    if value:
        return value
    # 3) .env file
    value = _load_env_file().get(name)
    if value:
        return value
    return None


def has_secret(name: str, service: str = "JobTrackAI") -> bool:
    return get_secret(name, service) is not None


def require_secret(name: str, service: str = "JobTrackAI") -> str:
    value = get_secret(name, service)
    if not value:
        raise RuntimeError(f"Missing required secret: {name} (set it in .env or "
                           f"Windows Credential Manager).")
    return value


# Convenience accessors -----------------------------------------------------
def github_pat() -> Optional[str]:
    return get_secret("GITHUB_PAT")


def gemini_key() -> Optional[str]:
    return get_secret("GEMINI_API_KEY")


def linkedin_access_token() -> Optional[str]:
    return get_secret("LINKEDIN_ACCESS_TOKEN")
