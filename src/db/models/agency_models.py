"""ORM model for Agency (inmobiliaria / real-estate agency)."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from src.db.engine import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AgencyORM(Base):
    __tablename__ = "agencies"

    id = Column(String(36), primary_key=True)
    name = Column(String(200), nullable=False)
    slug = Column(String(300), unique=True, nullable=False, index=True)

    # Short avatar fallback shown on cards (e.g. "EV" for Engel & Völkers)
    initials = Column(String(8), nullable=True)
    logo_url = Column(String(1000), nullable=True)
    description = Column(Text, nullable=True)

    # Contact
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    whatsapp = Column(String(50), nullable=True)
    website = Column(String(500), nullable=True)

    location_id = Column(String(36), ForeignKey("locations.id"), nullable=True, index=True)

    is_verified = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)

    location = relationship("LocationORM")
    properties = relationship("PropertyORM", back_populates="agency")
    projects = relationship("ProjectORM", back_populates="agency")
