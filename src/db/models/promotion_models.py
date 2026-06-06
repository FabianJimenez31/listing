"""ORM models for Banner and FeaturedProperty."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from src.db.engine import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BannerORM(Base):
    __tablename__ = "banners"

    id = Column(String(36), primary_key=True)
    title = Column(String(255), nullable=False)

    # Positions: home_hero / home_inline / listing_top / listing_inline / detail_sidebar
    position = Column(String(50), nullable=False, index=True)

    image_desktop_url = Column(String(1000), nullable=False)
    image_mobile_url = Column(String(1000), nullable=True)
    cta_url = Column(String(1000), nullable=True)
    cta_text = Column(String(255), nullable=True)

    # Segmentation (all optional; NULL = not filtered by this dimension)
    locality_id = Column(String(36), ForeignKey("locations.id"), nullable=True, index=True)
    operation_type = Column(String(20), nullable=True)  # sale / rent / temporary
    property_kind = Column(String(30), nullable=True)

    priority = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    starts_at = Column(DateTime(timezone=True), nullable=True)
    ends_at = Column(DateTime(timezone=True), nullable=True)

    # Denormalized click/impression counters
    impressions_count = Column(Integer, default=0, nullable=False)
    clicks_count = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)

    locality = relationship("LocationORM", back_populates="banners")


class FeaturedPropertyORM(Base):
    __tablename__ = "featured_properties"

    id = Column(String(36), primary_key=True)
    property_id = Column(String(36), ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)

    # Scopes: home / search_results / locality
    scope = Column(String(30), nullable=False, index=True)
    locality_id = Column(String(36), ForeignKey("locations.id"), nullable=True, index=True)

    priority = Column(Integer, default=0, nullable=False)

    starts_at = Column(DateTime(timezone=True), nullable=False)
    ends_at = Column(DateTime(timezone=True), nullable=False)

    created_by_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    property = relationship("PropertyORM", back_populates="featured_entries")
    locality = relationship("LocationORM", back_populates="featured")
    created_by = relationship("UserORM", foreign_keys=[created_by_id])
