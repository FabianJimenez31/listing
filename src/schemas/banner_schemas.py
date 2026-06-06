"""Pydantic schemas for Banner and FeaturedProperty endpoints."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel
from src.schemas.property_schemas import PropertyListItem


class BannerResponse(BaseModel):
    id: str
    title: str
    position: str
    image_desktop_url: str
    image_mobile_url: str | None = None
    cta_url: str | None = None
    cta_text: str | None = None
    priority: int
    is_active: bool
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    impressions_count: int = 0
    clicks_count: int = 0

    model_config = {"from_attributes": True}


class BannerCreateRequest(BaseModel):
    title: str
    position: str
    image_desktop_url: str
    image_mobile_url: str | None = None
    cta_url: str | None = None
    cta_text: str | None = None
    locality_id: str | None = None
    operation_type: str | None = None
    property_kind: str | None = None
    priority: int = 0
    is_active: bool = True
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class FeaturedPropertyResponse(BaseModel):
    id: str
    property_id: str
    scope: str
    locality_id: str | None = None
    priority: int
    starts_at: datetime
    ends_at: datetime
    property: PropertyListItem | None = None

    model_config = {"from_attributes": True}


class FeaturedPropertyCreateRequest(BaseModel):
    property_id: str
    scope: str
    locality_id: str | None = None
    priority: int = 0
    starts_at: datetime
    ends_at: datetime
