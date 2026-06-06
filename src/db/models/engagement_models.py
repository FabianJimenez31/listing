"""ORM models for Favorite, AuditLog, and PropertyView."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from src.db.engine import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class FavoriteORM(Base):
    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "property_id", name="uq_favorite_user_property"),)

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    property_id = Column(String(36), ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    user = relationship("UserORM", back_populates="favorites")
    property = relationship("PropertyORM", back_populates="favorites")


class AuditLogORM(Base):
    """Append-only audit trail. Never update or delete rows."""

    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True)
    actor_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(String(36), nullable=False, index=True)
    action = Column(String(50), nullable=False, index=True)
    before_state = Column(JSON, nullable=True)
    after_state = Column(JSON, nullable=True)
    source_ip = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, index=True)

    actor = relationship("UserORM", foreign_keys=[actor_id])


class PropertyViewORM(Base):
    """Event store for property engagement metrics."""

    __tablename__ = "property_views"

    id = Column(String(36), primary_key=True)
    property_id = Column(String(36), ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)

    # Event classification
    event_type = Column(String(30), nullable=False, index=True)  # MetricEventType values
    source = Column(String(20), nullable=True)                   # ViewSource values

    # Privacy-safe fingerprints (HMAC-SHA256 of ip+session)
    session_hash = Column(String(64), nullable=True)

    utm = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, index=True)

    property = relationship("PropertyORM", back_populates="views")
