"""Integration tests for POST /api/v1/locations (agregar países / ciudades)."""
from __future__ import annotations

import pytest

from src.db.models.location_models import LocationORM

pytestmark = pytest.mark.integration


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create(client, token: str, **body):
    return client.post("/api/v1/locations", json=body, headers=_auth(token))


class TestCreateCountry:
    def test_create_country_without_slug(self, client, admin_user, admin_token):
        resp = _create(client, admin_token, name="Panamá", level="country")
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["name"] == "Panamá"
        assert body["slug"] == "panama"  # derivado del nombre, sin acentos
        assert body["parent_id"] is None
        assert body["is_active"] is True

    def test_country_shows_up_in_the_list(self, client, admin_user, admin_token):
        _create(client, admin_token, name="Panamá", level="country")
        names = [loc["name"] for loc in client.get("/api/v1/locations?level=country").json()]
        assert "Panamá" in names

    def test_country_rejects_parent(self, client, admin_user, admin_token):
        parent = _create(client, admin_token, name="Colombia", level="country").json()
        resp = _create(client, admin_token, name="Panamá", level="country", parent_id=parent["id"])
        assert resp.status_code == 422

    def test_duplicate_country_is_reported(self, client, admin_user, admin_token):
        _create(client, admin_token, name="Panamá", level="country")
        resp = _create(client, admin_token, name="panama", level="country")
        assert resp.status_code == 409
        assert "Ya existe" in resp.json()["error"]["message"]

    def test_reactivates_a_disabled_country(self, client, db_session, admin_user, admin_token):
        created = _create(client, admin_token, name="Panamá", level="country").json()
        db_session.get(LocationORM, created["id"]).is_active = False
        db_session.commit()

        resp = _create(client, admin_token, name="Panamá", level="country")
        assert resp.status_code == 201
        assert resp.json()["id"] == created["id"]
        assert resp.json()["is_active"] is True


class TestCreateCityBranch:
    def _panama(self, client, token):
        return _create(client, token, name="Panamá", level="country").json()

    def test_full_country_state_city_chain(self, client, admin_user, admin_token):
        country = self._panama(client, admin_token)
        state = _create(client, admin_token, name="Provincia de Panamá", level="state", parent_id=country["id"]).json()
        city = _create(client, admin_token, name="Ciudad de Panamá", level="city", parent_id=state["id"])
        assert city.status_code == 201, city.text
        assert city.json()["parent_id"] == state["id"]
        assert city.json()["slug"] == "ciudad-de-panama"

    def test_city_can_hang_directly_off_the_country(self, client, admin_user, admin_token):
        country = self._panama(client, admin_token)
        resp = _create(client, admin_token, name="Colón", level="city", parent_id=country["id"])
        assert resp.status_code == 201, resp.text
        assert resp.json()["parent_id"] == country["id"]

    def test_same_city_name_under_two_parents_gets_distinct_slugs(self, client, admin_user, admin_token):
        first = _create(client, admin_token, name="Colombia", level="country").json()
        second = _create(client, admin_token, name="Panamá", level="country").json()
        a = _create(client, admin_token, name="Centro", level="city", parent_id=first["id"]).json()
        b = _create(client, admin_token, name="Centro", level="city", parent_id=second["id"]).json()
        assert a["slug"] != b["slug"]
        assert a["slug"] == "centro"

    def test_city_name_matching_its_country_does_not_collide(self, client, admin_user, admin_token):
        country = self._panama(client, admin_token)  # slug "panama"
        city = _create(client, admin_token, name="Panamá", level="city", parent_id=country["id"])
        assert city.status_code == 201, city.text
        assert city.json()["slug"] != country["slug"]

    def test_city_requires_a_parent(self, client, admin_user, admin_token):
        resp = _create(client, admin_token, name="Ciudad de Panamá", level="city")
        assert resp.status_code == 422

    def test_unknown_parent_is_404(self, client, admin_user, admin_token):
        resp = _create(client, admin_token, name="X", level="city", parent_id="does-not-exist")
        assert resp.status_code == 404

    def test_invalid_level_is_rejected(self, client, admin_user, admin_token):
        resp = _create(client, admin_token, name="X", level="planet")
        assert resp.status_code == 422

    def test_blank_name_is_rejected(self, client, admin_user, admin_token):
        resp = _create(client, admin_token, name="   ", level="country")
        assert resp.status_code == 422

    def test_explicit_slug_is_respected(self, client, admin_user, admin_token):
        resp = _create(client, admin_token, name="Panamá", level="country", slug="rep-panama")
        assert resp.json()["slug"] == "rep-panama"


class TestCreateLocationAuthorization:
    def test_requires_permission(self, client, agent_user, agent_token):
        resp = _create(client, agent_token, name="Panamá", level="country")
        assert resp.status_code == 403

    def test_requires_auth(self, client):
        resp = client.post("/api/v1/locations", json={"name": "Panamá", "level": "country"})
        assert resp.status_code == 401


class TestCountryFilterUsesNewCountries:
    def test_new_country_is_filterable_by_slug(self, client, admin_user, admin_token):
        country = _create(client, admin_token, name="Panamá", level="country").json()
        _create(client, admin_token, name="Ciudad de Panamá", level="city", parent_id=country["id"])
        # El filtro `country` acepta el slug del país: responde sin error y vacío
        # (todavía no hay propiedades publicadas allí).
        resp = client.get("/api/v1/properties?country=panama")
        assert resp.status_code == 200
        assert resp.json()["meta"]["total"] == 0
