"""Property domain logic — the central real-estate listing entity.

A focused, single-responsibility module that models a real-estate
``Property``: its monetary value (``Money``), its classifying enums and the
publication lifecycle state machine. Pure domain layer: only the standard
library is used (dataclasses, enum, datetime, re, typing). No FastAPI,
SQLAlchemy, Pydantic, HTTP or database concerns live here.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timezone
from enum import Enum

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class OperationType(str, Enum):
    """The kind of commercial operation offered for a property."""

    SALE = "sale"
    RENT = "rent"
    TEMPORARY = "temporary"


class PropertyKind(str, Enum):
    """The physical kind of property being listed."""

    HOUSE = "house"
    APARTMENT = "apartment"
    LOT = "lot"
    OFFICE = "office"
    COMMERCIAL = "commercial"
    FARM = "farm"
    OTHER = "other"


class PropertyCondition(str, Enum):
    """The build/maintenance condition of a property."""

    NEW = "new"
    USED = "used"
    REMODELED = "remodeled"
    UNDER_CONSTRUCTION = "under_construction"


class PublicationStatus(str, Enum):
    """Lifecycle states a property can be in.

    Keep this Enum in sync with persisted database values. The harness
    command ``make validate-enums`` enforces that consistency.
    """

    DRAFT = "draft"
    PENDING = "pending"
    PUBLISHED = "published"
    PAUSED = "paused"
    SOLD = "sold"
    RENTED = "rented"
    REJECTED = "rejected"
    DELETED = "deleted"


class Currency(str, Enum):
    """Supported ISO 4217 currency codes (extensible)."""

    USD = "USD"
    EUR = "EUR"
    COP = "COP"
    MXN = "MXN"
    ARS = "ARS"
    CLP = "CLP"
    PEN = "PEN"
    BRL = "BRL"


@dataclass
class Money:
    """A monetary amount expressed in minor units (e.g. cents).

    Money is never represented as a float internally: ``amount_minor`` holds
    the value in the smallest currency unit and ``currency`` is a 3-letter
    ISO 4217 code.
    """

    amount_minor: int
    currency: str

    def __post_init__(self) -> None:
        if self.amount_minor < 0:
            raise ValueError("amount_minor cannot be negative")
        if not isinstance(self.currency, str) or len(self.currency) != 3:
            raise ValueError("currency must be a 3-letter ISO 4217 code")
        if self.currency != self.currency.upper():
            raise ValueError("currency must be uppercase")
        if self.currency not in {c.value for c in Currency}:
            raise ValueError(f"unsupported currency: {self.currency}")

    @property
    def as_major(self) -> float:
        """The amount in the major currency unit (minor units / 100)."""
        return round(self.amount_minor / 100, 2)


@dataclass
class Property:
    """A real-estate property listing and its publication lifecycle.

    The lifecycle methods implement the property state machine: transitions
    validate the current ``status`` and raise ``ValueError`` when an invalid
    transition is attempted.
    """

    id: str
    owner_id: str
    title: str
    slug: str
    description: str
    operation_type: OperationType
    property_kind: PropertyKind
    condition: PropertyCondition
    price: Money
    country: str
    city: str
    locality_id: str
    area_total: float
    bedrooms: int
    bathrooms: int
    parking_spots: int
    status: PublicationStatus = PublicationStatus.DRAFT
    state_province: str | None = None
    neighborhood: str | None = None
    address: str | None = None
    address_is_public: bool = False
    latitude: float | None = None
    longitude: float | None = None
    area_built: float | None = None
    year_built: int | None = None
    hoa_fees: Money | None = None
    is_featured: bool = False
    available_from: date | None = None
    main_image_id: str | None = None
    primary_cta: str | None = None
    amenities: list[str] = field(default_factory=list)
    image_ids: list[str] = field(default_factory=list)
    views_count: int = 0
    clicks_count: int = 0
    leads_count: int = 0
    published_at: datetime | None = None
    deleted_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.title:
            raise ValueError("title is required")
        if not self.slug:
            raise ValueError("slug is required")
        if not self.description:
            raise ValueError("description is required")
        if not SLUG_PATTERN.match(self.slug):
            raise ValueError(f"invalid slug: {self.slug}")
        if self.area_total <= 0:
            raise ValueError("area_total must be greater than 0")
        if self.bedrooms < 0:
            raise ValueError("bedrooms cannot be negative")
        if self.bathrooms < 0:
            raise ValueError("bathrooms cannot be negative")
        if self.parking_spots < 0:
            raise ValueError("parking_spots cannot be negative")
        if self.latitude is not None and not -90 <= self.latitude <= 90:
            raise ValueError("latitude must be between -90 and 90")
        if self.longitude is not None and not -180 <= self.longitude <= 180:
            raise ValueError("longitude must be between -180 and 180")

    def can_be_published(self) -> bool:
        """Whether the property satisfies the minimum publishing rules.

        Requires the minimum descriptive fields plus at least one image.
        """
        return bool(
            self.title
            and self.slug
            and self.description
            and self.area_total > 0
            and self.image_ids
        )

    def submit_for_review(self) -> None:
        """Transition DRAFT or REJECTED -> PENDING (owner action)."""
        if self.status not in {PublicationStatus.DRAFT, PublicationStatus.REJECTED}:
            raise ValueError(
                f"cannot submit for review from status {self.status.value}"
            )
        if not self.can_be_published():
            raise ValueError("minimum fields and at least one image are required")
        self.status = PublicationStatus.PENDING

    def approve(self, when: datetime | None = None) -> None:
        """Transition PENDING -> PUBLISHED (admin action), set published_at."""
        if self.status != PublicationStatus.PENDING:
            raise ValueError(f"cannot approve from status {self.status.value}")
        self.status = PublicationStatus.PUBLISHED
        self.published_at = when or datetime.now(timezone.utc)

    def reject(self, reason: str) -> None:
        """Transition PENDING -> REJECTED (admin action) with a reason."""
        if self.status != PublicationStatus.PENDING:
            raise ValueError(f"cannot reject from status {self.status.value}")
        if not reason:
            raise ValueError("a rejection reason is required")
        self.status = PublicationStatus.REJECTED

    def pause(self) -> None:
        """Transition PUBLISHED -> PAUSED (owner/admin action)."""
        if self.status != PublicationStatus.PUBLISHED:
            raise ValueError(f"cannot pause from status {self.status.value}")
        self.status = PublicationStatus.PAUSED

    def reactivate(self) -> None:
        """Transition PAUSED -> PUBLISHED (owner/admin action)."""
        if self.status != PublicationStatus.PAUSED:
            raise ValueError(f"cannot reactivate from status {self.status.value}")
        self.status = PublicationStatus.PUBLISHED

    def mark_sold(self) -> None:
        """Transition PUBLISHED|PAUSED -> SOLD (only for SALE operations)."""
        if self.operation_type != OperationType.SALE:
            raise ValueError("only SALE properties can be marked as sold")
        if self.status not in {PublicationStatus.PUBLISHED, PublicationStatus.PAUSED}:
            raise ValueError(f"cannot mark sold from status {self.status.value}")
        self.status = PublicationStatus.SOLD

    def mark_rented(self) -> None:
        """Transition PUBLISHED|PAUSED -> RENTED (RENT/TEMPORARY operations)."""
        if self.operation_type not in {OperationType.RENT, OperationType.TEMPORARY}:
            raise ValueError("only RENT or TEMPORARY properties can be marked rented")
        if self.status not in {PublicationStatus.PUBLISHED, PublicationStatus.PAUSED}:
            raise ValueError(f"cannot mark rented from status {self.status.value}")
        self.status = PublicationStatus.RENTED

    def soft_delete(self, when: datetime | None = None) -> None:
        """Soft delete any non-deleted property -> DELETED, set deleted_at."""
        if self.status == PublicationStatus.DELETED:
            raise ValueError("property is already deleted")
        self.status = PublicationStatus.DELETED
        self.deleted_at = when or datetime.now(timezone.utc)

    def duplicate(self, new_id: str, new_slug: str) -> Property:
        """Clone this property to a fresh DRAFT with reset metrics.

        The clone gets a new ``id`` and ``slug``, status DRAFT, all engagement
        metrics at 0 and no ``published_at`` / ``deleted_at`` timestamps.
        """
        if not new_id:
            raise ValueError("new_id is required")
        if not new_slug:
            raise ValueError("new_slug is required")
        return replace(
            self,
            id=new_id,
            slug=new_slug,
            status=PublicationStatus.DRAFT,
            is_featured=False,
            views_count=0,
            clicks_count=0,
            leads_count=0,
            published_at=None,
            deleted_at=None,
            amenities=list(self.amenities),
            image_ids=list(self.image_ids),
        )

    def is_publicly_visible(self) -> bool:
        """Whether the property is publicly visible (PUBLISHED, not deleted)."""
        return self.status == PublicationStatus.PUBLISHED and self.deleted_at is None
