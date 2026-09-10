from __future__ import annotations

import uuid

from src.db.models.location_models import LocationORM
from src.db.models.project_models import ProjectORM
from src.db.models.property_models import PropertyORM
from src.repositories.project_repo import ProjectRepository
from src.repositories.property_repo import PropertyRepository


def _id() -> str:
    return str(uuid.uuid4())


def test_property_text_search_matches_accentless_location(db_session):
    country = LocationORM(id=_id(), name="Colombia", slug="colombia", level="country")
    city = LocationORM(id=_id(), name="Bogotá", slug="bogota", level="city", parent_id=country.id)
    locality = LocationORM(id=_id(), name="Suba", slug="suba", level="locality", parent_id=city.id)
    barrio = LocationORM(id=_id(), name="El Batán", slug="suba-el-batan", level="neighborhood", parent_id=locality.id)
    prop = PropertyORM(
        id=_id(), owner_id=_id(), title="Hogar familiar", slug="hogar-familiar",
        operation_type="sale", property_kind="apartment", price_amount=35_000_000_000,
        currency="COP", status="published", location_id=barrio.id,
    )
    db_session.add_all([country, city, locality, barrio, prop])
    db_session.commit()

    items, total = PropertyRepository(db_session).search(text="batan, bogota")

    assert total == 1
    assert items[0].id == prop.id


def test_property_price_filter_is_currency_scoped(db_session):
    common = {
        "owner_id": _id(), "operation_type": "sale", "property_kind": "apartment",
        "price_amount": 50_000_000, "status": "published",
    }
    cop = PropertyORM(id=_id(), title="COP", slug="cop", currency="COP", **common)
    usd = PropertyORM(id=_id(), title="USD", slug="usd", currency="USD", **common)
    db_session.add_all([cop, usd])
    db_session.commit()

    items, total = PropertyRepository(db_session).search(max_price=50_000_000, currency="COP")

    assert total == 1
    assert items[0].currency == "COP"


def test_project_search_matches_location_subtree(db_session):
    country = LocationORM(id=_id(), name="Colombia", slug="colombia", level="country")
    city = LocationORM(id=_id(), name="Cali", slug="cali", level="city", parent_id=country.id)
    project = ProjectORM(id=_id(), title="Vivienda nueva", slug="vivienda-nueva", status="published", location_id=city.id)
    db_session.add_all([country, city, project])
    db_session.commit()

    ids = [city.id]
    items, total = ProjectRepository(db_session).search(location_ids=ids)

    assert total == 1
    assert items[0].id == project.id
