"""Unit tests for the amenity module."""
import pytest

from src.amenity import Amenity, PropertyAmenity


@pytest.fixture
def amenity() -> Amenity:
    return Amenity(id="a1b2c3", code="swimming_pool", name="Swimming Pool")


@pytest.fixture
def property_amenity() -> PropertyAmenity:
    return PropertyAmenity(property_id="p1", amenity_id="a1b2c3")


@pytest.mark.unit
def test_amenity_defaults(amenity: Amenity) -> None:
    assert amenity.is_active is True
    assert amenity.category is None
    assert amenity.icon is None


@pytest.mark.unit
def test_amenity_normalizes_code_to_lowercase() -> None:
    amenity = Amenity(id="x", code="GYM", name="Gym")
    assert amenity.code == "gym"


@pytest.mark.unit
def test_amenity_normalizes_spaces_to_underscores() -> None:
    amenity = Amenity(id="x", code="24h Security", name="Security")
    assert amenity.code == "24h_security"


@pytest.mark.unit
def test_amenity_normalizes_mixed_case_and_spaces() -> None:
    amenity = Amenity(id="x", code="Pet Friendly Zone", name="Pets")
    assert amenity.code == "pet_friendly_zone"


@pytest.mark.unit
def test_amenity_strips_surrounding_whitespace() -> None:
    amenity = Amenity(id="x", code="  Pool  ", name="Pool")
    assert amenity.code == "pool"


@pytest.mark.unit
def test_amenity_requires_code() -> None:
    with pytest.raises(ValueError):
        Amenity(id="x", code="", name="Gym")


@pytest.mark.unit
def test_amenity_blank_code_after_normalization_raises() -> None:
    with pytest.raises(ValueError):
        Amenity(id="x", code="   ", name="Gym")


@pytest.mark.unit
def test_amenity_requires_name() -> None:
    with pytest.raises(ValueError):
        Amenity(id="x", code="gym", name="")


@pytest.mark.unit
def test_amenity_keeps_optional_fields() -> None:
    amenity = Amenity(
        id="x",
        code="gym",
        name="Gym",
        category="comfort",
        icon="dumbbell",
        is_active=False,
    )
    assert amenity.category == "comfort"
    assert amenity.icon == "dumbbell"
    assert amenity.is_active is False


@pytest.mark.unit
def test_property_amenity_defaults(property_amenity: PropertyAmenity) -> None:
    assert property_amenity.value is None


@pytest.mark.unit
def test_property_amenity_accepts_value() -> None:
    pa = PropertyAmenity(property_id="p1", amenity_id="a1", value="2")
    assert pa.value == "2"


@pytest.mark.unit
def test_property_amenity_requires_property_id() -> None:
    with pytest.raises(ValueError):
        PropertyAmenity(property_id="", amenity_id="a1")


@pytest.mark.unit
def test_property_amenity_requires_amenity_id() -> None:
    with pytest.raises(ValueError):
        PropertyAmenity(property_id="p1", amenity_id="")


@pytest.mark.integration
def test_property_amenity_links_amenity(
    amenity: Amenity, property_amenity: PropertyAmenity
) -> None:
    assert property_amenity.amenity_id == amenity.id
    assert property_amenity.property_id == "p1"
