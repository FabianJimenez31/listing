"""Users router: profile management."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.deps import CurrentUser, DB, require_permission
from src.repositories.user_repo import RoleRepository, UserRepository
from src.schemas.user_schemas import UserResponse, UserRoleAssignRequest, UserUpdateRequest

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_me(current_user: CurrentUser):
    return current_user


@router.put("/me", response_model=UserResponse)
def update_me(body: UserUpdateRequest, current_user: CurrentUser, db: DB):
    if body.full_name is not None:
        current_user.full_name = body.full_name.strip()
    if body.phone is not None:
        current_user.phone = body.phone
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/{user_id}", response_model=UserResponse, dependencies=[Depends(require_permission("user:read"))])
def get_user(user_id: str, db: DB):
    user = UserRepository(db).get_active_by_id(user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return user


@router.patch(
    "/{user_id}/roles",
    response_model=UserResponse,
    dependencies=[Depends(require_permission("role:assign"))],
)
def assign_role(user_id: str, body: UserRoleAssignRequest, db: DB):
    user_repo = UserRepository(db)
    role_repo = RoleRepository(db)

    user = user_repo.get_active_by_id(user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    role = role_repo.get_by_id(body.role_id)
    if not role:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Role not found")

    if role not in user.roles:
        user.roles.append(role)
        db.commit()
        db.refresh(user)

    return user


@router.delete(
    "/{user_id}/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("role:assign"))],
)
def remove_role(user_id: str, role_id: str, db: DB):
    user = UserRepository(db).get_active_by_id(user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    role = next((r for r in user.roles if r.id == role_id), None)
    if role:
        user.roles.remove(role)
        db.commit()

    return None
