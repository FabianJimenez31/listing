"""Tests for Wompi-backed tour billing and the paid-tour gate."""
from __future__ import annotations

import asyncio
import hashlib
import io
import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from PIL import Image

from src.api.routers.tour_billing import (
    event_signature_valid,
    integrity_signature,
    price_in_cents,
)
from src.api.routers.virtual_tours import (
    MAX_SCENES_PER_TOUR,
    _assert_scene_capacity,
    create_tour,
)
from src.db.models.property_models import PropertyORM
from src.db.models.tour_payment_models import TourPaymentORM


class _MemoryUpload:
    def __init__(self, content: bytes) -> None:
        self._content = content

    async def read(self, size: int = -1) -> bytes:
        return self._content if size < 0 else self._content[:size]


def _pano() -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (800, 400), (20, 80, 140)).save(output, format="JPEG")
    return output.getvalue()


def test_price_defaults_to_50k_cop_in_cents(monkeypatch):
    monkeypatch.delenv("TOUR_PRICE_COP", raising=False)
    assert price_in_cents() == 5_000_000


def test_integrity_signature_matches_wompi_construction():
    # Valor de prueba; el patron real vive solo en .env.
    integrity_value = "integrity-" + "value-0123456789"
    import src.api.routers.tour_billing as billing

    original = billing._env
    billing._env = lambda name, default="": integrity_value if name == "WOMPI_INTEGRITY_SECRET" else original(name, default)
    try:
        result = integrity_signature("ref-123", 5_000_000, "COP")
    finally:
        billing._env = original
    expected = hashlib.sha256(f"ref-1235000000COP{integrity_value}".encode()).hexdigest()
    assert result == expected


def _event_payload(reference: str) -> dict:
    return {
        "event": "transaction.updated",
        "data": {
            "transaction": {
                "id": "tx-1",
                "status": "APPROVED",
                "reference": reference,
                "amount_in_cents": 5_000_000,
            }
        },
    }


def test_webhook_signature_valid_roundtrip():
    import json

    payload = _event_payload("ref-abc")
    properties = ["transaction.id", "transaction.status", "transaction.reference"]
    values = "".join(["tx-1", "APPROVED", "ref-abc"])
    timestamp = "1727000000"
    secret = "events_secret"
    checksum = hashlib.sha256(f"{values}{timestamp}{secret}".encode()).hexdigest()
    header = json.dumps({"properties": properties, "timestamp": timestamp, "signature": checksum})
    assert event_signature_valid(payload, header, secret) is True
    bad = checksum[:-1] + ("0" if checksum[-1] != "0" else "1")
    tampered = json.dumps({"properties": properties, "timestamp": timestamp, "signature": bad})
    assert event_signature_valid(payload, tampered, secret) is False


def _enable_billing(monkeypatch):
    monkeypatch.setenv("WOMPI_PUBLIC_KEY", "pub_test")
    monkeypatch.setenv("WOMPI_INTEGRITY_SECRET", "int_test")


def _make_property(db, owner_id: str) -> PropertyORM:
    prop = PropertyORM(
        id=str(uuid.uuid4()), owner_id=owner_id, title="Apto con pago",
        slug=f"apto-pago-{uuid.uuid4().hex[:8]}", operation_type="sale",
        property_kind="apartment", price_amount=100000, currency="COP", status="published",
    )
    db.add(prop)
    db.commit()
    return prop


def test_create_tour_requires_approved_payment(db_session, agent_user, monkeypatch):
    _enable_billing(monkeypatch)
    prop = _make_property(db_session, agent_user.id)
    with pytest.raises(HTTPException) as exc:
        create_tour("properties", prop.id, agent_user, db_session)
    assert exc.value.status_code == 402


def test_create_tour_consumes_paid_credit_once(db_session, agent_user, monkeypatch):
    _enable_billing(monkeypatch)
    prop = _make_property(db_session, agent_user.id)
    db_session.add(TourPaymentORM(
        id=str(uuid.uuid4()), user_id=agent_user.id, entity_type="properties",
        entity_id=prop.id, amount_in_cents=5_000_000, currency="COP", status="approved",
        reference=f"tour-{uuid.uuid4().hex[:16]}",
    ))
    db_session.commit()

    first = create_tour("properties", prop.id, agent_user, db_session)
    assert first.status == "draft"
    payment = db_session.query(TourPaymentORM).filter_by(entity_id=prop.id).one()
    assert payment.tour_id == first.id

    # Sin tour vigente y con el credito consumido, crear de nuevo exige otro pago.
    from src.db.models.virtual_tour_models import VirtualTourORM

    tour_orm = db_session.get(VirtualTourORM, first.id)
    db_session.delete(tour_orm)
    db_session.commit()
    with pytest.raises(HTTPException) as exc:
        create_tour("properties", prop.id, agent_user, db_session)
    assert exc.value.status_code == 402


def test_scene_capacity_rejects_the_eleventh_scene():
    tour = SimpleNamespace(scenes=list(range(MAX_SCENES_PER_TOUR)))
    with pytest.raises(HTTPException) as exc:
        _assert_scene_capacity(tour)
    assert exc.value.status_code == 422


def _legacy_tour(db, prop) -> str:
    from src.db.models.virtual_tour_models import VirtualTourORM

    tour_id = str(uuid.uuid4())
    db.add(VirtualTourORM(
        id=tour_id, property_id=prop.id, project_id=None, status="draft",
    ))
    db.commit()
    return tour_id


def _approve_credit(db, user, prop, tour_id=None):
    db.add(TourPaymentORM(
        id=str(uuid.uuid4()), user_id=user.id, entity_type="properties",
        entity_id=prop.id, amount_in_cents=5_000_000, currency="COP",
        status="approved", reference=f"tour-{uuid.uuid4().hex[:16]}",
        tour_id=tour_id,
    ))
    db.commit()


def test_legacy_tour_blocks_upload_until_paid(db_session, agent_user, monkeypatch):
    _enable_billing(monkeypatch)
    from src.api.routers.virtual_tours import upload_scene

    prop = _make_property(db_session, agent_user.id)
    tour_id = _legacy_tour(db_session, prop)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(upload_scene(
            "properties", prop.id, agent_user, db_session,
            file=_MemoryUpload(_pano()), title="Sala", hfov_deg=360, vfov_deg=180,
        ))
    assert exc.value.status_code == 402

    _approve_credit(db_session, agent_user, prop)
    scene = asyncio.run(upload_scene(
        "properties", prop.id, agent_user, db_session,
        file=_MemoryUpload(_pano()), title="Sala", hfov_deg=360, vfov_deg=180,
    ))
    assert scene.state == "ready"
    assert tour_id  # el tour sigue intacto


def test_publish_blocked_without_credit(db_session, agent_user, monkeypatch):
    _enable_billing(monkeypatch)
    from src.api.routers.virtual_tours import update_tour
    from src.db.models.virtual_tour_models import VirtualTourSceneORM
    from src.schemas.virtual_tour_schemas import TourUpdateRequest

    prop = _make_property(db_session, agent_user.id)
    tour_id = _legacy_tour(db_session, prop)
    with pytest.raises(HTTPException) as exc:
        update_tour("properties", prop.id, TourUpdateRequest(status="published"), agent_user, db_session)
    assert exc.value.status_code == 402

    _approve_credit(db_session, agent_user, prop, tour_id=tour_id)
    db_session.add(VirtualTourSceneORM(
        id=str(uuid.uuid4()), tour_id=tour_id, title="Sala", position=0,
        source="upload", state="ready", width=800, height=400,
        hfov_deg=360, vfov_deg=180, pano_url="https://cdn.test/sala.webp",
    ))
    db_session.commit()
    published = update_tour("properties", prop.id, TourUpdateRequest(status="published"), agent_user, db_session)
    assert published.status == "published"


def test_active_credit_exists_states(db_session, agent_user, monkeypatch):
    _enable_billing(monkeypatch)
    from src.api.routers.tour_billing import active_credit_exists

    prop = _make_property(db_session, agent_user.id)
    assert active_credit_exists(db_session, "properties", prop.id, None) is False
    _approve_credit(db_session, agent_user, prop)
    assert active_credit_exists(db_session, "properties", prop.id, None) is True


def test_credit_status_allows_staff_with_permission_not_owner(db_session, monkeypatch):
    """Regression FR-610: staff con permiso pero sin ser dueno no debe recibir 403."""
    _enable_billing(monkeypatch)
    from src.api.routers.tour_billing import credit_status
    from tests.conftest import _make_role, _make_user

    other_owner = _make_user(db_session, "owner-billing@test.local")
    prop = _make_property(db_session, other_owner.id)
    tour_id = _legacy_tour(db_session, prop)

    role = _make_role(db_session, "moderator", ["property:moderate"])
    staff = _make_user(db_session, "staff-billing@test.local", roles=[role])

    result = credit_status("properties", prop.id, staff, db_session)
    assert result["active"] is False

    _approve_credit(db_session, other_owner, prop, tour_id=tour_id)
    result = credit_status("properties", prop.id, staff, db_session)
    assert result["active"] is True
