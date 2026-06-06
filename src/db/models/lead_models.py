"""ORM model for leads."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import relationship

from src.db.engine import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class LeadORM(Base):
    __tablename__ = "leads"

    id = Column(String(36), primary_key=True)
    property_id = Column(String(36), ForeignKey("properties.id"), nullable=False, index=True)
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)

    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    message = Column(Text, nullable=True)

    channel = Column(String(20), nullable=False)           # form / whatsapp / call / visit
    status = Column(String(20), nullable=False, default="new", index=True)  # new / contacted / …

    consent_given = Column(Boolean, default=False, nullable=False)
    consent_text = Column(Text, nullable=True)

    source_ip = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    utm = Column(JSON, nullable=True)

    contacted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)

    property = relationship("PropertyORM", back_populates="leads")
    owner = relationship("UserORM", back_populates="leads_assigned", foreign_keys=[owner_id])
