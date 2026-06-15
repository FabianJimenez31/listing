"""Repository for the Location hierarchy + aggregation helpers."""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models.location_models import LocationORM
from src.db.models.property_models import PropertyORM
from src.repositories.base import BaseRepository

# Friendly country codes → seeded location slug
_COUNTRY_ALIASES = {
    "us": "estados-unidos",
    "usa": "estados-unidos",
    "co": "colombia",
}


class LocationRepository(BaseRepository[LocationORM]):
    def __init__(self, db: Session) -> None:
        super().__init__(LocationORM, db)

    def get_by_slug(self, slug: str) -> LocationORM | None:
        return self.db.scalar(select(LocationORM).where(LocationORM.slug == slug))

    def list_filtered(self, *, level: str | None = None, parent_id: str | None = None) -> list[LocationORM]:
        filters: list[Any] = []
        if level:
            filters.append(LocationORM.level == level)
        if parent_id:
            filters.append(LocationORM.parent_id == parent_id)
        stmt = select(LocationORM).where(*filters).order_by(LocationORM.name)
        return list(self.db.scalars(stmt).all())

    def subtree_ids(self, root_slug: str) -> list[str]:
        """Return the id of ``root_slug`` plus all descendant location ids.

        Drives the ``country`` filter ("Mercado USA"): a property anywhere under
        the country node matches. The locations table is small, so the hierarchy
        is walked in memory rather than with a recursive CTE.
        """
        root_slug = _COUNTRY_ALIASES.get(root_slug.lower(), root_slug)
        rows = self.db.execute(
            select(LocationORM.id, LocationORM.parent_id, LocationORM.slug)
        ).all()
        children: dict[str | None, list[str]] = {}
        slug_to_id: dict[str, str] = {}
        for loc_id, parent_id, slug in rows:
            children.setdefault(parent_id, []).append(loc_id)
            slug_to_id[slug] = loc_id

        root_id = slug_to_id.get(root_slug)
        if not root_id:
            return []
        out = [root_id]
        stack = [root_id]
        while stack:
            current = stack.pop()
            for child_id in children.get(current, []):
                out.append(child_id)
                stack.append(child_id)
        return out

    def featured_cities(self, limit: int = 8) -> list[tuple[LocationORM, int]]:
        """City-level locations ranked by published-property count (subtree).

        Properties hang off localities/neighborhoods, so each published property
        is rolled up to its nearest ``city`` ancestor.
        """
        locations = list(self.db.scalars(select(LocationORM)).all())
        by_id: dict[str, LocationORM] = {loc.id: loc for loc in locations}

        from sqlalchemy import func  # local import keeps top-level imports lean

        rows = self.db.execute(
            select(PropertyORM.location_id, func.count())
            .where(
                PropertyORM.status == "published",
                PropertyORM.deleted_at.is_(None),
                PropertyORM.location_id.is_not(None),
            )
            .group_by(PropertyORM.location_id)
        ).all()

        city_counts: dict[str, int] = {}
        for loc_id, count in rows:
            node = by_id.get(loc_id)
            while node is not None and node.level != "city":
                node = by_id.get(node.parent_id)
            if node is not None:
                city_counts[node.id] = city_counts.get(node.id, 0) + count

        cities = [loc for loc in locations if loc.level == "city" and loc.is_active]
        cities.sort(key=lambda c: (-city_counts.get(c.id, 0), c.name))
        return [(city, city_counts.get(city.id, 0)) for city in cities[:limit]]
