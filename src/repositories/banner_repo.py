"""Repository for Banner and FeaturedProperty entities."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from src.db.models.promotion_models import BannerORM, FeaturedPropertyORM
from src.repositories.base import BaseRepository


class BannerRepository(BaseRepository[BannerORM]):
    def __init__(self, db: Session) -> None:
        super().__init__(BannerORM, db)

    def list_active_for_position(
        self,
        position: str,
        now: datetime,
        *,
        locality_id: str | None = None,
        operation_type: str | None = None,
        property_kind: str | None = None,
    ) -> list[BannerORM]:
        filters = [
            BannerORM.position == position,
            BannerORM.is_active.is_(True),
            or_(BannerORM.starts_at.is_(None), BannerORM.starts_at <= now),
            or_(BannerORM.ends_at.is_(None), BannerORM.ends_at >= now),
        ]
        if locality_id:
            filters.append(
                or_(BannerORM.locality_id.is_(None), BannerORM.locality_id == locality_id)
            )
        if operation_type:
            filters.append(
                or_(BannerORM.operation_type.is_(None), BannerORM.operation_type == operation_type)
            )
        if property_kind:
            filters.append(
                or_(BannerORM.property_kind.is_(None), BannerORM.property_kind == property_kind)
            )
        stmt = (
            select(BannerORM)
            .where(and_(*filters))
            .order_by(BannerORM.priority.desc())
        )
        return list(self.db.scalars(stmt).all())


class FeaturedPropertyRepository(BaseRepository[FeaturedPropertyORM]):
    def __init__(self, db: Session) -> None:
        super().__init__(FeaturedPropertyORM, db)

    def list_active_for_scope(
        self,
        scope: str,
        now: datetime,
        *,
        locality_id: str | None = None,
        limit: int = 10,
    ) -> list[FeaturedPropertyORM]:
        filters = [
            FeaturedPropertyORM.scope == scope,
            FeaturedPropertyORM.starts_at <= now,
            FeaturedPropertyORM.ends_at >= now,
        ]
        if scope == "locality":
            if not locality_id:
                return []
            filters.append(FeaturedPropertyORM.locality_id == locality_id)

        stmt = (
            select(FeaturedPropertyORM)
            .where(and_(*filters))
            .order_by(FeaturedPropertyORM.priority.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())
