"""
Job_Track_AI — Optional Cloud sync (Google Cloud SQL / Firestore).

This module is entirely OPTIONAL and gated behind settings.enable_cloud_sync.
It provides the migration target for the hybrid model: local SQLite stays the
source of truth for offline control; GCP provides scalability + integration
with Gemini, Calendar, Gmail and Drive.

All GCP credentials come from .env / Credential Manager (GCP_SERVICE_ACCOUNT_KEY,
GCP_PROJECT_ID). This module imports GCP libs lazily so the local-only .exe does
not require them.
"""
from __future__ import annotations

import logging
from typing import Any

from config.settings import settings
from security.secrets import get_secret

log = logging.getLogger(__name__)


class CloudSync:
    """Facade over optional Firestore sync. No-op unless enabled."""
    def __init__(self):
        enabled = getattr(settings, "enable_cloud_sync", False)
        self.enabled = False
        if enabled:
            self._init_firestore()

    def _init_firestore(self) -> None:
        try:
            from google.cloud import firestore  # type: ignore
            cred_path = get_secret("GCP_SERVICE_ACCOUNT_KEY") or settings.gcp_service_account_key
            if cred_path:
                self._client = firestore.Client.from_service_account_json(cred_path)
            else:
                self._client = firestore.Client(project=settings.gcp_project_id)
            self.enabled = True
            log.info("Cloud sync enabled (Firestore).")
        except Exception as exc:  # pragma: no cover - optional dependency
            log.warning("Cloud sync unavailable (install google-cloud-firestore "
                        "and provide creds): %s", exc)
            self._client = None

    def push(self, collection: str, doc_id: str, data: dict[str, Any]) -> bool:
        if not self.enabled:
            return False
        try:
            self._client.collection(collection).document(doc_id).set(data)
            return True
        except Exception as exc:
            log.error("Cloud push failed for %s/%s: %s", collection, doc_id, exc)
            return False

    def pull(self, collection: str, doc_id: str) -> dict[str, Any] | None:
        if not self.enabled:
            return None
        try:
            doc = self._client.collection(collection).document(doc_id).get()
            return doc.to_dict()
        except Exception as exc:
            log.error("Cloud pull failed for %s/%s: %s", collection, doc_id, exc)
            return None
