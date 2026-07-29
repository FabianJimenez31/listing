"""ORM model for login one-time passwords (email 2FA).

A short-lived 6-digit code issued after a valid email+password login for staff
accounts (admin/agent). The plaintext code is never stored — only its hash. The
client exchanges the code for JWT tokens at /auth/login/verify.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from src.db.engine import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class LoginOtpORM(Base):
    __tablename__ = "login_otps"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Hash of the 6-digit code (bcrypt, same hasher as passwords).
    code_hash = Column(String(255), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    attempts = Column(Integer, nullable=False, default=0)
    consumed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
