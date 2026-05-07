"""Stripe webhook — flips audit `state.status="paid"` when prospect pays.

Verifies Stripe-Signature, dedupes by `event.id` via a flat-file flag,
looks up the workspace by `metadata.client_slug`, mutates state.json,
and optionally pings Slack via `SLACK_WEBHOOK_PAID`.

Per master plan §5.4: webhook does NOT auto-fire Stage 2. JR sees the
Slack ping and runs `freddy audit run <slug>` manually.
"""
from __future__ import annotations

import dataclasses
import hashlib
import hmac
import json
import logging
import os
import time
from pathlib import Path

import httpx
from fastapi import APIRouter, Header, HTTPException, Request, status

router = APIRouter(prefix="/v1/audit/stripe", tags=["stripe"])
logger = logging.getLogger(__name__)

SIG_TOLERANCE_SECONDS = 300


def _verify_signature(payload: bytes, sig_header: str, secret: str) -> None:
    parts = dict(p.split("=", 1) for p in sig_header.split(",") if "=" in p)
    timestamp, v1 = parts.get("t"), parts.get("v1")
    if not timestamp or not v1:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="malformed signature")
    if abs(time.time() - int(timestamp)) > SIG_TOLERANCE_SECONDS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="signature expired")
    signed = f"{timestamp}.".encode() + payload
    expected = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, v1):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="invalid signature")


def _events_dir() -> Path:
    explicit = os.environ.get("STRIPE_EVENTS_DIR")
    if explicit:
        return Path(explicit)
    cd = Path(os.environ.get("GOFREDDY_CLIENTS_DIR", "/data/clients"))
    return cd.parent / "_stripe_events"


def _is_duplicate(event_id: str) -> bool:
    return (_events_dir() / f"{event_id}.json").exists()


def _record_event(event_id: str, event: dict) -> None:
    d = _events_dir()
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{event_id}.json").write_text(json.dumps(event, sort_keys=True), encoding="utf-8")


def _slack_ping(slug: str) -> None:
    url = os.environ.get("SLACK_WEBHOOK_PAID", "").strip()
    if not url:
        return
    try:
        httpx.post(url, json={"text": f"Audit `{slug}` paid — ready to fire Stage 2"}, timeout=5.0)
    except Exception:
        logger.exception("slack ping failed for %s", slug)


@router.post("/webhook", status_code=200)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(..., alias="Stripe-Signature"),
) -> dict:
    secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    if not secret:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="webhook secret not configured")

    body = await request.body()
    _verify_signature(body, stripe_signature, secret)

    event = json.loads(body)
    event_id = event.get("id", "")
    event_type = event.get("type", "")
    if not event_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="missing event id")

    if _is_duplicate(event_id):
        return {"status": "duplicate", "event_id": event_id}

    if event_type != "checkout.session.completed":
        _record_event(event_id, event)
        return {"status": "ignored", "event_id": event_id, "type": event_type}

    metadata = (event.get("data", {}).get("object", {}) or {}).get("metadata") or {}
    slug = metadata.get("client_slug")
    if not slug:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="missing metadata.client_slug")

    clients_dir = Path(os.environ.get("GOFREDDY_CLIENTS_DIR", "/data/clients"))
    state_path = clients_dir / slug / "audit" / "state.json"
    if not state_path.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"no audit workspace for slug={slug}")

    from src.audit.state import AuditStateFile
    AuditStateFile(path=state_path).mutate(lambda s: dataclasses.replace(s, status="paid"))

    _record_event(event_id, event)
    _slack_ping(slug)
    return {"status": "ok", "event_id": event_id, "slug": slug}
