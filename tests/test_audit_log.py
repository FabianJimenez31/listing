"""Unit tests for the audit log module."""
from datetime import datetime, timezone

import pytest

from src.audit_log import AuditAction, AuditLog


@pytest.fixture
def entry() -> AuditLog:
    return AuditLog(
        id="11111111-1111-4111-8111-111111111111",
        action=AuditAction.CREATE,
        entity_type="property",
        entity_id="22222222-2222-4222-8222-222222222222",
    )


@pytest.mark.unit
def test_action_values_match_contract() -> None:
    assert AuditAction.CREATE.value == "create"
    assert AuditAction.UPDATE.value == "update"
    assert AuditAction.DELETE.value == "delete"
    assert AuditAction.PUBLISH.value == "publish"
    assert AuditAction.APPROVE.value == "approve"
    assert AuditAction.REJECT.value == "reject"
    assert AuditAction.PAUSE.value == "pause"
    assert AuditAction.REACTIVATE.value == "reactivate"
    assert AuditAction.MARK_SOLD.value == "mark_sold"
    assert AuditAction.MARK_RENTED.value == "mark_rented"
    assert AuditAction.DUPLICATE.value == "duplicate"
    assert AuditAction.LOGIN.value == "login"
    assert AuditAction.LOGOUT.value == "logout"
    assert AuditAction.ROLE_ASSIGN.value == "role_assign"
    assert AuditAction.PERMISSION_CHANGE.value == "permission_change"
    assert AuditAction.CONFIG_CHANGE.value == "config_change"


@pytest.mark.unit
def test_action_is_str_enum() -> None:
    assert isinstance(AuditAction.LOGIN, str)
    assert AuditAction.LOGIN == "login"


@pytest.mark.unit
def test_action_enum_is_complete() -> None:
    assert len(list(AuditAction)) == 16


@pytest.mark.unit
def test_defaults_are_none(entry: AuditLog) -> None:
    assert entry.actor_id is None
    assert entry.before is None
    assert entry.after is None
    assert entry.ip is None
    assert entry.user_agent is None


@pytest.mark.unit
def test_created_at_autofilled_utc(entry: AuditLog) -> None:
    assert isinstance(entry.created_at, datetime)
    assert entry.created_at.tzinfo == timezone.utc


@pytest.mark.unit
def test_explicit_created_at_preserved() -> None:
    stamp = datetime(2026, 1, 1, tzinfo=timezone.utc)
    log = AuditLog(
        id="id-1",
        action=AuditAction.UPDATE,
        entity_type="user",
        entity_id="u-1",
        created_at=stamp,
    )
    assert log.created_at is stamp


@pytest.mark.unit
def test_requires_id() -> None:
    with pytest.raises(ValueError):
        AuditLog(
            id="",
            action=AuditAction.CREATE,
            entity_type="property",
            entity_id="p-1",
        )


@pytest.mark.unit
def test_requires_entity_type() -> None:
    with pytest.raises(ValueError):
        AuditLog(
            id="id-1",
            action=AuditAction.CREATE,
            entity_type="",
            entity_id="p-1",
        )


@pytest.mark.unit
def test_requires_entity_id() -> None:
    with pytest.raises(ValueError):
        AuditLog(
            id="id-1",
            action=AuditAction.CREATE,
            entity_type="property",
            entity_id="",
        )


@pytest.mark.unit
def test_rejects_invalid_action() -> None:
    with pytest.raises(ValueError):
        AuditLog(
            id="id-1",
            action="create",  # type: ignore[arg-type]
            entity_type="property",
            entity_id="p-1",
        )


@pytest.mark.unit
def test_record_factory_builds_entry() -> None:
    log = AuditLog.record(
        id="id-9",
        action=AuditAction.PUBLISH,
        entity_type="property",
        entity_id="p-9",
    )
    assert isinstance(log, AuditLog)
    assert log.id == "id-9"
    assert log.action is AuditAction.PUBLISH
    assert log.entity_type == "property"
    assert log.entity_id == "p-9"
    assert log.actor_id is None
    assert isinstance(log.created_at, datetime)
    assert log.created_at.tzinfo == timezone.utc


@pytest.mark.unit
def test_record_factory_carries_all_fields() -> None:
    before = {"status": "pending"}
    after = {"status": "published"}
    log = AuditLog.record(
        id="id-10",
        action=AuditAction.APPROVE,
        entity_type="property",
        entity_id="p-10",
        actor_id="admin-1",
        before=before,
        after=after,
        ip="203.0.113.7",
        user_agent="Mozilla/5.0",
    )
    assert log.actor_id == "admin-1"
    assert log.before == before
    assert log.after == after
    assert log.ip == "203.0.113.7"
    assert log.user_agent == "Mozilla/5.0"


@pytest.mark.unit
def test_record_factory_validates() -> None:
    with pytest.raises(ValueError):
        AuditLog.record(
            id="id-11",
            action=AuditAction.DELETE,
            entity_type="",
            entity_id="p-11",
        )


@pytest.mark.critical
def test_append_only_system_event_has_no_actor() -> None:
    log = AuditLog.record(
        id="id-sys",
        action=AuditAction.CONFIG_CHANGE,
        entity_type="config",
        entity_id="global",
        before={"flag": False},
        after={"flag": True},
    )
    assert log.actor_id is None
    assert log.action is AuditAction.CONFIG_CHANGE
    assert log.before == {"flag": False}
    assert log.after == {"flag": True}


@pytest.mark.integration
def test_audit_trail_accumulates_entries() -> None:
    trail: list[AuditLog] = []
    trail.append(
        AuditLog.record(
            id="a-1",
            action=AuditAction.CREATE,
            entity_type="property",
            entity_id="p-1",
            actor_id="agent-1",
        )
    )
    trail.append(
        AuditLog.record(
            id="a-2",
            action=AuditAction.PUBLISH,
            entity_type="property",
            entity_id="p-1",
            actor_id="admin-1",
        )
    )
    trail.append(
        AuditLog.record(
            id="a-3",
            action=AuditAction.MARK_SOLD,
            entity_type="property",
            entity_id="p-1",
            actor_id="agent-1",
        )
    )

    assert len(trail) == 3
    assert [e.action for e in trail] == [
        AuditAction.CREATE,
        AuditAction.PUBLISH,
        AuditAction.MARK_SOLD,
    ]
    assert all(e.entity_id == "p-1" for e in trail)
