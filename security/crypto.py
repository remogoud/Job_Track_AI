"""
Job_Track_AI — AES-256-GCM encryption for sensitive fields (e.g. email).

Keys come exclusively from APP_ENCRYPTION_KEY in .env / Credential Manager.
If no key is configured, an ephemeral per-session key is derived from the
machine hostname + a warning is logged. For real deployments always set a
persistent key so encrypted data survives restarts.
"""
from __future__ import annotations

import os
import base64
import hashlib
import logging
import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from config.settings import settings
from security.secrets import get_secret

log = logging.getLogger(__name__)
AESGCM_KEYLEN = 32  # bytes


def _load_key() -> bytes:
    raw = get_secret("APP_ENCRYPTION_KEY")
    if raw:
        return hashlib.sha256(raw.encode("utf-8")).digest()[:AESGCM_KEYLEN]
    # Ephemeral fallback (warn loudly — data won't decrypt across restarts).
    machine = os.environ.get("COMPUTERNAME", "jobtrack")
    log.warning("APP_ENCRYPTION_KEY not set — using ephemeral session key. "
                "Set it in .env for persistent encryption.")
    return hashlib.sha256(f"ephemeral-{machine}-{settings.project_root}".encode()).digest()[:AESGCM_KEYLEN]


def encrypt(plaintext: str) -> str:
    """Return base64(nonce + ciphertext+tag)."""
    if not plaintext:
        return ""
    nonce = secrets.token_bytes(12)
    cipher = AESGCM(_load_key())
    ct = cipher.encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.b64encode(nonce + ct).decode("utf-8")


def decrypt(payload: str) -> str | None:
    if not payload:
        return None
    try:
        blob = base64.b64decode(payload)
        nonce, ct = blob[:12], blob[12:]
        cipher = AESGCM(_load_key())
        return cipher.decrypt(nonce, ct, None).decode("utf-8")
    except Exception:
        log.exception("Decryption failed — key mismatch or corrupted data.")
        return None
