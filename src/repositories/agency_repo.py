"""Repository for Agency entities."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.db.models.agency_models import AgencyORM
from src.db.models.property_models import PropertyORM
from src.repositories.base import BaseRepository


class AgencyRepository(BaseRepository[AgencyORM]):
    def __init__(self, db: Session) -> None:
        super().__init__(AgencyORM, db)

    def list_active(self) -> list[AgencyORM]:
        stmt = select(AgencyORM).where(AgencyORM.is_active.is_(True)).order_by(AgencyORM.name)
        return list(self.db.scalars(stmt).all())

    def get_by_slug(self, slug: str) -> AgencyORM | None:
        return self.db.scalar(select(AgencyORM).where(AgencyORM.slug == slug))

    def slug_exists(self, slug: str) -> bool:
        return self.db.scalar(select(AgencyORM.id).where(AgencyORM.slug == slug)) is not None

    def published_property_counts(self) -> dict[str, int]:
        """Map agency_id → number of published, non-deleted properties."""
        rows = self.db.execute(
            select(PropertyORM.agency_id, func.count())
            .where(
                PropertyORM.status == "published",
                PropertyORM.deleted_at.is_(None),
                PropertyORM.agency_id.is_not(None),
            )
            .group_by(PropertyORM.agency_id)
        ).all()
        return {agency_id: count for agency_id, count in rows}
