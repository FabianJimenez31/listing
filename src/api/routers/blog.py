"""Blog posts router."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.deps import DB, OptionalUser, require_permission
from src.db.models.blog_models import PostORM
from src.repositories.blog_repo import BlogRepository
from src.schemas.blog_schemas import (
    PostCreateRequest,
    PostListItem,
    PostResponse,
    PostUpdateRequest,
)
from src.schemas.pagination_schemas import make_page
from src.text.slug import slugify

router = APIRouter(tags=["blog"])


def _unique_slug(repo: BlogRepository, base: str) -> str:
    base = base or "post"
    slug, i = base, 2
    while repo.slug_exists(slug):
        slug = f"{base}-{i}"
        i += 1
    return slug


@router.get("/posts", response_model=dict)
def list_posts(
    db: DB,
    user: OptionalUser,
    category: str | None = Query(None),
    status_filter: str | None = Query(
        None, alias="status", description="Editors only: 'all' returns drafts too"
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
):
    repo = BlogRepository(db)
    if status_filter == "all" and user and user.has_permission("post:create"):
        items, total = repo.list_admin(category=category, page=page, page_size=page_size)
    else:
        items, total = repo.list_published(category=category, page=page, page_size=page_size)
    data = [PostListItem.model_validate(p).model_dump() for p in items]
    return make_page(data, page, page_size, total)


@router.get("/posts/{slug}", response_model=PostResponse)
def get_post(slug: str, db: DB, user: OptionalUser):
    repo = BlogRepository(db)
    post = repo.get_by_slug(slug)
    if not post:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
    if post.status != "published" and not (user and user.has_permission("post:create")):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
    return post


@router.post("/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(body: PostCreateRequest, db: DB, user=Depends(require_permission("post:create"))):
    repo = BlogRepository(db)
    slug = _unique_slug(repo, body.slug or slugify(body.title))
    published_at = datetime.now(timezone.utc) if body.status == "published" else None
    post = PostORM(
        id=str(uuid.uuid4()),
        slug=slug,
        author_id=user.id,
        published_at=published_at,
        **body.model_dump(exclude={"slug"}),
    )
    repo.add(post)
    db.commit()
    db.refresh(post)
    return post


@router.put(
    "/posts/{post_id}",
    response_model=PostResponse,
    dependencies=[Depends(require_permission("post:update"))],
)
def update_post(post_id: str, body: PostUpdateRequest, db: DB):
    repo = BlogRepository(db)
    post = repo.get_by_id(post_id)
    if not post or post.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
    updates = body.model_dump(exclude_unset=True)
    if updates.get("status") == "published" and post.published_at is None:
        post.published_at = datetime.now(timezone.utc)
    for key, value in updates.items():
        setattr(post, key, value)
    db.commit()
    db.refresh(post)
    return post


@router.delete(
    "/posts/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("post:delete"))],
)
def delete_post(post_id: str, db: DB):
    repo = BlogRepository(db)
    post = repo.get_by_id(post_id)
    if not post or post.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
    post.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return None
