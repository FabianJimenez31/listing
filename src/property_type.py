"""Property type catalog domain logic.

A focused, single-responsibility module that models the administrable
``PropertyType`` catalog (``code`` maps to :class:`PropertyKind`), enabling
type management "without touching code" per the canonical Listing contract.

Domain layer only: stdlib dataclasses + enum + validation. No FastAPI /
SQLAlchemy / Pydantic / HTTP / DB.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from src.property import PropertyKind


# Canonical slug regex from the contract: lowercase alphanumerics separated
# by single hyphens, no leading/trailing/double hyphens.
_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass
class PropertyType:
    """An administrable catalog entry for a kind of property.

    Maps a :class:`PropertyKind` to display metadata so property types can
    be managed without code changes.

    Attributes:
        id: UUID v4 string primary key.
        code: The :class:`PropertyKind` this type represents. A string is
            accepted and coerced to the matching enum member.
        name: Human-readable display name.
        slug: URL-safe identifier matching the canonical slug regex.
        icon: Optional icon identifier for the UI.
        is_active: Whether the type is selectable. Defaults to True.
    """

    id: str
    code: PropertyKind
    name: str
    slug: str
    icon: str | None = None
    is_active: bool = True

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name is required")
        if not self.slug:
            raise ValueError("slug is required")
        if not _SLUG_RE.match(self.slug):
            raise ValueError(f"slug is invalid: {self.slug}")
        if not isinstance(self.code, PropertyKind):
            try:
                self.code = PropertyKind(self.code)
            except ValueError as exc:
                raise ValueError(f"code is invalid: {self.code!r}") from exc
