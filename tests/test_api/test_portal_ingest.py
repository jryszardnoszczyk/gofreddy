"""P3 ingest endpoint tests: POST /v1/portal/_ingest.

Operator-side endpoint for Claude Code hooks / Codex wrappers / etc. to
post canonical events. Auth is shared-secret bearer (GOFREDDY_INGEST_TOKEN),
NOT Supabase JWT — distinct from the rest of the portal API.

These are integration tests (require live Supabase to boot the app) but the
endpoint itself doesn't touch Supabase. The endpoint:
  - 503 when GOFREDDY_INGEST_TOKEN env var unset
  - 401 when bearer missing or doesn't match
  - 400 on schema violations (missing kind / source / unknown kind no x- prefix)
  - 200 on success, returns {event_id, kind, path}
  - Writes the event to client_events_path(client_id) per the canonical schema
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import httpx
import pytest


@pytest.mark.asyncio
async def test_ingest_503_when_token_unset(
    api_client: httpx.AsyncClient, monkeypatch
) -> None:
    monkeypatch.delenv("GOFREDDY_INGEST_TOKEN", raising=False)
    r = await api_client.post(
        "/v1/portal/_ingest",
        json={"kind": "tool_call", "source": "claude_code"},
    )
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "ingest_disabled"


@pytest.mark.asyncio
async def test_ingest_401_when_bearer_missing(
    api_client: httpx.AsyncClient, monkeypatch
) -> None:
    monkeypatch.setenv("GOFREDDY_INGEST_TOKEN", "test-secret-xyz")
    r = await api_client.post(
        "/v1/portal/_ingest",
        json={"kind": "tool_call", "source": "claude_code"},
    )
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "missing_bearer"


@pytest.mark.asyncio
async def test_ingest_401_when_bearer_wrong(
    api_client: httpx.AsyncClient, monkeypatch
) -> None:
    monkeypatch.setenv("GOFREDDY_INGEST_TOKEN", "test-secret-xyz")
    r = await api_client.post(
        "/v1/portal/_ingest",
        json={"kind": "tool_call", "source": "claude_code"},
        headers={"Authorization": "Bearer wrong-secret"},
    )
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "bad_token"


@pytest.mark.asyncio
async def test_ingest_400_missing_kind(
    api_client: httpx.AsyncClient, monkeypatch
) -> None:
    monkeypatch.setenv("GOFREDDY_INGEST_TOKEN", "test-secret-xyz")
    r = await api_client.post(
        "/v1/portal/_ingest",
        json={"source": "claude_code"},
        headers={"Authorization": "Bearer test-secret-xyz"},
    )
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "missing_kind"


@pytest.mark.asyncio
async def test_ingest_400_unknown_kind_without_x_prefix(
    api_client: httpx.AsyncClient, monkeypatch
) -> None:
    monkeypatch.setenv("GOFREDDY_INGEST_TOKEN", "test-secret-xyz")
    r = await api_client.post(
        "/v1/portal/_ingest",
        json={"kind": "made_up_kind", "source": "claude_code"},
        headers={"Authorization": "Bearer test-secret-xyz"},
    )
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "unknown_kind"


@pytest.mark.asyncio
async def test_ingest_accepts_x_prefix_kind(
    api_client: httpx.AsyncClient, monkeypatch, tmp_path
) -> None:
    """The 'x-' prefix is the documented escape hatch for source-specific
    event kinds that haven't been promoted to KNOWN_KINDS yet."""
    monkeypatch.setenv("GOFREDDY_INGEST_TOKEN", "test-secret-xyz")
    # Redirect operator-internal log to tmp
    import autoresearch.events as events
    monkeypatch.setattr(events, "EVENTS_LOG", tmp_path / "events.jsonl")
    r = await api_client.post(
        "/v1/portal/_ingest",
        json={"kind": "x-claude-thinking", "source": "claude_code", "action": "extended_thinking"},
        headers={"Authorization": "Bearer test-secret-xyz"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["kind"] == "x-claude-thinking"
    assert "event_id" in body


@pytest.mark.asyncio
async def test_ingest_writes_to_operator_internal_when_no_client_id(
    api_client: httpx.AsyncClient, monkeypatch, tmp_path
) -> None:
    """No client_id → event lands at operator-internal EVENTS_LOG."""
    monkeypatch.setenv("GOFREDDY_INGEST_TOKEN", "test-secret-xyz")
    import autoresearch.events as events
    monkeypatch.setattr(events, "EVENTS_LOG", tmp_path / "events.jsonl")
    r = await api_client.post(
        "/v1/portal/_ingest",
        json={
            "kind": "tool_call",
            "source": "claude_code",
            "action": "Read",
            "session_id": "session-xyz",
        },
        headers={"Authorization": "Bearer test-secret-xyz"},
    )
    assert r.status_code == 200
    log_path = tmp_path / "events.jsonl"
    assert log_path.exists()
    payload = json.loads(log_path.read_text().splitlines()[0])
    assert payload["kind"] == "tool_call"
    assert payload["source"] == "claude_code"
    assert payload["action"] == "Read"
    assert payload["session_id"] == "session-xyz"
    assert "event_id" in payload
    assert "timestamp" in payload


@pytest.mark.asyncio
async def test_ingest_writes_to_per_client_path_with_client_id(
    api_client: httpx.AsyncClient, monkeypatch, tmp_path
) -> None:
    """client_id supplied → event lands at clients/<slug>/audit/events.jsonl."""
    monkeypatch.setenv("GOFREDDY_INGEST_TOKEN", "test-secret-xyz")
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        r = await api_client.post(
            "/v1/portal/_ingest",
            json={
                "kind": "edit",
                "source": "claude_code",
                "client_id": "klinika-melitus",
                "action": "Edit",
                "session_id": "session-xyz",
            },
            headers={"Authorization": "Bearer test-secret-xyz"},
        )
    finally:
        os.chdir(old_cwd)
    assert r.status_code == 200
    per_client = tmp_path / "clients/klinika-melitus/audit/events.jsonl"
    assert per_client.exists()
    payload = json.loads(per_client.read_text().splitlines()[0])
    assert payload["kind"] == "edit"
    assert payload["client_id"] == "klinika-melitus"
