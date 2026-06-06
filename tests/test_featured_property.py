"""Unit tests for the featured property module."""
from datetime import datetime

import pytest

from src.featured_property import (
    FeaturedProperty,
    FeaturedScope,
    select_featured,
)


@pytest.fixture
def featured() -> FeaturedProperty:
    return FeaturedProperty(
        id="feat-1",
        property_id="prop-1",
        scope=FeaturedScope.HOME,
        priority=5,
        starts_at=datetime(2026, 1, 1),
        ends_at=datetime(2026, 12, 31),
        impressions_count=200,
        clicks_count=10,
    )


@pytest.mark.unit
def test_scope_enum_values() -> None:
    assert FeaturedScope.HOME.value == "home"
    assert FeaturedScope.SEARCH_RESULTS.value == "search_results"
    assert FeaturedScope.LOCALITY.value == "locality"


@pytest.mark.unit
def test_defaults() -> None:
    feat = FeaturedProperty(id="f", property_id="p", scope=FeaturedScope.HOME)
    assert feat.priority == 0
    assert feat.locality_id is None
    assert feat.starts_at is None
    assert feat.ends_at is None
    assert feat.is_active is True
    assert feat.impressions_count == 0
    assert feat.clicks_count == 0


@pytest.mark.unit
def test_requires_property_id() -> None:
    with pytest.raises(ValueError):
        FeaturedProperty(id="f", property_id="", scope=FeaturedScope.HOME)


@pytest.mark.unit
def test_rejects_negative_priority() -> None:
    with pytest.raises(ValueError):
        FeaturedProperty(
            id="f", property_id="p", scope=FeaturedScope.HOME, priority=-1
        )


@pytest.mark.unit
def test_locality_scope_requires_locality_id() -> None:
    with pytest.raises(ValueError):
        FeaturedProperty(
            id="f", property_id="p", scope=FeaturedScope.LOCALITY
        )


@pytest.mark.unit
def test_locality_scope_with_locality_id_ok() -> None:
    feat = FeaturedProperty(
        id="f",
        property_id="p",
        scope=FeaturedScope.LOCALITY,
        locality_id="loc-1",
    )
    assert feat.locality_id == "loc-1"


@pytest.mark.unit
def test_rejects_window_when_start_not_before_end() -> None:
    with pytest.raises(ValueError):
        FeaturedProperty(
            id="f",
            property_id="p",
            scope=FeaturedScope.HOME,
            starts_at=datetime(2026, 6, 1),
            ends_at=datetime(2026, 6, 1),
        )
    with pytest.raises(ValueError):
        FeaturedProperty(
            id="f",
            property_id="p",
            scope=FeaturedScope.HOME,
            starts_at=datetime(2026, 6, 2),
            ends_at=datetime(2026, 6, 1),
        )


@pytest.mark.unit
def test_open_window_is_always_within_bounds() -> None:
    feat = FeaturedProperty(id="f", property_id="p", scope=FeaturedScope.HOME)
    assert feat.is_active_at(datetime(2000, 1, 1)) is True
    assert feat.is_active_at(datetime(2099, 1, 1)) is True


@pytest.mark.unit
def test_is_active_at_within_window(featured: FeaturedProperty) -> None:
    assert featured.is_active_at(datetime(2026, 6, 1)) is True


@pytest.mark.unit
def test_is_active_at_start_inclusive(featured: FeaturedProperty) -> None:
    assert featured.is_active_at(datetime(2026, 1, 1)) is True


@pytest.mark.unit
def test_is_active_at_before_start(featured: FeaturedProperty) -> None:
    assert featured.is_active_at(datetime(2025, 12, 31)) is False


@pytest.mark.unit
def test_is_active_at_end_exclusive(featured: FeaturedProperty) -> None:
    assert featured.is_active_at(datetime(2026, 12, 31)) is False


@pytest.mark.unit
def test_is_active_at_after_end(featured: FeaturedProperty) -> None:
    assert featured.is_active_at(datetime(2027, 1, 1)) is False


@pytest.mark.unit
def test_is_active_at_when_disabled(featured: FeaturedProperty) -> None:
    featured.is_active = False
    assert featured.is_active_at(datetime(2026, 6, 1)) is False


@pytest.mark.unit
def test_ctr_with_impressions(featured: FeaturedProperty) -> None:
    assert featured.ctr() == 0.05


@pytest.mark.unit
def test_ctr_without_impressions() -> None:
    feat = FeaturedProperty(
        id="f",
        property_id="p",
        scope=FeaturedScope.HOME,
        clicks_count=3,
    )
    assert feat.ctr() == 0.0


@pytest.mark.unit
def test_ctr_rounding() -> None:
    feat = FeaturedProperty(
        id="f",
        property_id="p",
        scope=FeaturedScope.HOME,
        impressions_count=3,
        clicks_count=1,
    )
    assert feat.ctr() == 0.3333


@pytest.mark.integration
def test_select_featured_filters_and_orders() -> None:
    moment = datetime(2026, 6, 1)
    a = FeaturedProperty(
        id="a", property_id="pa", scope=FeaturedScope.HOME, priority=1
    )
    b = FeaturedProperty(
        id="b", property_id="pb", scope=FeaturedScope.HOME, priority=9
    )
    c = FeaturedProperty(
        id="c", property_id="pc", scope=FeaturedScope.HOME, priority=5
    )
    other_scope = FeaturedProperty(
        id="d",
        property_id="pd",
        scope=FeaturedScope.SEARCH_RESULTS,
        priority=99,
    )
    inactive = FeaturedProperty(
        id="e",
        property_id="pe",
        scope=FeaturedScope.HOME,
        priority=99,
        is_active=False,
    )
    out_of_window = FeaturedProperty(
        id="g",
        property_id="pg",
        scope=FeaturedScope.HOME,
        priority=99,
        starts_at=datetime(2027, 1, 1),
    )

    result = select_featured(
        [a, b, c, other_scope, inactive, out_of_window],
        FeaturedScope.HOME,
        moment,
        limit=10,
    )

    assert result == [b, c, a]


@pytest.mark.integration
def test_select_featured_applies_limit() -> None:
    moment = datetime(2026, 6, 1)
    items = [
        FeaturedProperty(
            id=str(i),
            property_id=f"p{i}",
            scope=FeaturedScope.HOME,
            priority=i,
        )
        for i in range(5)
    ]

    result = select_featured(items, FeaturedScope.HOME, moment, limit=2)

    assert [item.id for item in result] == ["4", "3"]


@pytest.mark.unit
def test_select_featured_non_positive_limit() -> None:
    moment = datetime(2026, 6, 1)
    item = FeaturedProperty(
        id="a", property_id="pa", scope=FeaturedScope.HOME
    )
    assert select_featured([item], FeaturedScope.HOME, moment, limit=0) == []
    assert select_featured([item], FeaturedScope.HOME, moment, limit=-3) == []


@pytest.mark.unit
def test_select_featured_empty_input() -> None:
    moment = datetime(2026, 6, 1)
    assert select_featured([], FeaturedScope.HOME, moment, limit=5) == []
