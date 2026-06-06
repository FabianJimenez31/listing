"""Pydantic schemas for user responses and updates."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr


class RoleResponse(BaseModel):
    id: str
    name: str
    description: str | None = None

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    phone: str | None = None
    is_active: bool
    email_verified: bool
    created_at: datetime
    roles: list[RoleResponse] = []

    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    full_name: str | None = None
    phone: str | None = None


class UserRoleAssignRequest(BaseModel):
    role_id: str
