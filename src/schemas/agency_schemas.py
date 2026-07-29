"""Pydantic schemas for Agency endpoints."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AgencyResponse(BaseModel):
    id: str
    name: str
    slug: str
    initials: str | None = None
    logo_url: str | None = None
    description: str | None = None
    phone: str | None = None
    email: str | None = None
    whatsapp: str | None = None
    website: str | None = None
    location_id: str | None = None
    is_verified: bool = False
    is_active: bool = True
    property_count: int = 0
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class AgencyCreateRequest(BaseModel):
    name: str
    slug: str | None = None  # auto-generated from name if omitted
    initials: str | None = None
    logo_url: str | None = None
    description: str | None = None
    phone: str | None = None
    email: str | None = None
    whatsapp: str | None = None
    website: str | None = None
    location_id: str | None = None
    is_verified: bool = False
    is_active: bool = True


class AgencyUpdateRequest(BaseModel):
    name: str | None = None
    initials: str | None = None
    logo_url: str | None = None
    description: str | None = None
    phone: str | None = None
    email: str | None = None
    whatsapp: str | None = None
    website: str | None = None
    location_id: str | None = None
    is_verified: bool | None = None
    is_active: bool | None = None
