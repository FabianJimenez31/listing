"""Search router: public property listing with filters and pagination."""
from __future__ import annotations

from fastapi import APIRouter, Query
from sqlalchemy.orm import Session

from src.api.deps import DB
from src.repositories.property_repo import PropertyRepository
from src.schemas.pagination_schemas import make_page
from src.schemas.property_schemas import PropertyListItem

router = APIRouter(prefix="/properties", tags=["search"])


@router.get("", response_model=dict)
def search_properties(
    db: DB,
    q: str | None = Query(None, description="Free-text search (title/description)"),
    operation_type: str | None = Query(None, description="sale | rent | temporary"),
    property_kind: str | None = Query(None, description="house | apartment | lot | …"),
    location_id: str | None = Query(None, description="Filter by location UUID"),
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
    items, total = repo.search(
        status="published",
        operation_type=operation_type,
        property_kind=property_kind,
        location_id=location_id,
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
