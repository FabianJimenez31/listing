"""Repository for Lead entities."""
from __future__ import annotations

from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from src.db.models.lead_models import LeadORM
from src.repositories.base import BaseRepository


class LeadRepository(BaseRepository[LeadORM]):
    def __init__(self, db: Session) -> None:
        super().__init__(LeadORM, db)

    def list_for_property(
        self,
        property_id: str,
        *,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[LeadORM], int]:
        filters: list[Any] = [LeadORM.property_id == property_id]
        if status:
            filters.append(LeadORM.status == status)
        return self._paginate(filters, page, page_size)

    def list_for_agent(
        self,
        owner_id: str,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[LeadORM], int]:
        return self._paginate([LeadORM.owner_id == owner_id], page, page_size)

    def list_all_admin(
        self,
        *,
        property_id: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[LeadORM], int]:
        filters: list[Any] = []
        if property_id:
            filters.append(LeadORM.property_id == property_id)
        if status:
            filters.append(LeadORM.status == status)
        return self._paginate(filters, page, page_size)

    def _paginate(
        self,
        filters: list[Any],
        page: int,
        page_size: int,
    ) -> tuple[list[LeadORM], int]:
        base_stmt = select(LeadORM).where(and_(*filters) if filters else True)
        total = self.db.scalar(select(func.count()).select_from(base_stmt.subquery())) or 0
        stmt = base_stmt.order_by(LeadORM.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        return list(self.db.scalars(stmt).all()), total
