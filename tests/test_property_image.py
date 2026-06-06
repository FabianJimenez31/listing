"""Unit tests for the property image / media module."""
import pytest

from src.property_image import (
    ALLOWED_IMAGE_TYPES,
    MAX_IMAGE_BYTES,
    MIN_HEIGHT,
    MIN_WIDTH,
    ImageRole,
    MediaKind,
    PropertyImage,
    enforce_single_main,
    order_gallery,
)


@pytest.fixture
def image() -> PropertyImage:
    return PropertyImage(
        id="img-1",
        property_id="prop-1",
        original_url="https://cdn.example.com/original/1.jpg",
        content_type="image/jpeg",
        width=1024,
        height=768,
        bytes=512_000,
    )


@pytest.mark.unit
def test_defaults_to_gallery_and_image(image: PropertyImage) -> None:
    assert image.role == ImageRole.GALLERY
    assert image.media_kind == MediaKind.IMAGE
    assert image.position == 0


@pytest.mark.unit
def test_enum_values_match_contract() -> None:
    assert ImageRole.MAIN.value == "main"
    assert ImageRole.GALLERY.value == "gallery"
    assert MediaKind.IMAGE.value == "image"
    assert MediaKind.VIDEO.value == "video"
    assert MediaKind.FLOOR_PLAN.value == "floor_plan"
    assert MediaKind.VIRTUAL_TOUR.value == "virtual_tour"


@pytest.mark.unit
def test_module_constants() -> None:
    assert ALLOWED_IMAGE_TYPES == {"image/jpeg", "image/png", "image/webp"}
    assert MAX_IMAGE_BYTES == 10 * 1024 * 1024
    assert MIN_WIDTH == 800
    assert MIN_HEIGHT == 600


@pytest.mark.unit
def test_requires_property_id() -> None:
    with pytest.raises(ValueError):
        PropertyImage(id="x", property_id="", original_url="u")


@pytest.mark.unit
def test_requires_original_url() -> None:
    with pytest.raises(ValueError):
        PropertyImage(id="x", property_id="p", original_url="")


@pytest.mark.unit
def test_rejects_negative_position() -> None:
    with pytest.raises(ValueError):
        PropertyImage(id="x", property_id="p", original_url="u", position=-1)


@pytest.mark.unit
def test_rejects_disallowed_content_type_for_image() -> None:
    with pytest.raises(ValueError):
        PropertyImage(
            id="x",
            property_id="p",
            original_url="u",
            media_kind=MediaKind.IMAGE,
            content_type="image/gif",
        )


@pytest.mark.unit
def test_allows_disallowed_content_type_for_non_image() -> None:
    asset = PropertyImage(
        id="x",
        property_id="p",
        original_url="u",
        media_kind=MediaKind.VIDEO,
        content_type="video/mp4",
    )
    assert asset.content_type == "video/mp4"


@pytest.mark.unit
def test_content_type_optional_for_image() -> None:
    asset = PropertyImage(id="x", property_id="p", original_url="u")
    assert asset.content_type is None


@pytest.mark.unit
def test_rejects_oversized_bytes() -> None:
    with pytest.raises(ValueError):
        PropertyImage(
            id="x",
            property_id="p",
            original_url="u",
            bytes=MAX_IMAGE_BYTES + 1,
        )


@pytest.mark.unit
def test_accepts_bytes_at_limit() -> None:
    asset = PropertyImage(
        id="x",
        property_id="p",
        original_url="u",
        bytes=MAX_IMAGE_BYTES,
    )
    assert asset.bytes == MAX_IMAGE_BYTES


@pytest.mark.unit
def test_rejects_width_below_minimum() -> None:
    with pytest.raises(ValueError):
        PropertyImage(
            id="x",
            property_id="p",
            original_url="u",
            width=MIN_WIDTH - 1,
            height=MIN_HEIGHT,
        )


@pytest.mark.unit
def test_rejects_height_below_minimum() -> None:
    with pytest.raises(ValueError):
        PropertyImage(
            id="x",
            property_id="p",
            original_url="u",
            width=MIN_WIDTH,
            height=MIN_HEIGHT - 1,
        )


@pytest.mark.unit
def test_accepts_dimensions_at_minimum() -> None:
    asset = PropertyImage(
        id="x",
        property_id="p",
        original_url="u",
        width=MIN_WIDTH,
        height=MIN_HEIGHT,
    )
    assert asset.width == MIN_WIDTH
    assert asset.height == MIN_HEIGHT


@pytest.mark.unit
def test_width_only_skips_dimension_check() -> None:
    asset = PropertyImage(
        id="x",
        property_id="p",
        original_url="u",
        width=10,
    )
    assert asset.width == 10
    assert asset.height is None


@pytest.mark.unit
def test_make_main(image: PropertyImage) -> None:
    image.make_main()
    assert image.role == ImageRole.MAIN


@pytest.mark.unit
def test_set_position(image: PropertyImage) -> None:
    image.set_position(5)
    assert image.position == 5


@pytest.mark.unit
def test_set_position_rejects_negative(image: PropertyImage) -> None:
    with pytest.raises(ValueError):
        image.set_position(-1)


@pytest.mark.integration
def test_order_gallery() -> None:
    a = PropertyImage(id="a", property_id="p", original_url="u", position=2)
    b = PropertyImage(id="b", property_id="p", original_url="u", position=0)
    c = PropertyImage(id="c", property_id="p", original_url="u", position=1)
    ordered = order_gallery([a, b, c])
    assert ordered == [b, c, a]


@pytest.mark.critical
def test_enforce_single_main_ok() -> None:
    main = PropertyImage(
        id="a", property_id="p", original_url="u", role=ImageRole.MAIN
    )
    gallery = PropertyImage(id="b", property_id="p", original_url="u")
    enforce_single_main([main, gallery])


@pytest.mark.critical
def test_enforce_single_main_empty_is_ok() -> None:
    enforce_single_main([])


@pytest.mark.critical
def test_enforce_single_main_zero_raises() -> None:
    gallery = PropertyImage(id="b", property_id="p", original_url="u")
    with pytest.raises(ValueError):
        enforce_single_main([gallery])


@pytest.mark.critical
def test_enforce_single_main_multiple_raises() -> None:
    a = PropertyImage(
        id="a", property_id="p", original_url="u", role=ImageRole.MAIN
    )
    b = PropertyImage(
        id="b", property_id="p", original_url="u", role=ImageRole.MAIN
    )
    with pytest.raises(ValueError):
        enforce_single_main([a, b])
