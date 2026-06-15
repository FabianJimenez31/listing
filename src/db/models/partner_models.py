"""ORM model for Partner (allied agencies and developers shown on the home strip)."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from src.db.engine import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PartnerORM(Base):
    __tablename__ = "partners"

    id = Column(String(36), primary_key=True)
    name = Column(String(200), nullable=False)
    slug = Column(String(300), unique=True, nullable=False, index=True)
    logo_url = Column(String(1000), nullable=True)

    # inmobiliaria / constructora
    kind = Column(String(30), nullable=False, default="inmobiliaria")
    website = Column(String(500), nullable=True)

    priority = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
