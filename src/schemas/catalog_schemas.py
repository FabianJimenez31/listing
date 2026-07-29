"""Pydantic schemas for catalog aggregation endpoints (property types, cities)."""
from __future__ import annotations

from pydantic import BaseModel


class PropertyTypeItem(BaseModel):
    id: str
    code: str
    name: str
    slug: str
    icon: str | None = None
    property_count: int = 0

    model_config = {"from_attributes": True}


class FeaturedCityItem(BaseModel):
    id: str
    name: str
    slug: str
    level: str
    image_url: str | None = None
    center_lat: float | None = None
    center_lng: float | None = None
    property_count: int = 0

    model_config = {"from_attributes": True}
