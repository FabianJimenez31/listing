"""ORM model for hierarchical locations."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from src.db.engine import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class LocationORM(Base):
    __tablename__ = "locations"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    # Level: country / state / city / locality / neighborhood
    level = Column(String(50), nullable=False)
    parent_id = Column(String(36), ForeignKey("locations.id"), nullable=True, index=True)
    # Coordinates (lat/lng stored as floats; PostGIS GEOGRAPHY added via Alembic for production)
    center_lat = Column(Float, nullable=True)
    center_lng = Column(Float, nullable=True)
    # Cover photo for "Explora por ciudad" cards
    image_url = Column(String(1000), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)

    parent = relationship("LocationORM", remote_side="LocationORM.id", back_populates="children")
    children = relationship("LocationORM", back_populates="parent")
    properties = relationship("PropertyORM", back_populates="location")
    banners = relationship("BannerORM", back_populates="locality")
    featured = relationship("FeaturedPropertyORM", back_populates="locality")

    @property
    def path(self) -> list["LocationORM"]:
        """Ancestor chain from root to this node (e.g. Colombia → Bogotá → Chapinero).

        Used to render breadcrumbs on the property detail. Walks ``parent`` (a
        handful of lazy loads for a single property); the ``seen`` guard avoids
        an infinite loop if the data ever contains a cycle.
        """
        chain: list[LocationORM] = []
        node: LocationORM | None = self
        seen: set[str] = set()
        while node is not None and node.id not in seen:
            seen.add(node.id)
            chain.append(node)
            node = node.parent
        return list(reversed(chain))
