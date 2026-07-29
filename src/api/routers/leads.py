"""Leads router: lead capture and management."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status

from src.api.deps import CurrentUser, DB, OptionalUser, require_permission
from src.db.models.lead_models import LeadORM
from src.repositories.lead_repo import LeadRepository
from src.repositories.property_repo import PropertyRepository
from src.schemas.lead_schemas import LeadCreateRequest, LeadResponse, LeadStatusUpdateRequest
from src.schemas.pagination_schemas import make_page

router = APIRouter(prefix="/leads", tags=["leads"])


@router.post("", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
def create_lead(body: LeadCreateRequest, request: Request, db: DB):
    """Public endpoint: capture a lead for a property."""
    prop_repo = PropertyRepository(db)
    prop = prop_repo.get_by_id(body.property_id)
    if not prop or prop.status != "published":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Property not found or not published")

    lead = LeadORM(
        id=str(uuid.uuid4()),
        property_id=body.property_id,
        name=body.name,
        email=body.email,
        phone=body.phone,
        message=body.message,
        channel=body.channel,
        consent_given=body.consent_given,
        consent_text=body.consent_text,
        utm=body.utm,
        source_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    LeadRepository(db).add(lead)
    db.commit()
    db.refresh(lead)
    return lead


@router.get("", response_model=dict, dependencies=[Depends(require_permission("lead:read"))])
def list_leads(
    current_user: CurrentUser,
    db: DB,
    property_id: str | None = None,
    status_filter: str | None = None,
    page: int = 1,
    page_size: int = 20,
):
    repo = LeadRepository(db)

    # ADMIN/SUPERADMIN see all; agents see their own assigned leads only
    if current_user.has_permission("lead:read_all"):
        items, total = repo.list_all_admin(property_id=property_id, status=status_filter, page=page, page_size=page_size)
    else:
        items, total = repo.list_for_agent(current_user.id, page=page, page_size=page_size)

    data = [LeadResponse.model_validate(item).model_dump() for item in items]
    return make_page(data, page, page_size, total)


@router.patch("/{lead_id}", response_model=LeadResponse)
def update_lead_status(
    lead_id: str,
    body: LeadStatusUpdateRequest,
    current_user: CurrentUser,
    db: DB,
):
    repo = LeadRepository(db)
    lead = repo.get_by_id(lead_id)
    if not lead:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead not found")

    # Only the assigned agent, property owner, or admin can update
    if (
        lead.owner_id != current_user.id
        and not current_user.has_permission("lead:update_all")
    ):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not authorized to update this lead")

    if lead.status in ("closed", "discarded"):
        raise HTTPException(status.HTTP_409_CONFLICT, f"Lead is in terminal status: {lead.status}")

    lead.status = body.status
    if body.owner_id:
        lead.owner_id = body.owner_id
    db.commit()
    db.refresh(lead)
    return lead
