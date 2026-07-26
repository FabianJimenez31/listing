"""Pydantic schemas for Location endpoints."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, field_validator

LocationLevel = Literal["country", "state", "city", "locality", "neighborhood"]


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
    """Create a node of the location tree (país → ciudad → localidad → barrio).

    ``slug`` is optional: when omitted the API derives a unique one from ``name``
    (so the admin UI only has to send the name, the level and the parent).
    """

    name: str
    slug: str | None = None
    level: LocationLevel
    parent_id: str | None = None
    center_lat: float | None = None
    center_lng: float | None = None

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name must not be blank")
        return v.strip()
