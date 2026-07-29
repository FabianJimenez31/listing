"""Agencies (inmobiliarias) router."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.deps import DB, require_permission
from src.db.models.agency_models import AgencyORM
from src.repositories.agency_repo import AgencyRepository
from src.schemas.agency_schemas import (
    AgencyCreateRequest,
    AgencyResponse,
    AgencyUpdateRequest,
)
from src.text.slug import slugify

router = APIRouter(prefix="/agencies", tags=["agencies"])


def _to_response(agency: AgencyORM, count: int = 0) -> AgencyResponse:
    resp = AgencyResponse.model_validate(agency)
    resp.property_count = count
    return resp


def _unique_slug(repo: AgencyRepository, base: str) -> str:
    base = base or "inmobiliaria"
    slug, i = base, 2
    while repo.slug_exists(slug):
        slug = f"{base}-{i}"
        i += 1
    return slug


@router.get("", response_model=list[AgencyResponse])
def list_agencies(db: DB):
    repo = AgencyRepository(db)
    counts = repo.published_property_counts()
    return [_to_response(a, counts.get(a.id, 0)) for a in repo.list_active()]


@router.get("/{slug}", response_model=AgencyResponse)
def get_agency(slug: str, db: DB):
    repo = AgencyRepository(db)
    agency = repo.get_by_slug(slug)
    if not agency:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Agency not found")
    counts = repo.published_property_counts()
    return _to_response(agency, counts.get(agency.id, 0))


@router.post(
    "",
    response_model=AgencyResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("agency:create"))],
)
def create_agency(body: AgencyCreateRequest, db: DB):
    repo = AgencyRepository(db)
    slug = _unique_slug(repo, body.slug or slugify(body.name))
    agency = AgencyORM(id=str(uuid.uuid4()), slug=slug, **body.model_dump(exclude={"slug"}))
    repo.add(agency)
    db.commit()
    db.refresh(agency)
    return _to_response(agency, 0)


@router.put(
    "/{agency_id}",
    response_model=AgencyResponse,
    dependencies=[Depends(require_permission("agency:update"))],
)
def update_agency(agency_id: str, body: AgencyUpdateRequest, db: DB):
    repo = AgencyRepository(db)
    agency = repo.get_by_id(agency_id)
    if not agency:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Agency not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(agency, key, value)
    db.commit()
    db.refresh(agency)
    counts = repo.published_property_counts()
    return _to_response(agency, counts.get(agency.id, 0))


@router.delete(
    "/{agency_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("agency:delete"))],
)
def delete_agency(agency_id: str, db: DB):
    repo = AgencyRepository(db)
    agency = repo.get_by_id(agency_id)
    if not agency:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Agency not found")
    repo.delete(agency)
    db.commit()
    return None
