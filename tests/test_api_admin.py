"""Integration tests for /api/v1/admin/* and /api/v1/metrics/event."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration

_PROPERTY_PAYLOAD = {
    "title": "Propiedad admin test",
    "operation_type": "sale",
    "property_kind": "apartment",
    "price_amount": 2000000,
    "currency": "MXN",
}


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create_and_submit(client, agent_token):
    resp = client.post("/api/v1/properties", json=_PROPERTY_PAYLOAD, headers=_auth(agent_token))
    prop_id = resp.json()["id"]
    client.post(f"/api/v1/properties/{prop_id}/submit", headers=_auth(agent_token))
    return prop_id


def _publish(client, agent_token, admin_token):
    prop_id = _create_and_submit(client, agent_token)
    client.post(f"/api/v1/properties/{prop_id}/approve", headers=_auth(admin_token))
    return prop_id


# ---------------------------------------------------------------------------
# Moderation queue
# ---------------------------------------------------------------------------

class TestModerationQueue:
    def test_moderation_requires_permission(self, client, agent_user, agent_token):
        resp = client.get("/api/v1/admin/moderation", headers=_auth(agent_token))
        assert resp.status_code == 403

    def test_moderation_unauthenticated(self, client):
        resp = client.get("/api/v1/admin/moderation")
        assert resp.status_code == 401

    def test_moderation_returns_pending_properties(self, client, agent_user, agent_token, admin_user, admin_token):
        _create_and_submit(client, agent_token)
        _create_and_submit(client, agent_token)
        resp = client.get("/api/v1/admin/moderation", headers=_auth(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["meta"]["total"] >= 2
        assert all(p["status"] == "pending" for p in data["data"])

    def test_moderation_excludes_published(self, client, agent_user, agent_token, admin_user, admin_token):
        _publish(client, agent_token, admin_token)
        resp = client.get("/api/v1/admin/moderation", headers=_auth(admin_token))
        assert all(p["status"] == "pending" for p in resp.json()["data"])


# ---------------------------------------------------------------------------
# Admin stats
# ---------------------------------------------------------------------------

class TestAdminStats:
    def test_stats_requires_permission(self, client, agent_user, agent_token):
        resp = client.get("/api/v1/admin/stats", headers=_auth(agent_token))
        assert resp.status_code == 403

    def test_stats_returns_counts(self, client, admin_user, admin_token, agent_user, agent_token):
        _publish(client, agent_token, admin_token)
        resp = client.get("/api/v1/admin/stats", headers=_auth(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert "total_users" in data
        assert "published_properties" in data
        assert data["total_users"] >= 2  # agent + admin
        assert data["published_properties"] >= 1


# ---------------------------------------------------------------------------
# Admin user list
# ---------------------------------------------------------------------------

class TestAdminUsers:
    def test_list_users_requires_permission(self, client, agent_user, agent_token):
        resp = client.get("/api/v1/admin/users", headers=_auth(agent_token))
        assert resp.status_code == 403

    def test_list_users_returns_paginated(self, client, admin_user, admin_token, agent_user):
        resp = client.get("/api/v1/admin/users", headers=_auth(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert "meta" in data
        assert data["meta"]["total"] >= 2  # agent + admin


# ---------------------------------------------------------------------------
# Metrics events
# ---------------------------------------------------------------------------

class TestMetricsEvent:
    def test_record_view_event(self, client, agent_user, agent_token, admin_user, admin_token):
        prop_id = _publish(client, agent_token, admin_token)
        resp = client.post("/api/v1/metrics/event", json={
            "property_id": prop_id,
            "event_type": "view",
            "source": "organic",
        })
        assert resp.status_code == 202
        assert resp.json()["accepted"] is True

    def test_record_cta_click_event(self, client, agent_user, agent_token, admin_user, admin_token):
        prop_id = _publish(client, agent_token, admin_token)
        resp = client.post("/api/v1/metrics/event", json={
            "property_id": prop_id,
            "event_type": "cta_click",
        })
        assert resp.status_code == 202

    def test_event_for_draft_not_accepted(self, client, agent_user, agent_token):
        resp_prop = client.post("/api/v1/properties", json=_PROPERTY_PAYLOAD, headers=_auth(agent_token))
        prop_id = resp_prop.json()["id"]
        resp = client.post("/api/v1/metrics/event", json={
            "property_id": prop_id,
            "event_type": "view",
        })
        assert resp.status_code == 202
        assert resp.json()["accepted"] is False

    def test_view_event_increments_views_count(self, client, agent_user, agent_token, admin_user, admin_token):
        prop_id = _publish(client, agent_token, admin_token)
        before = client.get(f"/api/v1/properties/{prop_id}").json()["views_count"]
        client.post("/api/v1/metrics/event", json={"property_id": prop_id, "event_type": "view"})
        after = client.get(f"/api/v1/properties/{prop_id}").json()["views_count"]
        assert after == before + 1
