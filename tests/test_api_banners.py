"""Integration tests for /api/v1/banners and /api/v1/featured."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

pytestmark = pytest.mark.integration

_NOW = datetime.now(timezone.utc)
_FUTURE = _NOW + timedelta(days=30)

_BANNER_PAYLOAD = {
    "title": "Banner prueba",
    "position": "HOME_HERO",
    "image_desktop_url": "https://cdn.test/banner.jpg",
    "priority": 1,
    "is_active": True,
    "starts_at": _NOW.isoformat(),
    "ends_at": _FUTURE.isoformat(),
}

_PROPERTY_PAYLOAD = {
    "title": "Propiedad para destacar",
    "operation_type": "sale",
    "property_kind": "house",
    "price_amount": 100000,
    "currency": "USD",
}


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _publish(client, agent_token, admin_token):
    resp = client.post("/api/v1/properties", json=_PROPERTY_PAYLOAD, headers=_auth(agent_token))
    prop_id = resp.json()["id"]
    client.post(f"/api/v1/properties/{prop_id}/submit", headers=_auth(agent_token))
    client.post(f"/api/v1/properties/{prop_id}/approve", headers=_auth(admin_token))
    return prop_id


# ---------------------------------------------------------------------------
# Banners
# ---------------------------------------------------------------------------

class TestBannerCRUD:
    def test_create_banner_admin(self, client, admin_user, admin_token):
        resp = client.post("/api/v1/banners", json=_BANNER_PAYLOAD, headers=_auth(admin_token))
        assert resp.status_code == 201
        data = resp.json()
        assert data["position"] == "HOME_HERO"
        assert data["title"] == "Banner prueba"
        assert data["priority"] == 1

    def test_create_banner_requires_permission(self, client, agent_user, agent_token):
        resp = client.post("/api/v1/banners", json=_BANNER_PAYLOAD, headers=_auth(agent_token))
        assert resp.status_code == 403

    def test_list_banners_public(self, client, admin_user, admin_token):
        client.post("/api/v1/banners", json=_BANNER_PAYLOAD, headers=_auth(admin_token))
        resp = client.get("/api/v1/banners")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) >= 1

    def test_list_banners_filter_by_position(self, client, admin_user, admin_token):
        client.post("/api/v1/banners", json=_BANNER_PAYLOAD, headers=_auth(admin_token))
        resp = client.get("/api/v1/banners?position=HOME_HERO")
        assert resp.status_code == 200

    def test_delete_banner_admin(self, client, admin_user, admin_token):
        create = client.post("/api/v1/banners", json=_BANNER_PAYLOAD, headers=_auth(admin_token))
        banner_id = create.json()["id"]
        resp = client.delete(f"/api/v1/banners/{banner_id}", headers=_auth(admin_token))
        assert resp.status_code == 204

    def test_delete_nonexistent_banner(self, client, admin_user, admin_token):
        resp = client.delete("/api/v1/banners/nonexistent", headers=_auth(admin_token))
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Featured properties
# ---------------------------------------------------------------------------

class TestFeaturedCRUD:
    def test_create_featured_home_scope(self, client, agent_user, agent_token, admin_user, admin_token):
        prop_id = _publish(client, agent_token, admin_token)
        resp = client.post("/api/v1/featured", json={
            "property_id": prop_id,
            "scope": "home",
            "priority": 5,
            "starts_at": _NOW.isoformat(),
            "ends_at": _FUTURE.isoformat(),
        }, headers=_auth(admin_token))
        assert resp.status_code == 201
        data = resp.json()
        assert data["scope"] == "home"
        assert data["property_id"] == prop_id

    def test_create_featured_locality_requires_locality_id(self, client, agent_user, agent_token, admin_user, admin_token):
        prop_id = _publish(client, agent_token, admin_token)
        resp = client.post("/api/v1/featured", json={
            "property_id": prop_id,
            "scope": "locality",
            "priority": 1,
            "starts_at": _NOW.isoformat(),
            "ends_at": _FUTURE.isoformat(),
        }, headers=_auth(admin_token))
        assert resp.status_code == 422

    def test_create_featured_requires_permission(self, client, agent_user, agent_token, admin_user, admin_token):
        prop_id = _publish(client, agent_token, admin_token)
        resp = client.post("/api/v1/featured", json={
            "property_id": prop_id,
            "scope": "home",
            "priority": 1,
            "starts_at": _NOW.isoformat(),
            "ends_at": _FUTURE.isoformat(),
        }, headers=_auth(agent_token))
        assert resp.status_code == 403

    def test_list_featured_public(self, client, agent_user, agent_token, admin_user, admin_token):
        prop_id = _publish(client, agent_token, admin_token)
        client.post("/api/v1/featured", json={
            "property_id": prop_id, "scope": "home", "priority": 1,
            "starts_at": _NOW.isoformat(), "ends_at": _FUTURE.isoformat(),
        }, headers=_auth(admin_token))
        resp = client.get("/api/v1/featured?scope=home")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_delete_featured(self, client, agent_user, agent_token, admin_user, admin_token):
        prop_id = _publish(client, agent_token, admin_token)
        create = client.post("/api/v1/featured", json={
            "property_id": prop_id, "scope": "home", "priority": 1,
            "starts_at": _NOW.isoformat(), "ends_at": _FUTURE.isoformat(),
        }, headers=_auth(admin_token))
        featured_id = create.json()["id"]
        resp = client.delete(f"/api/v1/featured/{featured_id}", headers=_auth(admin_token))
        assert resp.status_code == 204
