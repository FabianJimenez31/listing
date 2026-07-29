"""Unit tests for the favorite module."""
from datetime import datetime, timezone

import pytest

from src.favorite import Favorite, FavoriteSet


@pytest.fixture
def favorite() -> Favorite:
    return Favorite(id="fav-1", user_id="user-1", property_id="prop-1")


@pytest.mark.unit
def test_sets_default_created_at(favorite: Favorite) -> None:
    assert isinstance(favorite.created_at, datetime)


@pytest.mark.unit
def test_keeps_explicit_created_at() -> None:
    ts = datetime(2026, 6, 6, tzinfo=timezone.utc)
    fav = Favorite(id="fav-1", user_id="user-1", property_id="prop-1", created_at=ts)
    assert fav.created_at == ts


@pytest.mark.unit
def test_requires_user_id() -> None:
    with pytest.raises(ValueError):
        Favorite(id="fav-1", user_id="", property_id="prop-1")


@pytest.mark.unit
def test_requires_property_id() -> None:
    with pytest.raises(ValueError):
        Favorite(id="fav-1", user_id="user-1", property_id="")


@pytest.mark.unit
def test_add_and_len(favorite: Favorite) -> None:
    fs = FavoriteSet()
    assert len(fs) == 0
    fs.add(favorite)
    assert len(fs) == 1


@pytest.mark.unit
def test_add_rejects_duplicate_pair(favorite: Favorite) -> None:
    fs = FavoriteSet()
    fs.add(favorite)
    with pytest.raises(KeyError):
        fs.add(Favorite(id="fav-2", user_id="user-1", property_id="prop-1"))


@pytest.mark.unit
def test_same_property_different_users_allowed() -> None:
    fs = FavoriteSet()
    fs.add(Favorite(id="fav-1", user_id="user-1", property_id="prop-1"))
    fs.add(Favorite(id="fav-2", user_id="user-2", property_id="prop-1"))
    assert len(fs) == 2


@pytest.mark.unit
def test_same_user_different_properties_allowed() -> None:
    fs = FavoriteSet()
    fs.add(Favorite(id="fav-1", user_id="user-1", property_id="prop-1"))
    fs.add(Favorite(id="fav-2", user_id="user-1", property_id="prop-2"))
    assert len(fs) == 2


@pytest.mark.unit
def test_remove(favorite: Favorite) -> None:
    fs = FavoriteSet()
    fs.add(favorite)
    fs.remove("user-1", "prop-1")
    assert len(fs) == 0


@pytest.mark.unit
def test_remove_missing_raises() -> None:
    fs = FavoriteSet()
    with pytest.raises(KeyError):
        fs.remove("user-1", "prop-1")


@pytest.mark.unit
def test_remove_then_readd_allowed(favorite: Favorite) -> None:
    fs = FavoriteSet()
    fs.add(favorite)
    fs.remove("user-1", "prop-1")
    fs.add(Favorite(id="fav-9", user_id="user-1", property_id="prop-1"))
    assert len(fs) == 1


@pytest.mark.integration
def test_list_for_user_filters_by_owner() -> None:
    fs = FavoriteSet()
    a = Favorite(id="fav-1", user_id="user-1", property_id="prop-1")
    b = Favorite(id="fav-2", user_id="user-1", property_id="prop-2")
    c = Favorite(id="fav-3", user_id="user-2", property_id="prop-1")
    fs.add(a)
    fs.add(b)
    fs.add(c)

    user_1_favs = fs.list_for_user("user-1")
    assert len(user_1_favs) == 2
    assert a in user_1_favs
    assert b in user_1_favs
    assert c not in user_1_favs


@pytest.mark.unit
def test_list_for_user_empty() -> None:
    fs = FavoriteSet()
    assert fs.list_for_user("nobody") == []
