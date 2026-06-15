"""Search router: public property listing with filters and pagination."""
from __future__ import annotations

from fastapi import APIRouter, Query

from src.api.deps import DB, OptionalUser
from src.repositories.property_repo import PropertyRepository
from src.schemas.pagination_schemas import make_page
from src.schemas.property_schemas import PropertyListItem

router = APIRouter(prefix="/properties", tags=["search"])


@router.get("", response_model=dict)
def search_properties(
    db: DB,
    current_user: OptionalUser,
    q: str | None = Query(None, description="Free-text search (title/description)"),
    operation_type: str | None = Query(None, description="sale | rent | temporary"),
    property_kind: str | None = Query(None, description="house | apartment | lot | …"),
    location_id: str | None = Query(None, description="Filter by location UUID"),
    country: str | None = Query(None, description="Country slug or code (e.g. 'us', 'colombia') — Mercado USA"),
    agency_id: str | None = Query(None, description="Filter by agency UUID"),
    owner_id: str | None = Query(None, description="Filter by owner (admins with property:read_all)"),
    include_own: bool = Query(False, description="Return the caller's own properties across all statuses"),
    on_home: bool = Query(False, description="Only properties flagged to show on the home page"),
    min_price: int | None = Query(None, ge=0, description="Min price in minor units"),
    max_price: int | None = Query(None, ge=0, description="Max price in minor units"),
    min_bedrooms: int | None = Query(None, ge=0),
    max_bedrooms: int | None = Query(None, ge=0),
    min_area: float | None = Query(None, ge=0, description="Min total area m²"),
    max_area: float | None = Query(None, ge=0, description="Max total area m²"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    repo = PropertyRepository(db)

    # Default: public listing of published properties only.
    search_status: str | None = "published"
    search_owner: str | None = None
    if include_own and current_user:
        # "Mis propiedades": the caller's own listings in every status (drafts too)
        search_status = None
        search_owner = current_user.id
    elif owner_id and current_user and current_user.has_permission("property:read_all"):
        search_owner = owner_id

    items, total = repo.search(
        status=search_status,
        owner_id=search_owner,
        operation_type=operation_type,
        property_kind=property_kind,
        location_id=location_id,
        country=country,
        agency_id=agency_id,
        on_home=on_home,
        min_price=min_price,
        max_price=max_price,
        min_bedrooms=min_bedrooms,
        max_bedrooms=max_bedrooms,
        min_area=min_area,
        max_area=max_area,
        text=q,
        page=page,
        page_size=page_size,
    )

    # Attach main_image to each item for the list view
    result = []
    for prop in items:
        main_image = next((img for img in prop.images if img.role == "main"), None)
        item = PropertyListItem.model_validate(prop)
        item.main_image = main_image
        result.append(item.model_dump())

    return make_page(result, page, page_size, total)
