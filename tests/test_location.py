"""Unit tests for the location domain module."""
import math

import pytest

from src.location import Coordinates, Location


@pytest.fixture
def bogota() -> Coordinates:
    return Coordinates(latitude=4.7110, longitude=-74.0721)


@pytest.fixture
def medellin() -> Coordinates:
    return Coordinates(latitude=6.2442, longitude=-75.5812)


@pytest.fixture
def location() -> Location:
    return Location(
        id="loc-1",
        country="Colombia",
        city="Bogota",
        slug="bogota-chapinero",
    )


@pytest.mark.unit
def test_coordinates_store_values(bogota: Coordinates) -> None:
    assert bogota.latitude == 4.7110
    assert bogota.longitude == -74.0721


@pytest.mark.unit
@pytest.mark.parametrize("lat", [-90, -45.5, 0, 45.5, 90])
def test_latitude_within_range(lat: float) -> None:
    assert Coordinates(latitude=lat, longitude=0).latitude == lat


@pytest.mark.unit
@pytest.mark.parametrize("lon", [-180, -100.25, 0, 100.25, 180])
def test_longitude_within_range(lon: float) -> None:
    assert Coordinates(latitude=0, longitude=lon).longitude == lon


@pytest.mark.unit
@pytest.mark.parametrize("lat", [-90.1, 90.1, 200, -200])
def test_latitude_out_of_range(lat: float) -> None:
    with pytest.raises(ValueError):
        Coordinates(latitude=lat, longitude=0)


@pytest.mark.unit
@pytest.mark.parametrize("lon", [-180.1, 180.1, 360, -360])
def test_longitude_out_of_range(lon: float) -> None:
    with pytest.raises(ValueError):
        Coordinates(latitude=0, longitude=lon)


@pytest.mark.unit
def test_distance_to_self_is_zero(bogota: Coordinates) -> None:
    assert bogota.distance_km_to(bogota) == pytest.approx(0.0, abs=1e-9)


@pytest.mark.unit
def test_distance_is_symmetric(
    bogota: Coordinates, medellin: Coordinates
) -> None:
    assert bogota.distance_km_to(medellin) == pytest.approx(
        medellin.distance_km_to(bogota)
    )


@pytest.mark.unit
def test_haversine_known_distance(
    bogota: Coordinates, medellin: Coordinates
) -> None:
    # Bogota -> Medellin is roughly 240 km in a straight line.
    assert bogota.distance_km_to(medellin) == pytest.approx(240.0, abs=15.0)


@pytest.mark.unit
def test_haversine_quarter_meridian() -> None:
    # Equator pole-ward to the north pole is a quarter of the Earth's
    # circumference: ~10007 km.
    equator = Coordinates(latitude=0, longitude=0)
    north_pole = Coordinates(latitude=90, longitude=0)
    quarter = 2 * math.pi * 6371.0088 / 4
    assert equator.distance_km_to(north_pole) == pytest.approx(quarter, abs=1.0)


@pytest.mark.unit
def test_location_requires_country() -> None:
    with pytest.raises(ValueError):
        Location(id="x", country="", city="Bogota", slug="bogota")


@pytest.mark.unit
def test_location_requires_city() -> None:
    with pytest.raises(ValueError):
        Location(id="x", country="Colombia", city="", slug="bogota")


@pytest.mark.unit
def test_location_requires_slug() -> None:
    with pytest.raises(ValueError):
        Location(id="x", country="Colombia", city="Bogota", slug="")


@pytest.mark.unit
@pytest.mark.parametrize(
    "slug",
    ["Bogota", "bogota_chapinero", "-bogota", "bogota-", "bogota--norte", "café"],
)
def test_location_rejects_invalid_slug(slug: str) -> None:
    with pytest.raises(ValueError):
        Location(id="x", country="Colombia", city="Bogota", slug=slug)


@pytest.mark.unit
@pytest.mark.parametrize(
    "slug", ["bogota", "bogota-chapinero", "zona-norte-1", "a1b2c3"]
)
def test_location_accepts_valid_slug(slug: str) -> None:
    loc = Location(id="x", country="Colombia", city="Bogota", slug=slug)
    assert loc.slug == slug


@pytest.mark.unit
def test_location_defaults(location: Location) -> None:
    assert location.is_active is True
    assert location.state_province is None
    assert location.locality is None
    assert location.neighborhood is None
    assert location.parent_id is None
    assert location.center is None


@pytest.mark.unit
def test_is_root_true_without_parent(location: Location) -> None:
    assert location.is_root is True


@pytest.mark.unit
def test_is_root_false_with_parent() -> None:
    child = Location(
        id="c",
        country="Colombia",
        city="Bogota",
        slug="chapinero",
        parent_id="root",
    )
    assert child.is_root is False


@pytest.mark.unit
def test_activate_and_deactivate(location: Location) -> None:
    location.deactivate()
    assert location.is_active is False
    location.activate()
    assert location.is_active is True


@pytest.mark.integration
def test_location_distance_between_centers(
    bogota: Coordinates, medellin: Coordinates
) -> None:
    a = Location(
        id="a", country="Colombia", city="Bogota", slug="bogota", center=bogota
    )
    b = Location(
        id="b",
        country="Colombia",
        city="Medellin",
        slug="medellin",
        center=medellin,
    )
    assert a.distance_km_to(b) == pytest.approx(240.0, abs=15.0)


@pytest.mark.unit
def test_location_distance_requires_both_centers(
    location: Location, bogota: Coordinates
) -> None:
    with_center = Location(
        id="b", country="Colombia", city="Cali", slug="cali", center=bogota
    )
    with pytest.raises(ValueError):
        location.distance_km_to(with_center)
    with pytest.raises(ValueError):
        with_center.distance_km_to(location)


@pytest.mark.critical
def test_full_hierarchy_construction(bogota: Coordinates) -> None:
    country = Location(
        id="co", country="Colombia", city="Bogota", slug="colombia"
    )
    city = Location(
        id="bog",
        country="Colombia",
        city="Bogota",
        slug="bogota",
        state_province="Cundinamarca",
        parent_id=country.id,
        center=bogota,
        is_active=True,
    )
    assert country.is_root is True
    assert city.is_root is False
    assert city.parent_id == country.id
    assert city.center is bogota
    assert city.state_province == "Cundinamarca"
