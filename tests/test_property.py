"""Unit tests for the property domain module."""
from datetime import date, datetime

import pytest

from src.property import (
    Currency,
    Money,
    OperationType,
    Property,
    PropertyCondition,
    PropertyKind,
    PublicationStatus,
)


@pytest.fixture
def money() -> Money:
    return Money(amount_minor=250_000_00, currency="USD")


@pytest.fixture
def prop(money: Money) -> Property:
    return Property(
        id="p1",
        owner_id="u1",
        title="Bright apartment in Chapinero",
        slug="venta-apartamento-chapinero-a1b2c3",
        description="A bright two-bedroom apartment.",
        operation_type=OperationType.SALE,
        property_kind=PropertyKind.APARTMENT,
        condition=PropertyCondition.USED,
        price=money,
        country="CO",
        city="Bogota",
        locality_id="loc-1",
        area_total=72.5,
        bedrooms=2,
        bathrooms=2,
        parking_spots=1,
        image_ids=["img-1"],
    )


@pytest.fixture
def rental(money: Money) -> Property:
    return Property(
        id="p2",
        owner_id="u1",
        title="Studio for rent",
        slug="renta-apartamento-centro-x9y8z7",
        description="Cozy studio downtown.",
        operation_type=OperationType.RENT,
        property_kind=PropertyKind.APARTMENT,
        condition=PropertyCondition.NEW,
        price=money,
        country="CO",
        city="Bogota",
        locality_id="loc-2",
        area_total=35.0,
        bedrooms=1,
        bathrooms=1,
        parking_spots=0,
        image_ids=["img-9"],
    )


# --------------------------------------------------------------------------- #
# Money
# --------------------------------------------------------------------------- #
@pytest.mark.unit
def test_money_as_major(money: Money) -> None:
    assert money.as_major == 250000.0


@pytest.mark.unit
def test_money_zero_allowed() -> None:
    assert Money(amount_minor=0, currency="EUR").as_major == 0.0


@pytest.mark.unit
def test_money_rejects_negative() -> None:
    with pytest.raises(ValueError):
        Money(amount_minor=-1, currency="USD")


@pytest.mark.unit
def test_money_rejects_wrong_length() -> None:
    with pytest.raises(ValueError):
        Money(amount_minor=100, currency="US")


@pytest.mark.unit
def test_money_rejects_lowercase() -> None:
    with pytest.raises(ValueError):
        Money(amount_minor=100, currency="usd")


@pytest.mark.unit
def test_money_rejects_unsupported_currency() -> None:
    with pytest.raises(ValueError):
        Money(amount_minor=100, currency="JPY")


@pytest.mark.unit
def test_currency_enum_values() -> None:
    assert Currency.COP.value == "COP"
    assert Currency.MXN.value == "MXN"


# --------------------------------------------------------------------------- #
# Property validation
# --------------------------------------------------------------------------- #
@pytest.mark.unit
def test_property_defaults_to_draft(prop: Property) -> None:
    assert prop.status == PublicationStatus.DRAFT
    assert prop.views_count == 0
    assert prop.published_at is None
    assert prop.deleted_at is None


@pytest.mark.unit
def test_property_requires_title(money: Money) -> None:
    with pytest.raises(ValueError):
        _make(money, title="")


@pytest.mark.unit
def test_property_requires_slug(money: Money) -> None:
    with pytest.raises(ValueError):
        _make(money, slug="")


@pytest.mark.unit
def test_property_requires_description(money: Money) -> None:
    with pytest.raises(ValueError):
        _make(money, description="")


@pytest.mark.unit
def test_property_rejects_invalid_slug(money: Money) -> None:
    with pytest.raises(ValueError):
        _make(money, slug="Not_A_Slug")


@pytest.mark.unit
def test_property_rejects_nonpositive_area(money: Money) -> None:
    with pytest.raises(ValueError):
        _make(money, area_total=0)


@pytest.mark.unit
def test_property_rejects_negative_bedrooms(money: Money) -> None:
    with pytest.raises(ValueError):
        _make(money, bedrooms=-1)


@pytest.mark.unit
def test_property_rejects_negative_bathrooms(money: Money) -> None:
    with pytest.raises(ValueError):
        _make(money, bathrooms=-1)


@pytest.mark.unit
def test_property_rejects_negative_parking(money: Money) -> None:
    with pytest.raises(ValueError):
        _make(money, parking_spots=-1)


@pytest.mark.unit
def test_property_rejects_bad_latitude(money: Money) -> None:
    with pytest.raises(ValueError):
        _make(money, latitude=91.0)


@pytest.mark.unit
def test_property_rejects_bad_longitude(money: Money) -> None:
    with pytest.raises(ValueError):
        _make(money, longitude=-181.0)


@pytest.mark.unit
def test_property_accepts_valid_coordinates(money: Money) -> None:
    p = _make(money, latitude=4.65, longitude=-74.05)
    assert p.latitude == 4.65
    assert p.longitude == -74.05


@pytest.mark.unit
def test_property_accepts_optional_fields(money: Money) -> None:
    p = _make(
        money,
        state_province="Cundinamarca",
        neighborhood="Chapinero Alto",
        address="Calle 1",
        address_is_public=True,
        area_built=60.0,
        year_built=2015,
        hoa_fees=Money(amount_minor=500_00, currency="USD"),
        available_from=date(2026, 1, 1),
        primary_cta="contact",
    )
    assert p.hoa_fees is not None
    assert p.available_from == date(2026, 1, 1)


# --------------------------------------------------------------------------- #
# can_be_published
# --------------------------------------------------------------------------- #
@pytest.mark.unit
def test_can_be_published_true(prop: Property) -> None:
    assert prop.can_be_published() is True


@pytest.mark.unit
def test_can_be_published_false_without_images(money: Money) -> None:
    p = _make(money, image_ids=[])
    assert p.can_be_published() is False


# --------------------------------------------------------------------------- #
# Lifecycle: submit_for_review
# --------------------------------------------------------------------------- #
@pytest.mark.critical
def test_submit_for_review_from_draft(prop: Property) -> None:
    prop.submit_for_review()
    assert prop.status == PublicationStatus.PENDING


@pytest.mark.critical
def test_submit_for_review_from_rejected(prop: Property) -> None:
    prop.submit_for_review()
    prop.reject("missing photos")
    prop.submit_for_review()
    assert prop.status == PublicationStatus.PENDING


@pytest.mark.unit
def test_submit_for_review_requires_image(money: Money) -> None:
    p = _make(money, image_ids=[])
    with pytest.raises(ValueError):
        p.submit_for_review()


@pytest.mark.unit
def test_submit_for_review_invalid_state(prop: Property) -> None:
    prop.submit_for_review()
    prop.approve()
    with pytest.raises(ValueError):
        prop.submit_for_review()


# --------------------------------------------------------------------------- #
# Lifecycle: approve / reject
# --------------------------------------------------------------------------- #
@pytest.mark.critical
def test_approve_sets_published_at(prop: Property) -> None:
    prop.submit_for_review()
    when = datetime(2026, 6, 6, 12, 0, 0)
    prop.approve(when=when)
    assert prop.status == PublicationStatus.PUBLISHED
    assert prop.published_at == when


@pytest.mark.unit
def test_approve_defaults_timestamp(prop: Property) -> None:
    prop.submit_for_review()
    prop.approve()
    assert prop.published_at is not None


@pytest.mark.unit
def test_approve_invalid_state(prop: Property) -> None:
    with pytest.raises(ValueError):
        prop.approve()


@pytest.mark.critical
def test_reject_from_pending(prop: Property) -> None:
    prop.submit_for_review()
    prop.reject("blurry photos")
    assert prop.status == PublicationStatus.REJECTED


@pytest.mark.unit
def test_reject_requires_reason(prop: Property) -> None:
    prop.submit_for_review()
    with pytest.raises(ValueError):
        prop.reject("")


@pytest.mark.unit
def test_reject_invalid_state(prop: Property) -> None:
    with pytest.raises(ValueError):
        prop.reject("nope")


# --------------------------------------------------------------------------- #
# Lifecycle: pause / reactivate
# --------------------------------------------------------------------------- #
@pytest.mark.critical
def test_pause_and_reactivate(prop: Property) -> None:
    prop.submit_for_review()
    prop.approve()
    prop.pause()
    assert prop.status == PublicationStatus.PAUSED
    prop.reactivate()
    assert prop.status == PublicationStatus.PUBLISHED


@pytest.mark.unit
def test_pause_invalid_state(prop: Property) -> None:
    with pytest.raises(ValueError):
        prop.pause()


@pytest.mark.unit
def test_reactivate_invalid_state(prop: Property) -> None:
    with pytest.raises(ValueError):
        prop.reactivate()


# --------------------------------------------------------------------------- #
# Lifecycle: mark_sold / mark_rented
# --------------------------------------------------------------------------- #
@pytest.mark.critical
def test_mark_sold_from_published(prop: Property) -> None:
    prop.submit_for_review()
    prop.approve()
    prop.mark_sold()
    assert prop.status == PublicationStatus.SOLD


@pytest.mark.unit
def test_mark_sold_from_paused(prop: Property) -> None:
    prop.submit_for_review()
    prop.approve()
    prop.pause()
    prop.mark_sold()
    assert prop.status == PublicationStatus.SOLD


@pytest.mark.unit
def test_mark_sold_wrong_operation(rental: Property) -> None:
    rental.submit_for_review()
    rental.approve()
    with pytest.raises(ValueError):
        rental.mark_sold()


@pytest.mark.unit
def test_mark_sold_invalid_state(prop: Property) -> None:
    with pytest.raises(ValueError):
        prop.mark_sold()


@pytest.mark.critical
def test_mark_rented_from_published(rental: Property) -> None:
    rental.submit_for_review()
    rental.approve()
    rental.mark_rented()
    assert rental.status == PublicationStatus.RENTED


@pytest.mark.unit
def test_mark_rented_temporary_operation(money: Money) -> None:
    p = _make(money, operation_type=OperationType.TEMPORARY)
    p.submit_for_review()
    p.approve()
    p.pause()
    p.mark_rented()
    assert p.status == PublicationStatus.RENTED


@pytest.mark.unit
def test_mark_rented_wrong_operation(prop: Property) -> None:
    prop.submit_for_review()
    prop.approve()
    with pytest.raises(ValueError):
        prop.mark_rented()


@pytest.mark.unit
def test_mark_rented_invalid_state(rental: Property) -> None:
    with pytest.raises(ValueError):
        rental.mark_rented()


# --------------------------------------------------------------------------- #
# Lifecycle: soft_delete
# --------------------------------------------------------------------------- #
@pytest.mark.critical
def test_soft_delete_sets_timestamp(prop: Property) -> None:
    when = datetime(2026, 6, 6, 9, 0, 0)
    prop.soft_delete(when=when)
    assert prop.status == PublicationStatus.DELETED
    assert prop.deleted_at == when


@pytest.mark.unit
def test_soft_delete_default_timestamp(prop: Property) -> None:
    prop.soft_delete()
    assert prop.deleted_at is not None


@pytest.mark.unit
def test_soft_delete_already_deleted(prop: Property) -> None:
    prop.soft_delete()
    with pytest.raises(ValueError):
        prop.soft_delete()


# --------------------------------------------------------------------------- #
# duplicate
# --------------------------------------------------------------------------- #
@pytest.mark.integration
def test_duplicate_resets_state(prop: Property) -> None:
    prop.submit_for_review()
    prop.approve()
    prop.views_count = 42
    prop.clicks_count = 7
    prop.leads_count = 3
    prop.is_featured = True
    clone = prop.duplicate(new_id="p1-copy", new_slug="venta-apartamento-copia-z9z9z9")
    assert clone.id == "p1-copy"
    assert clone.slug == "venta-apartamento-copia-z9z9z9"
    assert clone.status == PublicationStatus.DRAFT
    assert clone.is_featured is False
    assert clone.views_count == 0
    assert clone.clicks_count == 0
    assert clone.leads_count == 0
    assert clone.published_at is None
    assert clone.deleted_at is None
    # The original is untouched.
    assert prop.status == PublicationStatus.PUBLISHED
    assert prop.views_count == 42


@pytest.mark.integration
def test_duplicate_copies_lists_independently(prop: Property) -> None:
    clone = prop.duplicate(new_id="p1-copy", new_slug="copia-aaa-bbb")
    clone.image_ids.append("img-new")
    clone.amenities.append("pool")
    assert prop.image_ids == ["img-1"]
    assert prop.amenities == []


@pytest.mark.unit
def test_duplicate_requires_new_id(prop: Property) -> None:
    with pytest.raises(ValueError):
        prop.duplicate(new_id="", new_slug="valid-slug")


@pytest.mark.unit
def test_duplicate_requires_new_slug(prop: Property) -> None:
    with pytest.raises(ValueError):
        prop.duplicate(new_id="x", new_slug="")


# --------------------------------------------------------------------------- #
# is_publicly_visible
# --------------------------------------------------------------------------- #
@pytest.mark.unit
def test_not_visible_when_draft(prop: Property) -> None:
    assert prop.is_publicly_visible() is False


@pytest.mark.unit
def test_visible_when_published(prop: Property) -> None:
    prop.submit_for_review()
    prop.approve()
    assert prop.is_publicly_visible() is True


@pytest.mark.unit
def test_not_visible_when_deleted(prop: Property) -> None:
    prop.submit_for_review()
    prop.approve()
    prop.soft_delete()
    assert prop.is_publicly_visible() is False


def _make(money: Money, **overrides: object) -> Property:
    """Build a Property with sensible defaults, overriding selected fields."""
    kwargs: dict[str, object] = {
        "id": "p1",
        "owner_id": "u1",
        "title": "Bright apartment",
        "slug": "venta-apartamento-chapinero-a1b2c3",
        "description": "A bright apartment.",
        "operation_type": OperationType.SALE,
        "property_kind": PropertyKind.APARTMENT,
        "condition": PropertyCondition.USED,
        "price": money,
        "country": "CO",
        "city": "Bogota",
        "locality_id": "loc-1",
        "area_total": 72.5,
        "bedrooms": 2,
        "bathrooms": 2,
        "parking_spots": 1,
        "image_ids": ["img-1"],
    }
    kwargs.update(overrides)
    return Property(**kwargs)  # type: ignore[arg-type]
