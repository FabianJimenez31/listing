"""Unit tests for the user / RBAC module."""
import pytest

from src.user import PermissionCode, Role, User


@pytest.fixture
def role() -> Role:
    return Role(
        id="r-1",
        name="agent",
        description="Real-estate agent",
        permission_codes={PermissionCode.PROPERTY_CREATE.value},
    )


@pytest.fixture
def user(role: Role) -> User:
    return User(
        id="u-1",
        email="agent@example.com",
        full_name="Ada Agent",
        role=role,
    )


# --- PermissionCode -------------------------------------------------------


@pytest.mark.unit
def test_permission_code_values_are_resource_action() -> None:
    assert PermissionCode.PROPERTY_READ_PUBLIC.value == "property:read_public"
    assert PermissionCode.CONFIG_MANAGE.value == "config:manage"
    assert PermissionCode.PROPERTY_TYPE_MANAGE.value == "property_type:manage"


@pytest.mark.unit
def test_permission_code_is_a_str() -> None:
    assert PermissionCode.USER_READ == "user:read"


# --- Role -----------------------------------------------------------------


@pytest.mark.unit
def test_role_requires_name() -> None:
    with pytest.raises(ValueError):
        Role(id="r", name="")


@pytest.mark.unit
def test_role_defaults() -> None:
    r = Role(id="r", name="registered_user")
    assert r.description is None
    assert r.permission_codes == set()
    assert r.is_system is False


@pytest.mark.unit
def test_role_grant_adds_code() -> None:
    r = Role(id="r", name="admin")
    r.grant(PermissionCode.PROPERTY_APPROVE.value)
    assert r.has_permission("property:approve")


@pytest.mark.unit
def test_role_grant_is_idempotent() -> None:
    r = Role(id="r", name="admin")
    r.grant("property:approve")
    r.grant("property:approve")
    assert r.permission_codes == {"property:approve"}


@pytest.mark.unit
def test_role_grant_requires_code() -> None:
    r = Role(id="r", name="admin")
    with pytest.raises(ValueError):
        r.grant("")


@pytest.mark.unit
def test_role_revoke_removes_code(role: Role) -> None:
    role.revoke("property:create")
    assert not role.has_permission("property:create")


@pytest.mark.unit
def test_role_revoke_missing_is_noop(role: Role) -> None:
    role.revoke("does:not_exist")
    assert role.has_permission("property:create")


@pytest.mark.unit
def test_role_has_permission_false_when_absent(role: Role) -> None:
    assert role.has_permission("user:delete") is False


# --- User -----------------------------------------------------------------


@pytest.mark.unit
def test_user_requires_email() -> None:
    with pytest.raises(ValueError):
        User(id="u", email="", full_name="x")


@pytest.mark.unit
@pytest.mark.parametrize(
    "bad_email",
    ["not-an-email", "missing-domain@", "@missing-local.com", "no@dot", "a b@c.com"],
)
def test_user_rejects_invalid_email(bad_email: str) -> None:
    with pytest.raises(ValueError):
        User(id="u", email=bad_email, full_name="x")


@pytest.mark.unit
def test_user_accepts_valid_email() -> None:
    u = User(id="u", email="jane.doe@listing.co", full_name="Jane")
    assert u.email == "jane.doe@listing.co"


@pytest.mark.unit
def test_user_requires_full_name() -> None:
    with pytest.raises(ValueError):
        User(id="u", email="a@b.com", full_name="")


@pytest.mark.unit
def test_user_defaults() -> None:
    u = User(id="u", email="a@b.com", full_name="Anon")
    assert u.role is None
    assert u.phone is None
    assert u.whatsapp is None
    assert u.password_hash is None
    assert u.is_active is True
    assert u.email_verified is False
    assert u.avatar_url is None


@pytest.mark.unit
def test_user_can_with_role(user: User) -> None:
    assert user.can("property:create") is True


@pytest.mark.unit
def test_user_cannot_when_permission_absent(user: User) -> None:
    assert user.can("property:approve") is False


@pytest.mark.unit
def test_user_cannot_without_role() -> None:
    u = User(id="u", email="a@b.com", full_name="No Role")
    assert u.can("property:create") is False


@pytest.mark.unit
def test_user_cannot_when_inactive(role: Role) -> None:
    u = User(
        id="u",
        email="a@b.com",
        full_name="Inactive",
        role=role,
        is_active=False,
    )
    assert u.can("property:create") is False


@pytest.mark.critical
def test_rbac_grant_revoke_flow() -> None:
    admin_role = Role(id="r-admin", name="admin", is_system=True)
    admin = User(id="u-admin", email="admin@listing.co", full_name="Admin")
    admin.role = admin_role

    assert admin.can(PermissionCode.PROPERTY_APPROVE.value) is False
    admin_role.grant(PermissionCode.PROPERTY_APPROVE.value)
    assert admin.can("property:approve") is True
    admin_role.revoke("property:approve")
    assert admin.can("property:approve") is False
