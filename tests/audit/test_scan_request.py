"""L4 #6 free scan handler tests.

Standalone — minimal FastAPI app with just the scan router. The scan
worker is a v1 placeholder; tests assert it runs synchronously via
TestClient (FastAPI fires BackgroundTasks before returning).
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.routers import scan as scan_router


@pytest.fixture
def env(tmp_path: Path, monkeypatch):
    scans_dir = tmp_path / "_scans"
    monkeypatch.setenv("GOFREDDY_SCANS_DIR", str(scans_dir))
    monkeypatch.setenv("SCAN_PUBLIC_BASE_URL", "https://reports.test.example/scan")
    monkeypatch.delenv("SLACK_WEBHOOK_LEADS", raising=False)
    return scans_dir


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(scan_router.router)
    return TestClient(app)


# ─── input validation ────────────────────────────────────────────────


def test_scan_request_missing_url_returns_422(client, env):
    r = client.post("/v1/scan/request", json={"email": "p@example.com"})
    assert r.status_code == 422


def test_scan_request_missing_email_returns_422(client, env):
    r = client.post("/v1/scan/request", json={"url": "https://example.com"})
    assert r.status_code == 422


def test_scan_request_invalid_email_returns_422(client, env):
    r = client.post(
        "/v1/scan/request",
        json={"url": "https://example.com", "email": "not-an-email"},
    )
    assert r.status_code == 422


def test_scan_request_invalid_url_returns_422(client, env):
    r = client.post(
        "/v1/scan/request",
        json={"url": "not-a-url", "email": "p@example.com"},
    )
    assert r.status_code == 422


# ─── happy path ──────────────────────────────────────────────────────


def test_scan_request_returns_202_with_tracking_url(client, env):
    r = client.post(
        "/v1/scan/request",
        json={"url": "https://acme.example", "email": "buyer@acme.example",
              "vertical": "saas", "geo": "us-east"},
    )
    assert r.status_code == 202, r.text
    payload = r.json()
    assert payload["scan_id"]
    assert payload["tracking_url"].startswith("https://reports.test.example/scan/")
    assert payload["scan_id"] in payload["tracking_url"]


def test_scan_request_persists_state_file(client, env):
    scans_dir = env
    r = client.post(
        "/v1/scan/request",
        json={"url": "https://acme.example", "email": "buyer@acme.example",
              "vertical": "saas", "segment": "smb"},
    )
    assert r.status_code == 202
    scan_id = r.json()["scan_id"]
    state_path = scans_dir / scan_id / "state.json"
    assert state_path.exists()
    state = json.loads(state_path.read_text())
    assert state["url"].rstrip("/") == "https://acme.example"
    assert state["email"] == "buyer@acme.example"
    assert state["firmographics"] == {"vertical": "saas", "segment": "smb"}
    # Background task fires synchronously during TestClient response
    assert state["scan_status"] == "delivered"


def test_scan_request_writes_synthesis_md(client, env):
    scans_dir = env
    r = client.post(
        "/v1/scan/request",
        json={"url": "https://acme.example", "email": "buyer@acme.example"},
    )
    scan_id = r.json()["scan_id"]
    synthesis_path = scans_dir / scan_id / "synthesis.md"
    assert synthesis_path.exists()
    content = synthesis_path.read_text()
    assert "AI Visibility Scan" in content
    assert "acme.example" in content


# ─── status lookup ───────────────────────────────────────────────────


def test_scan_status_returns_404_for_unknown_id(client, env):
    r = client.get("/v1/scan/scan_unknown")
    assert r.status_code == 404


def test_scan_status_returns_state(client, env):
    r1 = client.post(
        "/v1/scan/request",
        json={"url": "https://acme.example", "email": "buyer@acme.example"},
    )
    scan_id = r1.json()["scan_id"]
    r2 = client.get(f"/v1/scan/{scan_id}")
    assert r2.status_code == 200
    payload = r2.json()
    assert payload["scan_id"] == scan_id
    assert payload["status"] == "delivered"


# ─── slack lead ping ─────────────────────────────────────────────────


def test_slack_lead_ping_fires_when_webhook_url_set(client, env, monkeypatch):
    monkeypatch.setenv("SLACK_WEBHOOK_LEADS", "https://hooks.slack.example/leads")
    with patch("src.api.routers.scan.httpx.post") as mock_post:
        r = client.post(
            "/v1/scan/request",
            json={"url": "https://acme.example", "email": "buyer@acme.example"},
        )
    assert r.status_code == 202
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == "https://hooks.slack.example/leads"
    assert "acme.example" in kwargs["json"]["text"]
    assert "buyer@acme.example" in kwargs["json"]["text"]


def test_slack_lead_ping_skipped_when_no_url(client, env):
    with patch("src.api.routers.scan.httpx.post") as mock_post:
        r = client.post(
            "/v1/scan/request",
            json={"url": "https://acme.example", "email": "buyer@acme.example"},
        )
    assert r.status_code == 202
    mock_post.assert_not_called()


# ─── worker error path ───────────────────────────────────────────────


def test_scan_worker_marks_failed_on_exception(env, monkeypatch):
    """If the synthesis worker raises mid-flight, state flips to 'failed'."""
    scans_dir = env
    # Seed a running state directly, then invoke _run_scan with synthesis
    # forced to raise. Verifies the worker's exception handler updates state.
    state = scan_router.ScanState(
        scan_id="scan_fail_test",
        url="https://acme.example",
        email="buyer@acme.example",
        firmographics={},
        scan_status="running",
        created_at="2026-05-07T00:00:00+00:00",
    )
    scan_router._save_state(state)

    real_write = Path.write_text

    def selective_boom(self, *args, **kwargs):
        if self.name == "synthesis.md":
            raise RuntimeError("simulated synthesis crash")
        return real_write(self, *args, **kwargs)

    with patch.object(Path, "write_text", selective_boom):
        scan_router._run_scan("scan_fail_test")

    final = json.loads((scans_dir / "scan_fail_test" / "state.json").read_text())
    assert final["scan_status"] == "failed"
    assert "simulated synthesis crash" in final["error"]
