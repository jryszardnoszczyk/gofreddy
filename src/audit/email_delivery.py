"""Email delivery via Resend — L4 #7.

One vendor in v1: Resend. Free tier (3K emails/mo), modern API, single
HTTPS POST. Picked over Postmark/SES because (a) no SMTP plumbing,
(b) zero-config domain verification on free tier for outbound testing.

Environment:
- ``RESEND_API_KEY``  — required; ``send_email`` is a no-op without it
- ``EMAIL_FROM``      — defaults to ``Freddy <noreply@gofreddy.ai>``

Failures are logged but never raised — email is best-effort. Callers
receive an empty string when the send didn't fire (missing key, HTTP
error, invalid response).
"""
from __future__ import annotations

import logging
import os
from typing import Iterable

import httpx

RESEND_ENDPOINT = "https://api.resend.com/emails"
DEFAULT_FROM = "Freddy <noreply@gofreddy.ai>"

logger = logging.getLogger(__name__)


def send_email(
    to: str | Iterable[str],
    subject: str,
    html: str,
    *,
    text: str | None = None,
    from_addr: str | None = None,
) -> str:
    """POST to Resend; return email_id on success, empty string otherwise."""
    api_key = os.environ.get("RESEND_API_KEY", "").strip()
    if not api_key:
        logger.info("RESEND_API_KEY unset — skipping email to %s", to)
        return ""

    recipients = [to] if isinstance(to, str) else list(to)
    payload = {
        "from": from_addr or os.environ.get("EMAIL_FROM", DEFAULT_FROM),
        "to": recipients,
        "subject": subject,
        "html": html,
    }
    if text:
        payload["text"] = text

    try:
        response = httpx.post(
            RESEND_ENDPOINT,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=10.0,
        )
        response.raise_for_status()
        body = response.json()
        return str(body.get("id", ""))
    except Exception:
        logger.exception("resend send failed for %s", recipients)
        return ""
