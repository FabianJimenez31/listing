"""Shared schemas: pagination envelope, error envelope, base response."""
from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class PageResponse(BaseModel, Generic[T]):
    data: list[T]
    meta: PaginationMeta


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Any = None


class ErrorEnvelope(BaseModel):
    error: ErrorDetail


def make_page(items: list[Any], page: int, page_size: int, total: int) -> dict[str, Any]:
    total_pages = max(1, (total + page_size - 1) // page_size)
    return {
        "data": items,
        "meta": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
        },
    }
