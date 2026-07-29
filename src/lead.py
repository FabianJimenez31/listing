"""Lead domain logic.

A focused, single-responsibility module modelling a contact lead generated
for a property listing and the lifecycle of its qualification status. Pure
domain layer: dataclasses, enums, validations and transition methods only
(no FastAPI/SQLAlchemy/Pydantic/HTTP/DB).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class LeadStatus(str, Enum):
    """Qualification states a lead can be in.

    ``CLOSED`` and ``DISCARDED`` are terminal: a lead may not transition out
    of them (only to itself). Keep this Enum in sync with persisted database
    values.
    """

    NEW = "new"
    CONTACTED = "contacted"
    NEGOTIATING = "negotiating"
    CLOSED = "closed"
    DISCARDED = "discarded"


class LeadChannel(str, Enum):
    """Channel through which a lead reached the platform."""

    FORM = "form"
    WHATSAPP = "whatsapp"
    CALL = "call"
    VISIT = "visit"


# Channels that legally require explicit consent before a lead is recorded.
_CONSENT_REQUIRED_CHANNELS = frozenset({LeadChannel.FORM, LeadChannel.VISIT})

# Terminal states from which no outbound transition is allowed.
_TERMINAL_STATUSES = frozenset({LeadStatus.CLOSED, LeadStatus.DISCARDED})


@dataclass
class Lead:
    """A single contact lead generated for a property.

    Attributes:
        id: UUID v4 string identifier.
        property_id: FK to the property the lead is about (required).
        name: Name supplied by the prospective contact.
        channel: Channel through which the lead arrived.
        email: Contact email; required if ``phone`` is missing.
        phone: Contact phone; required if ``email`` is missing.
        message: Free-text message from the prospect.
        owner_id: FK to the assigned agent (``User``), if any.
        status: Current qualification status; defaults to ``NEW``.
        consent_given: Whether explicit consent was granted.
        consent_text: Snapshot of the consent wording accepted.
        source_ip: Origin IP captured at submission.
        user_agent: Origin user agent captured at submission.
        utm: UTM tracking parameters.
        contacted_at: Timestamp set when the lead is first contacted.
    """

    id: str
    property_id: str
    name: str
    channel: LeadChannel
    email: str | None = None
    phone: str | None = None
    message: str | None = None
    owner_id: str | None = None
    status: LeadStatus = LeadStatus.NEW
    consent_given: bool = False
    consent_text: str | None = None
    source_ip: str | None = None
    user_agent: str | None = None
    utm: dict = field(default_factory=dict)
    contacted_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.property_id:
            raise ValueError("property_id is required")
        if not self.email and not self.phone:
            raise ValueError("at least one of email or phone is required")
        if self.email and not _EMAIL_RE.match(self.email):
            raise ValueError(f"invalid email: {self.email}")
        if self.channel in _CONSENT_REQUIRED_CHANNELS and not self.consent_given:
            raise ValueError("consent required")

    def _guard_terminal(self) -> None:
        """Raise if the lead is in a terminal state."""
        if self.status in _TERMINAL_STATUSES:
            raise ValueError(f"cannot transition from terminal status: {self.status.value}")

    def mark_contacted(self, when: datetime | None = None) -> None:
        """Transition the lead to ``CONTACTED`` and stamp ``contacted_at``.

        Args:
            when: Timestamp to record; defaults to ``datetime.now(timezone.utc)``.

        Raises:
            ValueError: If the lead is in a terminal status.
        """
        self._guard_terminal()
        self.status = LeadStatus.CONTACTED
        self.contacted_at = when or datetime.now(timezone.utc)

    def mark_negotiating(self) -> None:
        """Transition the lead to ``NEGOTIATING``.

        Raises:
            ValueError: If the lead is in a terminal status.
        """
        self._guard_terminal()
        self.status = LeadStatus.NEGOTIATING

    def close(self) -> None:
        """Transition the lead to ``CLOSED`` (terminal).

        Idempotent when already ``CLOSED``.

        Raises:
            ValueError: If the lead is ``DISCARDED``.
        """
        if self.status == LeadStatus.CLOSED:
            return
        self._guard_terminal()
        self.status = LeadStatus.CLOSED

    def discard(self) -> None:
        """Transition the lead to ``DISCARDED`` (terminal).

        Idempotent when already ``DISCARDED``.

        Raises:
            ValueError: If the lead is ``CLOSED``.
        """
        if self.status == LeadStatus.DISCARDED:
            return
        self._guard_terminal()
        self.status = LeadStatus.DISCARDED
