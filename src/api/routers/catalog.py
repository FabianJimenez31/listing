"""Catalog aggregation router: property types + featured cities (with counts)."""
from __future__ import annotations

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from src.api.deps import DB
from src.db.models.catalog_models import PropertyTypeORM
from src.db.models.property_models import PropertyORM
from src.repositories.location_repo import LocationRepository
from src.schemas.catalog_schemas import FeaturedCityItem, PropertyTypeItem

router = APIRouter(tags=["catalog"])


@router.get("/property-types", response_model=list[PropertyTypeItem])
def list_property_types(db: DB):
    """Active property types with their published-property counts (category pills)."""
    rows = db.execute(
        select(PropertyORM.property_type_id, func.count())
        .where(
            PropertyORM.status == "published",
            PropertyORM.deleted_at.is_(None),
            PropertyORM.property_type_id.is_not(None),
        )
        .group_by(PropertyORM.property_type_id)
    ).all()
    counts = {type_id: count for type_id, count in rows}

    types = db.scalars(
        select(PropertyTypeORM)
        .where(PropertyTypeORM.is_active.is_(True))
        .order_by(PropertyTypeORM.name)
    ).all()

    result: list[PropertyTypeItem] = []
    for property_type in types:
        item = PropertyTypeItem.model_validate(property_type)
        item.property_count = counts.get(property_type.id, 0)
        result.append(item)
    return result


@router.get("/cities/featured", response_model=list[FeaturedCityItem])
def featured_cities(db: DB, limit: int = Query(8, ge=1, le=24)):
    """City-level locations with a cover image, ranked by property count."""
    result: list[FeaturedCityItem] = []
    for location, count, image_url in LocationRepository(db).featured_cities(limit=limit):
        item = FeaturedCityItem.model_validate(location)
        item.property_count = count
        item.image_url = image_url
        result.append(item)
    return result
