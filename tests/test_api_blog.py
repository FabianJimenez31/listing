"""Integration tests for /api/v1/posts (blog)."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestBlogCRUD:
    def test_create_post_admin(self, client, admin_user, admin_token):
        resp = client.post(
            "/api/v1/posts",
            json={"title": "Cómo invertir en Miami", "status": "published", "category": "Mercado USA"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["slug"] == "como-invertir-en-miami"
        assert data["status"] == "published"
        assert data["published_at"] is not None
        assert data["author_id"] == admin_user.id

    def test_create_requires_permission(self, client, agent_user, agent_token):
        resp = client.post("/api/v1/posts", json={"title": "X"}, headers=_auth(agent_token))
        assert resp.status_code == 403

    def test_list_only_published(self, client, admin_user, admin_token):
        client.post("/api/v1/posts", json={"title": "Publicado", "status": "published"}, headers=_auth(admin_token))
        client.post("/api/v1/posts", json={"title": "Borrador", "status": "draft"}, headers=_auth(admin_token))
        resp = client.get("/api/v1/posts")
        assert resp.status_code == 200
        body = resp.json()
        assert body["meta"]["total"] == 1
        assert body["data"][0]["title"] == "Publicado"

    def test_draft_detail_hidden_from_public(self, client, admin_user, admin_token):
        created = client.post(
            "/api/v1/posts", json={"title": "Secreto", "status": "draft"}, headers=_auth(admin_token)
        ).json()
        assert client.get(f"/api/v1/posts/{created['slug']}").status_code == 404

    def test_publish_via_update(self, client, admin_user, admin_token):
        created = client.post(
            "/api/v1/posts", json={"title": "Pendiente", "status": "draft"}, headers=_auth(admin_token)
        ).json()
        resp = client.put(
            f"/api/v1/posts/{created['id']}", json={"status": "published"}, headers=_auth(admin_token)
        )
        assert resp.status_code == 200
        assert resp.json()["published_at"] is not None
        assert client.get(f"/api/v1/posts/{created['slug']}").status_code == 200

    def test_status_all_shows_drafts_to_editor(self, client, admin_user, admin_token):
        client.post("/api/v1/posts", json={"title": "Borrador", "status": "draft"}, headers=_auth(admin_token))
        # public: drafts hidden
        assert client.get("/api/v1/posts").json()["meta"]["total"] == 0
        # editor with status=all: draft visible
        r = client.get("/api/v1/posts?status=all", headers=_auth(admin_token))
        assert r.json()["meta"]["total"] == 1

    def test_delete_post(self, client, admin_user, admin_token):
        created = client.post(
            "/api/v1/posts", json={"title": "Borrar", "status": "published"}, headers=_auth(admin_token)
        ).json()
        resp = client.delete(f"/api/v1/posts/{created['id']}", headers=_auth(admin_token))
        assert resp.status_code == 204
        assert client.get("/api/v1/posts").json()["meta"]["total"] == 0
