"""Listing catalog domain logic.

A focused, single-responsibility module that models product listings and
their lifecycle status. Used as the reference implementation that the
IA-Framework quality harness (tests, coverage, SonarQube) validates.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ListingStatus(str, Enum):
    """Lifecycle states a listing can be in.

    Keep this Enum in sync with persisted database values. The harness
    command ``make validate-enums`` enforces that consistency.
    """

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


@dataclass
class Listing:
    """A single product listing."""

    sku: str
    title: str
    price_cents: int
    status: ListingStatus = ListingStatus.DRAFT
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.sku:
            raise ValueError("sku is required")
        if self.price_cents < 0:
            raise ValueError("price_cents cannot be negative")

    @property
    def price(self) -> float:
        """Price as a float in the major currency unit."""
        return round(self.price_cents / 100, 2)

    def publish(self) -> None:
        """Transition the listing to PUBLISHED."""
        if self.status == ListingStatus.ARCHIVED:
            raise ValueError("cannot publish an archived listing")
        self.status = ListingStatus.PUBLISHED

    def archive(self) -> None:
        """Transition the listing to ARCHIVED."""
        self.status = ListingStatus.ARCHIVED


class Catalog:
    """An in-memory collection of listings keyed by SKU."""

    def __init__(self) -> None:
        self._items: dict[str, Listing] = {}

    def add(self, listing: Listing) -> None:
        if listing.sku in self._items:
            raise KeyError(f"duplicate sku: {listing.sku}")
        self._items[listing.sku] = listing

    def get(self, sku: str) -> Listing:
        return self._items[sku]

    def published(self) -> list[Listing]:
        return [it for it in self._items.values() if it.status == ListingStatus.PUBLISHED]

    def total_value_cents(self) -> int:
        return sum(it.price_cents for it in self._items.values())

    def __len__(self) -> int:
        return len(self._items)
