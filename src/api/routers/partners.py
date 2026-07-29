"""Partners (allied agencies & developers) router."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.deps import DB, require_permission
from src.db.models.partner_models import PartnerORM
from src.repositories.partner_repo import PartnerRepository
from src.schemas.partner_schemas import PartnerCreateRequest, PartnerResponse
from src.text.slug import slugify

router = APIRouter(tags=["partners"])


@router.get("/partners", response_model=list[PartnerResponse])
def list_partners(db: DB):
    return PartnerRepository(db).list_active()


@router.post(
    "/partners",
    response_model=PartnerResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("partner:create"))],
)
def create_partner(body: PartnerCreateRequest, db: DB):
    repo = PartnerRepository(db)
    base = body.slug or slugify(body.name) or "aliado"
    slug, i = base, 2
    while repo.slug_exists(slug):
        slug = f"{base}-{i}"
        i += 1
    partner = PartnerORM(id=str(uuid.uuid4()), slug=slug, **body.model_dump(exclude={"slug"}))
    repo.add(partner)
    db.commit()
    db.refresh(partner)
    return partner


@router.delete(
    "/partners/{partner_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("partner:delete"))],
)
def delete_partner(partner_id: str, db: DB):
    repo = PartnerRepository(db)
    partner = repo.get_by_id(partner_id)
    if not partner:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Partner not found")
    repo.delete(partner)
    db.commit()
    return None
