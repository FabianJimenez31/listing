"""ORM model for SeoMetadata (polymorphic entity SEO data)."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Index, JSON, String, Text
from sqlalchemy.orm import declared_attr

from src.db.engine import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SeoMetadataORM(Base):
    __tablename__ = "seo_metadata"
    __table_args__ = (
        Index("ix_seo_entity", "entity_type", "entity_id", unique=True),
    )

    id = Column(String(36), primary_key=True)

    # Polymorphic FK (entity_type = "property" | "location" | "page")
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(36), nullable=False)

    meta_title = Column(String(70), nullable=True)
    meta_description = Column(String(160), nullable=True)
    og_title = Column(String(70), nullable=True)
    og_description = Column(String(160), nullable=True)
    og_image_url = Column(String(1000), nullable=True)

    canonical_url = Column(String(1000), nullable=True)
    robots = Column(String(100), default="index,follow", nullable=False)

    # JSON-LD schema.org object (schema_org is reserved, so we use jsonld)
    jsonld = Column(JSON, nullable=True)

    # Array of old slugs that redirect to the canonical (stored as JSON array)
    redirect_from = Column(JSON, nullable=True)

    is_noindex = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
