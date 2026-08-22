"""Integration coverage for manual virtual-tour composition and publication."""
from __future__ import annotations

import io
import uuid

import pytest
from PIL import Image

from src.db.models.property_models import PropertyORM
from src.db.models.virtual_tour_models import VirtualTourHotspotORM

pytestmark = pytest.mark.integration


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _pano() -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (800, 400), (70, 110, 150)).save(output, format="JPEG")
    return output.getvalue()


def _property(db, user) -> PropertyORM:
    prop = PropertyORM(
        id=str(uuid.uuid4()), owner_id=user.id, title="Casa tour",
        slug=f"casa-tour-{uuid.uuid4().hex[:8]}", operation_type="sale",
        property_kind="house", price_amount=100000, currency="COP", status="published",
    )
    db.add(prop)
    db.commit()
    return prop


def _upload(client, token, property_id, title):
    return client.post(
        f"/api/v1/properties/{property_id}/tour/scenes",
        data={"title": title, "hfov_deg": "360", "vfov_deg": "180"},
        files={"file": ("pano.jpg", io.BytesIO(_pano()), "image/jpeg")},
        headers=_auth(token),
    )


def test_manual_tour_draft_publish_hotspot_and_scene_cascade(
    client, db_session, agent_user, agent_token,
):
    prop = _property(db_session, agent_user)
    created = client.post(
        f"/api/v1/properties/{prop.id}/tour", headers=_auth(agent_token)
    )
    assert created.status_code == 201
    assert created.json()["status"] == "draft"

    hidden = client.get(f"/api/v1/properties/{prop.id}/tour")
    assert hidden.status_code == 404

    first = _upload(client, agent_token, prop.id, "Sala")
    second = _upload(client, agent_token, prop.id, "Cocina")
    assert first.status_code == second.status_code == 201
    first_id, second_id = first.json()["id"], second.json()["id"]

    hotspot = client.put(
        f"/api/v1/tour/scenes/{first_id}/hotspots",
        json={"hotspots": [{
            "to_scene_id": second_id, "yaw": 0.5, "pitch": -0.1, "label": "Ir a cocina",
        }]},
        headers=_auth(agent_token),
    )
    assert hotspot.status_code == 200
    assert len(hotspot.json()["hotspots"]) == 1

    published = client.patch(
        f"/api/v1/properties/{prop.id}/tour",
        json={"status": "published", "start_scene_id": first_id},
        headers=_auth(agent_token),
    )
    assert published.status_code == 200
    public = client.get(f"/api/v1/properties/{prop.id}/tour")
    assert public.status_code == 200
    assert [scene["title"] for scene in public.json()["scenes"]] == ["Sala", "Cocina"]

    deleted = client.delete(
        f"/api/v1/tour/scenes/{second_id}", headers=_auth(agent_token)
    )
    assert deleted.status_code == 204
    assert db_session.query(VirtualTourHotspotORM).count() == 0


def test_upload_rejects_non_equirectangular_image(client, db_session, agent_user, agent_token):
    prop = _property(db_session, agent_user)
    client.post(f"/api/v1/properties/{prop.id}/tour", headers=_auth(agent_token))
    output = io.BytesIO()
    Image.new("RGB", (800, 600)).save(output, format="JPEG")
    response = client.post(
        f"/api/v1/properties/{prop.id}/tour/scenes",
        data={"title": "Sala"},
        files={"file": ("regular.jpg", io.BytesIO(output.getvalue()), "image/jpeg")},
        headers=_auth(agent_token),
    )
    assert response.status_code == 422
