"""User and RBAC domain logic.

A focused, single-responsibility module that models the access-control
layer of the Listing system: the ``PermissionCode`` catalog, ``Role``
aggregates of permission codes, and ``User`` accounts that delegate
authorization decisions to their assigned role.

Domain layer only: dataclasses, enums, validations and domain methods.
No FastAPI / SQLAlchemy / Pydantic / HTTP / DB dependencies.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class PermissionCode(str, Enum):
    """Canonical ``resource:action`` permission codes.

    Member values match the contract verbatim. Authorization throughout
    the domain is expressed in terms of these codes (stored as plain
    strings on a :class:`Role`).
    """

    PROPERTY_READ_PUBLIC = "property:read_public"
    PROPERTY_READ_ANY = "property:read_any"
    PROPERTY_CREATE = "property:create"
    PROPERTY_UPDATE_OWN = "property:update_own"
    PROPERTY_UPDATE_ANY = "property:update_any"
    PROPERTY_DELETE_OWN = "property:delete_own"
    PROPERTY_DELETE_ANY = "property:delete_any"
    PROPERTY_PAUSE_OWN = "property:pause_own"
    PROPERTY_PUBLISH_REQUEST = "property:publish_request"
    PROPERTY_APPROVE = "property:approve"
    PROPERTY_REJECT = "property:reject"
    PROPERTY_FEATURE = "property:feature"
    IMAGE_UPLOAD_OWN = "image:upload_own"
    IMAGE_MANAGE_ANY = "image:manage_any"
    LEAD_READ_OWN = "lead:read_own"
    LEAD_READ_ANY = "lead:read_any"
    LEAD_UPDATE_STATUS = "lead:update_status"
    LEAD_ASSIGN = "lead:assign"
    FAVORITE_MANAGE_OWN = "favorite:manage_own"
    USER_READ = "user:read"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    ROLE_ASSIGN = "role:assign"
    PERMISSION_MANAGE = "permission:manage"
    BANNER_MANAGE = "banner:manage"
    FEATURED_MANAGE = "featured:manage"
    LOCATION_MANAGE = "location:manage"
    PROPERTY_TYPE_MANAGE = "property_type:manage"
    AMENITY_MANAGE = "amenity:manage"
    METRICS_READ_OWN = "metrics:read_own"
    METRICS_READ_GLOBAL = "metrics:read_global"
    AUDIT_READ = "audit:read"
    SEO_MANAGE = "seo:manage"
    CONFIG_MANAGE = "config:manage"


@dataclass
class Role:
    """A named bundle of permission codes assigned to users.

    Attributes:
        id: UUID v4 string primary key.
        name: Unique role name (e.g. ``"agent"``). Required.
        description: Optional human-readable description.
        permission_codes: Set of ``resource:action`` codes granted.
        is_system: Whether this is a seeded, non-deletable system role.
    """

    id: str
    name: str
    description: str | None = None
    permission_codes: set[str] = field(default_factory=set)
    is_system: bool = False

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name is required")

    def grant(self, code: str) -> None:
        """Add a permission code to this role.

        Granting a code that is already present is a no-op.
        """
        if not code:
            raise ValueError("code is required")
        self.permission_codes.add(code)

    def revoke(self, code: str) -> None:
        """Remove a permission code from this role.

        Revoking a code that is not present is a no-op.
        """
        self.permission_codes.discard(code)

    def has_permission(self, code: str) -> bool:
        """Return whether this role grants the given permission code."""
        return code in self.permission_codes


@dataclass
class User:
    """An account in the Listing system.

    Attributes:
        id: UUID v4 string primary key.
        email: Unique login email. Required and format-validated.
        full_name: Display name. Required.
        role: Assigned :class:`Role`, or ``None`` for an unassigned user.
        phone: Optional contact phone.
        whatsapp: Optional WhatsApp contact number.
        password_hash: Optional stored password hash.
        is_active: Whether the account may act (inactive denies all).
        email_verified: Whether the email has been verified.
        avatar_url: Optional avatar image URL.
    """

    id: str
    email: str
    full_name: str
    role: Role | None = None
    phone: str | None = None
    whatsapp: str | None = None
    password_hash: str | None = None
    is_active: bool = True
    email_verified: bool = False
    avatar_url: str | None = None

    def __post_init__(self) -> None:
        if not self.email:
            raise ValueError("email is required")
        if not _EMAIL_RE.match(self.email):
            raise ValueError(f"invalid email: {self.email}")
        if not self.full_name:
            raise ValueError("full_name is required")

    def can(self, code: str) -> bool:
        """Return whether the user is allowed to perform ``code``.

        An inactive user, or one without an assigned role, can do
        nothing. Otherwise the decision is delegated to the role.
        """
        if not self.is_active or self.role is None:
            return False
        return self.role.has_permission(code)
