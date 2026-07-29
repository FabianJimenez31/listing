"""SEO metadata domain logic.

A focused, single-responsibility module that models the SEO metadata
attached to a listing entity (titles, descriptions, Open Graph fields,
canonical URL, JSON-LD, robots directives and old-slug redirects).

Pure domain layer: dataclasses + validations + domain methods only. No
FastAPI/SQLAlchemy/Pydantic/HTTP/DB — stdlib only.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

MAX_TITLE = 70
MAX_DESCRIPTION = 160

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass
class SeoMetadata:
    """SEO metadata for a single entity (e.g. a Property).

    Attributes:
        id: UUID v4 string primary key.
        entity_type: Type of the entity the metadata describes.
        entity_id: Identifier of the described entity.
        slug: URL slug, must match the canonical slug regex.
        meta_title: ``<title>`` value, at most ``MAX_TITLE`` chars.
        meta_description: Meta description, at most ``MAX_DESCRIPTION`` chars.
        og_title: Optional Open Graph title.
        og_description: Optional Open Graph description.
        og_image_url: Optional Open Graph image URL.
        canonical_url: Optional canonical URL.
        jsonld: Structured data (JSON-LD) payload.
        robots: Robots directive, defaults to ``"index,follow"``.
        redirect_from: Old slugs that should redirect to this one.
    """

    id: str
    entity_type: str
    entity_id: str
    slug: str
    meta_title: str
    meta_description: str
    og_title: str | None = None
    og_description: str | None = None
    og_image_url: str | None = None
    canonical_url: str | None = None
    jsonld: dict = field(default_factory=dict)
    robots: str = "index,follow"
    redirect_from: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.slug:
            raise ValueError("slug is required")
        if not SLUG_PATTERN.match(self.slug):
            raise ValueError(f"invalid slug: {self.slug}")
        if not self.meta_title:
            raise ValueError("meta_title is required")
        if len(self.meta_title) > MAX_TITLE:
            raise ValueError(f"meta_title exceeds {MAX_TITLE} characters")
        if len(self.meta_description) > MAX_DESCRIPTION:
            raise ValueError(f"meta_description exceeds {MAX_DESCRIPTION} characters")

    def add_redirect(self, old_slug: str) -> None:
        """Register an old slug that should redirect to this one.

        Args:
            old_slug: The previous slug to redirect from.

        Raises:
            ValueError: If ``old_slug`` is empty or not a valid slug.
        """
        if not old_slug:
            raise ValueError("old_slug is required")
        if not SLUG_PATTERN.match(old_slug):
            raise ValueError(f"invalid slug: {old_slug}")
        if old_slug not in self.redirect_from:
            self.redirect_from.append(old_slug)

    def set_noindex(self) -> None:
        """Mark this entity as non-indexable by search engines."""
        self.robots = "noindex,nofollow"
