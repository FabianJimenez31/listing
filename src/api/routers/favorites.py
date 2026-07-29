"""Favorites router: saved properties per user."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from src.api.deps import CurrentUser, DB
from src.db.models.engagement_models import FavoriteORM
from src.schemas.pagination_schemas import make_page

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.get("", response_model=dict)
def list_favorites(current_user: CurrentUser, db: DB, page: int = 1, page_size: int = 20):
    from sqlalchemy import func
    total_stmt = select(func.count(FavoriteORM.id)).where(FavoriteORM.user_id == current_user.id)
    total = db.scalar(total_stmt) or 0
    stmt = (
        select(FavoriteORM)
        .where(FavoriteORM.user_id == current_user.id)
        .order_by(FavoriteORM.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = list(db.scalars(stmt).all())
    data = [{"id": f.id, "property_id": f.property_id, "created_at": f.created_at.isoformat()} for f in items]
    return make_page(data, page, page_size, total)


@router.post("/{property_id}", status_code=status.HTTP_201_CREATED)
def add_favorite(property_id: str, current_user: CurrentUser, db: DB):
    exists = db.scalar(
        select(FavoriteORM).where(
            FavoriteORM.user_id == current_user.id,
            FavoriteORM.property_id == property_id,
        )
    )
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "Already in favorites")

    fav = FavoriteORM(id=str(uuid.uuid4()), user_id=current_user.id, property_id=property_id)
    db.add(fav)
    db.commit()
    return {"id": fav.id, "property_id": property_id}


@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite(property_id: str, current_user: CurrentUser, db: DB):
    fav = db.scalar(
        select(FavoriteORM).where(
            FavoriteORM.user_id == current_user.id,
            FavoriteORM.property_id == property_id,
        )
    )
    if fav:
        db.delete(fav)
        db.commit()
    return None
