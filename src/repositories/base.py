"""Generic CRUD repository base."""
from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.db.engine import Base

ModelT = TypeVar("ModelT", bound=Base)  # type: ignore[type-arg]


class BaseRepository(Generic[ModelT]):
    """Thin CRUD base. All subclasses filter soft-deleted rows by default."""

    def __init__(self, model: type[ModelT], db: Session) -> None:
        self.model = model
        self.db = db

    def get_by_id(self, id: str) -> ModelT | None:
        return self.db.get(self.model, id)

    def list_all(self, skip: int = 0, limit: int = 20) -> list[ModelT]:
        stmt = select(self.model).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def count_all(self) -> int:
        stmt = select(func.count()).select_from(self.model)
        return self.db.scalar(stmt) or 0

    def add(self, obj: ModelT) -> ModelT:
        self.db.add(obj)
        self.db.flush()
        return obj

    def delete(self, obj: ModelT) -> None:
        self.db.delete(obj)
        self.db.flush()

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, obj: ModelT) -> None:
        self.db.refresh(obj)
