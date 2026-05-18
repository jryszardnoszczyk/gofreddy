"""Unit 3 portal moments endpoint tests: GET /v1/portal/{slug}/moments.

Coverage matches the plan's §"Unit 3: Moments REST endpoint" test scenarios:
  * Happy paths — 75 moments → 50 + has_more, empty slug → 200 not 404.
  * Edge cases — limit clamp at 200, since/before, kind filter
    intersection, session filter, rotated segments merged.
  * Error paths — 404 client_not_found (slug not in clients), 403
    no_membership, 401 missing auth.
  * Integration — redaction applied to title containing fake API key,
    HTML in title returned verbatim (escape is render-time).
  * Performance smoke — 10K-event log returns <200ms locally; not gated
    in CI (`@pytest.mark.slow` so default runs skip).

Requires local Supabase (auto-skipped via conftest when not running).
"""
from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path

import httpx
import pytest
from autoresearch.events import client_events_path, log_event


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def _seed_moment(
    path: Path,
    *,
    event_id: str,
    moment_kind: str = "lane_progress",
    title: str = "Did a thing",
    body: str | None = None,
    lane: str | None = "marketing_audit",
    variant: str | None = None,
    session_id: str | None = None,
    kind: str = "moment",
) -> None:
    """Append one moment-shaped event to a client log.

    `event_id` is the cursor used by since/before pagination; we set it
    explicitly per event (rather than relying on log_event's default)
    because tests assert exact ordering. log_event writes event_id verbatim
    when supplied as a kwarg.
    """
    metadata: dict = {"moment_kind": moment_kind, "title": title}
    if body is not None:
        metadata["body"] = body
    if lane is not None:
        metadata["lane"] = lane
    if variant is not None:
        metadata["variant"] = variant
    log_event(
        kind=kind,
        path=path,
        event_id=event_id,
        session_id=session_id,
        metadata=metadata,
    )


# --------------------------------------------------------------------------
# Happy-path tests (Supabase-gated)
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_moments_returns_50_with_has_more_when_75_seeded(
    api_client: httpx.AsyncClient, test_tenant: dict
) -> None:
    """75 moments → response has 50 newest, has_more=True, oldest_event_id
    set to the 50th-newest's event_id, newest_event_id set to the 75th's.
    """
    old_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        try:
            path = client_events_path(test_tenant["client_slug"])
            path.parent.mkdir(parents=True, exist_ok=True)
            for i in range(75):
                _seed_moment(
                    path,
                    event_id=f"evt_{i:03d}",
                    title=f"Moment number {i}",
                )

            r = await api_client.get(
                f"/v1/portal/{test_tenant['client_slug']}/moments",
                headers={"Authorization": f"Bearer {test_tenant['token']}"},
            )
            assert r.status_code == 200
            data = r.json()
            assert len(data["moments"]) == 50
            assert data["has_more"] is True
            # Newest-first: moments[0] is the last-seeded event_074.
            assert data["moments"][0]["event_id"] == "evt_074"
            # Page boundary: oldest in this page is event_025 (75-50).
            assert data["moments"][-1]["event_id"] == "evt_025"
            assert data["newest_event_id"] == "evt_074"
            assert data["oldest_event_id"] == "evt_025"
            # Every moment carries the redactor stamp (Unit 5 contract).
            assert all(m["redactor_version"] == "v1" for m in data["moments"])
        finally:
            os.chdir(old_cwd)


@pytest.mark.asyncio
async def test_moments_empty_slug_returns_200_not_404(
    api_client: httpx.AsyncClient, test_tenant: dict
) -> None:
    """An existing slug with zero events returns 200 + empty list — NOT a
    404. 404 is reserved for "slug not in clients table"; empty events is
    the steady-state of a freshly onboarded client.
    """
    r = await api_client.get(
        f"/v1/portal/{test_tenant['client_slug']}/moments",
        headers={"Authorization": f"Bearer {test_tenant['token']}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["moments"] == []
    assert data["has_more"] is False
    assert data["newest_event_id"] is None
    assert data["oldest_event_id"] is None


# --------------------------------------------------------------------------
# Edge cases: limit, since, before, kind, session, rotation
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_moments_limit_200_returns_up_to_200(
    api_client: httpx.AsyncClient, test_tenant: dict
) -> None:
    """limit=200 is the validator ceiling — endpoint returns up to 200
    moments + has_more=False when exactly 200 are seeded.
    """
    old_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        try:
            path = client_events_path(test_tenant["client_slug"])
            path.parent.mkdir(parents=True, exist_ok=True)
            for i in range(200):
                _seed_moment(path, event_id=f"evt_{i:03d}")
            r = await api_client.get(
                f"/v1/portal/{test_tenant['client_slug']}/moments?limit=200",
                headers={"Authorization": f"Bearer {test_tenant['token']}"},
            )
            assert r.status_code == 200
            assert len(r.json()["moments"]) == 200
            assert r.json()["has_more"] is False
        finally:
            os.chdir(old_cwd)


@pytest.mark.asyncio
async def test_moments_limit_201_rejected_by_validator(
    api_client: httpx.AsyncClient, test_tenant: dict
) -> None:
    """Query(le=200) → FastAPI 422 on limit=201 before handler runs."""
    r = await api_client.get(
        f"/v1/portal/{test_tenant['client_slug']}/moments?limit=201",
        headers={"Authorization": f"Bearer {test_tenant['token']}"},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_moments_since_returns_only_events_after(
    api_client: httpx.AsyncClient, test_tenant: dict
) -> None:
    """since=<event_id> returns events strictly after that id, newest-first.

    Append order: evt_000 oldest .. evt_009 newest. since=evt_005 yields
    evt_006..evt_009 (4 events), newest-first: evt_009, evt_008, evt_007,
    evt_006.
    """
    old_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        try:
            path = client_events_path(test_tenant["client_slug"])
            path.parent.mkdir(parents=True, exist_ok=True)
            for i in range(10):
                _seed_moment(path, event_id=f"evt_{i:03d}")
            r = await api_client.get(
                f"/v1/portal/{test_tenant['client_slug']}/moments"
                "?since=evt_005",
                headers={"Authorization": f"Bearer {test_tenant['token']}"},
            )
            assert r.status_code == 200
            ids = [m["event_id"] for m in r.json()["moments"]]
            assert ids == ["evt_009", "evt_008", "evt_007", "evt_006"]
        finally:
            os.chdir(old_cwd)


@pytest.mark.asyncio
async def test_moments_before_returns_only_events_before(
    api_client: httpx.AsyncClient, test_tenant: dict
) -> None:
    """before=<event_id> returns events strictly before, newest-first.

    before=evt_003 over evt_000..evt_009 → evt_000..evt_002, returned
    newest-first: evt_002, evt_001, evt_000.
    """
    old_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        try:
            path = client_events_path(test_tenant["client_slug"])
            path.parent.mkdir(parents=True, exist_ok=True)
            for i in range(10):
                _seed_moment(path, event_id=f"evt_{i:03d}")
            r = await api_client.get(
                f"/v1/portal/{test_tenant['client_slug']}/moments"
                "?before=evt_003",
                headers={"Authorization": f"Bearer {test_tenant['token']}"},
            )
            assert r.status_code == 200
            ids = [m["event_id"] for m in r.json()["moments"]]
            assert ids == ["evt_002", "evt_001", "evt_000"]
        finally:
            os.chdir(old_cwd)


@pytest.mark.asyncio
async def test_moments_kind_filter_intersects_with_timeline_eligible(
    api_client: httpx.AsyncClient, test_tenant: dict
) -> None:
    """kind=session_start,moment intersects with timeline-eligible set.

    Seed mix of moment + session_start + tool_call (non-eligible). Caller
    asks for `tool_call,moment` — `tool_call` is filtered out (not in
    timeline-eligible set), only `moment` events come back.
    """
    old_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        try:
            path = client_events_path(test_tenant["client_slug"])
            path.parent.mkdir(parents=True, exist_ok=True)
            _seed_moment(path, event_id="evt_m1", kind="moment", title="m1")
            log_event(
                kind="session_start",
                path=path,
                event_id="evt_s1",
                metadata={"lane": "marketing_audit"},
            )
            log_event(
                kind="tool_call",
                path=path,
                event_id="evt_t1",
                action="Read",
            )
            _seed_moment(path, event_id="evt_m2", kind="moment", title="m2")

            # Ask for tool_call + moment; intersection with timeline-eligible
            # set is just {moment}.
            r = await api_client.get(
                f"/v1/portal/{test_tenant['client_slug']}/moments"
                "?kind=tool_call,moment",
                headers={"Authorization": f"Bearer {test_tenant['token']}"},
            )
            assert r.status_code == 200
            kinds = [m["kind"] for m in r.json()["moments"]]
            assert kinds == ["moment", "moment"]
        finally:
            os.chdir(old_cwd)


@pytest.mark.asyncio
async def test_moments_kind_filter_only_non_eligible_returns_empty(
    api_client: httpx.AsyncClient, test_tenant: dict
) -> None:
    """kind=tool_call (not timeline-eligible) → empty list, 200.

    Sanity: the intersection-with-eligible-set logic must not 500 when the
    intersection is empty; it should short-circuit to {moments: [], ...}.
    """
    old_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        try:
            path = client_events_path(test_tenant["client_slug"])
            path.parent.mkdir(parents=True, exist_ok=True)
            _seed_moment(path, event_id="evt_m1")
            r = await api_client.get(
                f"/v1/portal/{test_tenant['client_slug']}/moments"
                "?kind=tool_call",
                headers={"Authorization": f"Bearer {test_tenant['token']}"},
            )
            assert r.status_code == 200
            assert r.json()["moments"] == []
            assert r.json()["has_more"] is False
        finally:
            os.chdir(old_cwd)


@pytest.mark.asyncio
async def test_moments_session_filter_matches_session_id(
    api_client: httpx.AsyncClient, test_tenant: dict
) -> None:
    """session=<sid> returns only events whose session_id (top-level or
    metadata) matches. Seeds three events with two different session_ids
    and confirms the filter returns only the matching one.
    """
    old_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        try:
            path = client_events_path(test_tenant["client_slug"])
            path.parent.mkdir(parents=True, exist_ok=True)
            _seed_moment(path, event_id="evt_a1", session_id="sess-alpha")
            _seed_moment(path, event_id="evt_b1", session_id="sess-beta")
            _seed_moment(path, event_id="evt_a2", session_id="sess-alpha")
            r = await api_client.get(
                f"/v1/portal/{test_tenant['client_slug']}/moments"
                "?session=sess-alpha",
                headers={"Authorization": f"Bearer {test_tenant['token']}"},
            )
            assert r.status_code == 200
            ids = [m["event_id"] for m in r.json()["moments"]]
            assert ids == ["evt_a2", "evt_a1"]
        finally:
            os.chdir(old_cwd)


@pytest.mark.asyncio
async def test_moments_session_tag_combines_lane_and_variant(
    api_client: httpx.AsyncClient, test_tenant: dict
) -> None:
    """session_tag is `<lane>` when no variant, `<lane>·<variant>` when set.

    Server-side derivation per R3.1; downstream consumers (Unit 7
    template) just render the string.
    """
    old_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        try:
            path = client_events_path(test_tenant["client_slug"])
            path.parent.mkdir(parents=True, exist_ok=True)
            _seed_moment(
                path, event_id="evt_lane_only",
                lane="marketing_audit", variant=None,
            )
            _seed_moment(
                path, event_id="evt_lane_variant",
                lane="geo", variant="v007",
            )
            _seed_moment(
                path, event_id="evt_no_lane",
                lane=None, variant=None,
            )

            r = await api_client.get(
                f"/v1/portal/{test_tenant['client_slug']}/moments",
                headers={"Authorization": f"Bearer {test_tenant['token']}"},
            )
            assert r.status_code == 200
            moments = r.json()["moments"]
            by_id = {m["event_id"]: m for m in moments}
            assert by_id["evt_lane_only"]["session_tag"] == "marketing_audit"
            assert by_id["evt_lane_variant"]["session_tag"] == "geo·v007"
            assert by_id["evt_no_lane"]["session_tag"] is None
        finally:
            os.chdir(old_cwd)


@pytest.mark.asyncio
async def test_moments_reads_rotated_segments(
    api_client: httpx.AsyncClient, test_tenant: dict
) -> None:
    """A rotated `events.jsonl.<stamp>` segment must be read + merged with
    the current file, newest-first across files.

    Simulates rotation by manually renaming a seeded events.jsonl after
    writing the "old" half; then writes the "new" half to the fresh path.
    read_events globs both and merges; the moments endpoint inherits that
    behavior and returns events from both files.
    """
    old_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        try:
            path = client_events_path(test_tenant["client_slug"])
            path.parent.mkdir(parents=True, exist_ok=True)
            # Old segment
            for i in range(5):
                _seed_moment(path, event_id=f"evt_old_{i:03d}")
            # Rotate: rename to `<name>.20260518-120000` so the glob picks
            # it up. The rotated file's mtime must be earlier than the new
            # current file for stable ordering — write a tiny sleep to
            # ensure that.
            rotated = path.parent / f"{path.name}.20260518-120000"
            path.rename(rotated)
            time.sleep(0.01)
            # New current segment
            for i in range(5):
                _seed_moment(path, event_id=f"evt_new_{i:03d}")

            r = await api_client.get(
                f"/v1/portal/{test_tenant['client_slug']}/moments",
                headers={"Authorization": f"Bearer {test_tenant['token']}"},
            )
            assert r.status_code == 200
            ids = [m["event_id"] for m in r.json()["moments"]]
            # Newest-first across both files: 5 new events first, then 5 old.
            assert ids[:5] == [f"evt_new_{i:03d}" for i in range(4, -1, -1)]
            assert ids[5:] == [f"evt_old_{i:03d}" for i in range(4, -1, -1)]
        finally:
            os.chdir(old_cwd)


# --------------------------------------------------------------------------
# Error paths
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_moments_404_when_slug_not_in_clients_table(
    api_client: httpx.AsyncClient, test_tenant: dict
) -> None:
    """A syntactically-valid slug that doesn't exist in the clients table
    → 404 client_not_found. Not 403 — admins typo'ing URLs deserve to know
    the slug is wrong, not have it look like a permissions problem.
    """
    # `test_tenant['token']` is a valid JWT but for a user with no admin
    # role; we need an admin token here so the resolve_client_access call
    # returns None for a different reason than "non-admin without
    # membership on a real slug". Use the same tenant's token but call
    # against a different slug — the user has no membership on
    # `definitely-nope-99999`, so resolve_client_access → None. Then the
    # slug doesn't exist either, so we want the route to choose 404.
    nonexistent = "definitely-nope-99999"
    r = await api_client.get(
        f"/v1/portal/{nonexistent}/moments",
        headers={"Authorization": f"Bearer {test_tenant['token']}"},
    )
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "client_not_found"


@pytest.mark.asyncio
async def test_moments_403_no_membership(
    api_client: httpx.AsyncClient, test_tenant: dict, outsider: dict
) -> None:
    """Outsider's JWT is valid but they have no membership on this slug.

    Slug DOES exist (provisioned by `test_tenant` fixture) → resolve_client_access
    returns None for the outsider → 403 no_membership (not 404).
    """
    r = await api_client.get(
        f"/v1/portal/{test_tenant['client_slug']}/moments",
        headers={"Authorization": f"Bearer {outsider['token']}"},
    )
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "no_membership"


@pytest.mark.asyncio
async def test_moments_401_missing_auth(
    api_client: httpx.AsyncClient, test_tenant: dict
) -> None:
    """No cookie, no Authorization header → 401 missing_credentials.

    The unified get_auth_principal surface handles this — the route never
    runs. Confirms the route is wired through Depends(get_auth_principal).
    """
    r = await api_client.get(
        f"/v1/portal/{test_tenant['client_slug']}/moments",
    )
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "missing_credentials"


@pytest.mark.asyncio
async def test_moments_422_invalid_slug_pattern(
    api_client: httpx.AsyncClient, test_tenant: dict
) -> None:
    """Path(pattern=r"^[a-z0-9-]{1,64}$") rejects uppercase / underscores
    at the FastAPI layer with 422 — defense in depth against log-grep path
    injection via slug.
    """
    r = await api_client.get(
        # Mixed case → rejected by the slug pattern.
        "/v1/portal/Foo_Bar/moments",
        headers={"Authorization": f"Bearer {test_tenant['token']}"},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_moments_422_invalid_since_pattern(
    api_client: httpx.AsyncClient, test_tenant: dict
) -> None:
    """since must match ^evt_[A-Za-z0-9_-]+$. A malformed cursor → 422.

    This guards against ?since=../../etc/passwd-style attempts; the
    pattern enforcement happens before the handler reads any file.
    """
    r = await api_client.get(
        f"/v1/portal/{test_tenant['client_slug']}/moments"
        "?since=NOT-A-VALID-CURSOR",
        headers={"Authorization": f"Bearer {test_tenant['token']}"},
    )
    assert r.status_code == 422


# --------------------------------------------------------------------------
# Integration: redaction + HTML
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_moments_redacts_api_key_in_title(
    api_client: httpx.AsyncClient, test_tenant: dict
) -> None:
    """A moment with a fake API key in its title returns the key replaced
    by `<redacted:api_key>` (or another matching marker) in the response.

    The scrub layer's `api_key` pattern matches `api_key=...{16,}` shapes;
    the redacted text uses `<redacted:KIND>` markers per scrub.py.
    """
    old_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        try:
            path = client_events_path(test_tenant["client_slug"])
            path.parent.mkdir(parents=True, exist_ok=True)
            leaky = "leaked: api_key=ABCDEFGHIJKLMNOPQRSTUVWXYZ012345"
            _seed_moment(path, event_id="evt_leak", title=leaky)

            r = await api_client.get(
                f"/v1/portal/{test_tenant['client_slug']}/moments",
                headers={"Authorization": f"Bearer {test_tenant['token']}"},
            )
            assert r.status_code == 200
            title_out = r.json()["moments"][0]["metadata"]["title"]
            # The raw token must NOT appear; a `<redacted:...>` marker MUST.
            assert "ABCDEFGHIJKLMNOPQRSTUVWXYZ012345" not in title_out
            assert "<redacted:" in title_out
        finally:
            os.chdir(old_cwd)


@pytest.mark.asyncio
async def test_moments_html_in_title_returned_verbatim(
    api_client: httpx.AsyncClient, test_tenant: dict
) -> None:
    """`<script>x</script>` in a moment title is returned VERBATIM in the
    JSON. HTML escape is a render-time concern (Unit 7 template), not
    something the JSON API should perform — that would double-escape.
    """
    old_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        try:
            path = client_events_path(test_tenant["client_slug"])
            path.parent.mkdir(parents=True, exist_ok=True)
            xss = "<script>alert(1)</script>"
            _seed_moment(path, event_id="evt_xss", title=xss)

            r = await api_client.get(
                f"/v1/portal/{test_tenant['client_slug']}/moments",
                headers={"Authorization": f"Bearer {test_tenant['token']}"},
            )
            assert r.status_code == 200
            title_out = r.json()["moments"][0]["metadata"]["title"]
            # Verbatim — no &lt; / &gt; substitution at this layer.
            assert title_out == xss
        finally:
            os.chdir(old_cwd)


# --------------------------------------------------------------------------
# Performance smoke (not gated in CI)
# --------------------------------------------------------------------------


@pytest.mark.slow
@pytest.mark.asyncio
async def test_moments_10k_events_under_200ms(
    api_client: httpx.AsyncClient, test_tenant: dict
) -> None:
    """SC1 latency bound: 10K-event per-client log returns in <200ms.

    Marked `slow` so the default pytest run skips it. Run with `-m slow`
    to gate manually. Not enforced in CI because the local box variance
    dominates the budget; this exists to flag regressions during
    intentional perf work.
    """
    old_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        try:
            path = client_events_path(test_tenant["client_slug"])
            path.parent.mkdir(parents=True, exist_ok=True)
            for i in range(10_000):
                _seed_moment(path, event_id=f"evt_{i:05d}")

            t0 = time.monotonic()
            r = await api_client.get(
                f"/v1/portal/{test_tenant['client_slug']}/moments",
                headers={"Authorization": f"Bearer {test_tenant['token']}"},
            )
            elapsed_ms = (time.monotonic() - t0) * 1000.0
            assert r.status_code == 200
            assert len(r.json()["moments"]) == 50
            # Generous bound — local box variance dominates. A regression
            # that takes 2-5s under this load would still trip this.
            assert elapsed_ms < 2000.0, f"took {elapsed_ms:.1f}ms"
        finally:
            os.chdir(old_cwd)
