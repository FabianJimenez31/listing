"""Pydantic schemas for Project (development) endpoints."""
from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, field_validator

from src.schemas.property_schemas import AgencyEmbedded, LocationEmbedded


class ProjectImageItem(BaseModel):
    id: str
    role: str
    position: int
    cdn_url: str
    thumb_url: str | None = None
    alt_text: str | None = None

    model_config = {"from_attributes": True}


class ProjectImageCreateRequest(BaseModel):
    cdn_url: str
    thumb_url: str | None = None
    alt_text: str | None = None
    role: Literal["main", "gallery"] = "gallery"
    position: int = 0


class ProjectCreateRequest(BaseModel):
    title: str
    description: str | None = None
    developer_name: str | None = None
    stage: Literal["preventa", "construccion", "entrega_inmediata"] = "preventa"
    agency_id: str | None = None
    location_id: str | None = None
    property_type_id: str | None = None
    price_from: int | None = None  # minor units
    price_to: int | None = None
    currency: str = "COP"
    bedrooms_min: int | None = None
    bedrooms_max: int | None = None
    bathrooms_min: int | None = None
    bathrooms_max: int | None = None
    area_min_m2: float | None = None
    area_max_m2: float | None = None
    total_units: int | None = None
    available_units: int | None = None
    delivery_date: date | None = None
    address_street: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    contact_whatsapp: str | None = None
    cover_image_url: str | None = None

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
        return v


class ProjectUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    developer_name: str | None = None
    stage: Literal["preventa", "construccion", "entrega_inmediata"] | None = None
    agency_id: str | None = None
    location_id: str | None = None
    property_type_id: str | None = None
    price_from: int | None = None
    price_to: int | None = None
    currency: str | None = None
    bedrooms_min: int | None = None
    bedrooms_max: int | None = None
    bathrooms_min: int | None = None
    bathrooms_max: int | None = None
    area_min_m2: float | None = None
    area_max_m2: float | None = None
    total_units: int | None = None
    available_units: int | None = None
    delivery_date: date | None = None
    address_street: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    contact_whatsapp: str | None = None
    cover_image_url: str | None = None


class ProjectListItem(BaseModel):
    id: str
    title: str
    slug: str
    stage: str
    status: str
    developer_name: str | None = None
    price_from: int | None = None
    price_to: int | None = None
    currency: str
    bedrooms_min: int | None = None
    bedrooms_max: int | None = None
    area_min_m2: float | None = None
    area_max_m2: float | None = None
    cover_image_url: str | None = None
    created_at: datetime
    location: LocationEmbedded | None = None
    agency: AgencyEmbedded | None = None

    model_config = {"from_attributes": True}


class ProjectResponse(BaseModel):
    id: str
    agency_id: str | None = None
    location_id: str | None = None
    property_type_id: str | None = None
    developer_name: str | None = None
    title: str
    slug: str
    description: str | None = None
    stage: str
    status: str
    price_from: int | None = None
    price_to: int | None = None
    currency: str
    bedrooms_min: int | None = None
    bedrooms_max: int | None = None
    bathrooms_min: int | None = None
    bathrooms_max: int | None = None
    area_min_m2: float | None = None
    area_max_m2: float | None = None
    total_units: int | None = None
    available_units: int | None = None
    delivery_date: date | None = None
    address_street: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    contact_whatsapp: str | None = None
    cover_image_url: str | None = None
    views_count: int = 0
    leads_count: int = 0
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    images: list[ProjectImageItem] = []
    location: LocationEmbedded | None = None
    agency: AgencyEmbedded | None = None

    model_config = {"from_attributes": True}
