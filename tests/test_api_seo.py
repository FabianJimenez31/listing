"""Integration tests for SEO endpoints: /robots.txt and /sitemap.xml."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration

_PROPERTY_PAYLOAD = {
    "title": "Propiedad SEO",
    "operation_type": "sale",
    "property_kind": "apartment",
    "price_amount": 100000,
    "currency": "USD",
}


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestRobotsTxt:
    def test_robots_returns_200(self, client):
        resp = client.get("/robots.txt")
        assert resp.status_code == 200

    def test_robots_content_type(self, client):
        resp = client.get("/robots.txt")
        assert "text/plain" in resp.headers["content-type"]

    def test_robots_has_sitemap_reference(self, client):
        resp = client.get("/robots.txt")
        assert "Sitemap:" in resp.text
        assert "sitemap.xml" in resp.text

    def test_robots_disallows_api(self, client):
        resp = client.get("/robots.txt")
        assert "Disallow: /api/" in resp.text


class TestSitemapXml:
    def test_sitemap_returns_200(self, client):
        resp = client.get("/sitemap.xml")
        assert resp.status_code == 200

    def test_sitemap_content_type(self, client):
        resp = client.get("/sitemap.xml")
        assert "xml" in resp.headers["content-type"]

    def test_sitemap_has_xml_declaration(self, client):
        resp = client.get("/sitemap.xml")
        assert resp.text.startswith('<?xml version="1.0"')

    def test_sitemap_includes_published_property(self, client, agent_user, agent_token, admin_user, admin_token):
        # Create and publish a property
        create_resp = client.post("/api/v1/properties", json=_PROPERTY_PAYLOAD, headers=_auth(agent_token))
        prop_id = create_resp.json()["id"]
        prop_nid = create_resp.json()["nid"]
        client.post(f"/api/v1/properties/{prop_id}/submit", headers=_auth(agent_token))
        client.post(f"/api/v1/properties/{prop_id}/approve", headers=_auth(admin_token))

        resp = client.get("/sitemap.xml")
        # Canonical public URL is the numeric Record ID (NID), HubSpot-style.
        assert f"/propiedades/{prop_nid}" in resp.text

    def test_sitemap_excludes_draft_property(self, client, agent_user, agent_token):
        create_resp = client.post("/api/v1/properties", json=_PROPERTY_PAYLOAD, headers=_auth(agent_token))
        prop_nid = create_resp.json()["nid"]

        resp = client.get("/sitemap.xml")
        assert f"/propiedades/{prop_nid}" not in resp.text

    def test_sitemap_includes_static_pages(self, client):
        resp = client.get("/sitemap.xml")
        assert "/propiedades" in resp.text
