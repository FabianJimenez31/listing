"""Smoke tests for Alembic migrations: up/down round-trip."""
from __future__ import annotations

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

pytestmark = pytest.mark.integration

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_TEST_DB_FILE = _PROJECT_ROOT / "temp" / "test_migration.db"
_TEST_DB_URL = f"sqlite:///{_TEST_DB_FILE}"


@pytest.fixture(scope="module")
def alembic_cfg():
    cfg = Config(str(_PROJECT_ROOT / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", _TEST_DB_URL)
    cfg.set_main_option("script_location", str(_PROJECT_ROOT / "alembic"))
    return cfg


@pytest.fixture(autouse=True, scope="module")
def cleanup_db():
    yield
    if _TEST_DB_FILE.exists():
        _TEST_DB_FILE.unlink()


class TestAlembicMigrations:
    def test_upgrade_head_creates_tables(self, alembic_cfg):
        command.upgrade(alembic_cfg, "head")

        engine = create_engine(_TEST_DB_URL)
        tables = set(inspect(engine).get_table_names())
        engine.dispose()

        expected = {
            "users", "roles", "permissions",
            "user_role", "role_permission",
            "locations",
            "property_types", "amenities", "property_amenities",
            "properties", "property_images",
            "leads",
            "banners", "featured_properties",
            "favorites", "audit_logs", "property_views",
            "seo_metadata",
            "alembic_version",
        }
        assert expected.issubset(tables), f"Missing tables: {expected - tables}"

    def test_alembic_version_recorded(self, alembic_cfg):
        engine = create_engine(_TEST_DB_URL)
        with engine.connect() as conn:
            version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
        engine.dispose()
        assert version is not None
        assert len(version) > 0

    def test_downgrade_base_removes_tables(self, alembic_cfg):
        command.downgrade(alembic_cfg, "base")

        engine = create_engine(_TEST_DB_URL)
        tables = set(inspect(engine).get_table_names())
        engine.dispose()

        domain_tables = tables - {"alembic_version"}
        assert len(domain_tables) == 0, f"Tables remain after downgrade: {domain_tables}"

    def test_upgrade_after_downgrade(self, alembic_cfg):
        command.upgrade(alembic_cfg, "head")

        engine = create_engine(_TEST_DB_URL)
        tables = set(inspect(engine).get_table_names())
        engine.dispose()

        assert "properties" in tables
        assert "users" in tables
