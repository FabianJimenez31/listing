"""Repository for Property and PropertyImage entities."""
from __future__ import annotations

from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, joinedload

from src.db.models.property_models import PropertyImageORM, PropertyORM
from src.repositories.base import BaseRepository


class PropertyRepository(BaseRepository[PropertyORM]):
    def __init__(self, db: Session) -> None:
        super().__init__(PropertyORM, db)

    def get_by_slug(self, slug: str) -> PropertyORM | None:
        stmt = select(PropertyORM).where(
            PropertyORM.slug == slug,
            PropertyORM.deleted_at.is_(None),
        )
        return self.db.scalar(stmt)

    def get_published_by_slug(self, slug: str) -> PropertyORM | None:
        stmt = select(PropertyORM).where(
            PropertyORM.slug == slug,
            PropertyORM.status == "published",
            PropertyORM.deleted_at.is_(None),
        ).options(
            joinedload(PropertyORM.images),
            joinedload(PropertyORM.location),
            joinedload(PropertyORM.owner),
        )
        return self.db.scalar(stmt)

    def get_with_images(self, id: str) -> PropertyORM | None:
        stmt = (
            select(PropertyORM)
            .where(PropertyORM.id == id, PropertyORM.deleted_at.is_(None))
            .options(joinedload(PropertyORM.images), joinedload(PropertyORM.location))
        )
        return self.db.scalar(stmt)

    def slug_exists(self, slug: str, exclude_id: str | None = None) -> bool:
        stmt = select(PropertyORM.id).where(PropertyORM.slug == slug)
        if exclude_id:
            stmt = stmt.where(PropertyORM.id != exclude_id)
        return self.db.scalar(stmt) is not None

    def search(
        self,
        *,
        status: str | None = "published",
        operation_type: str | None = None,
        property_kind: str | None = None,
        location_id: str | None = None,
        min_price: int | None = None,
        max_price: int | None = None,
        min_bedrooms: int | None = None,
        max_bedrooms: int | None = None,
        min_area: float | None = None,
        max_area: float | None = None,
        text: str | None = None,
        owner_id: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[PropertyORM], int]:
        filters: list[Any] = [PropertyORM.deleted_at.is_(None)]

        if status:
            filters.append(PropertyORM.status == status)
        if operation_type:
            filters.append(PropertyORM.operation_type == operation_type)
        if property_kind:
            filters.append(PropertyORM.property_kind == property_kind)
        if location_id:
            filters.append(PropertyORM.location_id == location_id)
        if min_price is not None:
            filters.append(PropertyORM.price_amount >= min_price)
        if max_price is not None:
            filters.append(PropertyORM.price_amount <= max_price)
        if min_bedrooms is not None:
            filters.append(PropertyORM.bedrooms >= min_bedrooms)
        if max_bedrooms is not None:
            filters.append(PropertyORM.bedrooms <= max_bedrooms)
        if min_area is not None:
            filters.append(PropertyORM.total_area_m2 >= min_area)
        if max_area is not None:
            filters.append(PropertyORM.total_area_m2 <= max_area)
        if owner_id:
            filters.append(PropertyORM.owner_id == owner_id)
        if text:
            pattern = f"%{text}%"
            filters.append(or_(
                PropertyORM.title.ilike(pattern),
                PropertyORM.description.ilike(pattern),
            ))

        base_stmt = select(PropertyORM).where(and_(*filters))
        total = self.db.scalar(select(func.count()).select_from(base_stmt.subquery())) or 0

        stmt = (
            base_stmt
            .options(joinedload(PropertyORM.images), joinedload(PropertyORM.location))
            .order_by(PropertyORM.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list(self.db.scalars(stmt).unique().all())
        return items, total

    def list_by_owner(self, owner_id: str, page: int = 1, page_size: int = 20) -> tuple[list[PropertyORM], int]:
        return self.search(status=None, owner_id=owner_id, page=page, page_size=page_size)


class PropertyImageRepository(BaseRepository[PropertyImageORM]):
    def __init__(self, db: Session) -> None:
        super().__init__(PropertyImageORM, db)

    def list_by_property(self, property_id: str) -> list[PropertyImageORM]:
        stmt = (
            select(PropertyImageORM)
            .where(PropertyImageORM.property_id == property_id)
            .order_by(PropertyImageORM.position)
        )
        return list(self.db.scalars(stmt).all())

    def get_main_image(self, property_id: str) -> PropertyImageORM | None:
        stmt = select(PropertyImageORM).where(
            PropertyImageORM.property_id == property_id,
            PropertyImageORM.role == "main",
        )
        return self.db.scalar(stmt)
