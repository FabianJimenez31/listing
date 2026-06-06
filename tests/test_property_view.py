"""Unit tests for the property view (engagement event) module."""
from datetime import datetime, timezone

import pytest

from src.property_view import (
    MetricEventType,
    PropertyView,
    ViewSource,
    aggregate,
    ctr,
)


@pytest.fixture
def event() -> PropertyView:
    return PropertyView(id="EVT-1", property_id="PROP-1")


@pytest.mark.unit
def test_defaults_to_view_and_direct(event: PropertyView) -> None:
    assert event.event_type == MetricEventType.VIEW
    assert event.source == ViewSource.DIRECT


@pytest.mark.unit
def test_optional_fields_default_to_none(event: PropertyView) -> None:
    assert event.session_hash is None
    assert event.ip_hash is None
    assert event.referrer is None


@pytest.mark.unit
def test_created_at_defaults_to_aware_utc(event: PropertyView) -> None:
    assert isinstance(event.created_at, datetime)
    assert event.created_at.tzinfo is timezone.utc


@pytest.mark.unit
def test_requires_property_id() -> None:
    with pytest.raises(ValueError):
        PropertyView(id="EVT-X", property_id="")


@pytest.mark.unit
def test_accepts_explicit_fields() -> None:
    created = datetime(2026, 1, 1, tzinfo=timezone.utc)
    view = PropertyView(
        id="EVT-2",
        property_id="PROP-9",
        event_type=MetricEventType.WHATSAPP_CLICK,
        source=ViewSource.FEATURED,
        session_hash="sess",
        ip_hash="iphash",
        referrer="https://example.com",
        created_at=created,
    )
    assert view.event_type == MetricEventType.WHATSAPP_CLICK
    assert view.source == ViewSource.FEATURED
    assert view.session_hash == "sess"
    assert view.ip_hash == "iphash"
    assert view.referrer == "https://example.com"
    assert view.created_at == created


@pytest.mark.unit
def test_metric_event_type_values() -> None:
    assert MetricEventType.VIEW.value == "view"
    assert MetricEventType.CTA_CLICK.value == "cta_click"
    assert MetricEventType.WHATSAPP_CLICK.value == "whatsapp_click"
    assert MetricEventType.CALL_CLICK.value == "call_click"
    assert MetricEventType.VISIT_REQUEST.value == "visit_request"
    assert MetricEventType.SHARE.value == "share"
    assert MetricEventType.FAVORITE.value == "favorite"


@pytest.mark.unit
def test_view_source_values() -> None:
    assert ViewSource.ORGANIC.value == "organic"
    assert ViewSource.SEARCH.value == "search"
    assert ViewSource.FEATURED.value == "featured"
    assert ViewSource.DIRECT.value == "direct"
    assert ViewSource.SHARE.value == "share"


@pytest.mark.unit
def test_aggregate_empty_returns_empty_dict() -> None:
    assert aggregate([]) == {}


@pytest.mark.unit
def test_aggregate_counts_by_event_type_value() -> None:
    events = [
        PropertyView(id="1", property_id="P", event_type=MetricEventType.VIEW),
        PropertyView(id="2", property_id="P", event_type=MetricEventType.VIEW),
        PropertyView(id="3", property_id="P", event_type=MetricEventType.CTA_CLICK),
        PropertyView(id="4", property_id="P", event_type=MetricEventType.SHARE),
    ]
    assert aggregate(events) == {"view": 2, "cta_click": 1, "share": 1}


@pytest.mark.unit
def test_ctr_zero_views_returns_zero() -> None:
    assert ctr(0, 5) == 0.0


@pytest.mark.unit
def test_ctr_computes_ratio() -> None:
    assert ctr(100, 25) == 0.25


@pytest.mark.unit
def test_ctr_full_ratio() -> None:
    assert ctr(10, 10) == 1.0


@pytest.mark.integration
def test_aggregate_and_ctr_pipeline() -> None:
    events = [
        PropertyView(id="1", property_id="P", event_type=MetricEventType.VIEW),
        PropertyView(id="2", property_id="P", event_type=MetricEventType.VIEW),
        PropertyView(id="3", property_id="P", event_type=MetricEventType.VIEW),
        PropertyView(id="4", property_id="P", event_type=MetricEventType.VIEW),
        PropertyView(id="5", property_id="P", event_type=MetricEventType.CTA_CLICK),
    ]
    counts = aggregate(events)
    assert counts["view"] == 4
    assert ctr(counts["view"], counts.get("cta_click", 0)) == 0.25
