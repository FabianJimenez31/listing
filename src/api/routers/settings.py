"""Site settings router — global, admin-editable branding.

GET    /settings             — public; the SPA reads brand + footer config on load
PUT    /settings             — admin; update footer copy, social, legal and ally logos
POST   /settings/logo        — admin; upload/replace the brand logo (multipart)
DELETE /settings/logo        — admin; clear the logo (revert to the text wordmark)
POST   /settings/footer-logo — admin; upload an ally logo image, returns its URL

Storage mirrors property images: in development files land under temp/uploads/
and are served at /static/; in production set STORAGE_BACKEND=s3 + the S3 env vars.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from src.api.deps import DB, CurrentUser, require_permission
from src.repositories.site_settings_repo import SiteSettingsRepository
from src.schemas.site_settings_schemas import (
    FooterLogoUploadResponse,
    SiteSettingsResponse,
    SiteSettingsUpdateRequest,
)
from src.storage.image_store import (
    ALLOWED_CONTENT_TYPES as _ALLOWED_CONTENT_TYPES,
    MAX_BYTES as _MAX_BYTES,
    remove as _remove,
    store as _store,
)

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SiteSettingsResponse)
def get_settings(db: DB):
    """Return public branding settings. Open to anonymous visitors."""
    return SiteSettingsRepository(db).get_or_create()


@router.put(
    "",
    response_model=SiteSettingsResponse,
    dependencies=[Depends(require_permission("settings:manage"))],
)
def update_settings(body: SiteSettingsUpdateRequest, current_user: CurrentUser, db: DB):
    """Update the footer configuration (copy, social links, legal links, ally logos)."""
    repo = SiteSettingsRepository(db)
    settings = repo.get_or_create()

    data = body.model_dump()
    data["footer_logos"] = [logo.model_dump() for logo in body.footer_logos]
    for field, value in data.items():
        setattr(settings, field, value)
    settings.updated_by_id = current_user.id
    db.commit()
    db.refresh(settings)
    return settings


@router.post(
    "/footer-logo",
    response_model=FooterLogoUploadResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("settings:manage"))],
)
async def upload_footer_logo(db: DB, file: UploadFile = File(...)):
    """Upload an ally/partner logo for the footer strip. Returns its URL + storage key."""
    if file.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Content-Type {file.content_type!r} not allowed. Use JPEG, PNG, WebP, or GIF.",
        )

    file_bytes = await file.read()
    if len(file_bytes) > _MAX_BYTES:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"File too large ({len(file_bytes)} bytes). Max 10 MB.",
        )

    ext = (file.filename or "logo").rsplit(".", 1)[-1].lower()
    storage_key = f"branding/footer-{uuid.uuid4()}.{ext}"
    cdn_url = _store(file_bytes, storage_key)
    return FooterLogoUploadResponse(url=cdn_url, storage_key=storage_key)


@router.post(
    "/logo",
    response_model=SiteSettingsResponse,
    dependencies=[Depends(require_permission("settings:manage"))],
)
async def upload_logo(current_user: CurrentUser, db: DB, file: UploadFile = File(...)):
    """Upload (or replace) the site logo. Content-Type must be JPEG, PNG, WebP, or GIF; max 10 MB."""
    if file.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Content-Type {file.content_type!r} not allowed. Use JPEG, PNG, WebP, or GIF.",
        )

    file_bytes = await file.read()
    if len(file_bytes) > _MAX_BYTES:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"File too large ({len(file_bytes)} bytes). Max 10 MB.",
        )

    ext = (file.filename or "logo").rsplit(".", 1)[-1].lower()
    storage_key = f"branding/logo-{uuid.uuid4()}.{ext}"
    cdn_url = _store(file_bytes, storage_key)

    repo = SiteSettingsRepository(db)
    settings = repo.get_or_create()

    old_key = settings.logo_storage_key
    settings.logo_url = cdn_url
    settings.logo_storage_key = storage_key
    settings.updated_by_id = current_user.id
    db.commit()
    db.refresh(settings)

    # Drop the previous file only after the new one is committed.
    if old_key and old_key != storage_key:
        _remove(old_key)

    return settings


@router.delete(
    "/logo",
    response_model=SiteSettingsResponse,
    dependencies=[Depends(require_permission("settings:manage"))],
)
def delete_logo(current_user: CurrentUser, db: DB):
    """Remove the current logo so the portal falls back to the text wordmark."""
    repo = SiteSettingsRepository(db)
    settings = repo.get_or_create()

    old_key = settings.logo_storage_key
    settings.logo_url = None
    settings.logo_storage_key = None
    settings.updated_by_id = current_user.id
    db.commit()
    db.refresh(settings)

    if old_key:
        _remove(old_key)

    return settings
