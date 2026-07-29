"""Pydantic schemas for Partner (allied agencies & developers) endpoints."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class PartnerResponse(BaseModel):
    id: str
    name: str
    slug: str
    logo_url: str | None = None
    kind: str
    website: str | None = None
    priority: int = 0
    is_active: bool = True

    model_config = {"from_attributes": True}


class PartnerCreateRequest(BaseModel):
    name: str
    slug: str | None = None  # auto-generated from name if omitted
    logo_url: str | None = None
    kind: Literal["inmobiliaria", "constructora"] = "inmobiliaria"
    website: str | None = None
    priority: int = 0
    is_active: bool = True
