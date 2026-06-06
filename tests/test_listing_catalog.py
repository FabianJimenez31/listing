"""Unit tests for the listing catalog module."""
import pytest

from src.listing_catalog import Catalog, Listing, ListingStatus


@pytest.fixture
def listing() -> Listing:
    return Listing(sku="SKU-1", title="Widget", price_cents=1999, tags=["new"])


@pytest.mark.unit
def test_listing_defaults_to_draft(listing: Listing) -> None:
    assert listing.status == ListingStatus.DRAFT


@pytest.mark.unit
def test_price_is_major_units(listing: Listing) -> None:
    assert listing.price == 19.99


@pytest.mark.unit
def test_requires_sku() -> None:
    with pytest.raises(ValueError):
        Listing(sku="", title="x", price_cents=1)


@pytest.mark.unit
def test_rejects_negative_price() -> None:
    with pytest.raises(ValueError):
        Listing(sku="x", title="x", price_cents=-1)


@pytest.mark.unit
def test_publish_and_archive(listing: Listing) -> None:
    listing.publish()
    assert listing.status == ListingStatus.PUBLISHED
    listing.archive()
    assert listing.status == ListingStatus.ARCHIVED


@pytest.mark.unit
def test_cannot_publish_archived(listing: Listing) -> None:
    listing.archive()
    with pytest.raises(ValueError):
        listing.publish()


@pytest.mark.integration
def test_catalog_aggregations() -> None:
    cat = Catalog()
    a = Listing(sku="A", title="A", price_cents=1000)
    b = Listing(sku="B", title="B", price_cents=2500)
    cat.add(a)
    cat.add(b)
    a.publish()

    assert len(cat) == 2
    assert cat.get("A") is a
    assert cat.total_value_cents() == 3500
    assert cat.published() == [a]
    with pytest.raises(KeyError):
        cat.add(Listing(sku="A", title="dup", price_cents=1))
