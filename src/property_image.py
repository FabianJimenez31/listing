"""Property image and media domain logic.

A focused, single-responsibility module that models the multimedia assets
attached to a property (photos, videos, floor plans, virtual tours) and the
domain rules that keep a gallery consistent: a single MAIN image, ordered
positions, and basic upload-quality constraints.

This is the canonical home of the ``ImageRole`` and ``MediaKind`` enums.
Pure domain layer: stdlib only (dataclasses, enum, datetime, typing). No
FastAPI / SQLAlchemy / Pydantic / HTTP / DB concerns live here.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

ALLOWED_IMAGE_TYPES: set[str] = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_BYTES: int = 10 * 1024 * 1024
MIN_WIDTH: int = 800
MIN_HEIGHT: int = 600


class ImageRole(str, Enum):
    """Role a media asset plays within a property's gallery."""

    MAIN = "main"
    GALLERY = "gallery"


class MediaKind(str, Enum):
    """Kind of media asset attached to a property."""

    IMAGE = "image"
    VIDEO = "video"
    FLOOR_PLAN = "floor_plan"
    VIRTUAL_TOUR = "virtual_tour"


@dataclass
class PropertyImage:
    """A single multimedia asset attached to a property.

    Attributes:
        id: UUID v4 string identifying the asset.
        property_id: FK to the owning Property.
        original_url: URL of the uploaded source asset (required).
        role: Whether this is the MAIN or a GALLERY asset.
        media_kind: The kind of media (image, video, floor plan, tour).
        cdn_url: CDN-served URL, if processed.
        thumb_url: Thumbnail URL, if generated.
        position: Zero-based ordering within the gallery.
        width: Pixel width, when known.
        height: Pixel height, when known.
        bytes: Size in bytes, when known.
        content_type: MIME type, when known.
        alt_text: Accessibility / SEO alt text.
        created_at: Creation timestamp (UTC).
    """

    id: str
    property_id: str
    original_url: str
    role: ImageRole = ImageRole.GALLERY
    media_kind: MediaKind = MediaKind.IMAGE
    cdn_url: str | None = None
    thumb_url: str | None = None
    position: int = 0
    width: int | None = None
    height: int | None = None
    bytes: int | None = None
    content_type: str | None = None
    alt_text: str | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.property_id:
            raise ValueError("property_id is required")
        if not self.original_url:
            raise ValueError("original_url is required")
        if self.position < 0:
            raise ValueError("position cannot be negative")
        if (
            self.media_kind == MediaKind.IMAGE
            and self.content_type is not None
            and self.content_type not in ALLOWED_IMAGE_TYPES
        ):
            raise ValueError(f"content_type not allowed: {self.content_type}")
        if self.bytes is not None and self.bytes > MAX_IMAGE_BYTES:
            raise ValueError("bytes exceeds MAX_IMAGE_BYTES")
        if self.width is not None and self.height is not None:
            if self.width < MIN_WIDTH or self.height < MIN_HEIGHT:
                raise ValueError("image dimensions below minimum")

    def make_main(self) -> None:
        """Promote this asset to the MAIN role."""
        self.role = ImageRole.MAIN

    def set_position(self, n: int) -> None:
        """Set the gallery position.

        Args:
            n: New zero-based position; must be non-negative.

        Raises:
            ValueError: If ``n`` is negative.
        """
        if n < 0:
            raise ValueError("position cannot be negative")
        self.position = n


def order_gallery(images: list[PropertyImage]) -> list[PropertyImage]:
    """Return the images sorted by ascending position.

    Args:
        images: The images to order.

    Returns:
        A new list ordered by ``position``.
    """
    return sorted(images, key=lambda img: img.position)


def enforce_single_main(images: list[PropertyImage]) -> None:
    """Validate that a non-empty gallery has exactly one MAIN image.

    Args:
        images: The images to validate.

    Raises:
        ValueError: If there are images but not exactly one MAIN.
    """
    if not images:
        return
    main_count = sum(1 for img in images if img.role == ImageRole.MAIN)
    if main_count != 1:
        raise ValueError(f"expected exactly 1 MAIN image, found {main_count}")
