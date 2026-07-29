"""Repository for User, Role, and Permission entities."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from src.db.models.user_models import PermissionORM, RoleORM, UserORM
from src.repositories.base import BaseRepository


class UserRepository(BaseRepository[UserORM]):
    def __init__(self, db: Session) -> None:
        super().__init__(UserORM, db)

    def get_by_email(self, email: str) -> UserORM | None:
        stmt = select(UserORM).where(
            UserORM.email == email,
            UserORM.deleted_at.is_(None),
        )
        return self.db.scalar(stmt)

    def get_active_by_id(self, id: str) -> UserORM | None:
        stmt = (
            select(UserORM)
            .where(UserORM.id == id, UserORM.deleted_at.is_(None))
            .options(joinedload(UserORM.roles).joinedload(RoleORM.permissions))
        )
        return self.db.scalar(stmt)

    def count_superadmins(self) -> int:
        stmt = (
            select(UserORM)
            .join(UserORM.roles)
            .where(RoleORM.name == "SUPERADMIN", UserORM.deleted_at.is_(None))
        )
        return len(self.db.scalars(stmt).all())


class RoleRepository(BaseRepository[RoleORM]):
    def __init__(self, db: Session) -> None:
        super().__init__(RoleORM, db)

    def get_by_name(self, name: str) -> RoleORM | None:
        stmt = select(RoleORM).where(RoleORM.name == name)
        return self.db.scalar(stmt)


class PermissionRepository(BaseRepository[PermissionORM]):
    def __init__(self, db: Session) -> None:
        super().__init__(PermissionORM, db)

    def get_by_code(self, code: str) -> PermissionORM | None:
        stmt = select(PermissionORM).where(PermissionORM.code == code)
        return self.db.scalar(stmt)
