"""Integration tests for /api/v1/projects."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration

_PROJECT_PAYLOAD = {
    "title": "Torres Verde",
    "developer_name": "Proppia Developments",
    "stage": "preventa",
    "price_from": 29000000000,
    "price_to": 52000000000,
    "currency": "COP",
    "bedrooms_min": 1,
    "bedrooms_max": 3,
    "area_min_m2": 52.0,
    "area_max_m2": 90.0,
}


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create(client, token, **overrides):
    payload = {**_PROJECT_PAYLOAD, **overrides}
    return client.post("/api/v1/projects", json=payload, headers=_auth(token))


def _publish(client, agent_token, admin_token, **overrides):
    created = _create(client, agent_token, **overrides).json()
    client.post(f"/api/v1/projects/{created['id']}/submit", headers=_auth(agent_token))
    client.post(f"/api/v1/projects/{created['id']}/approve", headers=_auth(admin_token))
    return created


class TestProjectCRUD:
    def test_create_project_agent(self, client, agent_user, agent_token):
        resp = _create(client, agent_token)
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "draft"
        assert data["stage"] == "preventa"
        assert data["slug"].startswith("torres-verde")

    def test_create_unauthenticated(self, client):
        resp = client.post("/api/v1/projects", json=_PROJECT_PAYLOAD)
        assert resp.status_code == 401

    def test_draft_hidden_from_public_detail(self, client, agent_user, agent_token):
        created = _create(client, agent_token).json()
        resp = client.get(f"/api/v1/projects/{created['slug']}")
        assert resp.status_code == 404

    def test_publish_lifecycle(self, client, agent_user, agent_token, admin_user, admin_token):
        project = _publish(client, agent_token, admin_token)
        resp = client.get(f"/api/v1/projects/{project['slug']}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "published"

    def test_approve_requires_moderate(self, client, agent_user, agent_token):
        created = _create(client, agent_token).json()
        client.post(f"/api/v1/projects/{created['id']}/submit", headers=_auth(agent_token))
        # agent lacks project:moderate
        resp = client.post(f"/api/v1/projects/{created['id']}/approve", headers=_auth(agent_token))
        assert resp.status_code == 403


class TestProjectSearch:
    def test_list_published_only(self, client, agent_user, agent_token, admin_user, admin_token):
        _create(client, agent_token, title="Borrador oculto")  # stays draft
        _publish(client, agent_token, admin_token, title="Torres Verde")
        resp = client.get("/api/v1/projects")
        assert resp.status_code == 200
        body = resp.json()
        assert body["meta"]["total"] == 1
        assert body["data"][0]["title"] == "Torres Verde"

    def test_filter_by_stage(self, client, agent_user, agent_token, admin_user, admin_token):
        _publish(client, agent_token, admin_token, title="Preventa", stage="preventa")
        _publish(client, agent_token, admin_token, title="Construccion", stage="construccion")
        resp = client.get("/api/v1/projects?stage=construccion")
        assert resp.json()["meta"]["total"] == 1
        assert resp.json()["data"][0]["title"] == "Construccion"

    def test_add_image(self, client, agent_user, agent_token):
        created = _create(client, agent_token).json()
        resp = client.post(
            f"/api/v1/projects/{created['id']}/images",
            json={"cdn_url": "https://cdn.test/p.jpg", "role": "main"},
            headers=_auth(agent_token),
        )
        assert resp.status_code == 201
        images = client.get(f"/api/v1/projects/{created['id']}/images").json()
        assert len(images) == 1
        assert images[0]["cdn_url"] == "https://cdn.test/p.jpg"


class TestProjectAdminListing:
    def test_status_all_shows_drafts_to_editor(self, client, agent_user, agent_token):
        _create(client, agent_token, title="Borrador")
        # public listing: drafts hidden
        assert client.get("/api/v1/projects").json()["meta"]["total"] == 0
        # editor with status=all: draft visible
        r = client.get("/api/v1/projects?status=all", headers=_auth(agent_token))
        assert r.json()["meta"]["total"] == 1

    def test_status_all_ignored_without_auth(self, client, agent_user, agent_token):
        _create(client, agent_token, title="Borrador")
        assert client.get("/api/v1/projects?status=all").json()["meta"]["total"] == 0


class TestProjectImageUpload:
    def test_upload_and_delete(self, client, agent_user, agent_token):
        created = _create(client, agent_token).json()
        png = b"\x89PNG\r\n\x1a\n" + b"0" * 64
        up = client.post(
            f"/api/v1/projects/{created['id']}/images/upload",
            files={"file": ("p.png", png, "image/png")},
            headers=_auth(agent_token),
        )
        assert up.status_code == 201
        assert up.json()["cdn_url"]
        img_id = up.json()["id"]
        assert len(client.get(f"/api/v1/projects/{created['id']}/images").json()) == 1

        d = client.delete(f"/api/v1/projects/{created['id']}/images/{img_id}", headers=_auth(agent_token))
        assert d.status_code == 204
        assert client.get(f"/api/v1/projects/{created['id']}/images").json() == []

    def test_upload_rejects_non_image(self, client, agent_user, agent_token):
        created = _create(client, agent_token).json()
        r = client.post(
            f"/api/v1/projects/{created['id']}/images/upload",
            files={"file": ("x.txt", b"hello", "text/plain")},
            headers=_auth(agent_token),
        )
        assert r.status_code == 422
