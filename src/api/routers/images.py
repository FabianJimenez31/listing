"""Image upload/delete/reorder endpoints for properties.

POST   /properties/{id}/images         — upload one image (multipart/form-data)
DELETE /properties/{id}/images/{img_id} — delete an image
PATCH  /properties/{id}/images/reorder  — reorder images by id list

Storage: in development, files are saved under temp/uploads/. In production
set STORAGE_BACKEND=s3 and the required S3 env vars; the storage_key is then
the S3 object key and cdn_url points to the CDN hostname.
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from src.api.deps import CurrentUser, DB
from src.db.models.property_models import PropertyImageORM, PropertyORM
from src.repositories.property_repo import PropertyRepository

router = APIRouter(prefix="/properties", tags=["images"])

# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------

_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
_MAX_BYTES = 10 * 1024 * 1024  # 10 MB

_STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local")
_LOCAL_UPLOAD_DIR = Path(os.getenv("LOCAL_UPLOAD_DIR", "temp/uploads"))
_CDN_BASE_URL = os.getenv("CDN_BASE_URL", "http://localhost:8000/static")


def _save_local(file_bytes: bytes, storage_key: str) -> str:
    dest = _LOCAL_UPLOAD_DIR / storage_key
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(file_bytes)
    return f"{_CDN_BASE_URL}/{storage_key}"


def _delete_local(storage_key: str) -> None:
    path = _LOCAL_UPLOAD_DIR / storage_key
    if path.exists():
        path.unlink()


def _store(file_bytes: bytes, storage_key: str) -> str:
    """Save bytes and return the public CDN URL."""
    if _STORAGE_BACKEND == "s3":
        # S3 upload path — requires boto3 + env vars AWS_ACCESS_KEY_ID, etc.
        try:
            import boto3  # type: ignore
            s3 = boto3.client("s3")
            bucket = os.environ["S3_BUCKET"]
            s3.put_object(Bucket=bucket, Key=storage_key, Body=file_bytes)
            return f"{_CDN_BASE_URL}/{storage_key}"
        except ImportError:
            raise HTTPException(500, "boto3 not installed; set STORAGE_BACKEND=local")
    return _save_local(file_bytes, storage_key)


def _remove(storage_key: str) -> None:
    if _STORAGE_BACKEND != "s3":
        _delete_local(storage_key)
    # S3 deletion omitted for brevity; add boto3.delete_object in production


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
