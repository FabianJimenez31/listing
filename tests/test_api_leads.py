"""Integration tests for /api/v1/leads."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration

_PROPERTY_PAYLOAD = {
    "title": "Apartamento Centro",
    "operation_type": "rent",
    "property_kind": "apartment",
    "price_amount": 80000,
    "currency": "USD",
}


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _publish_property(client, agent_token, admin_token, payload=None):
    payload = payload or _PROPERTY_PAYLOAD
    resp = client.post("/api/v1/properties", json=payload, headers=_auth(agent_token))
    prop_id = resp.json()["id"]
    client.post(f"/api/v1/properties/{prop_id}/submit", headers=_auth(agent_token))
    client.post(f"/api/v1/properties/{prop_id}/approve", headers=_auth(admin_token))
    return prop_id


class TestLeadCreate:
    def test_create_form_lead_with_consent(self, client, agent_user, agent_token, admin_user, admin_token):
        prop_id = _publish_property(client, agent_token, admin_token)
        resp = client.post("/api/v1/leads", json={
            "property_id": prop_id,
            "name": "Pedro López",
            "email": "pedro@example.com",
            "channel": "form",
            "consent_given": True,
            "consent_text": "Acepto el aviso de privacidad",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "new"
        assert data["channel"] == "form"
        assert data["consent_given"] is True

    def test_form_lead_without_consent_fails(self, client, agent_user, agent_token, admin_user, admin_token):
        prop_id = _publish_property(client, agent_token, admin_token)
        resp = client.post("/api/v1/leads", json={
            "property_id": prop_id,
            "name": "Ana",
            "email": "ana@example.com",
            "channel": "form",
            "consent_given": False,
        })
        assert resp.status_code == 422

    def test_whatsapp_lead_no_consent_needed(self, client, agent_user, agent_token, admin_user, admin_token):
        prop_id = _publish_property(client, agent_token, admin_token)
        resp = client.post("/api/v1/leads", json={
            "property_id": prop_id,
            "name": "Luis",
            "phone": "+525512345678",
            "channel": "whatsapp",
        })
        assert resp.status_code == 201

    def test_lead_for_unpublished_property_fails(self, client, agent_user, agent_token):
        resp_prop = client.post("/api/v1/properties", json=_PROPERTY_PAYLOAD, headers=_auth(agent_token))
        prop_id = resp_prop.json()["id"]
        resp = client.post("/api/v1/leads", json={
            "property_id": prop_id,
            "name": "X",
            "email": "x@x.com",
            "channel": "form",
            "consent_given": True,
        })
        assert resp.status_code == 404

    def test_lead_requires_email_or_phone(self, client, agent_user, agent_token, admin_user, admin_token):
        prop_id = _publish_property(client, agent_token, admin_token)
        resp = client.post("/api/v1/leads", json={
            "property_id": prop_id,
            "name": "No Contact",
            "channel": "whatsapp",
        })
        assert resp.status_code == 422


class TestLeadList:
    def test_list_leads_requires_auth(self, client):
        resp = client.get("/api/v1/leads")
        assert resp.status_code == 401

    def test_admin_sees_all_leads(self, client, agent_user, agent_token, admin_user, admin_token):
        prop_id = _publish_property(client, agent_token, admin_token)
        client.post("/api/v1/leads", json={
            "property_id": prop_id, "name": "X", "email": "x@x.com",
            "channel": "form", "consent_given": True,
        })
        resp = client.get("/api/v1/leads", headers=_auth(admin_token))
        assert resp.status_code == 200
        assert resp.json()["meta"]["total"] >= 1
