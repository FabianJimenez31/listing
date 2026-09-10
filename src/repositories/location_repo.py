"""Repository for the Location hierarchy + aggregation helpers."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models.location_models import LocationORM
from src.db.models.property_models import PropertyImageORM, PropertyORM
from src.repositories.base import BaseRepository
from src.text.search_normalization import normalize_search_text
from src.text.slug import slugify

# External stock/placeholder hosts seeded onto locations. Treated as "no curated
# image" so a real property cover wins (some, e.g. Unsplash links, are now dead).
_PLACEHOLDER_IMAGE_HOSTS = ("picsum.photos", "unsplash.com")

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

    def find_sibling(self, *, name: str, level: str, parent_id: str | None) -> LocationORM | None:
        """Same name, same level, same parent — i.e. the node the admin is about to
        duplicate. Case/accent-insensitive on the generated slug, so "Panamá" and
        "panama" are recognised as the same place."""
        target = slugify(name)
        candidates = self.db.scalars(
            select(LocationORM).where(
                LocationORM.level == level,
                LocationORM.parent_id == parent_id,
            )
        ).all()
        for candidate in candidates:
            if slugify(candidate.name) == target:
                return candidate
        return None

    def unique_slug(self, base: str, parent: LocationORM | None) -> str:
        """A free slug for a new node: ``base``, then ``parent-base``, then ``base-2``…

        The ``slug`` column is globally unique, so names that repeat across cities
        ("Centro", "El Poblado") need disambiguation.
        """
        base = slugify(base) or "ubicacion"
        candidates = [base]
        if parent is not None:
            candidates.append(f"{slugify(parent.slug)}-{base}")
        for i in range(2, 100):
            candidates.append(f"{base}-{i}")
        for candidate in candidates:
            if self.get_by_slug(candidate) is None:
                return candidate
        return f"{base}-{uuid.uuid4().hex[:8]}"

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

    def searchable_subtree_ids(self, text: str) -> list[str]:
        """IDs below locations whose name/slug contains all normalized words."""
        tokens = normalize_search_text(text).split()
        if not tokens:
            return []

        rows = self.db.execute(
            select(LocationORM.id, LocationORM.parent_id, LocationORM.name, LocationORM.slug)
        ).all()
        children: dict[str | None, list[str]] = {}
        by_id: dict[str, tuple[str | None, str, str]] = {}
        for loc_id, parent_id, name, slug in rows:
            children.setdefault(parent_id, []).append(loc_id)
            by_id[loc_id] = (parent_id, name, slug)

        matches: list[str] = []
        for loc_id in by_id:
            path_parts: list[str] = []
            current_id: str | None = loc_id
            seen: set[str] = set()
            while current_id and current_id not in seen and current_id in by_id:
                seen.add(current_id)
                parent_id, name, slug = by_id[current_id]
                path_parts.extend((normalize_search_text(name), normalize_search_text(slug)))
                current_id = parent_id
            searchable = " ".join(path_parts)
            if all(token in searchable for token in tokens):
                matches.append(loc_id)

        found: set[str] = set(matches)
        stack = list(matches)
        while stack:
            for child_id in children.get(stack.pop(), []):
                if child_id not in found:
                    found.add(child_id)
                    stack.append(child_id)
        return list(found)

    def city_name_by_location(self) -> dict[str, str]:
        """``location_id`` → name of its nearest ``city`` ancestor (itself included).

        Properties hang off mixed levels (barrio, localidad, city). The inventory
        export rolls every row up to its city with this single lookup instead of
        walking ``parent`` per property.
        """
        rows = self.db.execute(
            select(LocationORM.id, LocationORM.parent_id, LocationORM.level, LocationORM.name)
        ).all()
        by_id = {row.id: row for row in rows}

        cities: dict[str, str] = {}
        for row in rows:
            node = row
            seen: set[str] = set()
            while node is not None and node.level != "city" and node.id not in seen:
                seen.add(node.id)
                node = by_id.get(node.parent_id)
            if node is not None and node.level == "city":
                cities[row.id] = node.name
        return cities

    def featured_cities(self, limit: int = 8) -> list[tuple[LocationORM, int, str | None]]:
        """City-level locations ranked by published-property count (subtree), each
        with a representative cover image.

        Properties hang off localities/neighborhoods, so each published property is
        rolled up to its nearest ``city`` ancestor. The image is the city's own
        curated ``image_url`` when set, otherwise the cover photo of a published
        property in that city (newest first) — so cards are never empty. A picsum
        placeholder stored on the location is treated as "unset" so a real photo
        takes over.
        """
        locations = list(self.db.scalars(select(LocationORM)).all())
        by_id: dict[str, LocationORM] = {loc.id: loc for loc in locations}

        from sqlalchemy import func  # local import keeps top-level imports lean

        def city_of(loc_id: str | None) -> LocationORM | None:
            node = by_id.get(loc_id)
            while node is not None and node.level != "city":
                node = by_id.get(node.parent_id)
            return node

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
            node = city_of(loc_id)
            if node is not None:
                city_counts[node.id] = city_counts.get(node.id, 0) + count

        # One representative cover per city: the main photo of the newest published
        # property rolled up to that city (setdefault keeps the first / newest seen).
        img_rows = self.db.execute(
            select(PropertyORM.location_id, PropertyImageORM.cdn_url)
            .join(PropertyImageORM, PropertyImageORM.property_id == PropertyORM.id)
            .where(
                PropertyORM.status == "published",
                PropertyORM.deleted_at.is_(None),
                PropertyImageORM.role == "main",
                PropertyImageORM.cdn_url.is_not(None),
            )
            .order_by(PropertyORM.created_at.desc())
        ).all()

        city_image: dict[str, str] = {}
        for loc_id, cdn_url in img_rows:
            node = city_of(loc_id)
            if node is not None:
                city_image.setdefault(node.id, cdn_url)

        def cover(city: LocationORM) -> str | None:
            own = city.image_url
            is_placeholder = own and any(h in own for h in _PLACEHOLDER_IMAGE_HOSTS)
            if own and not is_placeholder:
                return own  # genuinely curated location image wins
            return city_image.get(city.id) or own  # else a real property cover

        cities = [loc for loc in locations if loc.level == "city" and loc.is_active]
        cities.sort(key=lambda c: (-city_counts.get(c.id, 0), c.name))
        return [(city, city_counts.get(city.id, 0), cover(city)) for city in cities[:limit]]
