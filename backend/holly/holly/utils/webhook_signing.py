"""Helpers for signing and verifying container -> Django webhook callbacks.

Each container is provisioned with a *per-mission* token derived from a single
server-side secret (``CONTAINER_WEBHOOK_SECRET``). The container signs the raw
request body with that token; Django re-derives the expected token from the
mission id in the payload and verifies the signature. This prevents unauthenticated
callers from forging mission/job status updates, and limits a compromised
container to forging updates for its own mission only.
"""

from __future__ import annotations

import hashlib
import hmac

from django.conf import settings

SIGNATURE_HEADER = "X-Holly-Signature"
_SIGNATURE_PREFIX = "sha256="


def mission_webhook_token(mission_id: str) -> str:
    """Derive the per-mission webhook token handed to a container."""
    secret = settings.CONTAINER_WEBHOOK_SECRET.encode()
    return hmac.new(secret, str(mission_id).encode(), hashlib.sha256).hexdigest()


def sign_body(token: str, body: bytes) -> str:
    """Return the ``sha256=...`` signature for ``body`` using ``token``."""
    digest = hmac.new(token.encode(), body, hashlib.sha256).hexdigest()
    return f"{_SIGNATURE_PREFIX}{digest}"


def verify_signature(mission_id: str, body: bytes, signature: str | None) -> bool:
    """Constant-time verify a webhook signature for the given mission."""
    if not signature:
        return False
    expected = sign_body(mission_webhook_token(mission_id), body)
    return hmac.compare_digest(expected, signature)
