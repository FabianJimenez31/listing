"""Repository for Partner entities (allied agencies & developers)."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models.partner_models import PartnerORM
from src.repositories.base import BaseRepository


class PartnerRepository(BaseRepository[PartnerORM]):
    def __init__(self, db: Session) -> None:
        super().__init__(PartnerORM, db)

    def list_active(self) -> list[PartnerORM]:
        stmt = (
            select(PartnerORM)
            .where(PartnerORM.is_active.is_(True))
            .order_by(PartnerORM.priority.desc(), PartnerORM.name)
        )
        return list(self.db.scalars(stmt).all())

    def slug_exists(self, slug: str) -> bool:
        return self.db.scalar(select(PartnerORM.id).where(PartnerORM.slug == slug)) is not None
