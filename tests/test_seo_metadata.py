"""Unit tests for the SEO metadata module."""
import pytest

from src.seo_metadata import (
    MAX_DESCRIPTION,
    MAX_TITLE,
    SeoMetadata,
)


@pytest.fixture
def seo() -> SeoMetadata:
    return SeoMetadata(
        id="11111111-1111-4111-8111-111111111111",
        entity_type="property",
        entity_id="22222222-2222-4222-8222-222222222222",
        slug="venta-apartamento-chapinero-a1b2c3",
        meta_title="Apartamento en venta en Chapinero",
        meta_description="Hermoso apartamento en Chapinero, listo para estrenar.",
    )


@pytest.mark.unit
def test_defaults(seo: SeoMetadata) -> None:
    assert seo.robots == "index,follow"
    assert seo.jsonld == {}
    assert seo.redirect_from == []
    assert seo.og_title is None
    assert seo.og_description is None
    assert seo.og_image_url is None
    assert seo.canonical_url is None


@pytest.mark.unit
def test_constants() -> None:
    assert MAX_TITLE == 70
    assert MAX_DESCRIPTION == 160


@pytest.mark.unit
def test_requires_slug() -> None:
    with pytest.raises(ValueError):
        SeoMetadata(
            id="x",
            entity_type="property",
            entity_id="y",
            slug="",
            meta_title="Title",
            meta_description="Desc",
        )


@pytest.mark.unit
@pytest.mark.parametrize(
    "bad_slug",
    [
        "Venta-Apartamento",
        "venta_apartamento",
        "venta apartamento",
        "-venta-apartamento",
        "venta-apartamento-",
        "venta--apartamento",
        "ventá-apartamento",
    ],
)
def test_rejects_invalid_slug(bad_slug: str) -> None:
    with pytest.raises(ValueError):
        SeoMetadata(
            id="x",
            entity_type="property",
            entity_id="y",
            slug=bad_slug,
            meta_title="Title",
            meta_description="Desc",
        )


@pytest.mark.unit
def test_accepts_valid_slug() -> None:
    meta = SeoMetadata(
        id="x",
        entity_type="property",
        entity_id="y",
        slug="abc123",
        meta_title="Title",
        meta_description="Desc",
    )
    assert meta.slug == "abc123"


@pytest.mark.unit
def test_requires_meta_title() -> None:
    with pytest.raises(ValueError):
        SeoMetadata(
            id="x",
            entity_type="property",
            entity_id="y",
            slug="valid-slug",
            meta_title="",
            meta_description="Desc",
        )


@pytest.mark.unit
def test_meta_title_too_long() -> None:
    with pytest.raises(ValueError):
        SeoMetadata(
            id="x",
            entity_type="property",
            entity_id="y",
            slug="valid-slug",
            meta_title="a" * (MAX_TITLE + 1),
            meta_description="Desc",
        )


@pytest.mark.unit
def test_meta_title_at_limit() -> None:
    meta = SeoMetadata(
        id="x",
        entity_type="property",
        entity_id="y",
        slug="valid-slug",
        meta_title="a" * MAX_TITLE,
        meta_description="Desc",
    )
    assert len(meta.meta_title) == MAX_TITLE


@pytest.mark.unit
def test_meta_description_too_long() -> None:
    with pytest.raises(ValueError):
        SeoMetadata(
            id="x",
            entity_type="property",
            entity_id="y",
            slug="valid-slug",
            meta_title="Title",
            meta_description="a" * (MAX_DESCRIPTION + 1),
        )


@pytest.mark.unit
def test_meta_description_at_limit() -> None:
    meta = SeoMetadata(
        id="x",
        entity_type="property",
        entity_id="y",
        slug="valid-slug",
        meta_title="Title",
        meta_description="a" * MAX_DESCRIPTION,
    )
    assert len(meta.meta_description) == MAX_DESCRIPTION


@pytest.mark.unit
def test_empty_meta_description_allowed() -> None:
    meta = SeoMetadata(
        id="x",
        entity_type="property",
        entity_id="y",
        slug="valid-slug",
        meta_title="Title",
        meta_description="",
    )
    assert meta.meta_description == ""


@pytest.mark.unit
def test_add_redirect(seo: SeoMetadata) -> None:
    seo.add_redirect("venta-apto-chapinero-old")
    assert seo.redirect_from == ["venta-apto-chapinero-old"]


@pytest.mark.unit
def test_add_redirect_dedup(seo: SeoMetadata) -> None:
    seo.add_redirect("old-slug-one")
    seo.add_redirect("old-slug-one")
    seo.add_redirect("old-slug-two")
    assert seo.redirect_from == ["old-slug-one", "old-slug-two"]


@pytest.mark.unit
def test_add_redirect_requires_value(seo: SeoMetadata) -> None:
    with pytest.raises(ValueError):
        seo.add_redirect("")


@pytest.mark.unit
def test_add_redirect_rejects_invalid_slug(seo: SeoMetadata) -> None:
    with pytest.raises(ValueError):
        seo.add_redirect("Not A Slug")


@pytest.mark.unit
def test_set_noindex(seo: SeoMetadata) -> None:
    seo.set_noindex()
    assert seo.robots == "noindex,nofollow"


@pytest.mark.critical
def test_full_lifecycle() -> None:
    meta = SeoMetadata(
        id="33333333-3333-4333-8333-333333333333",
        entity_type="property",
        entity_id="44444444-4444-4444-8444-444444444444",
        slug="arriendo-casa-laureles-z9y8x7",
        meta_title="Casa en arriendo en Laureles",
        meta_description="Amplia casa familiar en Laureles con jardin.",
        og_title="Casa en Laureles",
        og_description="Disponible ya",
        og_image_url="https://cdn.example.com/og.jpg",
        canonical_url="https://example.com/arriendo-casa-laureles-z9y8x7",
        jsonld={"@type": "Residence"},
    )
    meta.add_redirect("casa-laureles-old")
    meta.add_redirect("casa-laureles-old")
    meta.set_noindex()

    assert meta.redirect_from == ["casa-laureles-old"]
    assert meta.robots == "noindex,nofollow"
    assert meta.jsonld == {"@type": "Residence"}
