"""Pydantic schemas for authentication endpoints."""
from __future__ import annotations

from pydantic import BaseModel, EmailStr, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: str | None = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("password must be at least 8 characters")
        return v

    @field_validator("full_name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("full_name must not be blank")
        return v.strip()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginResponse(BaseModel):
    """Login result: tokens directly, or an OTP challenge when 2FA is required."""

    access_token: str | None = None
    refresh_token: str | None = None
    token_type: str = "bearer"
    otp_required: bool = False
    challenge_id: str | None = None


class OtpVerifyRequest(BaseModel):
    challenge_id: str
    code: str


class RefreshRequest(BaseModel):
    refresh_token: str
