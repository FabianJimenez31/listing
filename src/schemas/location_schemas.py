"""Pydantic schemas for Location endpoints."""
from __future__ import annotations

from pydantic import BaseModel


class LocationResponse(BaseModel):
    id: str
    name: str
    slug: str
    level: str
    parent_id: str | None = None
    center_lat: float | None = None
    center_lng: float | None = None
    image_url: str | None = None
    is_active: bool

    model_config = {"from_attributes": True}


class LocationCreateRequest(BaseModel):
    name: str
    slug: str
    level: str
    parent_id: str | None = None
    center_lat: float | None = None
    center_lng: float | None = None
