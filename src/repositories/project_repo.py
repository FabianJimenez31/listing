"""Repository for Project and ProjectImage entities."""
from __future__ import annotations

from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, joinedload

from src.db.models.project_models import ProjectImageORM, ProjectORM
from src.repositories.base import BaseRepository
from src.repositories.location_repo import LocationRepository
from src.text.search_normalization import normalized_sql, search_like_pattern


class ProjectRepository(BaseRepository[ProjectORM]):
    def __init__(self, db: Session) -> None:
        super().__init__(ProjectORM, db)

    def get_by_slug(self, slug: str) -> ProjectORM | None:
        stmt = (
            select(ProjectORM)
            .where(ProjectORM.slug == slug, ProjectORM.deleted_at.is_(None))
            .options(
                joinedload(ProjectORM.images),
                joinedload(ProjectORM.location),
                joinedload(ProjectORM.agency),
            )
        )
        return self.db.scalar(stmt)

    def slug_exists(self, slug: str, exclude_id: str | None = None) -> bool:
        stmt = select(ProjectORM.id).where(ProjectORM.slug == slug)
        if exclude_id:
            stmt = stmt.where(ProjectORM.id != exclude_id)
        return self.db.scalar(stmt) is not None

    def search(
        self,
        *,
        status: str | None = "published",
        stage: str | None = None,
        location_id: str | None = None,
        location_ids: list[str] | None = None,
        country_ids: list[str] | None = None,
        property_type_id: str | None = None,
        min_price: int | None = None,
        max_price: int | None = None,
        text: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ProjectORM], int]:
        filters: list[Any] = [ProjectORM.deleted_at.is_(None)]

        if status:
            filters.append(ProjectORM.status == status)
        if stage:
            filters.append(ProjectORM.stage == stage)
        if location_id:
            filters.append(ProjectORM.location_id == location_id)
        if location_ids is not None:
            filters.append(ProjectORM.location_id.in_(location_ids or ["__none__"]))
        if country_ids is not None:
            filters.append(ProjectORM.location_id.in_(country_ids or ["__none__"]))
        if property_type_id:
            filters.append(ProjectORM.property_type_id == property_type_id)
        if min_price is not None:
            # A project matches if its range reaches the requested floor.
            filters.append(
                or_(ProjectORM.price_to >= min_price, ProjectORM.price_from >= min_price)
            )
        if max_price is not None:
            filters.append(ProjectORM.price_from <= max_price)
        if text:
            pattern = search_like_pattern(text)
            matching_locations = LocationRepository(self.db).searchable_subtree_ids(text)
            if pattern:
                filters.append(
                    or_(
                        normalized_sql(ProjectORM.title).like(pattern),
                        normalized_sql(ProjectORM.description).like(pattern),
                        normalized_sql(ProjectORM.developer_name).like(pattern),
                        ProjectORM.location_id.in_(matching_locations or ["__none__"]),
                    )
                )

        base_stmt = select(ProjectORM).where(and_(*filters))
        total = self.db.scalar(select(func.count()).select_from(base_stmt.subquery())) or 0

        stmt = (
            base_stmt
            .options(
                joinedload(ProjectORM.images),
                joinedload(ProjectORM.location),
                joinedload(ProjectORM.agency),
            )
            .order_by(ProjectORM.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list(self.db.scalars(stmt).unique().all())
        return items, total


class ProjectImageRepository(BaseRepository[ProjectImageORM]):
    def __init__(self, db: Session) -> None:
        super().__init__(ProjectImageORM, db)

    def list_by_project(self, project_id: str) -> list[ProjectImageORM]:
        stmt = (
            select(ProjectImageORM)
            .where(ProjectImageORM.project_id == project_id)
            .order_by(ProjectImageORM.position)
        )
        return list(self.db.scalars(stmt).all())
