"""FastAPI dependency injection: DB session, current user, permission guards."""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from src.auth.jwt_handler import decode_token
from src.db.engine import get_db
from src.db.models.user_models import RoleORM, UserORM
from src.repositories.user_repo import UserRepository

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> UserORM:
    """Require a valid JWT access token. Returns the active UserORM."""
    if not credentials:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing authorization token")
    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")

    if payload.get("type") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Expected access token")

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token payload")

    repo = UserRepository(db)
    user = repo.get_active_by_id(user_id)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")

    return user


def get_optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> UserORM | None:
    """Return the current user if a valid token is present, else None."""
    if not credentials:
        return None
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            return None
        user_id: str | None = payload.get("sub")
        if not user_id:
            return None
        return UserRepository(db).get_active_by_id(user_id)
    except JWTError:
        return None


def require_permission(code: str):
    """Return a FastAPI dependency that checks a specific permission code."""
    def _check(user: Annotated[UserORM, Depends(get_current_user)]) -> UserORM:
        if not user.has_permission(code):
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"Permission required: {code}")
        return user
    return _check


CurrentUser = Annotated[UserORM, Depends(get_current_user)]
OptionalUser = Annotated[UserORM | None, Depends(get_optional_user)]
DB = Annotated[Session, Depends(get_db)]
