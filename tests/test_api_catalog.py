"""Integration tests for catalog aggregation endpoints (property-types, cities)."""
from __future__ import annotations

import uuid

import pytest

from src.db.models.catalog_models import PropertyTypeORM
from src.db.models.location_models import LocationORM
from src.db.models.property_models import PropertyORM

pytestmark = pytest.mark.integration


def _seed_published_apartment(db, owner_id: str):
    apt = PropertyTypeORM(
        id=str(uuid.uuid4()), code="apartment", name="Apartamento", slug="apartamento", is_active=True
    )
    city = LocationORM(
        id=str(uuid.uuid4()), name="Bogotá", slug="bogota", level="city",
        is_active=True, image_url="https://img/bogota.jpg",
    )
    db.add_all([apt, city])
    db.flush()
    locality = LocationORM(
        id=str(uuid.uuid4()), name="Chapinero", slug="chapinero", level="locality",
        parent_id=city.id, is_active=True,
    )
    db.add(locality)
    db.flush()
    db.add(PropertyORM(
        id=str(uuid.uuid4()), owner_id=owner_id, title="Apto", slug="apto-1",
        operation_type="sale", property_kind="apartment", price_amount=1000, currency="COP",
        status="published", property_type_id=apt.id, location_id=locality.id,
    ))
    db.commit()


class TestPropertyTypes:
    def test_counts_published(self, client, db_session, agent_user):
        _seed_published_apartment(db_session, agent_user.id)
        resp = client.get("/api/v1/property-types")
        assert resp.status_code == 200
        by_code = {t["code"]: t for t in resp.json()}
        assert by_code["apartment"]["property_count"] == 1

    def test_type_without_properties_counts_zero(self, client, db_session, agent_user):
        db_session.add(PropertyTypeORM(
            id=str(uuid.uuid4()), code="lot", name="Lote", slug="lote", is_active=True
        ))
        db_session.commit()
        resp = client.get("/api/v1/property-types")
        by_code = {t["code"]: t for t in resp.json()}
        assert by_code["lot"]["property_count"] == 0


class TestFeaturedCities:
    def test_rollup_to_city(self, client, db_session, agent_user):
        # property hangs off a locality; count rolls up to its city ancestor
        _seed_published_apartment(db_session, agent_user.id)
        resp = client.get("/api/v1/cities/featured")
        assert resp.status_code == 200
        cities = {c["slug"]: c for c in resp.json()}
        assert "bogota" in cities
        assert cities["bogota"]["property_count"] == 1
        assert cities["bogota"]["image_url"] == "https://img/bogota.jpg"

    def test_empty_when_no_cities(self, client):
        resp = client.get("/api/v1/cities/featured")
        assert resp.status_code == 200
        assert resp.json() == []
