"""Banners and featured properties router."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.deps import DB, require_permission
from src.db.models.promotion_models import BannerORM, FeaturedPropertyORM
from src.repositories.banner_repo import BannerRepository, FeaturedPropertyRepository
from src.schemas.banner_schemas import (
    BannerCreateRequest,
    BannerResponse,
    FeaturedPropertyCreateRequest,
    FeaturedPropertyResponse,
)

router = APIRouter(tags=["banners"])


# ---------------------------------------------------------------------------
# Banners
# ---------------------------------------------------------------------------

@router.get("/banners", response_model=list[BannerResponse])
def list_banners(
    db: DB,
    position: str | None = Query(None),
    locality_id: str | None = Query(None),
    operation_type: str | None = Query(None),
    property_kind: str | None = Query(None),
):
    repo = BannerRepository(db)
    now = datetime.now(timezone.utc)

    if position:
        items = repo.list_active_for_position(
            position, now,
            locality_id=locality_id,
            operation_type=operation_type,
            property_kind=property_kind,
        )
    else:
        items = repo.list_all()

    return items


@router.post(
    "/banners",
    response_model=BannerResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("banner:create"))],
)
def create_banner(body: BannerCreateRequest, db: DB):
    banner = BannerORM(
        id=str(uuid.uuid4()),
        **body.model_dump(),
    )
    BannerRepository(db).add(banner)
    db.commit()
    db.refresh(banner)
    return banner


@router.delete(
    "/banners/{banner_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("banner:delete"))],
)
def delete_banner(banner_id: str, db: DB):
    repo = BannerRepository(db)
    banner = repo.get_by_id(banner_id)
    if not banner:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Banner not found")
    repo.delete(banner)
    db.commit()
    return None


# ---------------------------------------------------------------------------
# Featured properties
# ---------------------------------------------------------------------------

@router.get("/featured", response_model=list[FeaturedPropertyResponse])
def list_featured(
    db: DB,
    scope: str = Query("home", description="home | search_results | locality"),
    locality_id: str | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
):
    repo = FeaturedPropertyRepository(db)
    now = datetime.now(timezone.utc)
    return repo.list_active_for_scope(scope, now, locality_id=locality_id, limit=limit)


@router.post(
    "/featured",
    response_model=FeaturedPropertyResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("featured:create"))],
)
def create_featured(body: FeaturedPropertyCreateRequest, db: DB):
    if body.scope == "locality" and not body.locality_id:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "locality_id required for locality scope")

    now = datetime.now(timezone.utc)
    featured = FeaturedPropertyORM(
        id=str(uuid.uuid4()),
        property_id=body.property_id,
        scope=body.scope,
        locality_id=body.locality_id,
        priority=body.priority,
        starts_at=body.starts_at or now,
        ends_at=body.ends_at or (now + timedelta(days=365 * 10)),
    )
    FeaturedPropertyRepository(db).add(featured)
    db.commit()
    db.refresh(featured)
    return featured


@router.delete(
    "/featured/{featured_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("featured:delete"))],
)
def delete_featured(featured_id: str, db: DB):
    repo = FeaturedPropertyRepository(db)
    item = repo.get_by_id(featured_id)
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Featured entry not found")
    repo.delete(item)
    db.commit()
    return None
