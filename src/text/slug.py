"""Slug generation from human-readable text (accent-aware)."""
from __future__ import annotations

import re
import unicodedata


def slugify(text: str) -> str:
    """Turn arbitrary text into a URL-safe slug.

    Strips accents ("Bogotá" → "bogota"), lowercases, and collapses runs of
    non-alphanumeric characters into single hyphens.
    """
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    normalized = normalized.lower().strip()
    normalized = re.sub(r"[^a-z0-9\s-]", "", normalized)
    normalized = re.sub(r"[\s-]+", "-", normalized)
    return normalized.strip("-")
