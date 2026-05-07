"""L4 #5 Stripe webhook handler tests.

Standalone — no DB / Supabase dependency. Spins up a minimal FastAPI
app with just the stripe router so the tests run on any machine.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.routers import stripe as stripe_router
from src.audit.state import AuditState, AuditStateFile

WEBHOOK_SECRET = "whsec_test_2026"


@pytest.fixture
def env(tmp_path: Path, monkeypatch):
    clients_dir = tmp_path / "clients"
    events_dir = tmp_path / "_stripe_events"
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WEBHOOK_SECRET)
    monkeypatch.setenv("GOFREDDY_CLIENTS_DIR", str(clients_dir))
    monkeypatch.setenv("STRIPE_EVENTS_DIR", str(events_dir))
    monkeypatch.delenv("SLACK_WEBHOOK_PAID", raising=False)
    return clients_dir, events_dir


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(stripe_router.router)
    return TestClient(app)


def _seed_audit(clients_dir: Path, slug: str = "acme") -> Path:
    audit_dir = clients_dir / slug / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    sf = AuditStateFile(path=audit_dir / "state.json")
    sf.save(AuditState(audit_id="aud_test01", client_slug=slug, prospect_domain="acme.example",
                       status="brief_confirmed"))
    return audit_dir


def _sign(body: bytes, ts: int | None = None, secret: str = WEBHOOK_SECRET) -> str:
    ts = ts if ts is not None else int(time.time())
    signed = f"{ts}.".encode() + body
    sig = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return f"t={ts},v1={sig}"


def _event(event_id: str = "evt_1", event_type: str = "checkout.session.completed",
           slug: str | None = "acme") -> dict:
    return {
        "id": event_id, "type": event_type,
        "data": {"object": {"metadata": ({"client_slug": slug} if slug else {})}},
    }


# ─── signature verification ──────────────────────────────────────────


def test_missing_secret_returns_503(client, env, monkeypatch):
    monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)
    body = json.dumps(_event()).encode()
    r = client.post("/v1/audit/stripe/webhook", content=body,
                    headers={"Stripe-Signature": _sign(body)})
    assert r.status_code == 503


def test_invalid_signature_rejected(client, env):
    body = json.dumps(_event()).encode()
    r = client.post("/v1/audit/stripe/webhook", content=body,
                    headers={"Stripe-Signature": "t=1,v1=deadbeef"})
    assert r.status_code == 400


def test_expired_signature_rejected(client, env):
    body = json.dumps(_event()).encode()
    old_ts = int(time.time()) - 600  # 10 min stale, > 5 min tolerance
    r = client.post("/v1/audit/stripe/webhook", content=body,
                    headers={"Stripe-Signature": _sign(body, ts=old_ts)})
    assert r.status_code == 400


def test_malformed_signature_rejected(client, env):
    body = json.dumps(_event()).encode()
    r = client.post("/v1/audit/stripe/webhook", content=body,
                    headers={"Stripe-Signature": "garbage-no-equals"})
    assert r.status_code == 400


# ─── happy path ──────────────────────────────────────────────────────


def test_valid_webhook_flips_state_to_paid(client, env):
    clients_dir, events_dir = env
    _seed_audit(clients_dir, "acme")
    body = json.dumps(_event(event_id="evt_happy")).encode()
    r = client.post("/v1/audit/stripe/webhook", content=body,
                    headers={"Stripe-Signature": _sign(body)})
    assert r.status_code == 200, r.text
    payload = r.json()
    assert payload["status"] == "ok"
    assert payload["slug"] == "acme"
    state = json.loads((clients_dir / "acme" / "audit" / "state.json").read_text())
    assert state["status"] == "paid"
    assert (events_dir / "evt_happy.json").exists()


# ─── idempotency ─────────────────────────────────────────────────────


def test_duplicate_event_returns_duplicate_status(client, env):
    clients_dir, events_dir = env
    _seed_audit(clients_dir, "acme")
    body = json.dumps(_event(event_id="evt_dup")).encode()
    sig = _sign(body)

    r1 = client.post("/v1/audit/stripe/webhook", content=body, headers={"Stripe-Signature": sig})
    assert r1.status_code == 200
    assert r1.json()["status"] == "ok"

    r2 = client.post("/v1/audit/stripe/webhook", content=body, headers={"Stripe-Signature": sig})
    assert r2.status_code == 200
    assert r2.json()["status"] == "duplicate"


# ─── error paths ─────────────────────────────────────────────────────


def test_missing_metadata_client_slug_returns_400(client, env):
    clients_dir, _ = env
    _seed_audit(clients_dir, "acme")  # workspace exists, but webhook lacks metadata
    body = json.dumps(_event(event_id="evt_no_slug", slug=None)).encode()
    r = client.post("/v1/audit/stripe/webhook", content=body,
                    headers={"Stripe-Signature": _sign(body)})
    assert r.status_code == 400


def test_unknown_slug_returns_404(client, env):
    body = json.dumps(_event(event_id="evt_no_workspace", slug="ghost")).encode()
    r = client.post("/v1/audit/stripe/webhook", content=body,
                    headers={"Stripe-Signature": _sign(body)})
    assert r.status_code == 404


def test_ignored_event_type_acknowledged_without_state_change(client, env):
    clients_dir, events_dir = env
    _seed_audit(clients_dir, "acme")
    body = json.dumps(_event(event_id="evt_other", event_type="customer.created")).encode()
    r = client.post("/v1/audit/stripe/webhook", content=body,
                    headers={"Stripe-Signature": _sign(body)})
    assert r.status_code == 200
    assert r.json()["status"] == "ignored"
    state = json.loads((clients_dir / "acme" / "audit" / "state.json").read_text())
    assert state["status"] == "brief_confirmed"  # unchanged
    assert (events_dir / "evt_other.json").exists()


# ─── slack ping (optional) ───────────────────────────────────────────


def test_slack_ping_fires_when_webhook_url_set(client, env, monkeypatch):
    clients_dir, _ = env
    _seed_audit(clients_dir, "acme")
    monkeypatch.setenv("SLACK_WEBHOOK_PAID", "https://hooks.slack.example/test")
    body = json.dumps(_event(event_id="evt_slack")).encode()
    with patch("src.api.routers.stripe.httpx.post") as mock_post:
        r = client.post("/v1/audit/stripe/webhook", content=body,
                        headers={"Stripe-Signature": _sign(body)})
    assert r.status_code == 200
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == "https://hooks.slack.example/test"
    assert "acme" in kwargs["json"]["text"]


def test_slack_ping_silently_skipped_when_no_url(client, env):
    clients_dir, _ = env
    _seed_audit(clients_dir, "acme")
    body = json.dumps(_event(event_id="evt_no_slack")).encode()
    with patch("src.api.routers.stripe.httpx.post") as mock_post:
        r = client.post("/v1/audit/stripe/webhook", content=body,
                        headers={"Stripe-Signature": _sign(body)})
    assert r.status_code == 200
    mock_post.assert_not_called()
