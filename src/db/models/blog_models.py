"""ORM model for blog Post (Blog de inversión)."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from src.db.engine import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PostORM(Base):
    __tablename__ = "posts"

    id = Column(String(36), primary_key=True)
    author_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)

    title = Column(String(255), nullable=False)
    slug = Column(String(300), unique=True, nullable=False, index=True)
    excerpt = Column(String(500), nullable=True)
    content = Column(Text, nullable=True)
    cover_image_url = Column(String(1000), nullable=True)
    category = Column(String(80), nullable=True, index=True)

    # draft / published
    status = Column(String(20), nullable=False, default="draft", index=True)
    published_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    author = relationship("UserORM")
