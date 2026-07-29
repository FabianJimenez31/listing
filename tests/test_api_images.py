"""Integration tests for /api/v1/properties/{id}/images."""
from __future__ import annotations

import io
import pytest

pytestmark = pytest.mark.integration

_PROPERTY_PAYLOAD = {
    "title": "Casa con fotos",
    "operation_type": "sale",
    "property_kind": "house",
    "price_amount": 200000000,
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


def _fake_jpeg(size: int = 1024) -> bytes:
    """Minimal JPEG bytes (SOI + EOI markers)."""
    return b"\xff\xd8\xff\xe0" + b"\x00" * (size - 6) + b"\xff\xd9"


class TestImageUpload:
    def test_upload_image_success(self, client, agent_user, agent_token):
        resp = client.post("/api/v1/properties", json=_PROPERTY_PAYLOAD, headers=_auth(agent_token))
        prop_id = resp.json()["id"]

        upload = client.post(
            f"/api/v1/properties/{prop_id}/images",
            files={"file": ("photo.jpg", io.BytesIO(_fake_jpeg()), "image/jpeg")},
            headers=_auth(agent_token),
        )
        assert upload.status_code == 201
        data = upload.json()
        assert data["role"] == "gallery"
        assert data["content_type"] == "image/jpeg"
        assert data["cdn_url"] is not None

    def test_upload_requires_auth(self, client, agent_user, agent_token):
        resp = client.post("/api/v1/properties", json=_PROPERTY_PAYLOAD, headers=_auth(agent_token))
        prop_id = resp.json()["id"]
        upload = client.post(
            f"/api/v1/properties/{prop_id}/images",
            files={"file": ("photo.jpg", io.BytesIO(_fake_jpeg()), "image/jpeg")},
        )
        assert upload.status_code == 401

    def test_upload_wrong_content_type(self, client, agent_user, agent_token):
        resp = client.post("/api/v1/properties", json=_PROPERTY_PAYLOAD, headers=_auth(agent_token))
        prop_id = resp.json()["id"]
        upload = client.post(
            f"/api/v1/properties/{prop_id}/images",
            files={"file": ("doc.pdf", io.BytesIO(b"%PDF"), "application/pdf")},
            headers=_auth(agent_token),
        )
        assert upload.status_code == 422

    def test_upload_nonexistent_property(self, client, agent_user, agent_token):
        upload = client.post(
            "/api/v1/properties/nonexistent-id/images",
            files={"file": ("photo.jpg", io.BytesIO(_fake_jpeg()), "image/jpeg")},
            headers=_auth(agent_token),
        )
        assert upload.status_code == 404

    def test_upload_other_user_property_forbidden(self, client, agent_user, agent_token, admin_user, admin_token):
        resp = client.post("/api/v1/properties", json=_PROPERTY_PAYLOAD, headers=_auth(agent_token))
        prop_id = resp.json()["id"]
        # admin_user uploads to agent's property (admin can because has property:moderate)
        # Use a different non-admin user for forbidden test: register a third user
        client.post("/api/v1/auth/register", json={
            "email": "other@test.com", "password": "Pass1234!", "full_name": "Other",
        })
        tokens = client.post("/api/v1/auth/login", json={
            "email": "other@test.com", "password": "Pass1234!",
        }).json()
        other_token = tokens["access_token"]
        upload = client.post(
            f"/api/v1/properties/{prop_id}/images",
            files={"file": ("photo.jpg", io.BytesIO(_fake_jpeg()), "image/jpeg")},
            headers=_auth(other_token),
        )
        assert upload.status_code == 403

    def test_upload_main_demotes_existing_main(self, client, agent_user, agent_token):
        resp = client.post("/api/v1/properties", json=_PROPERTY_PAYLOAD, headers=_auth(agent_token))
        prop_id = resp.json()["id"]

        # Upload first main image
        img1 = client.post(
            f"/api/v1/properties/{prop_id}/images?role=main",
            files={"file": ("photo1.jpg", io.BytesIO(_fake_jpeg()), "image/jpeg")},
            headers=_auth(agent_token),
        )
        assert img1.json()["role"] == "main"

        # Upload second main image — first should become gallery
        img2 = client.post(
            f"/api/v1/properties/{prop_id}/images?role=main",
            files={"file": ("photo2.jpg", io.BytesIO(_fake_jpeg()), "image/jpeg")},
            headers=_auth(agent_token),
        )
        assert img2.status_code == 201
        assert img2.json()["role"] == "main"


class TestImageDelete:
    def test_delete_image(self, client, agent_user, agent_token):
        resp = client.post("/api/v1/properties", json=_PROPERTY_PAYLOAD, headers=_auth(agent_token))
        prop_id = resp.json()["id"]

        img = client.post(
            f"/api/v1/properties/{prop_id}/images",
            files={"file": ("photo.jpg", io.BytesIO(_fake_jpeg()), "image/jpeg")},
            headers=_auth(agent_token),
        ).json()

        del_resp = client.delete(
            f"/api/v1/properties/{prop_id}/images/{img['id']}",
            headers=_auth(agent_token),
        )
        assert del_resp.status_code == 204

    def test_delete_nonexistent_image(self, client, agent_user, agent_token):
        resp = client.post("/api/v1/properties", json=_PROPERTY_PAYLOAD, headers=_auth(agent_token))
        prop_id = resp.json()["id"]
        del_resp = client.delete(
            f"/api/v1/properties/{prop_id}/images/does-not-exist",
            headers=_auth(agent_token),
        )
        assert del_resp.status_code == 404


class TestImageReorder:
    def test_reorder_images(self, client, agent_user, agent_token):
        resp = client.post("/api/v1/properties", json=_PROPERTY_PAYLOAD, headers=_auth(agent_token))
        prop_id = resp.json()["id"]

        ids = []
        for _ in range(3):
            img = client.post(
                f"/api/v1/properties/{prop_id}/images",
                files={"file": ("photo.jpg", io.BytesIO(_fake_jpeg()), "image/jpeg")},
                headers=_auth(agent_token),
            ).json()
            ids.append(img["id"])

        # Reverse order
        reorder_resp = client.patch(
            f"/api/v1/properties/{prop_id}/images/reorder",
            json={"ordered_ids": list(reversed(ids))},
            headers=_auth(agent_token),
        )
        assert reorder_resp.status_code == 200
        result_ids = [img["id"] for img in reorder_resp.json()]
        assert result_ids == list(reversed(ids))
