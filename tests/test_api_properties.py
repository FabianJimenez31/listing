"""Integration tests for /api/v1/properties — CRUD and lifecycle."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration

_BASE_PAYLOAD = {
    "title": "Casa en Chapultepec",
    "operation_type": "sale",
    "property_kind": "house",
    "price_amount": 150000000,
    "currency": "MXN",
    "bedrooms": 3,
    "bathrooms": 2,
}


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestPropertyCreate:
    def test_create_success(self, client, agent_user, agent_token):
        resp = client.post("/api/v1/properties", json=_BASE_PAYLOAD, headers=_auth(agent_token))
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "draft"
        assert data["title"] == "Casa en Chapultepec"
        assert data["price_amount"] == 150000000
        assert data["currency"] == "MXN"
        assert "slug" in data

    def test_create_requires_auth(self, client):
        resp = client.post("/api/v1/properties", json=_BASE_PAYLOAD)
        assert resp.status_code == 401

    def test_create_negative_price(self, client, agent_token):
        resp = client.post("/api/v1/properties", json={**_BASE_PAYLOAD, "price_amount": -1}, headers=_auth(agent_token))
        assert resp.status_code == 422

    def test_create_blank_title(self, client, agent_token):
        resp = client.post("/api/v1/properties", json={**_BASE_PAYLOAD, "title": "   "}, headers=_auth(agent_token))
        assert resp.status_code == 422


class TestPropertyGet:
    def test_get_draft_by_owner(self, client, agent_user, agent_token):
        create_resp = client.post("/api/v1/properties", json=_BASE_PAYLOAD, headers=_auth(agent_token))
        prop_id = create_resp.json()["id"]
        resp = client.get(f"/api/v1/properties/{prop_id}", headers=_auth(agent_token))
        assert resp.status_code == 200

    def test_draft_hidden_from_public(self, client, agent_user, agent_token):
        create_resp = client.post("/api/v1/properties", json=_BASE_PAYLOAD, headers=_auth(agent_token))
        prop_id = create_resp.json()["id"]
        resp = client.get(f"/api/v1/properties/{prop_id}")  # no auth
        assert resp.status_code == 404

    def test_published_visible_to_public(self, client, agent_user, agent_token, admin_user, admin_token):
        create_resp = client.post("/api/v1/properties", json=_BASE_PAYLOAD, headers=_auth(agent_token))
        prop_id = create_resp.json()["id"]
        client.post(f"/api/v1/properties/{prop_id}/submit", headers=_auth(agent_token))
        client.post(f"/api/v1/properties/{prop_id}/approve", headers=_auth(admin_token))
        resp = client.get(f"/api/v1/properties/{prop_id}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "published"


class TestPropertyLifecycle:
    def _create_draft(self, client, token):
        resp = client.post("/api/v1/properties", json=_BASE_PAYLOAD, headers=_auth(token))
        return resp.json()["id"]

    def test_submit_for_review(self, client, agent_user, agent_token):
        prop_id = self._create_draft(client, agent_token)
        resp = client.post(f"/api/v1/properties/{prop_id}/submit", headers=_auth(agent_token))
        assert resp.status_code == 200
        assert resp.json()["status"] == "pending"

    def test_cannot_submit_twice(self, client, agent_user, agent_token):
        prop_id = self._create_draft(client, agent_token)
        client.post(f"/api/v1/properties/{prop_id}/submit", headers=_auth(agent_token))
        resp = client.post(f"/api/v1/properties/{prop_id}/submit", headers=_auth(agent_token))
        assert resp.status_code == 409

    def test_approve_requires_admin(self, client, agent_user, agent_token):
        prop_id = self._create_draft(client, agent_token)
        client.post(f"/api/v1/properties/{prop_id}/submit", headers=_auth(agent_token))
        resp = client.post(f"/api/v1/properties/{prop_id}/approve", headers=_auth(agent_token))
        assert resp.status_code == 403

    def test_full_lifecycle_draft_to_published(self, client, agent_user, agent_token, admin_user, admin_token):
        prop_id = self._create_draft(client, agent_token)
        client.post(f"/api/v1/properties/{prop_id}/submit", headers=_auth(agent_token))
        resp = client.post(f"/api/v1/properties/{prop_id}/approve", headers=_auth(admin_token))
        assert resp.status_code == 200
        assert resp.json()["status"] == "published"
        assert resp.json()["published_at"] is not None

    def test_reject_with_reason(self, client, agent_user, agent_token, admin_user, admin_token):
        prop_id = self._create_draft(client, agent_token)
        client.post(f"/api/v1/properties/{prop_id}/submit", headers=_auth(agent_token))
        resp = client.post(f"/api/v1/properties/{prop_id}/reject",
                          json={"reason": "Fotos insuficientes"},
                          headers=_auth(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "rejected"
        assert data["rejection_reason"] == "Fotos insuficientes"

    def test_pause_and_reactivate(self, client, agent_user, agent_token, admin_user, admin_token):
        prop_id = self._create_draft(client, agent_token)
        client.post(f"/api/v1/properties/{prop_id}/submit", headers=_auth(agent_token))
        client.post(f"/api/v1/properties/{prop_id}/approve", headers=_auth(admin_token))
        pause_resp = client.post(f"/api/v1/properties/{prop_id}/pause", headers=_auth(agent_token))
        assert pause_resp.json()["status"] == "paused"
        react_resp = client.post(f"/api/v1/properties/{prop_id}/reactivate", headers=_auth(agent_token))
        assert react_resp.json()["status"] == "published"

    def test_mark_sold(self, client, agent_user, agent_token, admin_user, admin_token):
        prop_id = self._create_draft(client, agent_token)
        client.post(f"/api/v1/properties/{prop_id}/submit", headers=_auth(agent_token))
        client.post(f"/api/v1/properties/{prop_id}/approve", headers=_auth(admin_token))
        resp = client.post(f"/api/v1/properties/{prop_id}/mark-sold", headers=_auth(agent_token))
        assert resp.json()["status"] == "sold"

    def test_mark_rented_wrong_operation_fails(self, client, agent_user, agent_token, admin_user, admin_token):
        prop_id = self._create_draft(client, agent_token)
        client.post(f"/api/v1/properties/{prop_id}/submit", headers=_auth(agent_token))
        client.post(f"/api/v1/properties/{prop_id}/approve", headers=_auth(admin_token))
        resp = client.post(f"/api/v1/properties/{prop_id}/mark-rented", headers=_auth(agent_token))
        assert resp.status_code == 422

    def test_duplicate_creates_draft(self, client, agent_user, agent_token, admin_user, admin_token):
        prop_id = self._create_draft(client, agent_token)
        client.post(f"/api/v1/properties/{prop_id}/submit", headers=_auth(agent_token))
        client.post(f"/api/v1/properties/{prop_id}/approve", headers=_auth(admin_token))
        resp = client.post(f"/api/v1/properties/{prop_id}/duplicate", headers=_auth(agent_token))
        assert resp.status_code == 200
        clone = resp.json()
        assert clone["status"] == "draft"
        assert clone["id"] != prop_id
        assert clone["slug"] != _BASE_PAYLOAD.get("slug")

    def test_soft_delete(self, client, agent_user, agent_token):
        prop_id = self._create_draft(client, agent_token)
        resp = client.delete(f"/api/v1/properties/{prop_id}", headers=_auth(agent_token))
        assert resp.status_code == 204
        get_resp = client.get(f"/api/v1/properties/{prop_id}", headers=_auth(agent_token))
        assert get_resp.status_code == 404


class TestSearch:
    def _publish(self, client, agent_token, admin_token, payload=None):
        payload = payload or _BASE_PAYLOAD
        create_resp = client.post("/api/v1/properties", json=payload, headers=_auth(agent_token))
        prop_id = create_resp.json()["id"]
        client.post(f"/api/v1/properties/{prop_id}/submit", headers=_auth(agent_token))
        client.post(f"/api/v1/properties/{prop_id}/approve", headers=_auth(admin_token))
        return prop_id

    def test_search_returns_published_only(self, client, agent_user, agent_token, admin_user, admin_token):
        self._publish(client, agent_token, admin_token)
        client.post("/api/v1/properties", json=_BASE_PAYLOAD, headers=_auth(agent_token))  # draft
        resp = client.get("/api/v1/properties")
        assert resp.status_code == 200
        data = resp.json()
        assert data["meta"]["total"] == 1

    def test_search_filter_by_operation_type(self, client, agent_user, agent_token, admin_user, admin_token):
        self._publish(client, agent_token, admin_token)
        resp = client.get("/api/v1/properties?operation_type=rent")
        assert resp.json()["meta"]["total"] == 0

    def test_search_filter_by_price(self, client, agent_user, agent_token, admin_user, admin_token):
        self._publish(client, agent_token, admin_token)
        resp = client.get("/api/v1/properties?min_price=200000000")
        assert resp.json()["meta"]["total"] == 0
        resp2 = client.get("/api/v1/properties?max_price=200000000")
        assert resp2.json()["meta"]["total"] == 1

    def test_search_pagination(self, client, agent_user, agent_token, admin_user, admin_token):
        for i in range(5):
            self._publish(client, agent_token, admin_token, {**_BASE_PAYLOAD, "title": f"Casa {i}"})
        resp = client.get("/api/v1/properties?page=1&page_size=2")
        data = resp.json()
        assert data["meta"]["total"] == 5
        assert data["meta"]["total_pages"] == 3
        assert len(data["data"]) == 2

    def test_include_own_returns_drafts_to_owner(self, client, agent_user, agent_token):
        # a freshly created (draft) property must be visible to its owner in the panel
        client.post("/api/v1/properties", json=_BASE_PAYLOAD, headers=_auth(agent_token))
        assert client.get("/api/v1/properties").json()["meta"]["total"] == 0  # public: hidden
        own = client.get("/api/v1/properties?include_own=true", headers=_auth(agent_token))
        assert own.status_code == 200
        body = own.json()
        assert body["meta"]["total"] == 1
        assert body["data"][0]["status"] == "draft"

    def test_include_own_ignored_without_auth(self, client, agent_user, agent_token):
        client.post("/api/v1/properties", json=_BASE_PAYLOAD, headers=_auth(agent_token))
        assert client.get("/api/v1/properties?include_own=true").json()["meta"]["total"] == 0


class TestShowOnHome:
    def _publish(self, client, agent_token, admin_token, **extra):
        payload = {**_BASE_PAYLOAD, **extra}
        cid = client.post("/api/v1/properties", json=payload, headers=_auth(agent_token)).json()["id"]
        client.post(f"/api/v1/properties/{cid}/submit", headers=_auth(agent_token))
        client.post(f"/api/v1/properties/{cid}/approve", headers=_auth(admin_token))
        return cid

    def test_on_home_lists_only_flagged_published(self, client, agent_user, agent_token, admin_user, admin_token):
        flagged = self._publish(client, agent_token, admin_token, show_on_home=True, title="EnPortada")
        plain = self._publish(client, agent_token, admin_token, title="NoPortada")
        ids = [i["id"] for i in client.get("/api/v1/properties?on_home=true").json()["data"]]
        assert flagged in ids
        assert plain not in ids

    def test_draft_flagged_not_on_home(self, client, agent_user, agent_token):
        # a flagged but unpublished property must NOT leak to the home
        client.post("/api/v1/properties", json={**_BASE_PAYLOAD, "show_on_home": True}, headers=_auth(agent_token))
        assert client.get("/api/v1/properties?on_home=true").json()["meta"]["total"] == 0

    def test_toggle_home_on_published_property(self, client, agent_user, agent_token, admin_user, admin_token):
        cid = self._publish(client, agent_token, admin_token, title="Toggle")
        assert client.get("/api/v1/properties?on_home=true").json()["meta"]["total"] == 0
        # PATCH /home works on a PUBLISHED property (no 409 from the edit guard)
        r = client.patch(f"/api/v1/properties/{cid}/home", json={"show_on_home": True}, headers=_auth(agent_token))
        assert r.status_code == 200
        assert r.json()["show_on_home"] is True
        assert cid in [i["id"] for i in client.get("/api/v1/properties?on_home=true").json()["data"]]
        client.patch(f"/api/v1/properties/{cid}/home", json={"show_on_home": False}, headers=_auth(agent_token))
        assert client.get("/api/v1/properties?on_home=true").json()["meta"]["total"] == 0

    def test_toggle_home_requires_auth(self, client, agent_user, agent_token, admin_user, admin_token):
        cid = self._publish(client, agent_token, admin_token, title="Owned")
        assert client.patch(f"/api/v1/properties/{cid}/home", json={"show_on_home": True}).status_code == 401
