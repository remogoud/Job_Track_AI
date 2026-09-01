"""
Job_Track_AI - Password hashing.

Uses PBKDF2-HMAC-SHA256 (stdlib, no external dependency so the .exe stays lean)
with 600_000 iterations and a random per-password salt. If passlib/bcrypt is
installed and configured, it would be preferred; this fallback is secure by
default and requires nothing extra.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import base64

_ITERATIONS = 600_000
_ALGO = "sha256"


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(_ALGO, password.encode("utf-8"), salt, _ITERATIONS)
    salt_b64 = base64.b64encode(salt).decode("utf-8")
    hash_b64 = base64.b64encode(digest).decode("utf-8")
    return f"pbkdf2${_ITERATIONS}${salt_b64}${hash_b64}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, iterations, salt_b64, hash_b64 = stored.split("$")
        iterations = int(iterations)
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)
    except (ValueError, TypeError):
        return False
    digest = hashlib.pbkdf2_hmac(_ALGO, password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(digest, expected)
