"""Normalization primitives for public catalog searches."""
from __future__ import annotations

import re
import unicodedata

from sqlalchemy import func
from sqlalchemy.sql.elements import ColumnElement

_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_NID_LABELS = {"", "nid", "codigo", "id"}


def normalize_search_text(value: str | None) -> str:
    """Return lowercase, accentless words separated by one space."""
    decomposed = unicodedata.normalize("NFKD", value or "")
    accentless = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(_NON_ALNUM.sub(" ", accentless.casefold()).split())


def search_like_pattern(value: str | None) -> str | None:
    """Build a LIKE pattern whose word gaps tolerate punctuation and spacing."""
    normalized = normalize_search_text(value)
    return f"%{'%'.join(normalized.split())}%" if normalized else None


def extract_nid(value: str | None) -> int | None:
    """Recognize a numeric property ID, including ``/100…`` and ``NID 100…``."""
    normalized = normalize_search_text(value)
    digits = "".join(char for char in normalized if char.isdigit())
    label = "".join(char for char in normalized if not char.isdigit()).strip()
    if len(digits) >= 7 and label in _NID_LABELS:
        return int(digits)
    return None


def normalized_sql(column: ColumnElement) -> ColumnElement:
    """Portable accent-insensitive SQL expression for SQLite and PostgreSQL."""
    expression = func.lower(func.coalesce(column, ""))
    for source, target in zip("áéíóúüñÁÉÍÓÚÜÑ", "aeiouunaeiouun", strict=True):
        expression = func.replace(expression, source, target)
    return expression
