"""Integration tests for /api/v1/agencies."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration

_AGENCY_PAYLOAD = {
    "name": "Engel & Völkers Bogotá",
    "initials": "EV",
    "phone": "+5715551234",
}


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestAgencyCRUD:
    def test_create_agency_admin(self, client, admin_user, admin_token):
        resp = client.post("/api/v1/agencies", json=_AGENCY_PAYLOAD, headers=_auth(admin_token))
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Engel & Völkers Bogotá"
        assert data["initials"] == "EV"
        # slug auto-generated (accent-stripped)
        assert data["slug"] == "engel-volkers-bogota"

    def test_create_agency_requires_permission(self, client, agent_user, agent_token):
        resp = client.post("/api/v1/agencies", json=_AGENCY_PAYLOAD, headers=_auth(agent_token))
        assert resp.status_code == 403

    def test_create_agency_unauthenticated(self, client):
        resp = client.post("/api/v1/agencies", json=_AGENCY_PAYLOAD)
        assert resp.status_code == 401

    def test_list_agencies_public(self, client, admin_user, admin_token):
        client.post("/api/v1/agencies", json=_AGENCY_PAYLOAD, headers=_auth(admin_token))
        resp = client.get("/api/v1/agencies")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) == 1
        assert resp.json()[0]["property_count"] == 0

    def test_get_agency_by_slug(self, client, admin_user, admin_token):
        client.post("/api/v1/agencies", json=_AGENCY_PAYLOAD, headers=_auth(admin_token))
        resp = client.get("/api/v1/agencies/engel-volkers-bogota")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Engel & Völkers Bogotá"

    def test_get_agency_not_found(self, client):
        resp = client.get("/api/v1/agencies/does-not-exist")
        assert resp.status_code == 404

    def test_unique_slug_on_duplicate_name(self, client, admin_user, admin_token):
        a = client.post("/api/v1/agencies", json=_AGENCY_PAYLOAD, headers=_auth(admin_token))
        b = client.post("/api/v1/agencies", json=_AGENCY_PAYLOAD, headers=_auth(admin_token))
        assert a.json()["slug"] != b.json()["slug"]

    def test_update_agency(self, client, admin_user, admin_token):
        created = client.post("/api/v1/agencies", json=_AGENCY_PAYLOAD, headers=_auth(admin_token)).json()
        resp = client.put(
            f"/api/v1/agencies/{created['id']}",
            json={"is_verified": True, "description": "Premium"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["is_verified"] is True
        assert resp.json()["description"] == "Premium"

    def test_delete_agency(self, client, admin_user, admin_token):
        created = client.post("/api/v1/agencies", json=_AGENCY_PAYLOAD, headers=_auth(admin_token)).json()
        resp = client.delete(f"/api/v1/agencies/{created['id']}", headers=_auth(admin_token))
        assert resp.status_code == 204
        assert client.get("/api/v1/agencies").json() == []
