"""Integration tests for /api/v1/favorites."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration

_PROPERTY_PAYLOAD = {
    "title": "Casa para guardar",
    "operation_type": "sale",
    "property_kind": "house",
    "price_amount": 500000,
    "currency": "MXN",
}


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _publish(client, agent_token, admin_token):
    resp = client.post("/api/v1/properties", json=_PROPERTY_PAYLOAD, headers=_auth(agent_token))
    prop_id = resp.json()["id"]
    client.post(f"/api/v1/properties/{prop_id}/submit", headers=_auth(agent_token))
    client.post(f"/api/v1/properties/{prop_id}/approve", headers=_auth(admin_token))
    return prop_id


class TestFavorites:
    def test_add_favorite(self, client, agent_user, agent_token, admin_user, admin_token):
        prop_id = _publish(client, agent_token, admin_token)
        resp = client.post(f"/api/v1/favorites/{prop_id}", headers=_auth(agent_token))
        assert resp.status_code == 201
        assert resp.json()["property_id"] == prop_id

    def test_add_favorite_requires_auth(self, client, agent_user, agent_token, admin_user, admin_token):
        prop_id = _publish(client, agent_token, admin_token)
        resp = client.post(f"/api/v1/favorites/{prop_id}")
        assert resp.status_code == 401

    def test_add_duplicate_favorite_conflict(self, client, agent_user, agent_token, admin_user, admin_token):
        prop_id = _publish(client, agent_token, admin_token)
        client.post(f"/api/v1/favorites/{prop_id}", headers=_auth(agent_token))
        resp = client.post(f"/api/v1/favorites/{prop_id}", headers=_auth(agent_token))
        assert resp.status_code == 409

    def test_list_favorites(self, client, agent_user, agent_token, admin_user, admin_token):
        prop_id = _publish(client, agent_token, admin_token)
        client.post(f"/api/v1/favorites/{prop_id}", headers=_auth(agent_token))
        resp = client.get("/api/v1/favorites", headers=_auth(agent_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["meta"]["total"] >= 1
        assert any(f["property_id"] == prop_id for f in data["data"])

    def test_list_favorites_requires_auth(self, client):
        resp = client.get("/api/v1/favorites")
        assert resp.status_code == 401

    def test_remove_favorite(self, client, agent_user, agent_token, admin_user, admin_token):
        prop_id = _publish(client, agent_token, admin_token)
        client.post(f"/api/v1/favorites/{prop_id}", headers=_auth(agent_token))
        resp = client.delete(f"/api/v1/favorites/{prop_id}", headers=_auth(agent_token))
        assert resp.status_code == 204
        # Confirm removed
        list_resp = client.get("/api/v1/favorites", headers=_auth(agent_token))
        assert list_resp.json()["meta"]["total"] == 0

    def test_remove_favorite_requires_auth(self, client, agent_user, agent_token, admin_user, admin_token):
        prop_id = _publish(client, agent_token, admin_token)
        resp = client.delete(f"/api/v1/favorites/{prop_id}")
        assert resp.status_code == 401
