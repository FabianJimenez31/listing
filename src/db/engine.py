"""SQLAlchemy engine, session factory, and declarative base.

DATABASE_URL defaults to a local SQLite file for development/testing.
Set DATABASE_URL env var to a PostgreSQL DSN for production:
  postgresql+psycopg2://user:pass@host:5432/listing
"""
from __future__ import annotations

import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./dev.db")

_connect_args: dict = (
    {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

engine = create_engine(DATABASE_URL, connect_args=_connect_args, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yields a database session, always closing on exit."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    """Create all tables registered with Base.metadata.

    Import all model modules before calling this so they register their
    Table objects with Base.metadata.
    """
    import src.db.models  # noqa: F401 — side-effect: registers all ORM models

    Base.metadata.create_all(bind=engine)
