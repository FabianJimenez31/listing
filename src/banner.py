"""Banner domain logic for the Listing real-estate platform.

A focused, single-responsibility domain module modelling promotional
banners and their scheduling window. Pure domain layer: dataclasses,
enums, validations and domain methods only (no FastAPI/SQLAlchemy/HTTP/DB).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class BannerPosition(str, Enum):
    """Placement slot a banner can occupy across the site."""

    HOME_HERO = "home_hero"
    HOME_INLINE = "home_inline"
    LISTING_TOP = "listing_top"
    LISTING_INLINE = "listing_inline"
    DETAIL_SIDEBAR = "detail_sidebar"


@dataclass
class Banner:
    """A promotional banner with a placement, schedule and targeting.

    Attributes:
        id: UUID v4 string primary key.
        title: Human-readable banner title (required).
        image_desktop_url: Desktop creative URL (required).
        image_mobile_url: Mobile creative URL (required).
        cta_label: Call-to-action label (required).
        cta_url: Call-to-action destination URL (required).
        position: Placement slot for the banner.
        priority: Ordering weight; higher shows first. Must be >= 0.
        description: Optional descriptive text.
        starts_at: Optional UTC start of the active window.
        ends_at: Optional UTC end of the active window.
        is_active: Master on/off switch.
        target_locality_id: Optional locality FK to scope the banner.
        target_city: Optional city to scope the banner.
        target_operation: Optional OperationType value to scope the banner.
        target_kind: Optional PropertyKind value to scope the banner.
        impressions_count: Denormalized impression counter.
        clicks_count: Denormalized click counter.
    """

    id: str
    title: str
    image_desktop_url: str
    image_mobile_url: str
    cta_label: str
    cta_url: str
    position: BannerPosition
    priority: int = 0
    description: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    is_active: bool = True
    target_locality_id: str | None = None
    target_city: str | None = None
    target_operation: str | None = None
    target_kind: str | None = None
    impressions_count: int = 0
    clicks_count: int = 0

    def __post_init__(self) -> None:
        if not self.title:
            raise ValueError("title is required")
        if not self.image_desktop_url:
            raise ValueError("image_desktop_url is required")
        if not self.image_mobile_url:
            raise ValueError("image_mobile_url is required")
        if not self.cta_label:
            raise ValueError("cta_label is required")
        if not self.cta_url:
            raise ValueError("cta_url is required")
        if self.priority < 0:
            raise ValueError("priority cannot be negative")
        if (
            self.starts_at is not None
            and self.ends_at is not None
            and self.starts_at >= self.ends_at
        ):
            raise ValueError("starts_at must be before ends_at")

    def is_active_at(self, moment: datetime) -> bool:
        """Return whether the banner is live at ``moment``.

        The banner must be active and ``moment`` must fall within the
        scheduling window. A missing bound is treated as open-ended.

        Args:
            moment: The UTC instant to evaluate.

        Returns:
            ``True`` if active and within the window, else ``False``.
        """
        if not self.is_active:
            return False
        if self.starts_at is not None and moment < self.starts_at:
            return False
        if self.ends_at is not None and moment > self.ends_at:
            return False
        return True

    def ctr(self) -> float:
        """Return the click-through rate (clicks / impressions).

        Returns:
            The CTR as a float, or ``0.0`` when there are no impressions.
        """
        if self.impressions_count == 0:
            return 0.0
        return self.clicks_count / self.impressions_count

    def register_impression(self) -> None:
        """Increment the impression counter by one."""
        self.impressions_count += 1

    def register_click(self) -> None:
        """Increment the click counter by one."""
        self.clicks_count += 1
