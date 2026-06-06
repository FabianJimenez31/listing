"""Pydantic schemas for property CRUD and lifecycle endpoints."""
from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, field_validator, model_validator


# ---------------------------------------------------------------------------
# Image sub-schema
# ---------------------------------------------------------------------------

class PropertyImageResponse(BaseModel):
    id: str
    role: str
    media_kind: str
    position: int
    cdn_url: str | None = None
    thumb_url: str | None = None
    width: int | None = None
    height: int | None = None
    alt_text: str | None = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Location sub-schema (embedded in property detail)
# ---------------------------------------------------------------------------

class LocationEmbedded(BaseModel):
    id: str
    name: str
    slug: str
    level: str
    center_lat: float | None = None
    center_lng: float | None = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Owner sub-schema
# ---------------------------------------------------------------------------

class OwnerEmbedded(BaseModel):
    id: str
    full_name: str
    email: str
    phone: str | None = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Create / Update
# ---------------------------------------------------------------------------

class PropertyCreateRequest(BaseModel):
    title: str
    description: str | None = None
    operation_type: Literal["sale", "rent", "temporary"]
    property_kind: Literal["house", "apartment", "lot", "office", "commercial", "farm", "other"]
    condition: Literal["new", "used", "remodeled", "under_construction"] | None = None
    price_amount: int  # minor units (cents)
    currency: str = "USD"
    total_area_m2: float | None = None
    built_area_m2: float | None = None
    bedrooms: int | None = None
    bathrooms: int | None = None
    parking_spots: int | None = None
    floor_number: int | None = None
    total_floors: int | None = None
    address_street: str | None = None
    address_detail: str | None = None
    location_id: str | None = None
    property_type_id: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    contact_whatsapp: str | None = None
    expires_at: date | None = None

    @field_validator("price_amount")
    @classmethod
    def price_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("price_amount must be non-negative")
        return v

    @field_validator("currency")
    @classmethod
    def currency_valid(cls, v: str) -> str:
        v = v.upper()
        if len(v) != 3:
            raise ValueError("currency must be a 3-character ISO 4217 code")
        return v

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("title must not be blank")
        if len(v) > 200:
            raise ValueError("title must be at most 200 characters")
        return v


class PropertyUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    price_amount: int | None = None
    currency: str | None = None
    total_area_m2: float | None = None
    built_area_m2: float | None = None
    bedrooms: int | None = None
    bathrooms: int | None = None
    parking_spots: int | None = None
    floor_number: int | None = None
    total_floors: int | None = None
    address_street: str | None = None
    address_detail: str | None = None
    location_id: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    contact_whatsapp: str | None = None
    expires_at: date | None = None


class PropertyRejectRequest(BaseModel):
    reason: str

    @field_validator("reason")
    @classmethod
    def reason_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("reason must not be blank")
        return v.strip()


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------

class PropertyResponse(BaseModel):
    id: str
    owner_id: str
    title: str
    slug: str
    description: str | None = None
    operation_type: str
    property_kind: str
    condition: str | None = None
    price_amount: int
    currency: str
    total_area_m2: float | None = None
    built_area_m2: float | None = None
    bedrooms: int | None = None
    bathrooms: int | None = None
    parking_spots: int | None = None
    floor_number: int | None = None
    total_floors: int | None = None
    address_street: str | None = None
    status: str
    published_at: datetime | None = None
    rejection_reason: str | None = None
    views_count: int = 0
    leads_count: int = 0
    favorites_count: int = 0
    created_at: datetime
    updated_at: datetime
    contact_phone: str | None = None
    contact_email: str | None = None
    contact_whatsapp: str | None = None
    images: list[PropertyImageResponse] = []
    location: LocationEmbedded | None = None
    owner: OwnerEmbedded | None = None

    model_config = {"from_attributes": True}


class PropertyListItem(BaseModel):
    id: str
    title: str
    slug: str
    operation_type: str
    property_kind: str
    price_amount: int
    currency: str
    total_area_m2: float | None = None
    bedrooms: int | None = None
    bathrooms: int | None = None
    status: str
    views_count: int = 0
    created_at: datetime
    main_image: PropertyImageResponse | None = None
    location: LocationEmbedded | None = None

    model_config = {"from_attributes": True}
