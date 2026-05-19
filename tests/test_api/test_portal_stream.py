"""P4 SSE stream endpoint integration tests: GET /v1/portal/{slug}/stream.

Tail-follower behavior (rotation, heartbeat, backlog, infinite tail, etc.)
is unit-tested directly against the generator in
tests/autoresearch/test_tail_events.py. These tests focus on route-level
wiring: auth (cookie or Authorization header — Unit 4 removed the ?token=
URL fallback), membership, response status, headers, content-type, and
that the route hands the correct path to the tailer.

Why no end-to-end "real infinite SSE through httpx" tests:
  httpx.ASGITransport buffers the entire response body before delivering
  the Response object to the client side. An infinite async generator
  (which the real tail_events_sse is, by design) therefore makes
  `client.stream(...).__aenter__` hang forever. We monkeypatch the route's
  tail_events_sse to a finite generator for body-level assertions; that
  proves the route is wiring the tailer correctly without relying on
  ASGITransport behavior the production server doesn't exhibit.

These require local Supabase (auto-skip when not running, per conftest).
"""
from __future__ import annotations

import json
from typing import AsyncIterator

import httpx
import pytest


# --- helpers --------------------------------------------------------------


def _parse_sse_data_line(raw: str) -> dict:
    """Extract the JSON payload from a single SSE `data:` line."""
    assert raw.startswith("data:"), f"not a data line: {raw!r}"
    return json.loads(raw[len("data:"):].strip())


def _make_finite_tail(events: list[dict]) -> tuple:
    """Return (tail_fn, captured) where tail_fn is a drop-in replacement
    for tail_events_sse that yields `events` then stops, and `captured`
    is a dict that records the path it was called with.

    The route imports tail_events_sse at module top so monkeypatch on
    src.api.routers.portal.tail_events_sse replaces it cleanly.
    """
    captured: dict = {}

    async def fake_tail(path, **_kwargs) -> AsyncIterator[str]:
        captured["path"] = path
        for ev in events:
            yield f"data: {json.dumps(ev)}\n\n"

    return fake_tail, captured


# --- auth -----------------------------------------------------------------


@pytest.mark.asyncio
async def test_stream_401_when_no_auth(
    api_client: httpx.AsyncClient, test_tenant: dict
) -> None:
    """No cookie, no Authorization header, no API key → 401.

    Error code is `missing_credentials` (the unified `get_auth_principal`
    surface) rather than the route-specific `missing_token` it used to
    return; Unit 4 retired the SSE-only `_resolve_principal_for_sse`
    helper that emitted the older code.
    """
    r = await api_client.get(f"/v1/portal/{test_tenant['client_slug']}/stream")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "missing_credentials"


@pytest.mark.asyncio
async def test_stream_401_when_bad_jwt(
    api_client: httpx.AsyncClient, test_tenant: dict
) -> None:
    r = await api_client.get(
        f"/v1/portal/{test_tenant['client_slug']}/stream",
        headers={"Authorization": "Bearer not-a-real-jwt"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_stream_403_for_non_member(
    api_client: httpx.AsyncClient, test_tenant: dict, outsider: dict
) -> None:
    """Outsider's JWT is valid but they have no membership on this client."""
    r = await api_client.get(
        f"/v1/portal/{test_tenant['client_slug']}/stream",
        headers={"Authorization": f"Bearer {outsider['token']}"},
    )
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "no_membership"


@pytest.mark.asyncio
async def test_stream_400_on_invalid_slug(
    api_client: httpx.AsyncClient, test_tenant: dict
) -> None:
    """Slug allowlist is alphanumerics + - _ . A '/' or '.' must reject."""
    # A '..' slug shouldn't be reachable to begin with (no such route match
    # given path constraints), so test with a clearly invalid charset.
    r = await api_client.get(
        "/v1/portal/has%20space/stream",
        headers={"Authorization": f"Bearer {test_tenant['token']}"},
    )
    # FastAPI URL-decodes path params; "has space" contains space → invalid_slug.
    assert r.status_code == 400


# --- streaming success (finite-tail mock; see module docstring) -----------


@pytest.mark.asyncio
async def test_stream_returns_sse_headers_and_body_for_member(
    api_client: httpx.AsyncClient, test_tenant: dict, monkeypatch
) -> None:
    """Member sees the route's SSE response: 200, text/event-stream, body
    contains the events the tailer yielded.

    Asserts the wire-up: route delegates to tail_events_sse and frames the
    output as SSE. Tail-follower behavior itself is unit-tested elsewhere.
    """
    fake_tail, captured = _make_finite_tail(
        [
            {"kind": "cost", "cost_usd": 0.42, "client_id": test_tenant["client_slug"]},
            {"kind": "render", "action": "render_judge"},
        ]
    )
    from src.api.routers import portal as portal_mod
    monkeypatch.setattr(portal_mod, "tail_events_sse", fake_tail)

    r = await api_client.get(
        f"/v1/portal/{test_tenant['client_slug']}/stream",
        headers={"Authorization": f"Bearer {test_tenant['token']}"},
    )
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")
    assert r.headers["cache-control"] == "no-cache"
    assert r.headers.get("x-accel-buffering") == "no"

    # Body should contain two SSE `data:` frames, in order.
    data_lines = [
        line for line in r.text.splitlines() if line.startswith("data:")
    ]
    records = [_parse_sse_data_line(line) for line in data_lines]
    assert records == [
        {"kind": "cost", "cost_usd": 0.42, "client_id": test_tenant["client_slug"]},
        {"kind": "render", "action": "render_judge"},
    ]


@pytest.mark.asyncio
async def test_stream_routes_to_correct_per_client_path(
    api_client: httpx.AsyncClient, test_tenant: dict, monkeypatch
) -> None:
    """Route must hand the per-client wide-log path to the tailer.

    `clients/<slug>/audit/events.jsonl` is the contract; a typo here would
    silently break tenant isolation (one client tailing another's log).
    """
    fake_tail, captured = _make_finite_tail([])
    from src.api.routers import portal as portal_mod
    monkeypatch.setattr(portal_mod, "tail_events_sse", fake_tail)

    r = await api_client.get(
        f"/v1/portal/{test_tenant['client_slug']}/stream",
        headers={"Authorization": f"Bearer {test_tenant['token']}"},
    )
    assert r.status_code == 200
    # path is a pathlib.Path; cast to str for the assertion
    assert (
        str(captured["path"])
        == f"clients/{test_tenant['client_slug']}/audit/events.jsonl"
    )


@pytest.mark.asyncio
async def test_stream_accepts_sb_session_cookie_for_eventsource(
    api_client: httpx.AsyncClient, test_tenant: dict, monkeypatch
) -> None:
    """EventSource can't send Authorization headers — the `sb_session`
    cookie (set by POST /v1/auth/cookie) carries the JWT instead. The
    prior `?token=<jwt>` URL fallback was removed in Unit 4 of the
    portal-moments redesign.
    """
    fake_tail, captured = _make_finite_tail(
        [{"kind": "render", "action": "render_judge"}]
    )
    from src.api.routers import portal as portal_mod
    monkeypatch.setattr(portal_mod, "tail_events_sse", fake_tail)

    r = await api_client.get(
        f"/v1/portal/{test_tenant['client_slug']}/stream",
        cookies={"sb_session": test_tenant["token"]},
    )
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")
    data_lines = [
        line for line in r.text.splitlines() if line.startswith("data:")
    ]
    assert len(data_lines) == 1
    assert _parse_sse_data_line(data_lines[0])["kind"] == "render"
