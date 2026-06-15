"""Pydantic schemas for blog Post endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class PostListItem(BaseModel):
    id: str
    title: str
    slug: str
    excerpt: str | None = None
    cover_image_url: str | None = None
    category: str | None = None
    status: str = "published"
    published_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PostResponse(BaseModel):
    id: str
    author_id: str | None = None
    title: str
    slug: str
    excerpt: str | None = None
    content: str | None = None
    cover_image_url: str | None = None
    category: str | None = None
    status: str
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PostCreateRequest(BaseModel):
    title: str
    slug: str | None = None  # auto-generated from title if omitted
    excerpt: str | None = None
    content: str | None = None
    cover_image_url: str | None = None
    category: str | None = None
    status: Literal["draft", "published"] = "draft"


class PostUpdateRequest(BaseModel):
    title: str | None = None
    excerpt: str | None = None
    content: str | None = None
    cover_image_url: str | None = None
    category: str | None = None
    status: Literal["draft", "published"] | None = None
