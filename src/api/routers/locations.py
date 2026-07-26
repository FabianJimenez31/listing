"""Locations router: location catalog."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select

from src.api.deps import DB, require_permission
from src.db.models.location_models import LocationORM
from src.repositories.location_repo import LocationRepository
from src.schemas.location_schemas import LocationCreateRequest, LocationResponse
from src.storage.image_store import (
    ALLOWED_CONTENT_TYPES,
    MAX_BYTES,
    remove as storage_remove,
    store as storage_store,
)

router = APIRouter(prefix="/locations", tags=["locations"])

_STATIC_MARKER = "/static/"


def _remove_uploaded_cover(image_url: str | None) -> None:
    """Best-effort delete of a previously uploaded location cover. Only our own
    ``/static`` uploads are removed; external/seeded URLs are left untouched."""
    if image_url and _STATIC_MARKER in image_url:
        storage_remove(image_url.split(_STATIC_MARKER, 1)[1])


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
    """Add a node to the location tree: país, ciudad, localidad o barrio.

    Used by the admin panel and by the inline "agregar ciudad/país que falta"
    buttons of the property and project forms. The slug is derived from the name
    when the caller omits it; an already-existing sibling is reported as a 409
    (and reactivated if it had been disabled) instead of failing on the unique
    slug constraint.
    """
    repo = LocationRepository(db)

    parent: LocationORM | None = None
    if body.level == "country":
        if body.parent_id:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY, "A country cannot have a parent location"
            )
    else:
        if not body.parent_id:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY, f"parent_id is required for level {body.level!r}"
            )
        parent = db.get(LocationORM, body.parent_id)
        if not parent:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Parent location not found")

    existing = repo.find_sibling(name=body.name, level=body.level, parent_id=body.parent_id)
    if existing is not None:
        if existing.is_active:
            where = f" en {parent.name}" if parent else ""
            raise HTTPException(
                status.HTTP_409_CONFLICT, f"Ya existe «{existing.name}»{where}. Selecciónala en la lista."
            )
        existing.is_active = True  # it was there but disabled — bring it back
        db.commit()
        db.refresh(existing)
        return existing

    loc = LocationORM(
        id=str(uuid.uuid4()),
        name=body.name,
        slug=repo.unique_slug(body.slug or body.name, parent),
        level=body.level,
        parent_id=body.parent_id,
        center_lat=body.center_lat,
        center_lng=body.center_lng,
    )
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return loc


@router.post(
    "/{location_id}/image/upload",
    response_model=LocationResponse,
    dependencies=[Depends(require_permission("location:create"))],
)
async def upload_location_image(location_id: str, db: DB, file: UploadFile = File(...)):
    """Set a curated cover image for a location (e.g. a city card on the home).
    A manual image wins over the auto-derived property cover; clear it to revert."""
    loc = db.get(LocationORM, location_id)
    if not loc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Location not found")
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Content-Type {file.content_type!r} not allowed. Use JPEG, PNG, or WebP.",
        )
    file_bytes = await file.read()
    if len(file_bytes) > MAX_BYTES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "File too large. Max 10 MB.")
    _remove_uploaded_cover(loc.image_url)  # drop the previous upload, if any
    ext = (file.filename or "image").rsplit(".", 1)[-1].lower()
    storage_key = f"locations/{location_id}/{uuid.uuid4()}.{ext}"
    loc.image_url = storage_store(file_bytes, storage_key)
    db.commit()
    db.refresh(loc)
    return loc


@router.delete(
    "/{location_id}/image",
    response_model=LocationResponse,
    dependencies=[Depends(require_permission("location:create"))],
)
def clear_location_image(location_id: str, db: DB):
    """Remove the curated cover image so the card reverts to the auto-derived one."""
    loc = db.get(LocationORM, location_id)
    if not loc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Location not found")
    _remove_uploaded_cover(loc.image_url)
    loc.image_url = None
    db.commit()
    db.refresh(loc)
    return loc
