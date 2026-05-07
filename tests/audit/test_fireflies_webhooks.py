"""L4 #9 Fireflies sales-call + walkthrough webhook tests."""
from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.routers import fireflies as ff_router
from src.audit.state import AuditState, AuditStateFile

SECRET = "ff_test_secret_2026"


@pytest.fixture
def env(tmp_path: Path, monkeypatch):
    clients_dir = tmp_path / "clients"
    events_dir = tmp_path / "_fireflies_events"
    monkeypatch.setenv("FIREFLIES_WEBHOOK_SECRET", SECRET)
    monkeypatch.setenv("GOFREDDY_CLIENTS_DIR", str(clients_dir))
    monkeypatch.setenv("FIREFLIES_EVENTS_DIR", str(events_dir))
    monkeypatch.delenv("SLACK_WEBHOOK_CALLS", raising=False)
    return clients_dir, events_dir


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(ff_router.router)
    return TestClient(app)


def _seed_audit(clients_dir: Path, slug: str = "acme") -> None:
    audit_dir = clients_dir / slug / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    AuditStateFile(path=audit_dir / "state.json").save(
        AuditState(audit_id="aud_test", client_slug=slug, prospect_domain="acme.example")
    )


def _sign(body: bytes, secret: str = SECRET) -> str:
    h = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={h}"


def _payload(transcript_id="tr_001", slug: str | None = "acme",
             transcript: str = "hello world transcript text") -> dict:
    return {
        "transcript_id": transcript_id,
        "metadata": ({"client_slug": slug} if slug else {}),
        "transcript": transcript,
    }


# ─── signature verification ──────────────────────────────────────────


def test_missing_secret_returns_503(client, env, monkeypatch):
    monkeypatch.delenv("FIREFLIES_WEBHOOK_SECRET", raising=False)
    body = json.dumps(_payload()).encode()
    r = client.post("/v1/audit/sales-call-transcript", content=body,
                    headers={"X-Hub-Signature-256": _sign(body)})
    assert r.status_code == 503


def test_invalid_signature_rejected(client, env):
    body = json.dumps(_payload()).encode()
    r = client.post("/v1/audit/sales-call-transcript", content=body,
                    headers={"X-Hub-Signature-256": "sha256=deadbeef"})
    assert r.status_code == 400


def test_malformed_signature_rejected(client, env):
    body = json.dumps(_payload()).encode()
    r = client.post("/v1/audit/sales-call-transcript", content=body,
                    headers={"X-Hub-Signature-256": "no-prefix-hex"})
    assert r.status_code == 400


def test_missing_signature_header_returns_422(client, env):
    body = json.dumps(_payload()).encode()
    r = client.post("/v1/audit/sales-call-transcript", content=body)
    assert r.status_code == 422


# ─── happy paths ─────────────────────────────────────────────────────


def test_sales_call_writes_transcript_to_correct_dir(client, env):
    clients_dir, _ = env
    _seed_audit(clients_dir, "acme")
    body = json.dumps(_payload(transcript_id="tr_sales_1")).encode()
    r = client.post("/v1/audit/sales-call-transcript", content=body,
                    headers={"X-Hub-Signature-256": _sign(body)})
    assert r.status_code == 200, r.text
    payload = r.json()
    assert payload["call_type"] == "sales_call"
    assert payload["slug"] == "acme"
    transcript_path = clients_dir / "acme" / "sales_call" / "transcript.txt"
    assert transcript_path.exists()
    assert transcript_path.read_text() == "hello world transcript text"


def test_walkthrough_call_writes_to_walkthrough_dir(client, env):
    clients_dir, _ = env
    _seed_audit(clients_dir, "acme")
    body = json.dumps(
        _payload(transcript_id="tr_walk_1", transcript="walkthrough text")
    ).encode()
    r = client.post("/v1/audit/walkthrough-call-transcript", content=body,
                    headers={"X-Hub-Signature-256": _sign(body)})
    assert r.status_code == 200, r.text
    assert r.json()["call_type"] == "walkthrough_call"
    transcript_path = clients_dir / "acme" / "walkthrough_call" / "transcript.txt"
    assert transcript_path.exists()
    assert transcript_path.read_text() == "walkthrough text"


def test_meeting_id_used_as_fallback_for_idempotency(client, env):
    clients_dir, events_dir = env
    _seed_audit(clients_dir, "acme")
    body = json.dumps({
        "meeting_id": "mtg_001",  # no transcript_id, falls back to meeting_id
        "metadata": {"client_slug": "acme"},
        "transcript": "x",
    }).encode()
    r = client.post("/v1/audit/sales-call-transcript", content=body,
                    headers={"X-Hub-Signature-256": _sign(body)})
    assert r.status_code == 200
    assert (events_dir / "mtg_001.json").exists()


# ─── idempotency ─────────────────────────────────────────────────────


def test_duplicate_transcript_id_returns_duplicate(client, env):
    clients_dir, _ = env
    _seed_audit(clients_dir, "acme")
    body = json.dumps(_payload(transcript_id="tr_dup")).encode()
    sig = _sign(body)
    r1 = client.post("/v1/audit/sales-call-transcript", content=body,
                     headers={"X-Hub-Signature-256": sig})
    assert r1.json()["status"] == "ok"
    r2 = client.post("/v1/audit/sales-call-transcript", content=body,
                     headers={"X-Hub-Signature-256": sig})
    assert r2.json()["status"] == "duplicate"


# ─── error paths ─────────────────────────────────────────────────────


def test_missing_transcript_id_returns_400(client, env):
    clients_dir, _ = env
    _seed_audit(clients_dir, "acme")
    body = json.dumps({"metadata": {"client_slug": "acme"}, "transcript": "x"}).encode()
    r = client.post("/v1/audit/sales-call-transcript", content=body,
                    headers={"X-Hub-Signature-256": _sign(body)})
    assert r.status_code == 400


def test_missing_client_slug_returns_400(client, env):
    body = json.dumps(_payload(slug=None)).encode()
    r = client.post("/v1/audit/sales-call-transcript", content=body,
                    headers={"X-Hub-Signature-256": _sign(body)})
    assert r.status_code == 400


def test_unknown_slug_returns_404(client, env):
    body = json.dumps(_payload(slug="ghost")).encode()
    r = client.post("/v1/audit/sales-call-transcript", content=body,
                    headers={"X-Hub-Signature-256": _sign(body)})
    assert r.status_code == 404


# ─── slack ping ──────────────────────────────────────────────────────


def test_slack_ping_fires_when_url_set(client, env, monkeypatch):
    clients_dir, _ = env
    _seed_audit(clients_dir, "acme")
    monkeypatch.setenv("SLACK_WEBHOOK_CALLS", "https://hooks.slack.example/calls")
    body = json.dumps(_payload(transcript_id="tr_slack")).encode()
    with patch("src.api.routers.fireflies.httpx.post") as mock_post:
        r = client.post("/v1/audit/sales-call-transcript", content=body,
                        headers={"X-Hub-Signature-256": _sign(body)})
    assert r.status_code == 200
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == "https://hooks.slack.example/calls"
    assert "Sales call" in kwargs["json"]["text"]
    assert "acme" in kwargs["json"]["text"]


def test_slack_ping_skipped_when_no_url(client, env):
    clients_dir, _ = env
    _seed_audit(clients_dir, "acme")
    body = json.dumps(_payload(transcript_id="tr_no_slack")).encode()
    with patch("src.api.routers.fireflies.httpx.post") as mock_post:
        r = client.post("/v1/audit/sales-call-transcript", content=body,
                        headers={"X-Hub-Signature-256": _sign(body)})
    assert r.status_code == 200
    mock_post.assert_not_called()
