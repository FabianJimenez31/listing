"""Minimal SMTP email sender, configured entirely from environment variables.

Env vars (all optional except SMTP_HOST to actually send):
    SMTP_HOST       SMTP server host. If unset, emails are NOT sent — the
                    message is logged instead (dev/local mode).
    SMTP_PORT       Port (default 587).
    SMTP_USER       Login username (optional; omit for unauthenticated relays).
    SMTP_PASSWORD   Login password.
    SMTP_FROM       From address (defaults to SMTP_USER).
    SMTP_STARTTLS   "true"/"false" — issue STARTTLS (default true).
    SMTP_SSL        "true"/"false" — use implicit TLS / SMTPS (default false).
"""
from __future__ import annotations

import logging
import os
import smtplib
import ssl
from email.message import EmailMessage

logger = logging.getLogger("notifications.email")


def smtp_configured() -> bool:
    """True when an SMTP host is set, i.e. real emails will be sent."""
    return bool(os.getenv("SMTP_HOST"))


def _truthy(name: str, default: str) -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")


def send_email(to: str, subject: str, body: str) -> bool:
    """Send a plain-text email. Returns True if sent via SMTP.

    When SMTP_HOST is not configured the email is logged (so the OTP flow is
    testable in dev) and the function returns False. SMTP failures propagate so
    the caller can surface a 5xx instead of silently swallowing them.
    """
    host = os.getenv("SMTP_HOST")
    if not host:
        logger.warning("SMTP not configured — email to %s not sent.\nSubject: %s\n%s", to, subject, body)
        return False

    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    sender = os.getenv("SMTP_FROM") or user or "no-reply@proppietario.co"

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    context = ssl.create_default_context()
    if _truthy("SMTP_SSL", "false"):
        with smtplib.SMTP_SSL(host, port, timeout=10, context=context) as server:
            if user:
                server.login(user, password)
            server.send_message(msg)
    else:
        with smtplib.SMTP(host, port, timeout=10) as server:
            if _truthy("SMTP_STARTTLS", "true"):
                server.starttls(context=context)
            if user:
                server.login(user, password)
            server.send_message(msg)
    logger.info("OTP email sent to %s", to)
    return True
