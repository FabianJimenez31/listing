"""Route-level tour workflow without an HTTP client compatibility layer."""
from __future__ import annotations

import asyncio
import io
import uuid

import pytest
from PIL import Image

from src.api.routers.virtual_tours import (
    create_tour,
    delete_scene,
    get_public_tour,
    replace_hotspots,
    update_tour,
    upload_scene,
)
from src.db.models.property_models import PropertyORM
from src.schemas.virtual_tour_schemas import (
    HotspotInput,
    HotspotReplaceRequest,
    TourUpdateRequest,
)

pytestmark = pytest.mark.integration


class _MemoryUpload:
    def __init__(self, content: bytes) -> None:
        self._content = content

    async def read(self, size: int = -1) -> bytes:
        return self._content if size < 0 else self._content[:size]


def _pano() -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (800, 400), (20, 80, 140)).save(output, format="JPEG")
    return output.getvalue()


def test_complete_manual_route_workflow(db_session, agent_user):
    prop = PropertyORM(
        id=str(uuid.uuid4()), owner_id=agent_user.id, title="Casa 360",
        slug=f"casa-360-{uuid.uuid4().hex[:8]}", operation_type="sale",
        property_kind="house", price_amount=100000, currency="COP", status="published",
    )
    db_session.add(prop)
    db_session.commit()

    tour = create_tour("properties", prop.id, agent_user, db_session)
    first = asyncio.run(upload_scene(
        "properties", prop.id, agent_user, db_session,
        file=_MemoryUpload(_pano()), title="Sala", hfov_deg=360, vfov_deg=180,
    ))
    second = asyncio.run(upload_scene(
        "properties", prop.id, agent_user, db_session,
        file=_MemoryUpload(_pano()), title="Cocina", hfov_deg=360, vfov_deg=180,
    ))
    replace_hotspots(
        first.id,
        HotspotReplaceRequest(hotspots=[HotspotInput(
            to_scene_id=second.id, yaw=0.4, pitch=-0.1, label="Cocina",
        )]),
        agent_user,
        db_session,
    )
    published = update_tour(
        "properties", prop.id,
        TourUpdateRequest(status="published", start_scene_id=first.id),
        agent_user, db_session,
    )
    assert published.status == "published"
    assert get_public_tour("properties", prop.id, db_session).id == tour.id

    delete_scene(second.id, agent_user, db_session)
    update_tour(
        "properties", prop.id, TourUpdateRequest(status="published"),
        agent_user, db_session,
    )
    public = get_public_tour("properties", prop.id, db_session)
    assert len(public.scenes) == 1
    assert public.scenes[0].hotspots == []
