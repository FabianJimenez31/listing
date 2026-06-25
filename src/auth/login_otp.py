"""Email 2FA for staff logins — issue and verify one-time codes.

Gated behind OTP_2FA_ENABLED (default off, so deploying the feature never locks
anyone out). When on, admin/agent logins require a 6-digit code emailed to the
account; public/registered users are unaffected.
"""
from __future__ import annotations

import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from src.auth.password import hash_password, verify_password
from src.db.models.login_otp_models import LoginOtpORM
from src.db.models.user_models import UserORM
from src.notifications.email_sender import send_email

STAFF_ROLES = {"ADMIN", "AGENT"}
CODE_TTL_MINUTES = 10
MAX_ATTEMPTS = 5


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def otp_2fa_enabled() -> bool:
    return os.getenv("OTP_2FA_ENABLED", "false").strip().lower() in ("1", "true", "yes", "on")


def user_requires_otp(user: UserORM) -> bool:
    """True when 2FA is on and the user holds a staff role (admin/agent)."""
    if not otp_2fa_enabled():
        return False
    return bool({role.name for role in user.roles} & STAFF_ROLES)


def generate_code() -> str:
    """A 6-digit numeric code. Separated out so tests can monkeypatch it."""
    return f"{secrets.randbelow(1_000_000):06d}"


def _send_code_email(email: str, code: str) -> None:
    send_email(
        to=email,
        subject="Tu código de acceso a Proppietario",
        body=(
            f"Tu código de verificación es: {code}\n\n"
            f"Vence en {CODE_TTL_MINUTES} minutos. "
            "Si no intentaste iniciar sesión, ignora este correo."
        ),
    )


def issue_challenge(db: Session, user: UserORM) -> str:
    """Create a fresh OTP for the user, email it, and return the challenge id.

    Any previous unconsumed challenge for the user is discarded. SMTP failures
    propagate so the caller can return a 5xx (and nothing is committed).
    """
    db.query(LoginOtpORM).filter(
        LoginOtpORM.user_id == user.id, LoginOtpORM.consumed_at.is_(None)
    ).delete(synchronize_session=False)

    code = generate_code()
    challenge = LoginOtpORM(
        id=str(uuid.uuid4()),
        user_id=user.id,
        code_hash=hash_password(code),
        expires_at=_utcnow() + timedelta(minutes=CODE_TTL_MINUTES),
        attempts=0,
    )
    db.add(challenge)
    db.flush()
    _send_code_email(user.email, code)
    db.commit()
    return challenge.id


def verify_challenge(db: Session, challenge_id: str, code: str) -> UserORM | None:
    """Return the user when the code is valid; otherwise None (and count the try)."""
    challenge = db.get(LoginOtpORM, challenge_id)
    if challenge is None or challenge.consumed_at is not None:
        return None

    expires_at = challenge.expires_at
    if expires_at.tzinfo is None:  # SQLite returns naive datetimes
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < _utcnow() or challenge.attempts >= MAX_ATTEMPTS:
        return None

    if not verify_password(code, challenge.code_hash):
        challenge.attempts += 1
        db.commit()
        return None

    challenge.consumed_at = _utcnow()
    db.commit()
    return db.get(UserORM, challenge.user_id)
