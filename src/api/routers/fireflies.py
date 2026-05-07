"""Fireflies two-call webhooks — L4 #9 sales + walkthrough capture.

Two endpoints share an HMAC-SHA256 verifier (GitHub-style
``X-Hub-Signature-256: sha256=<hex>``), filesystem-flag idempotency
keyed by ``transcript_id``, and slug-routed transcript writes to
``clients/<slug>/{sales_call,walkthrough_call}/transcript.txt``.

Sonnet-driven fit-signal extraction (master plan §5.3 step 3) is
deferred — lands when the sales/walkthrough extraction prompts are
written. v1 webhook just persists the raw transcript and pings Slack.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
from pathlib import Path
from typing import Literal

import httpx
from fastapi import APIRouter, Header, HTTPException, Request, status

router = APIRouter(prefix="/v1/audit", tags=["fireflies"])
logger = logging.getLogger(__name__)

CallType = Literal["sales_call", "walkthrough_call"]


def _verify_signature(payload: bytes, sig: str, secret: str) -> None:
    if not sig or not sig.startswith("sha256="):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="malformed signature")
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    received = sig.removeprefix("sha256=")
    if not hmac.compare_digest(expected, received):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="invalid signature")


def _events_dir() -> Path:
    explicit = os.environ.get("FIREFLIES_EVENTS_DIR")
    if explicit:
        return Path(explicit)
    cd = Path(os.environ.get("GOFREDDY_CLIENTS_DIR", "/data/clients"))
    return cd.parent / "_fireflies_events"


def _is_duplicate(transcript_id: str) -> bool:
    return (_events_dir() / f"{transcript_id}.json").exists()


def _record_event(transcript_id: str, event: dict) -> None:
    d = _events_dir()
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{transcript_id}.json").write_text(json.dumps(event, sort_keys=True), encoding="utf-8")


def _slack_ping(call_type: CallType, slug: str) -> None:
    url = os.environ.get("SLACK_WEBHOOK_CALLS", "").strip()
    if not url:
        return
    label = "Sales call" if call_type == "sales_call" else "Walkthrough call"
    try:
        httpx.post(
            url, json={"text": f"{label} transcript captured for `{slug}`"}, timeout=5.0
        )
    except Exception:
        logger.exception("slack ping failed for %s/%s", slug, call_type)


async def _handle(
    request: Request, sig: str, *, call_type: CallType
) -> dict:
    secret = os.environ.get("FIREFLIES_WEBHOOK_SECRET", "")
    if not secret:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, detail="webhook secret not configured"
        )
    body = await request.body()
    _verify_signature(body, sig, secret)

    event = json.loads(body)
    transcript_id = event.get("transcript_id") or event.get("meeting_id") or ""
    if not transcript_id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="missing transcript_id (or meeting_id)"
        )

    if _is_duplicate(transcript_id):
        return {"status": "duplicate", "transcript_id": transcript_id}

    slug = (event.get("metadata") or {}).get("client_slug")
    if not slug:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="missing metadata.client_slug"
        )

    clients_dir = Path(os.environ.get("GOFREDDY_CLIENTS_DIR", "/data/clients"))
    audit_dir = clients_dir / slug / "audit"
    if not (audit_dir / "state.json").exists():
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail=f"no audit workspace for slug={slug}"
        )

    transcript_text = event.get("transcript") or event.get("transcript_text") or ""
    call_dir = clients_dir / slug / call_type
    call_dir.mkdir(parents=True, exist_ok=True)
    (call_dir / "transcript.txt").write_text(transcript_text, encoding="utf-8")

    _record_event(transcript_id, event)
    _slack_ping(call_type, slug)
    return {
        "status": "ok",
        "transcript_id": transcript_id,
        "slug": slug,
        "call_type": call_type,
    }


@router.post("/sales-call-transcript", status_code=200)
async def sales_call_transcript(
    request: Request,
    x_hub_signature_256: str = Header(..., alias="X-Hub-Signature-256"),
) -> dict:
    return await _handle(request, x_hub_signature_256, call_type="sales_call")


@router.post("/walkthrough-call-transcript", status_code=200)
async def walkthrough_call_transcript(
    request: Request,
    x_hub_signature_256: str = Header(..., alias="X-Hub-Signature-256"),
) -> dict:
    return await _handle(request, x_hub_signature_256, call_type="walkthrough_call")
