"""Admin router: moderation queue, user management, global stats."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select

from src.api.deps import DB, require_permission
from src.db.models.property_models import PropertyORM
from src.db.models.user_models import UserORM
from src.repositories.property_repo import PropertyRepository
from src.schemas.pagination_schemas import make_page
from src.schemas.property_schemas import PropertyResponse

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get(
    "/moderation",
    response_model=dict,
    dependencies=[Depends(require_permission("property:moderate"))],
)
def moderation_queue(db: DB, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    """List all properties in PENDING status awaiting review."""
    repo = PropertyRepository(db)
    items, total = repo.search(status="pending", page=page, page_size=page_size)
    data = [PropertyResponse.model_validate(p).model_dump() for p in items]
    return make_page(data, page, page_size, total)


@router.get(
    "/stats",
    dependencies=[Depends(require_permission("metrics:read"))],
)
def global_stats(db: DB):
    """High-level platform counts."""
    total_users = db.scalar(select(func.count(UserORM.id)).where(UserORM.deleted_at.is_(None))) or 0
    total_properties = db.scalar(select(func.count(PropertyORM.id)).where(PropertyORM.deleted_at.is_(None))) or 0
    published = db.scalar(select(func.count(PropertyORM.id)).where(PropertyORM.status == "published", PropertyORM.deleted_at.is_(None))) or 0
    pending = db.scalar(select(func.count(PropertyORM.id)).where(PropertyORM.status == "pending", PropertyORM.deleted_at.is_(None))) or 0

    return {
        "total_users": total_users,
        "total_properties": total_properties,
        "published_properties": published,
        "pending_properties": pending,
    }


@router.get(
    "/users",
    response_model=dict,
    dependencies=[Depends(require_permission("user:read"))],
)
def list_users(db: DB, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    total = db.scalar(select(func.count(UserORM.id)).where(UserORM.deleted_at.is_(None))) or 0
    stmt = (
        select(UserORM)
        .where(UserORM.deleted_at.is_(None))
        .order_by(UserORM.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    users = list(db.scalars(stmt).all())
    data = [
        {"id": u.id, "email": u.email, "full_name": u.full_name, "is_active": u.is_active, "created_at": u.created_at.isoformat()}
        for u in users
    ]
    return make_page(data, page, page_size, total)
