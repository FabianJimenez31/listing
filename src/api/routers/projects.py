"""Projects (real-estate developments) router."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from src.api.deps import DB, OptionalUser, require_permission
from src.db.models.project_models import ProjectImageORM, ProjectORM
from src.repositories.location_repo import LocationRepository
from src.repositories.project_repo import ProjectImageRepository, ProjectRepository
from src.schemas.pagination_schemas import make_page
from src.schemas.project_schemas import (
    ProjectCreateRequest,
    ProjectImageCreateRequest,
    ProjectImageItem,
    ProjectListItem,
    ProjectResponse,
    ProjectUpdateRequest,
)
from src.storage.image_store import ALLOWED_CONTENT_TYPES, MAX_BYTES, remove as storage_remove, store as storage_store
from src.text.slug import slugify

router = APIRouter(prefix="/projects", tags=["projects"])


def _unique_slug(repo: ProjectRepository, base: str) -> str:
    base = base or "proyecto"
    slug, i = base, 2
    while repo.slug_exists(slug):
        slug = f"{base}-{i}"
        i += 1
    return slug


@router.get("", response_model=dict)
def search_projects(
    db: DB,
    user: OptionalUser,
    q: str | None = Query(None, description="Free-text (title/description/developer)"),
    stage: str | None = Query(None, description="preventa | construccion | entrega_inmediata"),
    location_id: str | None = Query(None),
    country: str | None = Query(None, description="Country slug or code (e.g. 'us')"),
    property_type_id: str | None = Query(None),
    min_price: int | None = Query(None, ge=0),
    max_price: int | None = Query(None, ge=0),
    status_filter: str | None = Query(
        None, alias="status", description="Editors only: a specific status or 'all' (drafts/pending)"
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    repo = ProjectRepository(db)
    # Public callers always see published only; editors (project:create) may
    # request other statuses (or 'all') to manage drafts from the admin UI.
    effective_status = "published"
    if status_filter and user and user.has_permission("project:create"):
        effective_status = None if status_filter in ("all", "*") else status_filter

    country_ids = LocationRepository(db).subtree_ids(country) if country else None
    items, total = repo.search(
        status=effective_status,
        stage=stage,
        location_id=location_id,
        country_ids=country_ids,
        property_type_id=property_type_id,
        min_price=min_price,
        max_price=max_price,
        text=q,
        page=page,
        page_size=page_size,
    )
    data = [ProjectListItem.model_validate(p).model_dump() for p in items]
    return make_page(data, page, page_size, total)


@router.get("/{slug}", response_model=ProjectResponse)
def get_project(slug: str, db: DB, user: OptionalUser):
    project = ProjectRepository(db).get_by_slug(slug)
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    if project.status != "published" and not (user and user.has_permission("project:create")):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    return project


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("project:create"))],
)
def create_project(body: ProjectCreateRequest, db: DB):
    repo = ProjectRepository(db)
    slug = _unique_slug(repo, slugify(body.title))
    project = ProjectORM(id=str(uuid.uuid4()), slug=slug, status="draft", **body.model_dump())
    repo.add(project)
    db.commit()
    return repo.get_by_slug(slug)


@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
    dependencies=[Depends(require_permission("project:create"))],
)
def update_project(project_id: str, body: ProjectUpdateRequest, db: DB):
    repo = ProjectRepository(db)
    project = repo.get_by_id(project_id)
    if not project or project.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(project, key, value)
    db.commit()
    return repo.get_by_slug(project.slug)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("project:create"))],
)
def delete_project(project_id: str, db: DB):
    repo = ProjectRepository(db)
    project = repo.get_by_id(project_id)
    if not project or project.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    project.deleted_at = datetime.now(timezone.utc)
    project.status = "deleted"
    db.commit()
    return None


@router.post(
    "/{project_id}/submit",
    response_model=ProjectResponse,
    dependencies=[Depends(require_permission("project:create"))],
)
def submit_project(project_id: str, db: DB):
    repo = ProjectRepository(db)
    project = repo.get_by_id(project_id)
    if not project or project.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    if project.status not in ("draft", "rejected", "paused"):
        raise HTTPException(status.HTTP_409_CONFLICT, f"Cannot submit from status '{project.status}'")
    project.status = "pending"
    db.commit()
    return repo.get_by_slug(project.slug)


@router.post(
    "/{project_id}/approve",
    response_model=ProjectResponse,
    dependencies=[Depends(require_permission("project:moderate"))],
)
def approve_project(project_id: str, db: DB):
    repo = ProjectRepository(db)
    project = repo.get_by_id(project_id)
    if not project or project.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    project.status = "published"
    if project.published_at is None:
        project.published_at = datetime.now(timezone.utc)
    db.commit()
    return repo.get_by_slug(project.slug)


@router.get("/{project_id}/images", response_model=list[ProjectImageItem])
def list_project_images(project_id: str, db: DB):
    repo = ProjectRepository(db)
    if not repo.get_by_id(project_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    return ProjectImageRepository(db).list_by_project(project_id)


@router.post(
    "/{project_id}/images",
    response_model=ProjectImageItem,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("project:create"))],
)
def add_project_image(project_id: str, body: ProjectImageCreateRequest, db: DB):
    repo = ProjectRepository(db)
    if not repo.get_by_id(project_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    image = ProjectImageORM(id=str(uuid.uuid4()), project_id=project_id, **body.model_dump())
    ProjectImageRepository(db).add(image)
    db.commit()
    db.refresh(image)
    return image


@router.post(
    "/{project_id}/images/upload",
    response_model=ProjectImageItem,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("project:create"))],
)
async def upload_project_image(
    project_id: str,
    db: DB,
    file: UploadFile = File(...),
    role: str = "gallery",
    alt_text: str | None = None,
):
    repo = ProjectRepository(db)
    project = repo.get_by_id(project_id)
    if not project or project.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Content-Type {file.content_type!r} not allowed. Use JPEG, PNG, or WebP.",
        )
    file_bytes = await file.read()
    if len(file_bytes) > MAX_BYTES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "File too large. Max 10 MB.")

    ext = (file.filename or "image").rsplit(".", 1)[-1].lower()
    storage_key = f"projects/{project_id}/{uuid.uuid4()}.{ext}"
    cdn_url = storage_store(file_bytes, storage_key)

    if role == "main":
        for img in project.images:
            if img.role == "main":
                img.role = "gallery"
        # Keep the denormalized cover in sync — list cards read cover_image_url.
        project.cover_image_url = cdn_url
    position = max((img.position for img in project.images), default=-1) + 1

    image = ProjectImageORM(
        id=str(uuid.uuid4()),
        project_id=project_id,
        role=role,
        position=position,
        storage_key=storage_key,
        cdn_url=cdn_url,
        thumb_url=cdn_url,
        alt_text=alt_text,
    )
    ProjectImageRepository(db).add(image)
    db.commit()
    db.refresh(image)
    return image


@router.patch(
    "/{project_id}/images/{image_id}/main",
    response_model=ProjectImageItem,
    dependencies=[Depends(require_permission("project:create"))],
)
def set_main_project_image(project_id: str, image_id: str, db: DB):
    """Promote an existing image to the cover (role=main), demoting the rest, and
    keep the denormalized cover_image_url in sync so list cards reflect it."""
    repo = ProjectRepository(db)
    project = repo.get_by_id(project_id)
    if not project or project.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    target = (
        db.query(ProjectImageORM)
        .filter_by(id=image_id, project_id=project_id)
        .first()
    )
    if not target:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Image not found")
    for img in project.images:
        img.role = "main" if img.id == image_id else "gallery"
    project.cover_image_url = target.cdn_url
    db.commit()
    db.refresh(target)
    return target


@router.delete(
    "/{project_id}/images/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("project:create"))],
)
def delete_project_image(project_id: str, image_id: str, db: DB):
    repo = ProjectRepository(db)
    project = repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    image = (
        db.query(ProjectImageORM)
        .filter_by(id=image_id, project_id=project_id)
        .first()
    )
    if not image:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Image not found")
    was_main = image.role == "main"
    if image.storage_key:
        storage_remove(image.storage_key)
    db.delete(image)
    db.flush()  # drop the row so it leaves project.images before we repoint the cover
    # If we removed the cover, promote the next remaining image (by position) and
    # keep cover_image_url in sync; clear it when no images remain.
    if was_main:
        remaining = sorted(
            (img for img in project.images if img.id != image_id),
            key=lambda i: i.position,
        )
        if remaining:
            remaining[0].role = "main"
            project.cover_image_url = remaining[0].cdn_url
        else:
            project.cover_image_url = None
    db.commit()
    return None
