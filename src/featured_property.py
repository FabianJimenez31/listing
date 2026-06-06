"""Featured property domain logic.

A focused, single-responsibility module that models promoted (featured)
properties: where they are showcased (scope), for how long (the active
window), and engagement counters used to compute their CTR. Pure domain
layer — dataclasses, enums, validations and selection helpers only, with no
framework, HTTP or database concerns.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class FeaturedScope(str, Enum):
    """Surfaces where a featured property can be promoted.

    Keep this Enum in sync with persisted database values. The harness
    command ``make validate-enums`` enforces that consistency.
    """

    HOME = "home"
    SEARCH_RESULTS = "search_results"
    LOCALITY = "locality"


@dataclass
class FeaturedProperty:
    """A property promoted within a given scope and time window.

    Attributes:
        id: Unique identifier (UUID v4 string).
        property_id: Identifier of the promoted property.
        scope: Surface where the property is featured.
        priority: Ordering weight; higher is shown first. Must be ``>= 0``.
        locality_id: Required when ``scope`` is ``FeaturedScope.LOCALITY``.
        starts_at: Optional inclusive start of the active window (UTC).
        ends_at: Optional exclusive end of the active window (UTC).
        is_active: Whether the promotion is enabled.
        impressions_count: Denormalized count of impressions.
        clicks_count: Denormalized count of clicks.
    """

    id: str
    property_id: str
    scope: FeaturedScope
    priority: int = 0
    locality_id: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    is_active: bool = True
    impressions_count: int = 0
    clicks_count: int = 0

    def __post_init__(self) -> None:
        if not self.property_id:
            raise ValueError("property_id is required")
        if self.priority < 0:
            raise ValueError("priority cannot be negative")
        if self.scope == FeaturedScope.LOCALITY and not self.locality_id:
            raise ValueError("locality_id is required when scope is LOCALITY")
        if (
            self.starts_at is not None
            and self.ends_at is not None
            and self.starts_at >= self.ends_at
        ):
            raise ValueError("starts_at must be before ends_at")

    def is_active_at(self, moment: datetime) -> bool:
        """Return whether the promotion is live at ``moment``.

        A promotion is live when it is enabled and ``moment`` falls within the
        configured window. ``starts_at`` is inclusive and ``ends_at`` is
        exclusive; an unset bound means the window is open on that side.

        Args:
            moment: The instant to evaluate (UTC).

        Returns:
            ``True`` when active and within the window, otherwise ``False``.
        """
        if not self.is_active:
            return False
        if self.starts_at is not None and moment < self.starts_at:
            return False
        if self.ends_at is not None and moment >= self.ends_at:
            return False
        return True

    def ctr(self) -> float:
        """Return the click-through rate as a fraction in ``[0.0, 1.0]``.

        Returns:
            ``clicks_count / impressions_count`` rounded to 4 decimals, or
            ``0.0`` when there have been no impressions.
        """
        if self.impressions_count <= 0:
            return 0.0
        return round(self.clicks_count / self.impressions_count, 4)


def select_featured(
    items: list[FeaturedProperty],
    scope: FeaturedScope,
    moment: datetime,
    limit: int,
) -> list[FeaturedProperty]:
    """Pick the promotions to show for a scope at a given instant.

    Filters ``items`` to those matching ``scope`` and active at ``moment``,
    orders them by ``priority`` descending and truncates to ``limit``.

    Args:
        items: Candidate promotions.
        scope: Surface being rendered.
        moment: The instant to evaluate the active window against (UTC).
        limit: Maximum number of promotions to return. Non-positive values
            yield an empty list.

    Returns:
        The selected promotions, highest priority first.
    """
    if limit <= 0:
        return []
    eligible = [
        item
        for item in items
        if item.scope == scope and item.is_active_at(moment)
    ]
    eligible.sort(key=lambda item: item.priority, reverse=True)
    return eligible[:limit]
