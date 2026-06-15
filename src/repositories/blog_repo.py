"""Repository for blog Post entities."""
from __future__ import annotations

from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from src.db.models.blog_models import PostORM
from src.repositories.base import BaseRepository


class BlogRepository(BaseRepository[PostORM]):
    def __init__(self, db: Session) -> None:
        super().__init__(PostORM, db)

    def get_by_slug(self, slug: str) -> PostORM | None:
        return self.db.scalar(
            select(PostORM).where(PostORM.slug == slug, PostORM.deleted_at.is_(None))
        )

    def get_published_by_slug(self, slug: str) -> PostORM | None:
        return self.db.scalar(
            select(PostORM).where(
                PostORM.slug == slug,
                PostORM.status == "published",
                PostORM.deleted_at.is_(None),
            )
        )

    def slug_exists(self, slug: str) -> bool:
        return self.db.scalar(select(PostORM.id).where(PostORM.slug == slug)) is not None

    def list_published(
        self, *, category: str | None = None, page: int = 1, page_size: int = 12
    ) -> tuple[list[PostORM], int]:
        filters: list[Any] = [PostORM.status == "published", PostORM.deleted_at.is_(None)]
        if category:
            filters.append(PostORM.category == category)

        base_stmt = select(PostORM).where(and_(*filters))
        total = self.db.scalar(select(func.count()).select_from(base_stmt.subquery())) or 0
        stmt = (
            base_stmt
            .order_by(PostORM.published_at.desc(), PostORM.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.db.scalars(stmt).all()), total

    def list_admin(
        self, *, category: str | None = None, page: int = 1, page_size: int = 50
    ) -> tuple[list[PostORM], int]:
        """All non-deleted posts (drafts included) — for the admin UI."""
        filters: list[Any] = [PostORM.deleted_at.is_(None)]
        if category:
            filters.append(PostORM.category == category)
        base_stmt = select(PostORM).where(and_(*filters))
        total = self.db.scalar(select(func.count()).select_from(base_stmt.subquery())) or 0
        stmt = (
            base_stmt
            .order_by(PostORM.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.db.scalars(stmt).all()), total
