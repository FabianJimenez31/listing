"""Location domain logic for the Listing platform.

A focused, single-responsibility module that models geographic
coordinates and hierarchical locations (country / state / city /
locality / neighborhood). Pure domain layer: dataclasses, enums,
validations and domain methods only (stdlib only).

Mirrors the ``Location`` entity of the canonical contract.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass

# Slug regex from the canonical contract: lowercase alphanumeric words
# separated by single hyphens, no leading/trailing/double hyphens.
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# Mean Earth radius in kilometers (used by the haversine formula).
EARTH_RADIUS_KM = 6371.0088


@dataclass
class Coordinates:
    """A geographic point expressed as decimal degrees (WGS84 / 4326).

    Attributes:
        latitude: Latitude in degrees, constrained to ``[-90, 90]``.
        longitude: Longitude in degrees, constrained to ``[-180, 180]``.
    """

    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        if not -90 <= self.latitude <= 90:
            raise ValueError("latitude must be between -90 and 90")
        if not -180 <= self.longitude <= 180:
            raise ValueError("longitude must be between -180 and 180")

    def distance_km_to(self, other: Coordinates) -> float:
        """Great-circle distance to ``other`` in kilometers (haversine).

        Args:
            other: The destination coordinate.

        Returns:
            The haversine distance between the two points, in kilometers.
        """
        lat1 = math.radians(self.latitude)
        lat2 = math.radians(other.latitude)
        d_lat = math.radians(other.latitude - self.latitude)
        d_lon = math.radians(other.longitude - self.longitude)

        a = (
            math.sin(d_lat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(d_lon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))
        return EARTH_RADIUS_KM * c


@dataclass
class Location:
    """A node in the geographic hierarchy used to place properties.

    Country, city and slug are mandatory. The remaining administrative
    levels are optional so the same entity can represent any depth of the
    hierarchy (a country root down to a neighborhood leaf).

    Attributes:
        id: UUID v4 primary key (string).
        country: Country name (required).
        city: City name (required).
        slug: URL-safe identifier matching :data:`SLUG_RE` (required).
        state_province: State / province name, if any.
        locality: Locality / district name, if any.
        neighborhood: Neighborhood name, if any.
        parent_id: ``id`` of the parent location node, if any.
        center: Geographic center of the location, if known.
        is_active: Whether the location is selectable / visible.
    """

    id: str
    country: str
    city: str
    slug: str
    state_province: str | None = None
    locality: str | None = None
    neighborhood: str | None = None
    parent_id: str | None = None
    center: Coordinates | None = None
    is_active: bool = True

    def __post_init__(self) -> None:
        if not self.country:
            raise ValueError("country is required")
        if not self.city:
            raise ValueError("city is required")
        if not self.slug:
            raise ValueError("slug is required")
        if not SLUG_RE.match(self.slug):
            raise ValueError(f"invalid slug: {self.slug}")

    @property
    def is_root(self) -> bool:
        """Whether this location has no parent node."""
        return self.parent_id is None

    def distance_km_to(self, other: Location) -> float:
        """Distance in kilometers between two located nodes.

        Args:
            other: The destination location.

        Returns:
            Haversine distance between the two centers, in kilometers.

        Raises:
            ValueError: If either location is missing its ``center``.
        """
        if self.center is None or other.center is None:
            raise ValueError("both locations require a center to measure distance")
        return self.center.distance_km_to(other.center)

    def activate(self) -> None:
        """Mark the location as active."""
        self.is_active = True

    def deactivate(self) -> None:
        """Mark the location as inactive."""
        self.is_active = False
