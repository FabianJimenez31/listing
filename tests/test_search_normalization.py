from sqlalchemy import create_engine, select

from src.text.search_normalization import (
    extract_nid,
    normalize_search_text,
    normalized_sql,
    search_like_pattern,
)


def test_normalizes_accents_commas_and_spacing():
    assert normalize_search_text("  Batán, Bogotá D.C. ") == "batan bogota d c"
    assert search_like_pattern("Batán, Bogotá") == "%batan%bogota%"


def test_extracts_nid_from_public_search_forms():
    assert extract_nid("/1000000149") == 1000000149
    assert extract_nid("NID 1000000149") == 1000000149
    assert extract_nid("Apartamento 1000000149") is None


def test_sql_normalization_is_sqlite_portable():
    engine = create_engine("sqlite://")
    with engine.connect() as connection:
        result = connection.execute(select(normalized_sql("BATÁN, Bogotá"))).scalar_one()
    assert result == "batan, bogota"
