"""Amenities router: amenity catalog."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.deps import DB
from src.db.models.catalog_models import AmenityORM

router = APIRouter(prefix="/amenities", tags=["amenities"])


@router.get("", response_model=list[dict])
def list_amenities(db: DB, category: str | None = None):
    stmt = select(AmenityORM).where(AmenityORM.is_active.is_(True))
    if category:
        stmt = stmt.where(AmenityORM.category == category)
    stmt = stmt.order_by(AmenityORM.category, AmenityORM.name)
    rows = list(db.scalars(stmt).all())
    return [{"id": r.id, "code": r.code, "name": r.name, "category": r.category, "icon": r.icon} for r in rows]
