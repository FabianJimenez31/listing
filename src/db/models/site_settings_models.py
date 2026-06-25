"""ORM model for SiteSettings.

A single-row ("singleton") table holding global site configuration that is
editable from the admin portal. Today it stores the brand logo; new branding
fields (favicon, site name, theme color…) can be added here without a new table.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import relationship

from src.db.engine import Base

# Fixed primary key for the one and only row. Helpers always read/write the
# settings by this id, so the table never holds more than a single record.
SINGLETON_ID = "default"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SiteSettingsORM(Base):
    __tablename__ = "site_settings"

    id = Column(String(36), primary_key=True, default=SINGLETON_ID)

    # Public URL of the uploaded brand logo. NULL → the SPA renders the text
    # wordmark fallback instead of an <img>.
    logo_url = Column(String(1000), nullable=True)
    # Storage key of the current logo, kept so the previous file can be removed
    # when the logo is replaced or cleared.
    logo_storage_key = Column(String(500), nullable=True)

    # ── Footer configuration (admin-editable) ───────────────────────────────
    # Footer brand logo, independent from the header `logo_url`. NULL → the
    # footer falls back to the header logo, then to the text wordmark.
    footer_logo_url = Column(String(1000), nullable=True)
    footer_logo_storage_key = Column(String(500), nullable=True)

    # Brand description and copyright line shown in the footer.
    footer_tagline = Column(Text, nullable=True)
    copyright_text = Column(String(500), nullable=True)

    # Social network links. NULL/empty → that icon does not link anywhere.
    social_instagram = Column(String(500), nullable=True)
    social_linkedin = Column(String(500), nullable=True)
    social_youtube = Column(String(500), nullable=True)

    # Legal links shown in the footer bottom bar.
    legal_privacy_url = Column(String(500), nullable=True)
    legal_terms_url = Column(String(500), nullable=True)
    legal_cookies_url = Column(String(500), nullable=True)

    # Ally / partner logos rendered as a strip in the footer.
    # JSON list of {"name", "image_url", "link", "storage_key"}.
    footer_logos = Column(JSON, nullable=False, default=list)

    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
    updated_by_id = Column(String(36), ForeignKey("users.id"), nullable=True)

    updated_by = relationship("UserORM", foreign_keys=[updated_by_id])
