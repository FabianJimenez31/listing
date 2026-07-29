"""Properties router: CRUD + full publication lifecycle.

Lifecycle transitions map to domain methods in src/property.py.
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.deps import CurrentUser, DB, OptionalUser, require_permission
from src.db.models.property_models import PropertyORM
from src.repositories.property_repo import PropertyRepository
from src.schemas.property_schemas import (
    PropertyCreateRequest,
    PropertyRejectRequest,
    PropertyResponse,
    PropertyUpdateRequest,
    ShowOnHomeRequest,
)

router = APIRouter(prefix="/properties", tags=["properties"])


# ---------------------------------------------------------------------------
# Slug generation
# ---------------------------------------------------------------------------

def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s-]+", "-", text)
    return text.strip("-")[:80]


def _make_slug(operation_type: str, property_kind: str, title: str, short_id: str) -> str:
    return f"{operation_type}-{property_kind}-{_slugify(title)}-{short_id}"


def _unique_slug(base_slug: str, repo: PropertyRepository) -> str:
    slug = base_slug
    i = 2
    while repo.slug_exists(slug):
        slug = f"{base_slug}-{i}"
        i += 1
    return slug


# ---------------------------------------------------------------------------
# Ownership guard
# ---------------------------------------------------------------------------

def _require_owner_or_admin(prop: PropertyORM, user: "UserORM") -> None:
    if prop.owner_id != user.id and not user.has_permission("property:moderate"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not the property owner")


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

@router.post("", response_model=PropertyResponse, status_code=status.HTTP_201_CREATED)
def create_property(body: PropertyCreateRequest, current_user: CurrentUser, db: DB):
    repo = PropertyRepository(db)
    short_id = str(uuid.uuid4())[:8]
    base_slug = _make_slug(body.operation_type, body.property_kind, body.title, short_id)
    slug = _unique_slug(base_slug, repo)

    prop = PropertyORM(
        id=str(uuid.uuid4()),
        owner_id=current_user.id,
        title=body.title,
        slug=slug,
        description=body.description,
        operation_type=body.operation_type,
        property_kind=body.property_kind,
        condition=body.condition,
        price_amount=body.price_amount,
        currency=body.currency,
        total_area_m2=body.total_area_m2,
        built_area_m2=body.built_area_m2,
        bedrooms=body.bedrooms,
        bathrooms=body.bathrooms,
        parking_spots=body.parking_spots,
        has_storage=body.has_storage,
        has_elevator=body.has_elevator,
        has_study=body.has_study,
        has_balcony=body.has_balcony,
        floor_number=body.floor_number,
        total_floors=body.total_floors,
        stratum=body.stratum,
        view_type=body.view_type,
        age_years=body.age_years,
        admin_fee_amount=body.admin_fee_amount,
        security_type=body.security_type,
        address_street=body.address_street,
        address_detail=body.address_detail,
        location_id=body.location_id,
        property_type_id=body.property_type_id,
        contact_phone=body.contact_phone,
        contact_email=body.contact_email,
        contact_whatsapp=body.contact_whatsapp,
        expires_at=body.expires_at,
        show_on_home=body.show_on_home,
        status="draft",
    )
    repo.add(prop)
    db.commit()
    db.refresh(prop)
    return prop


@router.get("/{property_id}", response_model=PropertyResponse)
def get_property(property_id: str, current_user: OptionalUser, db: DB):
    repo = PropertyRepository(db)
    prop = repo.get_with_images(property_id)
    if not prop:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Property not found")

    # Non-published properties visible only to owner or admin
    if prop.status != "published":
        if not current_user:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Property not found")
        if prop.owner_id != current_user.id and not current_user.has_permission("property:read_all"):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Property not found")

    return prop


@router.put("/{property_id}", response_model=PropertyResponse)
def update_property(property_id: str, body: PropertyUpdateRequest, current_user: CurrentUser, db: DB):
    repo = PropertyRepository(db)
    prop = repo.get_by_id(property_id)
    if not prop or prop.deleted_at:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Property not found")
    _require_owner_or_admin(prop, current_user)

    if prop.status not in ("draft", "paused", "rejected"):
        raise HTTPException(status.HTTP_409_CONFLICT, "Only draft/paused/rejected properties can be edited freely")

    update_data = body.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(prop, field, value)

    db.commit()
    db.refresh(prop)
    return prop


@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_property(property_id: str, current_user: CurrentUser, db: DB):
    repo = PropertyRepository(db)
    prop = repo.get_by_id(property_id)
    if not prop or prop.deleted_at:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Property not found")
    _require_owner_or_admin(prop, current_user)

    prop.deleted_at = datetime.now(timezone.utc)
    prop.status = "deleted"
    db.commit()
    return None


@router.patch("/{property_id}/home", response_model=PropertyResponse)
def set_show_on_home(property_id: str, body: ShowOnHomeRequest, current_user: CurrentUser, db: DB):
    """Toggle home-page visibility. Independent of the publication status guard
    (a published property can be added/removed from the home without pausing it)."""
    repo = PropertyRepository(db)
    prop = repo.get_by_id(property_id)
    if not prop or prop.deleted_at:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Property not found")
    _require_owner_or_admin(prop, current_user)
    prop.show_on_home = body.show_on_home
    db.commit()
    db.refresh(prop)
    return prop


# ---------------------------------------------------------------------------
# Lifecycle transitions
# ---------------------------------------------------------------------------

@router.post("/{property_id}/submit", response_model=PropertyResponse)
def submit_for_review(property_id: str, current_user: CurrentUser, db: DB):
    """DRAFT → PENDING: submit property for admin review."""
    prop = PropertyRepository(db).get_with_images(property_id)
    if not prop or prop.deleted_at:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Property not found")
    _require_owner_or_admin(prop, current_user)

    if prop.status != "draft":
        raise HTTPException(status.HTTP_409_CONFLICT, f"Cannot submit from status: {prop.status}")
    if not prop.title or not prop.price_amount:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Title and price are required to submit")

    prop.status = "pending"
    db.commit()
    db.refresh(prop)
    return prop


@router.post(
    "/{property_id}/approve",
    response_model=PropertyResponse,
    dependencies=[Depends(require_permission("property:moderate"))],
)
def approve_property(property_id: str, db: DB):
    """PENDING → PUBLISHED (admin only)."""
    prop = PropertyRepository(db).get_by_id(property_id)
    if not prop or prop.deleted_at:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Property not found")
    if prop.status != "pending":
        raise HTTPException(status.HTTP_409_CONFLICT, f"Cannot approve from status: {prop.status}")

    prop.status = "published"
    prop.published_at = datetime.now(timezone.utc)
    prop.rejection_reason = None
    db.commit()
    db.refresh(prop)
    return prop


@router.post(
    "/{property_id}/reject",
    response_model=PropertyResponse,
    dependencies=[Depends(require_permission("property:moderate"))],
)
def reject_property(property_id: str, body: PropertyRejectRequest, db: DB):
    """PENDING → REJECTED (admin only)."""
    prop = PropertyRepository(db).get_by_id(property_id)
    if not prop or prop.deleted_at:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Property not found")
    if prop.status != "pending":
        raise HTTPException(status.HTTP_409_CONFLICT, f"Cannot reject from status: {prop.status}")

    prop.status = "rejected"
    prop.rejection_reason = body.reason
    db.commit()
    db.refresh(prop)
    return prop


@router.post("/{property_id}/pause", response_model=PropertyResponse)
def pause_property(property_id: str, current_user: CurrentUser, db: DB):
    """PUBLISHED → PAUSED."""
    prop = PropertyRepository(db).get_by_id(property_id)
    if not prop or prop.deleted_at:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Property not found")
    _require_owner_or_admin(prop, current_user)
    if prop.status != "published":
        raise HTTPException(status.HTTP_409_CONFLICT, f"Cannot pause from status: {prop.status}")

    prop.status = "paused"
    db.commit()
    db.refresh(prop)
    return prop


@router.post("/{property_id}/reactivate", response_model=PropertyResponse)
def reactivate_property(property_id: str, current_user: CurrentUser, db: DB):
    """PAUSED → PUBLISHED."""
    prop = PropertyRepository(db).get_by_id(property_id)
    if not prop or prop.deleted_at:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Property not found")
    _require_owner_or_admin(prop, current_user)
    if prop.status != "paused":
        raise HTTPException(status.HTTP_409_CONFLICT, f"Cannot reactivate from status: {prop.status}")

    prop.status = "published"
    db.commit()
    db.refresh(prop)
    return prop


@router.post("/{property_id}/mark-sold", response_model=PropertyResponse)
def mark_sold(property_id: str, current_user: CurrentUser, db: DB):
    """PUBLISHED|PAUSED → SOLD (sale operation only)."""
    prop = PropertyRepository(db).get_by_id(property_id)
    if not prop or prop.deleted_at:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Property not found")
    _require_owner_or_admin(prop, current_user)
    if prop.operation_type != "sale":
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Only sale properties can be marked sold")
    if prop.status not in ("published", "paused"):
        raise HTTPException(status.HTTP_409_CONFLICT, f"Cannot mark sold from status: {prop.status}")

    prop.status = "sold"
    db.commit()
    db.refresh(prop)
    return prop


@router.post("/{property_id}/mark-rented", response_model=PropertyResponse)
def mark_rented(property_id: str, current_user: CurrentUser, db: DB):
    """PUBLISHED|PAUSED → RENTED (rent/temporary operation only)."""
    prop = PropertyRepository(db).get_by_id(property_id)
    if not prop or prop.deleted_at:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Property not found")
    _require_owner_or_admin(prop, current_user)
    if prop.operation_type not in ("rent", "temporary"):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Only rent/temporary properties can be marked rented")
    if prop.status not in ("published", "paused"):
        raise HTTPException(status.HTTP_409_CONFLICT, f"Cannot mark rented from status: {prop.status}")

    prop.status = "rented"
    db.commit()
    db.refresh(prop)
    return prop


@router.post("/{property_id}/duplicate", response_model=PropertyResponse)
def duplicate_property(property_id: str, current_user: CurrentUser, db: DB):
    """Clone a property as a new DRAFT (owner or admin)."""
    repo = PropertyRepository(db)
    source = repo.get_with_images(property_id)
    if not source or source.deleted_at:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Property not found")
    _require_owner_or_admin(source, current_user)

    short_id = str(uuid.uuid4())[:8]
    base_slug = _make_slug(source.operation_type, source.property_kind, source.title, short_id)
    slug = _unique_slug(base_slug, repo)

    clone = PropertyORM(
        id=str(uuid.uuid4()),
        owner_id=current_user.id,
        title=source.title,
        slug=slug,
        description=source.description,
        operation_type=source.operation_type,
        property_kind=source.property_kind,
        condition=source.condition,
        price_amount=source.price_amount,
        currency=source.currency,
        total_area_m2=source.total_area_m2,
        built_area_m2=source.built_area_m2,
        bedrooms=source.bedrooms,
        bathrooms=source.bathrooms,
        parking_spots=source.parking_spots,
        has_storage=source.has_storage,
        has_elevator=source.has_elevator,
        has_study=source.has_study,
        has_balcony=source.has_balcony,
        floor_number=source.floor_number,
        total_floors=source.total_floors,
        stratum=source.stratum,
        view_type=source.view_type,
        age_years=source.age_years,
        admin_fee_amount=source.admin_fee_amount,
        security_type=source.security_type,
        address_street=source.address_street,
        address_detail=source.address_detail,
        location_id=source.location_id,
        property_type_id=source.property_type_id,
        contact_phone=source.contact_phone,
        contact_email=source.contact_email,
        contact_whatsapp=source.contact_whatsapp,
        status="draft",
    )
    repo.add(clone)
    db.commit()
    db.refresh(clone)
    return clone
