"""Amenity domain logic.

A focused, single-responsibility module that models property amenities and
the association between a property and an amenity (``PropertyAmenity``).
Pure domain layer: stdlib dataclasses + validation only, no FastAPI / ORM /
HTTP / DB. Names and fields follow the canonical Listing contract.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Amenity:
    """A reusable property feature (e.g. pool, gym, security).

    Attributes:
        id: UUID v4 string primary key.
        code: Unique machine code, normalized to lowercase with spaces
            replaced by underscores.
        name: Human-readable display name.
        category: Optional grouping label (e.g. "comfort", "security").
        icon: Optional icon identifier for the UI.
        is_active: Whether the amenity is selectable. Defaults to True.
    """

    id: str
    code: str
    name: str
    category: str | None = None
    icon: str | None = None
    is_active: bool = True

    def __post_init__(self) -> None:
        if not self.code:
            raise ValueError("code is required")
        if not self.name:
            raise ValueError("name is required")
        self.code = self.code.strip().lower().replace(" ", "_")
        if not self.code:
            raise ValueError("code is required")


@dataclass
class PropertyAmenity:
    """Association between a property and an amenity (composite key).

    Attributes:
        property_id: UUID v4 string referencing the owning property.
        amenity_id: UUID v4 string referencing the amenity.
        value: Optional qualifier for the amenity (e.g. "2" parking spots).
    """

    property_id: str
    amenity_id: str
    value: str | None = None

    def __post_init__(self) -> None:
        if not self.property_id:
            raise ValueError("property_id is required")
        if not self.amenity_id:
            raise ValueError("amenity_id is required")
