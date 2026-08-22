"""ORM models for virtual tours, scenes, hotspots, and AI generation attempts."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from src.db.engine import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class VirtualTourORM(Base):
    __tablename__ = "virtual_tours"
    __table_args__ = (
        CheckConstraint(
            "(property_id IS NOT NULL AND project_id IS NULL) OR "
            "(property_id IS NULL AND project_id IS NOT NULL)",
            name="ck_virtual_tours_single_owner",
        ),
        Index(
            "uq_virtual_tours_property_id",
            "property_id",
            unique=True,
            postgresql_where=Column("property_id").is_not(None),
            sqlite_where=Column("property_id").is_not(None),
        ),
        Index(
            "uq_virtual_tours_project_id",
            "project_id",
            unique=True,
            postgresql_where=Column("project_id").is_not(None),
            sqlite_where=Column("project_id").is_not(None),
        ),
    )

    id = Column(String(36), primary_key=True)
    property_id = Column(
        String(36), ForeignKey("properties.id", ondelete="CASCADE"), nullable=True
    )
    project_id = Column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True
    )
    status = Column(String(20), nullable=False, default="draft", index=True)
    start_scene_id = Column(String(36), nullable=True)
    ai_disclaimer_ack = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    scenes = relationship(
        "VirtualTourSceneORM",
        back_populates="tour",
        cascade="all, delete-orphan",
        order_by="VirtualTourSceneORM.position",
    )


class VirtualTourSceneORM(Base):
    __tablename__ = "virtual_tour_scenes"

    id = Column(String(36), primary_key=True)
    tour_id = Column(
        String(36), ForeignKey("virtual_tours.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title = Column(String(120), nullable=False)
    position = Column(Integer, nullable=False, default=0)
    source = Column(String(10), nullable=False, default="upload")
    state = Column(String(10), nullable=False, default="ready", index=True)
    error_message = Column(String(500), nullable=True)
    storage_key = Column(String(500), nullable=True)
    thumb_storage_key = Column(String(500), nullable=True)
    pano_url = Column(String(1000), nullable=True)
    thumb_url = Column(String(1000), nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    initial_yaw = Column(Float, nullable=False, default=0.0)
    initial_pitch = Column(Float, nullable=False, default=0.0)
    hfov_deg = Column(Float, nullable=False, default=360.0)
    vfov_deg = Column(Float, nullable=False, default=180.0)
    source_image_ids = Column(JSON, nullable=True)
    provider = Column(String(60), nullable=True)
    provider_model = Column(String(80), nullable=True)
    cost_usd = Column(Numeric(10, 5), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    tour = relationship("VirtualTourORM", back_populates="scenes")
    hotspots = relationship(
        "VirtualTourHotspotORM",
        foreign_keys="VirtualTourHotspotORM.from_scene_id",
        back_populates="from_scene",
        cascade="all, delete-orphan",
    )
    incoming_hotspots = relationship(
        "VirtualTourHotspotORM",
        foreign_keys="VirtualTourHotspotORM.to_scene_id",
        back_populates="to_scene",
        cascade="all, delete-orphan",
    )
    generation_attempts = relationship(
        "VirtualTourGenerationAttemptORM",
        back_populates="scene",
        cascade="all, delete-orphan",
    )


class VirtualTourHotspotORM(Base):
    __tablename__ = "virtual_tour_hotspots"

    id = Column(String(36), primary_key=True)
    from_scene_id = Column(
        String(36),
        ForeignKey("virtual_tour_scenes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    to_scene_id = Column(
        String(36),
        ForeignKey("virtual_tour_scenes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    yaw = Column(Float, nullable=False)
    pitch = Column(Float, nullable=False)
    label = Column(String(120), nullable=True)

    from_scene = relationship(
        "VirtualTourSceneORM", foreign_keys=[from_scene_id], back_populates="hotspots"
    )
    to_scene = relationship(
        "VirtualTourSceneORM", foreign_keys=[to_scene_id], back_populates="incoming_hotspots"
    )


class VirtualTourGenerationAttemptORM(Base):
    __tablename__ = "virtual_tour_generation_attempts"

    id = Column(String(36), primary_key=True)
    scene_id = Column(
        String(36),
        ForeignKey("virtual_tour_scenes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    input_image_ids = Column(JSON, nullable=False, default=list)
    provider = Column(String(60), nullable=False)
    provider_model = Column(String(80), nullable=False)
    quality = Column(String(20), nullable=False)
    output_size = Column(String(30), nullable=False)
    seam_pass = Column(Boolean, nullable=False, default=False)
    state = Column(String(20), nullable=False, default="pending", index=True)
    estimated_cost_usd = Column(Numeric(10, 5), nullable=True)
    actual_cost_usd = Column(Numeric(10, 5), nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    scene = relationship("VirtualTourSceneORM", back_populates="generation_attempts")
