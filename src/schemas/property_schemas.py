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


class LocationCrumb(BaseModel):
    """A single hop of a location's ancestor chain (for breadcrumbs)."""

    id: str
    name: str
    slug: str
    level: str

    model_config = {"from_attributes": True}


class LocationDetailEmbedded(LocationEmbedded):
    """Location embedded on the property *detail* with its full root→leaf path.

    Kept separate from LocationEmbedded so list endpoints (cards) don't pay the
    parent-chain walk for every item.
    """

    path: list[LocationCrumb] = []


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
# Agency sub-schema (embedded on cards + detail)
# ---------------------------------------------------------------------------

class AgencyEmbedded(BaseModel):
    id: str
    name: str
    slug: str
    initials: str | None = None
    logo_url: str | None = None

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
    has_storage: bool = False  # depósito / bodega
    has_elevator: bool = False  # ascensor (edificio)
    has_study: bool = False  # zona de estudio
    has_balcony: bool = False  # balcón / terraza
    floor_number: int | None = None
    total_floors: int | None = None
    stratum: int | None = None  # estrato socioeconómico (1–6)
    view_type: Literal["internal", "external"] | None = None  # vista interna/externa
    age_years: int | None = None  # antigüedad en años
    admin_fee_amount: int | None = None  # valor administración (minor units, /mes)
    security_type: Literal["none", "private", "automated"] | None = None  # vigilancia
    address_street: str | None = None
    address_detail: str | None = None
    location_id: str | None = None
    property_type_id: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    contact_whatsapp: str | None = None
    expires_at: date | None = None
    show_on_home: bool = False

    @field_validator("price_amount")
    @classmethod
    def price_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("price_amount must be non-negative")
        return v

    @field_validator("stratum")
    @classmethod
    def stratum_in_range(cls, v: int | None) -> int | None:
        if v is not None and not (1 <= v <= 6):
            raise ValueError("stratum must be between 1 and 6")
        return v

    @field_validator("admin_fee_amount", "age_years")
    @classmethod
    def non_negative_optional(cls, v: int | None) -> int | None:
        if v is not None and v < 0:
            raise ValueError("value must be non-negative")
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
    has_storage: bool | None = None  # depósito / bodega
    has_elevator: bool | None = None  # ascensor (edificio)
    has_study: bool | None = None  # zona de estudio
    has_balcony: bool | None = None  # balcón / terraza
    floor_number: int | None = None
    total_floors: int | None = None
    stratum: int | None = None  # estrato socioeconómico (1–6)
    view_type: Literal["internal", "external"] | None = None  # vista interna/externa
    age_years: int | None = None  # antigüedad en años
    admin_fee_amount: int | None = None  # valor administración (minor units, /mes)
    security_type: Literal["none", "private", "automated"] | None = None  # vigilancia
    address_street: str | None = None
    address_detail: str | None = None
    location_id: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    contact_whatsapp: str | None = None
    expires_at: date | None = None
    show_on_home: bool | None = None


class ShowOnHomeRequest(BaseModel):
    show_on_home: bool


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
    nid: int  # public HubSpot-style numeric Record ID
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
    has_storage: bool = False  # depósito / bodega
    has_elevator: bool = False  # ascensor (edificio)
    has_study: bool = False  # zona de estudio
    has_balcony: bool = False  # balcón / terraza
    floor_number: int | None = None
    total_floors: int | None = None
    stratum: int | None = None  # estrato socioeconómico (1–6)
    view_type: str | None = None  # vista interna/externa
    age_years: int | None = None  # antigüedad en años
    admin_fee_amount: int | None = None  # valor administración (minor units, /mes)
    security_type: str | None = None  # vigilancia
    address_street: str | None = None
    status: str
    published_at: datetime | None = None
    rejection_reason: str | None = None
    views_count: int = 0
    leads_count: int = 0
    favorites_count: int = 0
    show_on_home: bool = False
    created_at: datetime
    updated_at: datetime
    contact_phone: str | None = None
    contact_email: str | None = None
    contact_whatsapp: str | None = None
    agency_id: str | None = None
    images: list[PropertyImageResponse] = []
    location: LocationDetailEmbedded | None = None
    owner: OwnerEmbedded | None = None
    agency: AgencyEmbedded | None = None

    model_config = {"from_attributes": True}


class PropertyListItem(BaseModel):
    id: str
    nid: int  # public HubSpot-style numeric Record ID
    title: str
    slug: str
    operation_type: str
    property_kind: str
    price_amount: int
    currency: str
    total_area_m2: float | None = None
    bedrooms: int | None = None
    bathrooms: int | None = None
    has_storage: bool = False  # depósito / bodega
    has_elevator: bool = False  # ascensor (edificio)
    has_study: bool = False  # zona de estudio
    status: str
    views_count: int = 0
    show_on_home: bool = False
    created_at: datetime
    main_image: PropertyImageResponse | None = None
    location: LocationEmbedded | None = None
    agency: AgencyEmbedded | None = None

    model_config = {"from_attributes": True}
