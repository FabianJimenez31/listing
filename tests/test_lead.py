"""Unit tests for the lead module."""
from datetime import datetime

import pytest

from src.lead import Lead, LeadChannel, LeadStatus


@pytest.fixture
def lead() -> Lead:
    return Lead(
        id="a1b2c3",
        property_id="prop-1",
        name="Jane Doe",
        channel=LeadChannel.WHATSAPP,
        phone="+57300000000",
    )


@pytest.fixture
def form_lead() -> Lead:
    return Lead(
        id="a1b2c4",
        property_id="prop-1",
        name="John Doe",
        channel=LeadChannel.FORM,
        email="john@example.com",
        consent_given=True,
        consent_text="I agree",
    )


# --- enum value contract -------------------------------------------------

@pytest.mark.unit
def test_lead_status_values() -> None:
    assert LeadStatus.NEW == "new"
    assert LeadStatus.CONTACTED == "contacted"
    assert LeadStatus.NEGOTIATING == "negotiating"
    assert LeadStatus.CLOSED == "closed"
    assert LeadStatus.DISCARDED == "discarded"


@pytest.mark.unit
def test_lead_channel_values() -> None:
    assert LeadChannel.FORM == "form"
    assert LeadChannel.WHATSAPP == "whatsapp"
    assert LeadChannel.CALL == "call"
    assert LeadChannel.VISIT == "visit"


# --- construction defaults ----------------------------------------------

@pytest.mark.unit
def test_defaults(lead: Lead) -> None:
    assert lead.status == LeadStatus.NEW
    assert lead.consent_given is False
    assert lead.utm == {}
    assert lead.contacted_at is None
    assert lead.owner_id is None


@pytest.mark.unit
def test_utm_is_independent_per_instance() -> None:
    a = Lead(id="1", property_id="p", name="a", channel=LeadChannel.CALL, phone="1")
    b = Lead(id="2", property_id="p", name="b", channel=LeadChannel.CALL, phone="2")
    a.utm["src"] = "google"
    assert b.utm == {}


# --- validations ---------------------------------------------------------

@pytest.mark.unit
def test_requires_property_id() -> None:
    with pytest.raises(ValueError):
        Lead(id="1", property_id="", name="x", channel=LeadChannel.CALL, phone="1")


@pytest.mark.unit
def test_requires_email_or_phone() -> None:
    with pytest.raises(ValueError):
        Lead(id="1", property_id="p", name="x", channel=LeadChannel.CALL)


@pytest.mark.unit
def test_accepts_only_email() -> None:
    lead = Lead(
        id="1", property_id="p", name="x", channel=LeadChannel.CALL,
        email="x@y.com",
    )
    assert lead.email == "x@y.com"


@pytest.mark.unit
def test_accepts_only_phone() -> None:
    lead = Lead(
        id="1", property_id="p", name="x", channel=LeadChannel.CALL, phone="123",
    )
    assert lead.phone == "123"


@pytest.mark.unit
@pytest.mark.parametrize("bad", ["nope", "a@b", "@b.com", "a@.com", "a b@c.com"])
def test_rejects_invalid_email(bad: str) -> None:
    with pytest.raises(ValueError):
        Lead(
            id="1", property_id="p", name="x", channel=LeadChannel.CALL,
            email=bad,
        )


@pytest.mark.unit
@pytest.mark.parametrize("channel", [LeadChannel.FORM, LeadChannel.VISIT])
def test_consent_required_channels(channel: LeadChannel) -> None:
    with pytest.raises(ValueError, match="consent required"):
        Lead(
            id="1", property_id="p", name="x", channel=channel,
            email="x@y.com", consent_given=False,
        )


@pytest.mark.unit
@pytest.mark.parametrize("channel", [LeadChannel.FORM, LeadChannel.VISIT])
def test_consent_given_channels_ok(channel: LeadChannel) -> None:
    lead = Lead(
        id="1", property_id="p", name="x", channel=channel,
        email="x@y.com", consent_given=True,
    )
    assert lead.consent_given is True


@pytest.mark.unit
@pytest.mark.parametrize("channel", [LeadChannel.WHATSAPP, LeadChannel.CALL])
def test_consent_not_required_for_non_form_channels(channel: LeadChannel) -> None:
    lead = Lead(
        id="1", property_id="p", name="x", channel=channel, phone="1",
    )
    assert lead.consent_given is False


# --- transitions ---------------------------------------------------------

@pytest.mark.unit
def test_mark_contacted_sets_timestamp(lead: Lead) -> None:
    lead.mark_contacted()
    assert lead.status == LeadStatus.CONTACTED
    assert isinstance(lead.contacted_at, datetime)


@pytest.mark.unit
def test_mark_contacted_with_explicit_when(lead: Lead) -> None:
    when = datetime(2026, 1, 1, 12, 0, 0)
    lead.mark_contacted(when)
    assert lead.contacted_at == when


@pytest.mark.unit
def test_mark_negotiating(lead: Lead) -> None:
    lead.mark_contacted()
    lead.mark_negotiating()
    assert lead.status == LeadStatus.NEGOTIATING


@pytest.mark.unit
def test_full_happy_path(lead: Lead) -> None:
    lead.mark_contacted()
    lead.mark_negotiating()
    lead.close()
    assert lead.status == LeadStatus.CLOSED


@pytest.mark.unit
def test_close_from_new(lead: Lead) -> None:
    lead.close()
    assert lead.status == LeadStatus.CLOSED


@pytest.mark.unit
def test_discard_from_new(lead: Lead) -> None:
    lead.discard()
    assert lead.status == LeadStatus.DISCARDED


# --- terminal-state guards ----------------------------------------------

@pytest.mark.critical
def test_close_is_idempotent(lead: Lead) -> None:
    lead.close()
    lead.close()  # no raise
    assert lead.status == LeadStatus.CLOSED


@pytest.mark.critical
def test_discard_is_idempotent(lead: Lead) -> None:
    lead.discard()
    lead.discard()  # no raise
    assert lead.status == LeadStatus.DISCARDED


@pytest.mark.critical
def test_cannot_contact_after_close(lead: Lead) -> None:
    lead.close()
    with pytest.raises(ValueError):
        lead.mark_contacted()


@pytest.mark.critical
def test_cannot_negotiate_after_close(lead: Lead) -> None:
    lead.close()
    with pytest.raises(ValueError):
        lead.mark_negotiating()


@pytest.mark.critical
def test_cannot_discard_after_close(lead: Lead) -> None:
    lead.close()
    with pytest.raises(ValueError):
        lead.discard()


@pytest.mark.critical
def test_cannot_contact_after_discard(lead: Lead) -> None:
    lead.discard()
    with pytest.raises(ValueError):
        lead.mark_contacted()


@pytest.mark.critical
def test_cannot_negotiate_after_discard(lead: Lead) -> None:
    lead.discard()
    with pytest.raises(ValueError):
        lead.mark_negotiating()


@pytest.mark.critical
def test_cannot_close_after_discard(lead: Lead) -> None:
    lead.discard()
    with pytest.raises(ValueError):
        lead.close()


@pytest.mark.integration
def test_assigned_owner_and_utm_roundtrip() -> None:
    lead = Lead(
        id="lead-9",
        property_id="prop-9",
        name="Ana",
        channel=LeadChannel.FORM,
        email="ana@example.com",
        consent_given=True,
        consent_text="Acepto",
        owner_id="agent-1",
        source_ip="10.0.0.1",
        user_agent="pytest",
        utm={"utm_source": "google", "utm_medium": "cpc"},
    )
    lead.mark_contacted()
    lead.mark_negotiating()
    lead.close()
    assert lead.owner_id == "agent-1"
    assert lead.utm["utm_source"] == "google"
    assert lead.status == LeadStatus.CLOSED
    assert lead.contacted_at is not None
