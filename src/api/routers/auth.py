"""Auth router: register, login, refresh, logout."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.deps import CurrentUser, DB
from src.auth.jwt_handler import create_access_token, create_refresh_token, decode_token
from src.auth.login_otp import issue_challenge, user_requires_otp, verify_challenge
from src.auth.password import hash_password, verify_password
from src.db.models.user_models import UserORM
from src.repositories.user_repo import UserRepository
from src.schemas.auth_schemas import (
    LoginRequest,
    LoginResponse,
    OtpVerifyRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from src.schemas.user_schemas import UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: DB):
    repo = UserRepository(db)
    if repo.get_by_email(body.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    user = UserORM(
        id=str(uuid.uuid4()),
        email=body.email.lower(),
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        phone=body.phone,
    )
    repo.add(user)
    db.commit()
    db.refresh(user)
    return UserResponse.from_orm_with_permissions(user)


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: DB):
    repo = UserRepository(db)
    user = repo.get_by_email(body.email.lower())
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    if not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Account is disabled")

    # Staff (admin/agent) log in passwordless when 2FA is on: just the email →
    # an emailed code, no password needed.
    if user_requires_otp(user):
        try:
            challenge_id = issue_challenge(db, user)
        except Exception:
            db.rollback()
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "No se pudo enviar el código de verificación. Intenta de nuevo.",
            )
        return LoginResponse(otp_required=True, challenge_id=challenge_id)

    # Password path: everyone else, and the fallback for staff when 2FA is off.
    if not body.password:
        return LoginResponse(password_required=True)
    if not verify_password(body.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")

    return LoginResponse(
        access_token=create_access_token(user.id, user.email),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/login/verify", response_model=TokenResponse)
def login_verify(body: OtpVerifyRequest, db: DB):
    """Exchange a valid OTP code for tokens (second step of staff 2FA login)."""
    user = verify_challenge(db, body.challenge_id, body.code)
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Código inválido o expirado")
    return TokenResponse(
        access_token=create_access_token(user.id, user.email),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, db: DB):
    from jose import JWTError
    try:
        payload = decode_token(body.refresh_token)
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token")

    if payload.get("type") != "refresh":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Expected refresh token")

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token payload")

    user = UserRepository(db).get_active_by_id(user_id)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")

    return TokenResponse(
        access_token=create_access_token(user.id, user.email),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(current_user: CurrentUser):
    """Stateless logout — client discards token. Token blocklist is a future enhancement."""
    return None


@router.get("/me", response_model=UserResponse)
def me(current_user: CurrentUser):
    return UserResponse.from_orm_with_permissions(current_user)
