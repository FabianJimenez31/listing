"""Integration tests for /api/v1/settings (site branding / logo)."""
from __future__ import annotations

import io

import pytest

pytestmark = pytest.mark.integration


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _fake_png(size: int = 1024) -> bytes:
    """Minimal PNG bytes (signature + filler)."""
    return b"\x89PNG\r\n\x1a\n" + b"\x00" * (size - 8)


class TestGetSettings:
    def test_get_settings_public_defaults(self, client):
        resp = client.get("/api/v1/settings")
        assert resp.status_code == 200
        data = resp.json()
        assert data["logo_url"] is None

    def test_get_settings_no_auth_required(self, client):
        # No Authorization header at all.
        assert client.get("/api/v1/settings").status_code == 200


class TestUploadLogo:
    def test_upload_logo_admin(self, client, admin_user, admin_token):
        resp = client.post(
            "/api/v1/settings/logo",
            files={"file": ("logo.png", io.BytesIO(_fake_png()), "image/png")},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["logo_url"] is not None

        # The public endpoint now reflects the uploaded logo.
        public = client.get("/api/v1/settings")
        assert public.json()["logo_url"] == resp.json()["logo_url"]

    def test_upload_logo_replaces_previous(self, client, admin_user, admin_token):
        first = client.post(
            "/api/v1/settings/logo",
            files={"file": ("a.png", io.BytesIO(_fake_png()), "image/png")},
            headers=_auth(admin_token),
        ).json()["logo_url"]
        second = client.post(
            "/api/v1/settings/logo",
            files={"file": ("b.png", io.BytesIO(_fake_png()), "image/png")},
            headers=_auth(admin_token),
        ).json()["logo_url"]
        assert first != second

    def test_upload_logo_requires_auth(self, client):
        resp = client.post(
            "/api/v1/settings/logo",
            files={"file": ("logo.png", io.BytesIO(_fake_png()), "image/png")},
        )
        assert resp.status_code == 401

    def test_upload_logo_requires_permission(self, client, agent_user, agent_token):
        resp = client.post(
            "/api/v1/settings/logo",
            files={"file": ("logo.png", io.BytesIO(_fake_png()), "image/png")},
            headers=_auth(agent_token),
        )
        assert resp.status_code == 403

    def test_upload_logo_wrong_content_type(self, client, admin_user, admin_token):
        resp = client.post(
            "/api/v1/settings/logo",
            files={"file": ("doc.pdf", io.BytesIO(b"%PDF"), "application/pdf")},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 422


class TestUploadLegalDocument:
    def test_upload_pdf_admin(self, client, admin_user, admin_token):
        resp = client.post(
            "/api/v1/settings/legal-document",
            params={"kind": "terminos"},
            files={"file": ("terminos.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["url"].endswith(".pdf")
        assert body["storage_key"].startswith("legal/terminos-")
        assert body["filename"] == "terminos.pdf"

    def test_uploaded_url_can_be_saved_as_legal_link(self, client, admin_user, admin_token):
        url = client.post(
            "/api/v1/settings/legal-document",
            params={"kind": "privacidad"},
            files={"file": ("p.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
            headers=_auth(admin_token),
        ).json()["url"]

        client.put(
            "/api/v1/settings",
            json={"legal_privacy_url": url, "footer_logos": []},
            headers=_auth(admin_token),
        )
        assert client.get("/api/v1/settings").json()["legal_privacy_url"] == url

    def test_unknown_kind_falls_back(self, client, admin_user, admin_token):
        resp = client.post(
            "/api/v1/settings/legal-document",
            params={"kind": "../../etc"},
            files={"file": ("x.pdf", io.BytesIO(b"%PDF"), "application/pdf")},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201
        assert resp.json()["storage_key"].startswith("legal/documento-")

    def test_rejects_image_content_type(self, client, admin_user, admin_token):
        resp = client.post(
            "/api/v1/settings/legal-document",
            files={"file": ("logo.png", io.BytesIO(_fake_png()), "image/png")},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 422

    def test_requires_permission(self, client, agent_user, agent_token):
        resp = client.post(
            "/api/v1/settings/legal-document",
            files={"file": ("x.pdf", io.BytesIO(b"%PDF"), "application/pdf")},
            headers=_auth(agent_token),
        )
        assert resp.status_code == 403

    def test_requires_auth(self, client):
        resp = client.post(
            "/api/v1/settings/legal-document",
            files={"file": ("x.pdf", io.BytesIO(b"%PDF"), "application/pdf")},
        )
        assert resp.status_code == 401


class TestUpdateFooter:
    def test_get_settings_exposes_footer_fields(self, client):
        data = client.get("/api/v1/settings").json()
        assert data["footer_logos"] == []
        assert data["footer_tagline"] is None

    def test_update_footer_admin(self, client, admin_user, admin_token):
        payload = {
            "footer_tagline": "Texto del footer",
            "copyright_text": "© 2026 Proppia",
            "social_instagram": "https://instagram.com/proppietario",
            "social_linkedin": None,
            "social_youtube": None,
            "legal_privacy_url": "/legal/privacidad",
            "legal_terms_url": "/legal/terminos",
            "legal_cookies_url": "/legal/cookies",
            "footer_logos": [
                {"name": "Aliado A", "image_url": "https://cdn.test/a.png", "link": "https://a.com", "storage_key": "branding/footer-a.png"},
                {"name": "Aliado B", "image_url": "https://cdn.test/b.png", "link": None, "storage_key": None},
            ],
        }
        resp = client.put("/api/v1/settings", json=payload, headers=_auth(admin_token))
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["footer_tagline"] == "Texto del footer"
        assert len(body["footer_logos"]) == 2
        assert body["footer_logos"][0]["name"] == "Aliado A"

        # Persisted and exposed publicly.
        public = client.get("/api/v1/settings").json()
        assert public["social_instagram"] == "https://instagram.com/proppietario"
        assert len(public["footer_logos"]) == 2

    def test_update_footer_requires_permission(self, client, agent_user, agent_token):
        resp = client.put("/api/v1/settings", json={"footer_logos": []}, headers=_auth(agent_token))
        assert resp.status_code == 403

    def test_update_footer_requires_auth(self, client):
        assert client.put("/api/v1/settings", json={"footer_logos": []}).status_code == 401

    def test_upload_footer_logo_admin(self, client, admin_user, admin_token):
        resp = client.post(
            "/api/v1/settings/footer-logo",
            files={"file": ("ally.png", io.BytesIO(_fake_png()), "image/png")},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["url"]
        assert body["storage_key"].startswith("branding/footer-")

    def test_upload_footer_logo_requires_permission(self, client, agent_user, agent_token):
        resp = client.post(
            "/api/v1/settings/footer-logo",
            files={"file": ("ally.png", io.BytesIO(_fake_png()), "image/png")},
            headers=_auth(agent_token),
        )
        assert resp.status_code == 403


class TestFooterBrandLogo:
    def test_default_footer_logo_url_none(self, client):
        assert client.get("/api/v1/settings").json()["footer_logo_url"] is None

    def test_upload_footer_brand_logo_admin(self, client, admin_user, admin_token):
        resp = client.post(
            "/api/v1/settings/footer-brand-logo",
            files={"file": ("footer.png", io.BytesIO(_fake_png()), "image/png")},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["footer_logo_url"] is not None
        # Independent from the header logo, which stays unset.
        assert body["logo_url"] is None
        # Public endpoint reflects it.
        assert client.get("/api/v1/settings").json()["footer_logo_url"] == body["footer_logo_url"]

    def test_upload_footer_brand_logo_requires_permission(self, client, agent_user, agent_token):
        resp = client.post(
            "/api/v1/settings/footer-brand-logo",
            files={"file": ("footer.png", io.BytesIO(_fake_png()), "image/png")},
            headers=_auth(agent_token),
        )
        assert resp.status_code == 403

    def test_delete_footer_brand_logo_clears_it(self, client, admin_user, admin_token):
        client.post(
            "/api/v1/settings/footer-brand-logo",
            files={"file": ("footer.png", io.BytesIO(_fake_png()), "image/png")},
            headers=_auth(admin_token),
        )
        resp = client.delete("/api/v1/settings/footer-brand-logo", headers=_auth(admin_token))
        assert resp.status_code == 200
        assert resp.json()["footer_logo_url"] is None
        assert client.get("/api/v1/settings").json()["footer_logo_url"] is None

    def test_delete_footer_brand_logo_requires_permission(self, client, agent_user, agent_token):
        resp = client.delete("/api/v1/settings/footer-brand-logo", headers=_auth(agent_token))
        assert resp.status_code == 403


class TestDeleteLogo:
    def test_delete_logo_clears_it(self, client, admin_user, admin_token):
        client.post(
            "/api/v1/settings/logo",
            files={"file": ("logo.png", io.BytesIO(_fake_png()), "image/png")},
            headers=_auth(admin_token),
        )
        resp = client.delete("/api/v1/settings/logo", headers=_auth(admin_token))
        assert resp.status_code == 200
        assert resp.json()["logo_url"] is None
        assert client.get("/api/v1/settings").json()["logo_url"] is None

    def test_delete_logo_requires_permission(self, client, agent_user, agent_token):
        resp = client.delete("/api/v1/settings/logo", headers=_auth(agent_token))
        assert resp.status_code == 403
