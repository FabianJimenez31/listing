from __future__ import annotations

import pytest
from fastapi import HTTPException

from src.api.routers.locations import create_location
from src.schemas.location_schemas import LocationCreateRequest


def _create(db_session, *, name: str, level: str, parent_id: str | None = None):
    return create_location(
        LocationCreateRequest(name=name, level=level, parent_id=parent_id),
        db_session,
    )


def test_duplicate_department_returns_the_existing_selection(db_session):
    country = _create(db_session, name="Colombia", level="country")
    original = _create(db_session, name="Antioquia", level="state", parent_id=country.id)

    selected = _create(db_session, name="antioquía", level="state", parent_id=country.id)

    assert selected.id == original.id


def test_department_must_belong_to_a_country(db_session):
    country = _create(db_session, name="Colombia", level="country")
    city = _create(db_session, name="Bogotá", level="city", parent_id=country.id)

    with pytest.raises(HTTPException) as error:
        _create(db_session, name="Inválido", level="state", parent_id=city.id)

    assert error.value.status_code == 422
