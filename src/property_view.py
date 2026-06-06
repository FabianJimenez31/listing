"""Property view / engagement event domain logic.

A focused, single-responsibility module that models property engagement
events (views and clicks) as defined by the Listing canonical contract.
This is the event store for property metrics; denormalized counters live on
Property/Banner/FeaturedProperty, not here.

Domain layer only: dataclasses, enums, validations, and domain helpers.
No FastAPI/SQLAlchemy/Pydantic/HTTP/DB — stdlib only.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class MetricEventType(str, Enum):
    """Type of engagement event captured for a property.

    Lives in this module per the canonical contract.
    """

    VIEW = "view"
    CTA_CLICK = "cta_click"
    WHATSAPP_CLICK = "whatsapp_click"
    CALL_CLICK = "call_click"
    VISIT_REQUEST = "visit_request"
    SHARE = "share"
    FAVORITE = "favorite"


class ViewSource(str, Enum):
    """Origin channel that produced the engagement event.

    Lives in this module per the canonical contract.
    """

    ORGANIC = "organic"
    SEARCH = "search"
    FEATURED = "featured"
    DIRECT = "direct"
    SHARE = "share"


@dataclass
class PropertyView:
    """A single property engagement event (view or click).

    Append-only metric event. Counters are denormalized elsewhere; this
    record is the raw source of truth for engagement analytics.
    """

    id: str
    property_id: str
    event_type: MetricEventType = MetricEventType.VIEW
    source: ViewSource = ViewSource.DIRECT
    session_hash: str | None = None
    ip_hash: str | None = None
    referrer: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.property_id:
            raise ValueError("property_id is required")


def aggregate(events: list[PropertyView]) -> dict[str, int]:
    """Count events grouped by their ``event_type`` value.

    Args:
        events: The engagement events to tally.

    Returns:
        A mapping of ``event_type.value`` to its occurrence count. Event
        types with no occurrences are omitted from the result.
    """
    counts: dict[str, int] = {}
    for event in events:
        key = event.event_type.value
        counts[key] = counts.get(key, 0) + 1
    return counts


def ctr(views: int, clicks: int) -> float:
    """Compute the click-through rate as ``clicks / views``.

    Args:
        views: The number of views (denominator).
        clicks: The number of clicks (numerator).

    Returns:
        The click-through ratio, or ``0.0`` when ``views`` is zero to
        avoid division by zero.
    """
    if views == 0:
        return 0.0
    return clicks / views
