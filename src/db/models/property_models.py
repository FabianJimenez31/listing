"""ORM models for Property and PropertyImage."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from src.db.engine import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PropertyORM(Base):
    __tablename__ = "properties"

    id = Column(String(36), primary_key=True)
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    location_id = Column(String(36), ForeignKey("locations.id"), nullable=True, index=True)
    property_type_id = Column(String(36), ForeignKey("property_types.id"), nullable=True, index=True)

    title = Column(String(200), nullable=False)
    slug = Column(String(300), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Operation & classification
    operation_type = Column(String(20), nullable=False)   # sale / rent / temporary
    property_kind = Column(String(30), nullable=False)    # house / apartment / lot / …
    condition = Column(String(30), nullable=True)         # new / used / remodeled / under_construction

    # Price: BIGINT minor units (cents) + ISO 4217 currency
    price_amount = Column(BigInteger, nullable=False)
    currency = Column(String(3), nullable=False, default="USD")

    # Dimensions
    total_area_m2 = Column(Float, nullable=True)
    built_area_m2 = Column(Float, nullable=True)
    bedrooms = Column(Integer, nullable=True)
    bathrooms = Column(Integer, nullable=True)
    parking_spots = Column(Integer, nullable=True)
    floor_number = Column(Integer, nullable=True)
    total_floors = Column(Integer, nullable=True)

    # Address (denormalized from Location)
    address_street = Column(String(500), nullable=True)
    address_detail = Column(String(500), nullable=True)

    # Publication lifecycle
    status = Column(String(20), nullable=False, default="draft", index=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(Date, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # Contact overrides (optional; agent's profile used if absent)
    contact_phone = Column(String(50), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_whatsapp = Column(String(50), nullable=True)

    # Denormalized metrics (updated by async workers)
    views_count = Column(Integer, default=0, nullable=False)
    leads_count = Column(Integer, default=0, nullable=False)
    favorites_count = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    owner = relationship("UserORM", back_populates="properties", foreign_keys=[owner_id])
    location = relationship("LocationORM", back_populates="properties")
    property_type = relationship("PropertyTypeORM", back_populates="properties")
    images = relationship("PropertyImageORM", back_populates="property", cascade="all, delete-orphan", order_by="PropertyImageORM.position")
    property_amenities = relationship("PropertyAmenityORM", back_populates="property", cascade="all, delete-orphan")
    leads = relationship("LeadORM", back_populates="property")
    favorites = relationship("FavoriteORM", back_populates="property")
    seo_metadata = relationship("SeoMetadataORM", primaryjoin="and_(SeoMetadataORM.entity_type=='property', foreign(SeoMetadataORM.entity_id)==PropertyORM.id)", uselist=False, viewonly=True)
    featured_entries = relationship("FeaturedPropertyORM", back_populates="property")
    views = relationship("PropertyViewORM", back_populates="property")
    audit_logs = relationship("AuditLogORM", primaryjoin="and_(AuditLogORM.entity_type=='property', foreign(AuditLogORM.entity_id)==PropertyORM.id)", viewonly=True)


class PropertyImageORM(Base):
    __tablename__ = "property_images"

    id = Column(String(36), primary_key=True)
    property_id = Column(String(36), ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)

    role = Column(String(20), nullable=False, default="gallery")  # main / gallery
    media_kind = Column(String(20), nullable=False, default="image")  # image / video / floor_plan / virtual_tour
    position = Column(Integer, nullable=False, default=0)

    storage_key = Column(String(500), nullable=False)
    cdn_url = Column(String(1000), nullable=True)
    thumb_url = Column(String(1000), nullable=True)

    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    bytes = Column(Integer, nullable=True)
    content_type = Column(String(100), nullable=True)
    alt_text = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    property = relationship("PropertyORM", back_populates="images")
