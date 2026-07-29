"""Metrics router: property engagement event recording."""
from __future__ import annotations

import hashlib
import hmac
import os
import uuid

from fastapi import APIRouter, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.api.deps import DB, OptionalUser
from src.db.models.engagement_models import PropertyViewORM
from src.db.models.property_models import PropertyORM

router = APIRouter(prefix="/metrics", tags=["metrics"])

_HMAC_KEY = os.getenv("METRICS_HMAC_KEY", "changeme-metrics-key").encode()


def _session_hash(ip: str, user_agent: str) -> str:
    raw = f"{ip}|{user_agent}".encode()
    return hmac.new(_HMAC_KEY, raw, hashlib.sha256).hexdigest()


class MetricEventRequest(BaseModel):
    property_id: str
    event_type: str  # view / cta_click / whatsapp_click / call_click / visit_request / share / favorite
    source: str | None = None  # organic / search / featured / direct / share
    utm: dict | None = None


@router.post("/event", status_code=status.HTTP_202_ACCEPTED)
def record_event(body: MetricEventRequest, request: Request, current_user: OptionalUser, db: DB):
    prop = db.get(PropertyORM, body.property_id)
    if not prop or prop.status != "published":
        return {"accepted": False, "reason": "property not found or not published"}

    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")
    session_hash = _session_hash(ip, ua)

    event = PropertyViewORM(
        id=str(uuid.uuid4()),
        property_id=body.property_id,
        event_type=body.event_type,
        source=body.source,
        session_hash=session_hash,
        utm=body.utm,
    )
    db.add(event)

    # Increment denormalized counter for view events
    if body.event_type == "view":
        prop.views_count = (prop.views_count or 0) + 1

    db.commit()
    return {"accepted": True}
