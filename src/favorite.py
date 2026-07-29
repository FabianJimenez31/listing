"""Favorite domain logic.

A focused, single-responsibility module modelling a user's favorite
(bookmark) of a property and an in-memory collection of those favorites.
Pure domain layer: dataclasses + validations only, no FastAPI/SQLAlchemy/DB.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class Favorite:
    """A user's favorite (bookmark) of a property.

    Maps to the ``favorites`` table. Uniqueness is enforced per
    ``(user_id, property_id)`` pair by the owning :class:`FavoriteSet`.

    Attributes:
        id: UUID v4 string primary key.
        user_id: FK to the owning ``User``.
        property_id: FK to the favorited ``Property``.
        created_at: UTC timestamp; defaults to now when omitted.
    """

    id: str
    user_id: str
    property_id: str
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.user_id:
            raise ValueError("user_id is required")
        if not self.property_id:
            raise ValueError("property_id is required")
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)


class FavoriteSet:
    """An in-memory collection of favorites, unique per (user, property)."""

    def __init__(self) -> None:
        self._items: dict[tuple[str, str], Favorite] = {}

    def add(self, favorite: Favorite) -> None:
        """Add a favorite, idempotent-unique per ``(user_id, property_id)``.

        Args:
            favorite: The favorite to register.

        Raises:
            KeyError: If the user has already favorited this property.
        """
        key = (favorite.user_id, favorite.property_id)
        if key in self._items:
            raise KeyError(
                f"duplicate favorite: {favorite.user_id}/{favorite.property_id}"
            )
        self._items[key] = favorite

    def remove(self, user_id: str, property_id: str) -> None:
        """Remove a favorite by its ``(user_id, property_id)`` pair.

        Args:
            user_id: The owning user.
            property_id: The favorited property.

        Raises:
            KeyError: If no such favorite exists.
        """
        del self._items[(user_id, property_id)]

    def list_for_user(self, user_id: str) -> list[Favorite]:
        """Return all favorites belonging to a single user."""
        return [fav for fav in self._items.values() if fav.user_id == user_id]

    def __len__(self) -> int:
        return len(self._items)
