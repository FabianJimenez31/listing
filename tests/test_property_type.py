"""Unit tests for the property type catalog module."""
import pytest

from src.property_type import PropertyKind, PropertyType


@pytest.fixture
def property_type() -> PropertyType:
    return PropertyType(
        id="11111111-1111-4111-8111-111111111111",
        code=PropertyKind.APARTMENT,
        name="Apartment",
        slug="apartment",
        icon="apartment-icon",
    )


@pytest.mark.unit
def test_valid_property_type(property_type: PropertyType) -> None:
    assert property_type.code is PropertyKind.APARTMENT
    assert property_type.name == "Apartment"
    assert property_type.slug == "apartment"
    assert property_type.icon == "apartment-icon"


@pytest.mark.unit
def test_defaults() -> None:
    pt = PropertyType(
        id="id-1",
        code=PropertyKind.HOUSE,
        name="House",
        slug="house",
    )
    assert pt.icon is None
    assert pt.is_active is True


@pytest.mark.unit
def test_code_string_is_coerced_to_enum() -> None:
    pt = PropertyType(id="id-1", code="office", name="Office", slug="office")
    assert pt.code is PropertyKind.OFFICE
    assert isinstance(pt.code, PropertyKind)


@pytest.mark.unit
@pytest.mark.parametrize(
    "code",
    ["house", "apartment", "lot", "office", "commercial", "farm", "other"],
)
def test_all_valid_string_codes(code: str) -> None:
    pt = PropertyType(id="id", code=code, name="X", slug="x")
    assert pt.code == PropertyKind(code)


@pytest.mark.unit
def test_invalid_string_code_raises() -> None:
    with pytest.raises(ValueError, match="code is invalid"):
        PropertyType(id="id", code="mansion", name="Mansion", slug="mansion")


@pytest.mark.unit
def test_invalid_typed_code_raises() -> None:
    with pytest.raises(ValueError, match="code is invalid"):
        PropertyType(id="id", code=123, name="Bad", slug="bad")


@pytest.mark.unit
def test_requires_name() -> None:
    with pytest.raises(ValueError, match="name is required"):
        PropertyType(id="id", code=PropertyKind.HOUSE, name="", slug="house")


@pytest.mark.unit
def test_requires_slug() -> None:
    with pytest.raises(ValueError, match="slug is required"):
        PropertyType(id="id", code=PropertyKind.HOUSE, name="House", slug="")


@pytest.mark.unit
@pytest.mark.parametrize(
    "slug",
    [
        "Apartment",      # uppercase
        "apart ment",     # space
        "-apartment",     # leading hyphen
        "apartment-",     # trailing hyphen
        "apart--ment",    # double hyphen
        "apart_ment",     # underscore
        "apartmént",      # non-ascii
    ],
)
def test_invalid_slug_raises(slug: str) -> None:
    with pytest.raises(ValueError, match="slug is invalid"):
        PropertyType(id="id", code=PropertyKind.HOUSE, name="House", slug=slug)


@pytest.mark.unit
@pytest.mark.parametrize("slug", ["house", "single-family-home", "lot123", "a", "1"])
def test_valid_slug_patterns(slug: str) -> None:
    pt = PropertyType(id="id", code=PropertyKind.LOT, name="Lot", slug=slug)
    assert pt.slug == slug


@pytest.mark.unit
def test_inactive_flag() -> None:
    pt = PropertyType(
        id="id",
        code=PropertyKind.FARM,
        name="Farm",
        slug="farm",
        is_active=False,
    )
    assert pt.is_active is False


@pytest.mark.integration
def test_catalog_of_all_kinds() -> None:
    catalog = [
        PropertyType(id=f"id-{kind.value}", code=kind, name=kind.value.title(), slug=kind.value)
        for kind in PropertyKind
    ]
    assert len(catalog) == len(PropertyKind)
    assert {pt.code for pt in catalog} == set(PropertyKind)
    assert all(isinstance(pt.code, PropertyKind) for pt in catalog)
