"""ORM models for Project (real-estate development) and ProjectImage.

A Project represents a "Proyecto" in the portal: a new development sold on
plans / pre-sale, with a *price range* and *unit ranges* rather than a single
fixed property.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
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


class ProjectORM(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True)
    agency_id = Column(String(36), ForeignKey("agencies.id"), nullable=True, index=True)
    location_id = Column(String(36), ForeignKey("locations.id"), nullable=True, index=True)
    property_type_id = Column(String(36), ForeignKey("property_types.id"), nullable=True, index=True)

    developer_name = Column(String(200), nullable=True)
    title = Column(String(200), nullable=False)
    slug = Column(String(300), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Construction stage: preventa / construccion / entrega_inmediata
    stage = Column(String(30), nullable=False, default="preventa", index=True)
    # Publication lifecycle: draft / pending / published / paused / deleted
    status = Column(String(20), nullable=False, default="draft", index=True)

    # Price RANGE in BIGINT minor units + ISO 4217 currency ("Desde $X")
    price_from = Column(BigInteger, nullable=True)
    price_to = Column(BigInteger, nullable=True)
    currency = Column(String(3), nullable=False, default="COP")

    # Unit ranges (a project offers several typologies)
    bedrooms_min = Column(Integer, nullable=True)
    bedrooms_max = Column(Integer, nullable=True)
    bathrooms_min = Column(Integer, nullable=True)
    bathrooms_max = Column(Integer, nullable=True)
    area_min_m2 = Column(Float, nullable=True)
    area_max_m2 = Column(Float, nullable=True)

    total_units = Column(Integer, nullable=True)
    available_units = Column(Integer, nullable=True)
    delivery_date = Column(Date, nullable=True)

    address_street = Column(String(500), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_whatsapp = Column(String(50), nullable=True)

    cover_image_url = Column(String(1000), nullable=True)

    views_count = Column(Integer, default=0, nullable=False)
    leads_count = Column(Integer, default=0, nullable=False)

    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    agency = relationship("AgencyORM", back_populates="projects")
    location = relationship("LocationORM")
    property_type = relationship("PropertyTypeORM")
    images = relationship(
        "ProjectImageORM",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="ProjectImageORM.position",
    )


class ProjectImageORM(Base):
    __tablename__ = "project_images"

    id = Column(String(36), primary_key=True)
    project_id = Column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )

    role = Column(String(20), nullable=False, default="gallery")  # main / gallery
    position = Column(Integer, nullable=False, default=0)

    # storage_key set for uploaded files (so they can be removed); null for URL-only images
    storage_key = Column(String(500), nullable=True)
    cdn_url = Column(String(1000), nullable=False)
    thumb_url = Column(String(1000), nullable=True)
    alt_text = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    project = relationship("ProjectORM", back_populates="images")
