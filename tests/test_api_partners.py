"""Integration tests for /api/v1/partners."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration

_PAYLOAD = {"name": "MARVAL", "kind": "constructora", "priority": 50}


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestPartnerCRUD:
    def test_create_partner_admin(self, client, admin_user, admin_token):
        resp = client.post("/api/v1/partners", json=_PAYLOAD, headers=_auth(admin_token))
        assert resp.status_code == 201
        assert resp.json()["name"] == "MARVAL"
        assert resp.json()["slug"] == "marval"

    def test_create_requires_permission(self, client, agent_user, agent_token):
        resp = client.post("/api/v1/partners", json=_PAYLOAD, headers=_auth(agent_token))
        assert resp.status_code == 403

    def test_list_partners_public_sorted_by_priority(self, client, admin_user, admin_token):
        client.post("/api/v1/partners", json={"name": "Low", "priority": 1}, headers=_auth(admin_token))
        client.post("/api/v1/partners", json={"name": "High", "priority": 99}, headers=_auth(admin_token))
        resp = client.get("/api/v1/partners")
        assert resp.status_code == 200
        names = [p["name"] for p in resp.json()]
        assert names == ["High", "Low"]

    def test_delete_partner(self, client, admin_user, admin_token):
        created = client.post("/api/v1/partners", json=_PAYLOAD, headers=_auth(admin_token)).json()
        resp = client.delete(f"/api/v1/partners/{created['id']}", headers=_auth(admin_token))
        assert resp.status_code == 204
        assert client.get("/api/v1/partners").json() == []

    def test_delete_missing_partner_404(self, client, admin_user, admin_token):
        resp = client.delete("/api/v1/partners/nope", headers=_auth(admin_token))
        assert resp.status_code == 404
