"""P5 Phase 2 portal tests: /summary expanded shape + pure-helper math.

Unit tests at the top exercise the cost-rollup, audit-page, lane-summary,
and recent-reports helpers directly — they're pure functions over event
lists, so no Supabase / no HTTP layer. Integration tests at the bottom
cover the /summary route end-to-end against a real test tenant.
"""
from __future__ import annotations

import datetime as _dt
import json

import httpx
import pytest

from src.api.routers.portal import (
    _audit_page,
    _cost_rollup,
    _lane_summary,
    _list_recent_reports,
    _parse_event_timestamp,
)


# --------------------------------------------------------------------------
# _parse_event_timestamp
# --------------------------------------------------------------------------


def test_parse_event_timestamp_accepts_z_suffix():
    ts = _parse_event_timestamp("2026-05-13T15:42:01.234Z")
    assert ts is not None
    assert ts.tzinfo is not None
    assert ts.year == 2026 and ts.hour == 15


def test_parse_event_timestamp_accepts_plus_zero():
    ts = _parse_event_timestamp("2026-05-13T15:42:01.234+00:00")
    assert ts is not None


def test_parse_event_timestamp_returns_none_on_malformed():
    assert _parse_event_timestamp("") is None
    assert _parse_event_timestamp(None) is None
    assert _parse_event_timestamp("not-a-timestamp") is None
    assert _parse_event_timestamp(12345) is None


# --------------------------------------------------------------------------
# _cost_rollup
# --------------------------------------------------------------------------


def _utc(year, month, day, hour=12) -> _dt.datetime:
    """Helper: build a fixed UTC datetime for deterministic bucketing."""
    return _dt.datetime(year, month, day, hour, 0, 0, tzinfo=_dt.timezone.utc)


def test_cost_rollup_empty_events_zero():
    now = _utc(2026, 5, 13)
    assert _cost_rollup([], now=now) == {
        "today_usd": 0.0,
        "week_usd": 0.0,
        "month_usd": 0.0,
    }


def test_cost_rollup_buckets_today_week_month():
    """Wednesday 2026-05-13 12:00 UTC. Week starts Monday 2026-05-11.
    Month starts 2026-05-01. Today = 2026-05-13."""
    now = _utc(2026, 5, 13)
    events = [
        # Today (should land in all three buckets)
        {"kind": "cost", "cost_usd": 1.0, "timestamp": "2026-05-13T06:00:00Z"},
        # Yesterday (week + month only)
        {"kind": "cost", "cost_usd": 2.0, "timestamp": "2026-05-12T22:00:00Z"},
        # Monday this week (week + month)
        {"kind": "cost", "cost_usd": 4.0, "timestamp": "2026-05-11T08:00:00Z"},
        # Earlier in month (month only)
        {"kind": "cost", "cost_usd": 8.0, "timestamp": "2026-05-02T10:00:00Z"},
        # Last month (none of the three)
        {"kind": "cost", "cost_usd": 16.0, "timestamp": "2026-04-30T10:00:00Z"},
    ]
    out = _cost_rollup(events, now=now)
    assert out["today_usd"] == 1.0
    assert out["week_usd"] == 1.0 + 2.0 + 4.0
    assert out["month_usd"] == 1.0 + 2.0 + 4.0 + 8.0


def test_cost_rollup_ignores_non_cost_kind():
    now = _utc(2026, 5, 13)
    events = [
        {"kind": "tool_call", "cost_usd": 99.0, "timestamp": "2026-05-13T06:00:00Z"},
        {"kind": "cost", "cost_usd": 1.0, "timestamp": "2026-05-13T06:00:00Z"},
    ]
    assert _cost_rollup(events, now=now)["today_usd"] == 1.0


def test_cost_rollup_skips_malformed_entries():
    """Bad timestamp / non-numeric cost / missing fields are silently ignored."""
    now = _utc(2026, 5, 13)
    events = [
        {"kind": "cost", "cost_usd": "not-a-number", "timestamp": "2026-05-13T06:00:00Z"},
        {"kind": "cost", "cost_usd": 1.0, "timestamp": "not-a-timestamp"},
        {"kind": "cost", "cost_usd": None, "timestamp": "2026-05-13T06:00:00Z"},
        {"kind": "cost", "timestamp": "2026-05-13T06:00:00Z"},  # no cost_usd
        {"kind": "cost", "cost_usd": 5.0, "timestamp": "2026-05-13T06:00:00Z"},  # the only valid one
    ]
    assert _cost_rollup(events, now=now)["today_usd"] == 5.0


# --------------------------------------------------------------------------
# _lane_summary
# --------------------------------------------------------------------------


def test_lane_summary_distinct_sorted():
    events = [
        {"kind": "tool_call", "lane": "x_engine"},
        {"kind": "cost", "lane": "marketing_audit"},
        {"kind": "tool_call", "lane": "x_engine"},
        {"kind": "cost"},  # no lane
        {"kind": "render", "lane": ""},  # empty string ignored
    ]
    assert _lane_summary(events) == ["marketing_audit", "x_engine"]


def test_lane_summary_empty():
    assert _lane_summary([]) == []


# --------------------------------------------------------------------------
# _audit_page
# --------------------------------------------------------------------------


def _ev(i: int, *, kind="tool_call", actor="agent", lane="marketing_audit") -> dict:
    return {
        "kind": kind,
        "actor": actor,
        "lane": lane,
        "timestamp": f"2026-05-13T{i % 24:02d}:00:00Z",
        "seq": i,  # for ordering assertions
    }


def test_audit_page_newest_first_and_paginates():
    events = [_ev(i) for i in range(120)]
    page1 = _audit_page(events, page=1, page_size=50)
    assert page1["total"] == 120
    assert page1["page"] == 1
    assert page1["page_size"] == 50
    assert len(page1["events"]) == 50
    # newest first → page 1 starts at seq=119, page 2 at seq=69
    assert page1["events"][0]["seq"] == 119
    page2 = _audit_page(events, page=2, page_size=50)
    assert page2["events"][0]["seq"] == 69
    page3 = _audit_page(events, page=3, page_size=50)
    # third page is the final 20 (120 - 100 = 20)
    assert len(page3["events"]) == 20
    assert page3["events"][0]["seq"] == 19
    # out-of-range page is empty but total is correct
    page4 = _audit_page(events, page=4, page_size=50)
    assert page4["events"] == []
    assert page4["total"] == 120


def test_audit_page_filter_by_kind():
    events = [
        _ev(0, kind="tool_call"),
        _ev(1, kind="cost"),
        _ev(2, kind="cost"),
        _ev(3, kind="tool_call"),
    ]
    out = _audit_page(events, kind="cost", page=1, page_size=10)
    assert out["total"] == 2
    assert {ev["seq"] for ev in out["events"]} == {1, 2}


def test_audit_page_filter_by_actor():
    events = [
        _ev(0, actor="agent"),
        _ev(1, actor="human"),
        _ev(2, actor="agent"),
    ]
    out = _audit_page(events, actor="human", page=1, page_size=10)
    assert out["total"] == 1
    assert out["events"][0]["seq"] == 1


def test_audit_page_filter_by_lane():
    events = [
        _ev(0, lane="x_engine"),
        _ev(1, lane="marketing_audit"),
    ]
    out = _audit_page(events, lane="marketing_audit", page=1, page_size=10)
    assert out["total"] == 1
    assert out["events"][0]["seq"] == 1


def test_audit_page_filters_combine():
    events = [
        _ev(0, kind="cost", actor="agent"),
        _ev(1, kind="cost", actor="human"),
        _ev(2, kind="tool_call", actor="agent"),
    ]
    out = _audit_page(events, kind="cost", actor="agent")
    assert out["total"] == 1
    assert out["events"][0]["seq"] == 0


# --------------------------------------------------------------------------
# _list_recent_reports
# --------------------------------------------------------------------------


def _seed_report(archive_root, variant, lane, fixture):
    """Create a fake report.html on disk for the recent-reports scanner."""
    d = archive_root / variant / "sessions" / lane / fixture
    d.mkdir(parents=True, exist_ok=True)
    p = d / "report.html"
    p.write_text("<html><body>fake report</body></html>")
    return p


def test_list_recent_reports_tenant_lane_requires_fixture_matches_slug(tmp_path):
    """marketing_audit is a tenant lane → fixture MUST equal slug."""
    _seed_report(tmp_path, "v007", "marketing_audit", "klinika-melitus")
    _seed_report(tmp_path, "v007", "marketing_audit", "some-other-client")

    out = _list_recent_reports(
        "klinika-melitus", "owner", archive_root=tmp_path
    )
    assert len(out) == 1
    assert out[0]["fixture"] == "klinika-melitus"
    assert out[0]["lane"] == "marketing_audit"
    assert out[0]["variant"] == "v007"
    assert out[0]["url"] == (
        "/v1/portal/klinika-melitus/reports/marketing_audit/v007/klinika-melitus"
    )


def test_list_recent_reports_operator_lane_admin_only(tmp_path):
    """geo / competitive / monitoring / storyboard / x_engine / linkedin_engine
    are operator-only → owners don't see them; admins do."""
    _seed_report(tmp_path, "v007", "geo", "mayoclinic")
    _seed_report(tmp_path, "v007", "marketing_audit", "klinika-melitus")

    owner_view = _list_recent_reports(
        "klinika-melitus", "owner", archive_root=tmp_path
    )
    # Only the marketing_audit report; geo is hidden from owners.
    assert {r["lane"] for r in owner_view} == {"marketing_audit"}

    admin_view = _list_recent_reports(
        "klinika-melitus", "admin", archive_root=tmp_path
    )
    assert {r["lane"] for r in admin_view} == {"geo", "marketing_audit"}


def test_list_recent_reports_sorted_by_mtime_desc(tmp_path):
    import time as _t
    p1 = _seed_report(tmp_path, "v001", "marketing_audit", "klinika-melitus")
    _t.sleep(0.01)  # ensure mtime differs
    p2 = _seed_report(tmp_path, "v007", "marketing_audit", "klinika-melitus")
    out = _list_recent_reports(
        "klinika-melitus", "owner", archive_root=tmp_path
    )
    assert [r["variant"] for r in out] == ["v007", "v001"]


def test_list_recent_reports_empty_when_archive_missing(tmp_path):
    assert _list_recent_reports(
        "klinika-melitus", "owner", archive_root=tmp_path / "no-such-dir"
    ) == []


def test_list_recent_reports_caps_at_limit(tmp_path):
    for i in range(15):
        # 15 owner-visible reports all on tenant lane with matching fixture
        v = f"v{i:03d}"
        # Variant regex requires v\d+(-[a-z0-9]+)?; v015 is fine
        _seed_report(tmp_path, v, "marketing_audit", "klinika-melitus")
    out = _list_recent_reports(
        "klinika-melitus", "owner", archive_root=tmp_path, limit=10
    )
    assert len(out) == 10


# --------------------------------------------------------------------------
# Integration: /summary expanded shape (Supabase-gated)
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_summary_returns_phase2_shape(
    api_client: httpx.AsyncClient, test_tenant: dict
) -> None:
    """Phase 2 /summary returns cost rollup + lanes + reports + audit page."""
    r = await api_client.get(
        f"/v1/portal/{test_tenant['client_slug']}/summary",
        headers={"Authorization": f"Bearer {test_tenant['token']}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["phase"] == 2
    # required keys for the frontend renderer
    assert set(data["cost"].keys()) == {"today_usd", "week_usd", "month_usd"}
    assert isinstance(data["lanes"], list)
    assert isinstance(data["recent_reports"], list)
    audit = data["audit"]
    assert set(audit.keys()) == {"events", "total", "page", "page_size"}
    assert audit["page"] == 1
    assert audit["page_size"] == 50


@pytest.mark.asyncio
async def test_summary_audit_kind_filter(
    api_client: httpx.AsyncClient, test_tenant: dict, monkeypatch
) -> None:
    """audit_kind query param filters the audit page server-side."""
    # Seed events for the client
    import os
    from autoresearch.events import client_events_path, log_event
    old_cwd = os.getcwd()
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        try:
            path = client_events_path(test_tenant["client_slug"])
            path.parent.mkdir(parents=True, exist_ok=True)
            log_event(kind="cost", path=path, cost_usd=0.42)
            log_event(kind="tool_call", path=path, action="Read")
            log_event(kind="tool_call", path=path, action="Write")

            r = await api_client.get(
                f"/v1/portal/{test_tenant['client_slug']}/summary"
                "?audit_kind=cost",
                headers={"Authorization": f"Bearer {test_tenant['token']}"},
            )
            assert r.status_code == 200
            audit = r.json()["audit"]
            # Only the kind=cost event passes the filter
            assert audit["total"] == 1
            assert audit["events"][0]["kind"] == "cost"
        finally:
            os.chdir(old_cwd)


@pytest.mark.asyncio
async def test_summary_cost_rollup_sums_events(
    api_client: httpx.AsyncClient, test_tenant: dict
) -> None:
    """Cost rollup math matches a hand-computed total against seeded events."""
    import os
    from autoresearch.events import client_events_path, log_event
    old_cwd = os.getcwd()
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        try:
            path = client_events_path(test_tenant["client_slug"])
            path.parent.mkdir(parents=True, exist_ok=True)
            # Three cost events all in the current UTC second → all in today/week/month
            log_event(kind="cost", path=path, cost_usd=1.5)
            log_event(kind="cost", path=path, cost_usd=2.25)
            log_event(kind="cost", path=path, cost_usd=0.125)

            r = await api_client.get(
                f"/v1/portal/{test_tenant['client_slug']}/summary",
                headers={"Authorization": f"Bearer {test_tenant['token']}"},
            )
            assert r.status_code == 200
            cost = r.json()["cost"]
            # All three landed today
            assert cost["today_usd"] == pytest.approx(1.5 + 2.25 + 0.125, abs=1e-6)
            assert cost["week_usd"] == pytest.approx(1.5 + 2.25 + 0.125, abs=1e-6)
            assert cost["month_usd"] == pytest.approx(1.5 + 2.25 + 0.125, abs=1e-6)
        finally:
            os.chdir(old_cwd)


@pytest.mark.asyncio
async def test_portal_shell_renders_phase2_template(
    api_client: httpx.AsyncClient, test_tenant: dict
) -> None:
    """The HTML shell at /portal/<slug> now serves the Phase 2 template.

    Distinguishes from the placeholder by a Phase-2-only marker.
    """
    r = await api_client.get(f"/portal/{test_tenant['client_slug']}")
    assert r.status_code == 200
    # Phase 2 markers
    assert "live agent transcript" in r.text.lower() or "freddy.live" in r.text.lower()
    assert "cost-card" in r.text or "cost ledger" in r.text.lower() or "this month" in r.text.lower()
    # The slug is rendered for personalization
    assert test_tenant["client_slug"] in r.text
