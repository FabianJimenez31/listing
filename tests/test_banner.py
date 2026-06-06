"""Unit tests for the banner domain module."""
from datetime import datetime

import pytest

from src.banner import Banner, BannerPosition


@pytest.fixture
def banner() -> Banner:
    return Banner(
        id="b1",
        title="Summer sale",
        image_desktop_url="https://cdn.example/desktop.jpg",
        image_mobile_url="https://cdn.example/mobile.jpg",
        cta_label="See more",
        cta_url="https://example/listings",
        position=BannerPosition.HOME_HERO,
    )


@pytest.fixture
def scheduled_banner() -> Banner:
    return Banner(
        id="b2",
        title="Window",
        image_desktop_url="https://cdn.example/d.jpg",
        image_mobile_url="https://cdn.example/m.jpg",
        cta_label="Go",
        cta_url="https://example/go",
        position=BannerPosition.LISTING_TOP,
        starts_at=datetime(2026, 1, 10),
        ends_at=datetime(2026, 1, 20),
    )


@pytest.mark.unit
def test_position_enum_values() -> None:
    assert BannerPosition.HOME_HERO == "home_hero"
    assert BannerPosition.HOME_INLINE == "home_inline"
    assert BannerPosition.LISTING_TOP == "listing_top"
    assert BannerPosition.LISTING_INLINE == "listing_inline"
    assert BannerPosition.DETAIL_SIDEBAR == "detail_sidebar"


@pytest.mark.unit
def test_defaults(banner: Banner) -> None:
    assert banner.priority == 0
    assert banner.is_active is True
    assert banner.description is None
    assert banner.impressions_count == 0
    assert banner.clicks_count == 0
    assert banner.target_locality_id is None
    assert banner.target_operation is None


@pytest.mark.unit
def test_requires_title() -> None:
    with pytest.raises(ValueError):
        Banner(
            id="x",
            title="",
            image_desktop_url="d",
            image_mobile_url="m",
            cta_label="c",
            cta_url="u",
            position=BannerPosition.HOME_HERO,
        )


@pytest.mark.unit
def test_requires_image_desktop_url() -> None:
    with pytest.raises(ValueError):
        Banner(
            id="x",
            title="t",
            image_desktop_url="",
            image_mobile_url="m",
            cta_label="c",
            cta_url="u",
            position=BannerPosition.HOME_HERO,
        )


@pytest.mark.unit
def test_requires_image_mobile_url() -> None:
    with pytest.raises(ValueError):
        Banner(
            id="x",
            title="t",
            image_desktop_url="d",
            image_mobile_url="",
            cta_label="c",
            cta_url="u",
            position=BannerPosition.HOME_HERO,
        )


@pytest.mark.unit
def test_requires_cta_label() -> None:
    with pytest.raises(ValueError):
        Banner(
            id="x",
            title="t",
            image_desktop_url="d",
            image_mobile_url="m",
            cta_label="",
            cta_url="u",
            position=BannerPosition.HOME_HERO,
        )


@pytest.mark.unit
def test_requires_cta_url() -> None:
    with pytest.raises(ValueError):
        Banner(
            id="x",
            title="t",
            image_desktop_url="d",
            image_mobile_url="m",
            cta_label="c",
            cta_url="",
            position=BannerPosition.HOME_HERO,
        )


@pytest.mark.unit
def test_rejects_negative_priority() -> None:
    with pytest.raises(ValueError):
        Banner(
            id="x",
            title="t",
            image_desktop_url="d",
            image_mobile_url="m",
            cta_label="c",
            cta_url="u",
            position=BannerPosition.HOME_HERO,
            priority=-1,
        )


@pytest.mark.unit
def test_rejects_start_after_end() -> None:
    with pytest.raises(ValueError):
        Banner(
            id="x",
            title="t",
            image_desktop_url="d",
            image_mobile_url="m",
            cta_label="c",
            cta_url="u",
            position=BannerPosition.HOME_HERO,
            starts_at=datetime(2026, 2, 1),
            ends_at=datetime(2026, 1, 1),
        )


@pytest.mark.unit
def test_rejects_equal_start_end() -> None:
    moment = datetime(2026, 1, 1)
    with pytest.raises(ValueError):
        Banner(
            id="x",
            title="t",
            image_desktop_url="d",
            image_mobile_url="m",
            cta_label="c",
            cta_url="u",
            position=BannerPosition.HOME_HERO,
            starts_at=moment,
            ends_at=moment,
        )


@pytest.mark.unit
def test_is_active_at_no_window(banner: Banner) -> None:
    assert banner.is_active_at(datetime(2026, 6, 6)) is True


@pytest.mark.unit
def test_is_active_at_inactive_flag(banner: Banner) -> None:
    banner.is_active = False
    assert banner.is_active_at(datetime(2026, 6, 6)) is False


@pytest.mark.unit
def test_is_active_at_before_window(scheduled_banner: Banner) -> None:
    assert scheduled_banner.is_active_at(datetime(2026, 1, 5)) is False


@pytest.mark.unit
def test_is_active_at_after_window(scheduled_banner: Banner) -> None:
    assert scheduled_banner.is_active_at(datetime(2026, 1, 25)) is False


@pytest.mark.unit
def test_is_active_at_within_window(scheduled_banner: Banner) -> None:
    assert scheduled_banner.is_active_at(datetime(2026, 1, 15)) is True


@pytest.mark.unit
def test_is_active_at_window_bounds(scheduled_banner: Banner) -> None:
    assert scheduled_banner.is_active_at(datetime(2026, 1, 10)) is True
    assert scheduled_banner.is_active_at(datetime(2026, 1, 20)) is True


@pytest.mark.unit
def test_is_active_at_only_start_bound() -> None:
    banner = Banner(
        id="x",
        title="t",
        image_desktop_url="d",
        image_mobile_url="m",
        cta_label="c",
        cta_url="u",
        position=BannerPosition.HOME_INLINE,
        starts_at=datetime(2026, 1, 10),
    )
    assert banner.is_active_at(datetime(2026, 1, 9)) is False
    assert banner.is_active_at(datetime(2026, 1, 11)) is True


@pytest.mark.unit
def test_is_active_at_only_end_bound() -> None:
    banner = Banner(
        id="x",
        title="t",
        image_desktop_url="d",
        image_mobile_url="m",
        cta_label="c",
        cta_url="u",
        position=BannerPosition.HOME_INLINE,
        ends_at=datetime(2026, 1, 20),
    )
    assert banner.is_active_at(datetime(2026, 1, 19)) is True
    assert banner.is_active_at(datetime(2026, 1, 21)) is False


@pytest.mark.unit
def test_ctr_zero_impressions(banner: Banner) -> None:
    assert banner.ctr() == 0.0


@pytest.mark.unit
def test_ctr_with_impressions(banner: Banner) -> None:
    banner.impressions_count = 200
    banner.clicks_count = 50
    assert banner.ctr() == 0.25


@pytest.mark.unit
def test_register_impression(banner: Banner) -> None:
    banner.register_impression()
    banner.register_impression()
    assert banner.impressions_count == 2


@pytest.mark.unit
def test_register_click(banner: Banner) -> None:
    banner.register_click()
    assert banner.clicks_count == 1


@pytest.mark.integration
def test_engagement_flow(banner: Banner) -> None:
    for _ in range(4):
        banner.register_impression()
    banner.register_click()
    assert banner.impressions_count == 4
    assert banner.clicks_count == 1
    assert banner.ctr() == 0.25


@pytest.mark.critical
def test_targeted_banner_construction() -> None:
    banner = Banner(
        id="b3",
        title="Bogota sale",
        image_desktop_url="https://cdn.example/d.jpg",
        image_mobile_url="https://cdn.example/m.jpg",
        cta_label="Ver",
        cta_url="https://example/co",
        position=BannerPosition.DETAIL_SIDEBAR,
        priority=5,
        description="Promo",
        target_locality_id="loc-1",
        target_city="Bogota",
        target_operation="sale",
        target_kind="apartment",
    )
    assert banner.priority == 5
    assert banner.target_city == "Bogota"
    assert banner.target_operation == "sale"
    assert banner.target_kind == "apartment"
    assert banner.is_active_at(datetime(2026, 6, 6)) is True
