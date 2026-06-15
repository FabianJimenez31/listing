"""Image upload/delete/reorder endpoints for properties.

POST   /properties/{id}/images         — upload one image (multipart/form-data)
DELETE /properties/{id}/images/{img_id} — delete an image
PATCH  /properties/{id}/images/reorder  — reorder images by id list

Storage: in development, files are saved under temp/uploads/. In production
set STORAGE_BACKEND=s3 and the required S3 env vars; the storage_key is then
the S3 object key and cdn_url points to the CDN hostname.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from src.api.deps import CurrentUser, DB
from src.db.models.property_models import PropertyImageORM, PropertyORM
from src.repositories.property_repo import PropertyRepository
from src.storage.image_store import (
    ALLOWED_CONTENT_TYPES as _ALLOWED_CONTENT_TYPES,
    MAX_BYTES as _MAX_BYTES,
    remove as _remove,
    store as _store,
)

router = APIRouter(prefix="/properties", tags=["images"])


# ---------------------------------------------------------------------------
# Guard helper
# ---------------------------------------------------------------------------

def _get_property_owned(property_id: str, user, db) -> PropertyORM:
    repo = PropertyRepository(db)
    prop = repo.get_by_id(property_id)
    if not prop or prop.deleted_at:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Property not found")
    if prop.owner_id != user.id and not user.has_permission("property:moderate"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not the property owner")
    return prop


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ImageResponse(BaseModel):
    id: str
    role: str
    media_kind: str
    position: int
    cdn_url: str | None
    thumb_url: str | None
    alt_text: str | None
    bytes: int | None
    content_type: str | None

    model_config = {"from_attributes": True}


class ReorderRequest(BaseModel):
    ordered_ids: list[str]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/{property_id}/images", response_model=ImageResponse, status_code=status.HTTP_201_CREATED)
async def upload_image(
    property_id: str,
    current_user: CurrentUser,
    db: DB,
    file: UploadFile = File(...),
    role: str = "gallery",
    alt_text: str | None = None,
):
    """Upload a single image for a property.

    - role: "main" (hero) or "gallery"
    - Content-Type must be image/jpeg, image/png, or image/webp
    - Max 10 MB per file
    """
    prop = _get_property_owned(property_id, current_user, db)

    if file.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Content-Type {file.content_type!r} not allowed. Use JPEG, PNG, or WebP.",
        )

    file_bytes = await file.read()
    if len(file_bytes) > _MAX_BYTES:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"File too large ({len(file_bytes)} bytes). Max 10 MB.",
        )

    ext = (file.filename or "image").rsplit(".", 1)[-1].lower()
    storage_key = f"{property_id}/{uuid.uuid4()}.{ext}"
    cdn_url = _store(file_bytes, storage_key)

    # If role=main, demote existing main image to gallery
    if role == "main":
        for img in prop.images:
            if img.role == "main":
                img.role = "gallery"

    position = max((img.position for img in prop.images), default=-1) + 1

    image = PropertyImageORM(
        id=str(uuid.uuid4()),
        property_id=property_id,
        role=role,
        media_kind="image",
        position=position,
        storage_key=storage_key,
        cdn_url=cdn_url,
        bytes=len(file_bytes),
        content_type=file.content_type,
        alt_text=alt_text,
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


@router.delete("/{property_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_image(property_id: str, image_id: str, current_user: CurrentUser, db: DB):
    _get_property_owned(property_id, current_user, db)

    image = db.query(PropertyImageORM).filter_by(id=image_id, property_id=property_id).first()
    if not image:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Image not found")

    _remove(image.storage_key)
    db.delete(image)
    db.commit()
    return None


@router.patch("/{property_id}/images/{image_id}/main", response_model=ImageResponse)
def set_main_image(property_id: str, image_id: str, current_user: CurrentUser, db: DB):
    """Promote an existing image to the cover (role=main), demoting the rest."""
    prop = _get_property_owned(property_id, current_user, db)
    target = db.query(PropertyImageORM).filter_by(id=image_id, property_id=property_id).first()
    if not target:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Image not found")
    for img in prop.images:
        img.role = "main" if img.id == image_id else "gallery"
    db.commit()
    db.refresh(target)
    return target


@router.patch("/{property_id}/images/reorder", response_model=list[ImageResponse])
def reorder_images(property_id: str, body: ReorderRequest, current_user: CurrentUser, db: DB):
    """Reorder images by providing an ordered list of image IDs."""
    prop = _get_property_owned(property_id, current_user, db)

    image_map = {img.id: img for img in prop.images}
    for idx, img_id in enumerate(body.ordered_ids):
        if img_id not in image_map:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Image {img_id} not found")
        image_map[img_id].position = idx

    db.commit()
    db.refresh(prop)
    return sorted(prop.images, key=lambda i: i.position)
