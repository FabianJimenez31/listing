"""Pydantic schemas for the site settings endpoints."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class FooterLogo(BaseModel):
    """An ally/partner logo rendered in the footer strip."""

    name: str = ""
    image_url: str
    link: str | None = None
    storage_key: str | None = None


class SiteSettingsResponse(BaseModel):
    """Public branding payload consumed by the SPA on every page load."""

    logo_url: str | None = None
    footer_logo_url: str | None = None
    footer_tagline: str | None = None
    copyright_text: str | None = None
    social_instagram: str | None = None
    social_linkedin: str | None = None
    social_youtube: str | None = None
    legal_privacy_url: str | None = None
    legal_terms_url: str | None = None
    legal_cookies_url: str | None = None
    footer_logos: list[FooterLogo] = Field(default_factory=list)
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class SiteSettingsUpdateRequest(BaseModel):
    """Editable footer fields (the logo itself is managed by its own endpoints)."""

    footer_tagline: str | None = None
    copyright_text: str | None = None
    social_instagram: str | None = None
    social_linkedin: str | None = None
    social_youtube: str | None = None
    legal_privacy_url: str | None = None
    legal_terms_url: str | None = None
    legal_cookies_url: str | None = None
    footer_logos: list[FooterLogo] = Field(default_factory=list)


class FooterLogoUploadResponse(BaseModel):
    url: str
    storage_key: str
