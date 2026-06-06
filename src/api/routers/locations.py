"""Locations router: location catalog."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from src.api.deps import DB, require_permission
from src.db.models.location_models import LocationORM
from src.schemas.location_schemas import LocationCreateRequest, LocationResponse

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("", response_model=list[LocationResponse])
def list_locations(db: DB, level: str | None = None, parent_id: str | None = None):
    stmt = select(LocationORM).where(LocationORM.is_active.is_(True))
    if level:
        stmt = stmt.where(LocationORM.level == level)
    if parent_id:
        stmt = stmt.where(LocationORM.parent_id == parent_id)
    stmt = stmt.order_by(LocationORM.name)
    return list(db.scalars(stmt).all())


@router.get("/{location_id}", response_model=LocationResponse)
def get_location(location_id: str, db: DB):
    loc = db.get(LocationORM, location_id)
    if not loc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Location not found")
    return loc


@router.post(
    "",
    response_model=LocationResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("location:create"))],
)
def create_location(body: LocationCreateRequest, db: DB):
    loc = LocationORM(
        id=str(uuid.uuid4()),
        name=body.name,
        slug=body.slug,
        level=body.level,
        parent_id=body.parent_id,
        center_lat=body.center_lat,
        center_lng=body.center_lng,
    )
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return loc
