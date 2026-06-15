"""Shared pytest fixtures for API integration tests.

Uses an in-memory SQLite database so tests run without a real PostgreSQL server.
Each test function gets a fresh database (via function-scoped fixtures).
"""
from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.app import create_app
from src.auth.password import hash_password
from src.db.engine import Base, get_db
from src.db import models  # noqa: F401 — registers all ORM models with Base.metadata
from src.db.models.user_models import PermissionORM, RoleORM, UserORM

# StaticPool forces all connections to share the same underlying SQLite connection,
# so tables created by create_all are visible to every subsequent session.
TEST_DB_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_engine():
    engine = create_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    Session = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------

def _make_permission(db, code: str) -> PermissionORM:
    perm = PermissionORM(id=str(uuid.uuid4()), code=code)
    db.add(perm)
    return perm


def _make_role(db, name: str, permission_codes: list[str] | None = None) -> RoleORM:
    role = RoleORM(id=str(uuid.uuid4()), name=name)
    db.add(role)
    db.flush()
    for code in (permission_codes or []):
        perm = db.query(PermissionORM).filter_by(code=code).first()
        if not perm:
            perm = _make_permission(db, code)
            db.flush()
        role.permissions.append(perm)
    return role


def _make_user(db, email: str, password: str = "Password123", roles: list[RoleORM] | None = None) -> UserORM:
    user = UserORM(
        id=str(uuid.uuid4()),
        email=email,
        hashed_password=hash_password(password),
        full_name="Test User",
    )
    db.add(user)
    db.flush()
    for role in (roles or []):
        user.roles.append(role)
    db.commit()
    db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Fixtures: common users
# ---------------------------------------------------------------------------

@pytest.fixture
def agent_user(db_session):
    role = _make_role(db_session, "AGENT", [
        "property:create", "property:update_own", "lead:read", "project:create",
    ])
    return _make_user(db_session, "agent@test.com", roles=[role])


@pytest.fixture
def admin_user(db_session):
    role = _make_role(db_session, "ADMIN", [
        "property:moderate", "property:read_all", "lead:read", "lead:read_all",
        "lead:update_all", "user:read", "role:assign", "banner:create", "banner:delete",
        "featured:create", "featured:delete", "location:create", "metrics:read",
        "project:create", "project:moderate",
        "agency:create", "agency:update", "agency:delete",
        "partner:create", "partner:delete",
        "post:create", "post:update", "post:delete",
    ])
    return _make_user(db_session, "admin@test.com", roles=[role])


@pytest.fixture
def agent_token(client, agent_user):
    resp = client.post("/api/v1/auth/login", json={"email": "agent@test.com", "password": "Password123"})
    return resp.json()["access_token"]


@pytest.fixture
def admin_token(client, admin_user):
    resp = client.post("/api/v1/auth/login", json={"email": "admin@test.com", "password": "Password123"})
    return resp.json()["access_token"]
