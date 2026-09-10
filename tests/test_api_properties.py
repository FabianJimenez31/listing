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

    def test_has_storage_defaults_false(self, client, agent_user, agent_token):
        resp = client.post("/api/v1/properties", json=_BASE_PAYLOAD, headers=_auth(agent_token))
        assert resp.status_code == 201
        assert resp.json()["has_storage"] is False

    def test_create_with_storage_persists(self, client, agent_user, agent_token):
        resp = client.post(
            "/api/v1/properties",
            json={**_BASE_PAYLOAD, "has_storage": True},
            headers=_auth(agent_token),
        )
        assert resp.status_code == 201
        prop_id = resp.json()["id"]
        assert resp.json()["has_storage"] is True
        # Survives a re-read.
        got = client.get(f"/api/v1/properties/{prop_id}", headers=_auth(agent_token))
        assert got.json()["has_storage"] is True

    def test_update_storage_flag(self, client, agent_user, agent_token):
        prop_id = client.post(
            "/api/v1/properties", json=_BASE_PAYLOAD, headers=_auth(agent_token)
        ).json()["id"]
        upd = client.put(
            f"/api/v1/properties/{prop_id}",
            json={"has_storage": True},
            headers=_auth(agent_token),
        )
        assert upd.status_code == 200
        assert upd.json()["has_storage"] is True

    def test_feature_flags_default_false(self, client, agent_user, agent_token):
        data = client.post("/api/v1/properties", json=_BASE_PAYLOAD, headers=_auth(agent_token)).json()
        assert data["has_elevator"] is False
        assert data["has_study"] is False

    def test_create_with_elevator_and_study_persists(self, client, agent_user, agent_token):
        resp = client.post(
            "/api/v1/properties",
            json={**_BASE_PAYLOAD, "has_elevator": True, "has_study": True},
            headers=_auth(agent_token),
        )
        assert resp.status_code == 201
        prop_id = resp.json()["id"]
        assert resp.json()["has_elevator"] is True
        assert resp.json()["has_study"] is True
        got = client.get(f"/api/v1/properties/{prop_id}", headers=_auth(agent_token)).json()
        assert got["has_elevator"] is True
        assert got["has_study"] is True


class TestPropertyDescriptiveFields:
    """Estrato, balcón/terraza, vista, administración, antigüedad, vigilancia, piso."""

    _EXTRA = {
        "stratum": 4,
        "has_balcony": True,
        "view_type": "external",
        "admin_fee_amount": 250000,  # minor units (centavos)
        "age_years": 8,
        "security_type": "private",
        "floor_number": 7,
        "total_floors": 12,
    }

    def test_defaults_when_absent(self, client, agent_user, agent_token):
        data = client.post("/api/v1/properties", json=_BASE_PAYLOAD, headers=_auth(agent_token)).json()
        assert data["has_balcony"] is False
        assert data["stratum"] is None
        assert data["view_type"] is None
        assert data["admin_fee_amount"] is None
        assert data["age_years"] is None
        assert data["security_type"] is None

    def test_create_persists_descriptive_fields(self, client, agent_user, agent_token):
        resp = client.post(
            "/api/v1/properties", json={**_BASE_PAYLOAD, **self._EXTRA}, headers=_auth(agent_token)
        )
        assert resp.status_code == 201, resp.text
        prop_id = resp.json()["id"]
        got = client.get(f"/api/v1/properties/{prop_id}", headers=_auth(agent_token)).json()
        for key, value in self._EXTRA.items():
            assert got[key] == value, key

    def test_update_descriptive_fields(self, client, agent_user, agent_token):
        prop_id = client.post(
            "/api/v1/properties", json=_BASE_PAYLOAD, headers=_auth(agent_token)
        ).json()["id"]
        upd = client.put(
            f"/api/v1/properties/{prop_id}",
            json={"stratum": 6, "security_type": "automated", "has_balcony": True},
            headers=_auth(agent_token),
        )
        assert upd.status_code == 200
        body = upd.json()
        assert body["stratum"] == 6
        assert body["security_type"] == "automated"
        assert body["has_balcony"] is True

    def test_stratum_out_of_range_rejected(self, client, agent_token):
        resp = client.post(
            "/api/v1/properties", json={**_BASE_PAYLOAD, "stratum": 7}, headers=_auth(agent_token)
        )
        assert resp.status_code == 422

    def test_invalid_view_type_rejected(self, client, agent_token):
        resp = client.post(
            "/api/v1/properties", json={**_BASE_PAYLOAD, "view_type": "panoramic"}, headers=_auth(agent_token)
        )
        assert resp.status_code == 422

    def test_duplicate_copies_descriptive_fields(self, client, agent_user, agent_token, admin_user, admin_token):
        prop_id = client.post(
            "/api/v1/properties", json={**_BASE_PAYLOAD, **self._EXTRA}, headers=_auth(agent_token)
        ).json()["id"]
        client.post(f"/api/v1/properties/{prop_id}/submit", headers=_auth(agent_token))
        client.post(f"/api/v1/properties/{prop_id}/approve", headers=_auth(admin_token))
        clone = client.post(f"/api/v1/properties/{prop_id}/duplicate", headers=_auth(agent_token)).json()
        for key, value in self._EXTRA.items():
            assert clone[key] == value, key


class TestPropertyLocationBreadcrumb:
    def _mkloc(self, client, admin_token, name, slug, level, parent=None):
        resp = client.post(
            "/api/v1/locations",
            json={"name": name, "slug": slug, "level": level, "parent_id": parent},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        return resp.json()["id"]

    def test_detail_returns_full_location_path(self, client, agent_user, agent_token, admin_user, admin_token):
        country = self._mkloc(client, admin_token, "Colombia", "colombia", "country")
        city = self._mkloc(client, admin_token, "Bogotá", "bogota", "city", country)
        barrio = self._mkloc(client, admin_token, "Chapinero", "chapinero", "locality", city)

        resp = client.post(
            "/api/v1/properties",
            json={**_BASE_PAYLOAD, "location_id": barrio},
            headers=_auth(agent_token),
        )
        assert resp.status_code == 201
        prop_id = resp.json()["id"]

        got = client.get(f"/api/v1/properties/{prop_id}", headers=_auth(agent_token)).json()
        assert got["location"]["id"] == barrio
        assert [c["name"] for c in got["location"]["path"]] == ["Colombia", "Bogotá", "Chapinero"]

    def test_path_is_single_node_when_no_parent(self, client, agent_user, agent_token, admin_user, admin_token):
        country = self._mkloc(client, admin_token, "Colombia", "colombia", "country")
        prop_id = client.post(
            "/api/v1/properties",
            json={**_BASE_PAYLOAD, "location_id": country},
            headers=_auth(agent_token),
        ).json()["id"]
        got = client.get(f"/api/v1/properties/{prop_id}", headers=_auth(agent_token)).json()
        assert [c["name"] for c in got["location"]["path"]] == ["Colombia"]


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


class TestPropertyNid:
    """HubSpot-style numeric Record ID (NID)."""

    def test_create_assigns_numeric_nid(self, client, agent_user, agent_token):
        resp = client.post("/api/v1/properties", json=_BASE_PAYLOAD, headers=_auth(agent_token))
        nid = resp.json()["nid"]
        assert isinstance(nid, int)
        assert nid >= 1_000_000_001

    def test_nids_are_unique_and_increasing(self, client, agent_user, agent_token):
        a = client.post("/api/v1/properties", json=_BASE_PAYLOAD, headers=_auth(agent_token)).json()["nid"]
        b = client.post("/api/v1/properties", json=_BASE_PAYLOAD, headers=_auth(agent_token)).json()["nid"]
        assert b > a

    def test_get_by_nid_resolves_property(self, client, agent_user, agent_token):
        created = client.post("/api/v1/properties", json=_BASE_PAYLOAD, headers=_auth(agent_token)).json()
        resp = client.get(f"/api/v1/properties/{created['nid']}", headers=_auth(agent_token))
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    def test_search_by_nid(self, client, agent_user, agent_token, admin_user, admin_token):
        created = client.post("/api/v1/properties", json=_BASE_PAYLOAD, headers=_auth(agent_token)).json()
        client.post(f"/api/v1/properties/{created['id']}/submit", headers=_auth(agent_token))
        client.post(f"/api/v1/properties/{created['id']}/approve", headers=_auth(admin_token))
        resp = client.get("/api/v1/properties", params={"nid": created["nid"]})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 1
        assert data[0]["nid"] == created["nid"]


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

    def test_search_q_recognizes_nid_with_leading_slash(self, client, agent_user, agent_token, admin_user, admin_token):
        prop_id = self._publish(client, agent_token, admin_token)
        nid = client.get(f"/api/v1/properties/{prop_id}", headers=_auth(agent_token)).json()["nid"]
        resp = client.get("/api/v1/properties", params={"q": f"/{nid}"})
        assert resp.json()["meta"]["total"] == 1

    def test_search_text_ignores_accents_and_matches_location(self, client, agent_user, agent_token, admin_user, admin_token):
        country = self._mkloc(client, admin_token, "Colombia", "colombia", "country")
        city = self._mkloc(client, admin_token, "Bogotá", "bogota", "city", country)
        locality = self._mkloc(client, admin_token, "Suba", "suba", "locality", city)
        barrio = self._mkloc(client, admin_token, "El Batán", "el-batan", "neighborhood", locality)
        self._publish(client, agent_token, admin_token, {**_BASE_PAYLOAD, "title": "Hogar familiar", "location_id": barrio})
        assert client.get("/api/v1/properties", params={"q": "batan"}).json()["meta"]["total"] == 1
        assert client.get("/api/v1/properties", params={"q": "bogota"}).json()["meta"]["total"] == 1

    def _mkloc(self, client, admin_token, name, slug, level, parent=None):
        resp = client.post(
            "/api/v1/locations",
            json={"name": name, "slug": slug, "level": level, "parent_id": parent},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        return resp.json()["id"]

    def test_search_filter_by_location_subtree(self, client, agent_user, agent_token, admin_user, admin_token):
        # País → Ciudad → Localidad → Barrio (la cascada de 4 niveles).
        country = self._mkloc(client, admin_token, "Colombia", "colombia", "country")
        city = self._mkloc(client, admin_token, "Bogotá", "bogota", "city", country)
        locality = self._mkloc(client, admin_token, "Chapinero", "chapinero", "locality", city)
        barrio = self._mkloc(client, admin_token, "Chicó", "chico", "neighborhood", locality)

        # Las propiedades cuelgan de niveles distintos: una del barrio, otra de la ciudad.
        self._publish(client, agent_token, admin_token, {**_BASE_PAYLOAD, "title": "En el barrio", "location_id": barrio})
        self._publish(client, agent_token, admin_token, {**_BASE_PAYLOAD, "title": "En la ciudad", "location_id": city})

        # Filtrar por la CIUDAD trae todo su subárbol (ciudad + barrio) = 2.
        assert client.get("/api/v1/properties?location=bogota").json()["meta"]["total"] == 2
        # Filtrar por el BARRIO (hoja) trae solo esa propiedad = 1.
        assert client.get("/api/v1/properties?location=chico").json()["meta"]["total"] == 1
        # Slug inexistente → filtro imposible (sin resultados), no ignorado.
        assert client.get("/api/v1/properties?location=zzz-no-existe").json()["meta"]["total"] == 0

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


@pytest.mark.integration
class TestAdminListAll:
    """Admins can list every owner's properties (every status) with ?all=true."""

    def test_admin_all_sees_other_owners_draft(self, client, agent_user, agent_token, admin_user, admin_token):
        created = client.post("/api/v1/properties", json=_BASE_PAYLOAD, headers=_auth(agent_token)).json()
        resp = client.get("/api/v1/properties?all=true", headers=_auth(admin_token))
        assert resp.status_code == 200
        nids = [p["nid"] for p in resp.json()["data"]]
        assert created["nid"] in nids  # an agent's draft is visible to the admin

    def test_non_admin_all_is_ignored(self, client, agent_user, agent_token):
        # Not an admin → ?all=true falls back to the public (published-only) view,
        # so the agent's own draft does NOT leak in.
        created = client.post("/api/v1/properties", json=_BASE_PAYLOAD, headers=_auth(agent_token)).json()
        resp = client.get("/api/v1/properties?all=true", headers=_auth(agent_token))
        nids = [p["nid"] for p in resp.json()["data"]]
        assert created["nid"] not in nids
