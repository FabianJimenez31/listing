"""ORM models for administrable catalogs: PropertyType, Amenity, PropertyAmenity."""
from __future__ import annotations

from sqlalchemy import Boolean, Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from src.db.engine import Base


class PropertyTypeORM(Base):
    __tablename__ = "property_types"

    id = Column(String(36), primary_key=True)
    # code maps to PropertyKind enum values (house, apartment, lot, …)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    icon = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    properties = relationship("PropertyORM", back_populates="property_type")


class AmenityORM(Base):
    __tablename__ = "amenities"

    id = Column(String(36), primary_key=True)
    code = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)
    icon = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    property_amenities = relationship("PropertyAmenityORM", back_populates="amenity")


class PropertyAmenityORM(Base):
    __tablename__ = "property_amenities"

    property_id = Column(String(36), ForeignKey("properties.id", ondelete="CASCADE"), primary_key=True)
    amenity_id = Column(String(36), ForeignKey("amenities.id", ondelete="CASCADE"), primary_key=True)
    # Optional freeform value (e.g. "2" for "2 parking spots")
    value = Column(String(255), nullable=True)

    property = relationship("PropertyORM", back_populates="property_amenities")
    amenity = relationship("AmenityORM", back_populates="property_amenities")
