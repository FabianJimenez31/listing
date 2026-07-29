"""Audit log domain logic.

A focused, single-responsibility module that models append-only audit log
entries for the Listing platform. An :class:`AuditLog` captures who did what
to which entity, with optional before/after snapshots and request context.

Pure domain layer: dataclasses, enums and validation only. No FastAPI,
SQLAlchemy, Pydantic, HTTP or DB concerns live here.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum


class AuditAction(str, Enum):
    """Actions that can be recorded in the audit trail.

    Values are the canonical lowercase/snake strings persisted in the
    database. Keep this Enum in sync with stored values; the harness
    command ``make validate-enums`` enforces that consistency.
    """

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    PUBLISH = "publish"
    APPROVE = "approve"
    REJECT = "reject"
    PAUSE = "pause"
    REACTIVATE = "reactivate"
    MARK_SOLD = "mark_sold"
    MARK_RENTED = "mark_rented"
    DUPLICATE = "duplicate"
    LOGIN = "login"
    LOGOUT = "logout"
    ROLE_ASSIGN = "role_assign"
    PERMISSION_CHANGE = "permission_change"
    CONFIG_CHANGE = "config_change"


@dataclass
class AuditLog:
    """A single append-only audit trail entry.

    Captures an :class:`AuditAction` performed by ``actor_id`` (nullable for
    system events) against the entity identified by ``entity_type`` and
    ``entity_id``. Optional ``before``/``after`` snapshots record the change,
    while ``ip`` and ``user_agent`` carry request context.

    Attributes:
        id: UUID v4 string primary key.
        action: The :class:`AuditAction` that was performed.
        entity_type: Logical name of the affected entity (e.g. ``"property"``).
        entity_id: Identifier of the affected entity.
        actor_id: User id that performed the action; ``None`` for system events.
        before: Snapshot of the entity state before the change.
        after: Snapshot of the entity state after the change.
        ip: Source IP address of the request.
        user_agent: Client user agent string.
        created_at: UTC timestamp the entry was recorded.
    """

    id: str
    action: AuditAction
    entity_type: str
    entity_id: str
    actor_id: str | None = None
    before: dict | None = None
    after: dict | None = None
    ip: str | None = None
    user_agent: str | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("id is required")
        if not isinstance(self.action, AuditAction):
            raise ValueError("action must be an AuditAction")
        if not self.entity_type:
            raise ValueError("entity_type is required")
        if not self.entity_id:
            raise ValueError("entity_id is required")
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

    @classmethod
    def record(
        cls,
        id: str,
        action: AuditAction,
        entity_type: str,
        entity_id: str,
        actor_id: str | None = None,
        before: dict | None = None,
        after: dict | None = None,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """Construct an append-only audit entry.

        Factory that stamps a fresh UTC ``created_at`` and returns a new
        :class:`AuditLog`. Audit entries are immutable by convention: never
        mutate a recorded entry, always record a new one.

        Args:
            id: UUID v4 string primary key.
            action: The :class:`AuditAction` that was performed.
            entity_type: Logical name of the affected entity.
            entity_id: Identifier of the affected entity.
            actor_id: User id that performed the action; ``None`` for system.
            before: Snapshot of the entity state before the change.
            after: Snapshot of the entity state after the change.
            ip: Source IP address of the request.
            user_agent: Client user agent string.

        Returns:
            The newly recorded :class:`AuditLog` entry.

        Raises:
            ValueError: If required fields are missing or ``action`` is invalid.
        """
        return cls(
            id=id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_id=actor_id,
            before=before,
            after=after,
            ip=ip,
            user_agent=user_agent,
            created_at=datetime.now(timezone.utc),
        )
