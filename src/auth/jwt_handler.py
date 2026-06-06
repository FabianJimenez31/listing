"""JWT access and refresh token creation and decoding.

Uses HS256 via python-jose. Secrets and expiry are read from environment
variables so nothing is hardcoded.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

# Required in production; defaults used for local dev only.
_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "changeme-in-production-at-least-32-chars")
_ALGORITHM: str = "HS256"
_ACCESS_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_EXPIRE_MINUTES", "30"))
_REFRESH_EXPIRE_DAYS: int = int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "7"))


def _make_token(data: dict[str, Any], expires_delta: timedelta) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + expires_delta
    return jwt.encode(payload, _SECRET_KEY, algorithm=_ALGORITHM)


def create_access_token(user_id: str, email: str) -> str:
    return _make_token(
        {"sub": user_id, "email": email, "type": "access"},
        timedelta(minutes=_ACCESS_EXPIRE_MINUTES),
    )


def create_refresh_token(user_id: str) -> str:
    return _make_token(
        {"sub": user_id, "type": "refresh"},
        timedelta(days=_REFRESH_EXPIRE_DAYS),
    )


def decode_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT. Raises JWTError on failure."""
    return jwt.decode(token, _SECRET_KEY, algorithms=[_ALGORITHM])
