"""Auth router: register, login, refresh, logout."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.deps import CurrentUser, DB
from src.auth.jwt_handler import create_access_token, create_refresh_token, decode_token
from src.auth.password import hash_password, verify_password
from src.db.models.user_models import UserORM
from src.repositories.user_repo import UserRepository
from src.schemas.auth_schemas import (
    LoginRequest,
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
    return user


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: DB):
    repo = UserRepository(db)
    user = repo.get_by_email(body.email.lower())
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    if not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Account is disabled")

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
    return current_user
