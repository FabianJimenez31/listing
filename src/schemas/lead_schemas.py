"""Pydantic schemas for Lead endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, field_validator


class LeadCreateRequest(BaseModel):
    property_id: str
    name: str
    email: str | None = None
    phone: str | None = None
    message: str | None = None
    channel: Literal["form", "whatsapp", "call", "visit"]
    consent_given: bool = False
    consent_text: str | None = None
    utm: dict | None = None

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name must not be blank")
        return v.strip()

    @field_validator("email")
    @classmethod
    def email_format(cls, v: str | None) -> str | None:
        return v

    def model_post_init(self, __context: object) -> None:
        if not self.email and not self.phone:
            raise ValueError("at least one of email or phone is required")
        if self.channel in ("form", "visit") and not self.consent_given:
            raise ValueError("consent_given is required for form and visit channels")


class LeadStatusUpdateRequest(BaseModel):
    status: Literal["contacted", "negotiating", "closed", "discarded"]
    owner_id: str | None = None


class LeadResponse(BaseModel):
    id: str
    property_id: str
    name: str
    email: str | None = None
    phone: str | None = None
    message: str | None = None
    channel: str
    status: str
    consent_given: bool
    owner_id: str | None = None
    contacted_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
