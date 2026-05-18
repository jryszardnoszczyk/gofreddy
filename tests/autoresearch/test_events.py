import json
import threading
from pathlib import Path

from autoresearch.events import (
    CANONICAL_FIELDS,
    KNOWN_KINDS,
    client_events_path,
    log_event,
    read_events,
)


def test_log_event_appends_jsonl_line(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    import autoresearch.events as events
    monkeypatch.setattr(events, "EVENTS_LOG", tmp_path / ".local/share/gofreddy/events.jsonl")
    log_event(kind="judge_unreachable", endpoint="/invoke/score", error="timeout")
    log_path = tmp_path / ".local/share/gofreddy/events.jsonl"
    assert log_path.exists()
    lines = log_path.read_text().splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["kind"] == "judge_unreachable"
    assert payload["endpoint"] == "/invoke/score"
    assert "timestamp" in payload


def test_read_events_filters_by_kind(tmp_path, monkeypatch):
    import autoresearch.events as events
    monkeypatch.setattr(events, "EVENTS_LOG", tmp_path / ".local/share/gofreddy/events.jsonl")
    log_event(kind="judge_unreachable", error="a")
    log_event(kind="judge_abstain", fixture_id="f1")
    log_event(kind="judge_unreachable", error="b")
    evs = list(read_events(kind="judge_unreachable"))
    assert len(evs) == 2
    assert all(e["kind"] == "judge_unreachable" for e in evs)


def test_read_events_concatenates_rotated_files(tmp_path, monkeypatch):
    import autoresearch.events as events
    monkeypatch.setattr(events, "EVENTS_LOG", tmp_path / ".local/share/gofreddy/events.jsonl")
    log_dir = tmp_path / ".local/share/gofreddy"
    log_dir.mkdir(parents=True)
    (log_dir / "events.jsonl.20260101-120000").write_text(
        json.dumps({"kind": "head_score", "score": 0.5, "timestamp": "2026-01-01"}) + "\n"
    )
    log_event(kind="head_score", score=0.7)
    evs = list(read_events(kind="head_score"))
    assert len(evs) == 2
    scores = [e["score"] for e in evs]
    assert 0.5 in scores and 0.7 in scores


def test_concurrent_writes_do_not_tear(tmp_path, monkeypatch):
    """Four threads writing large records simultaneously must never produce a torn line."""
    import autoresearch.events as events
    monkeypatch.setattr(events, "EVENTS_LOG", tmp_path / ".local/share/gofreddy/events.jsonl")
    big_payload = "x" * 8192  # exceeds PIPE_BUF
    def writer(n):
        for _ in range(20):
            log_event(kind="judge_raw", data=big_payload + str(n))
    threads = [threading.Thread(target=writer, args=(i,)) for i in range(4)]
    for t in threads: t.start()
    for t in threads: t.join()
    log_path = tmp_path / ".local/share/gofreddy/events.jsonl"
    lines = log_path.read_text().splitlines()
    assert len(lines) == 80
    for line in lines:
        json.loads(line)  # raises on torn


def test_read_events_raises_on_corrupt_line(tmp_path, monkeypatch):
    import autoresearch.events as events
    from autoresearch.events import EventLogCorruption
    log_path = tmp_path / ".local/share/gofreddy/events.jsonl"
    monkeypatch.setattr(events, "EVENTS_LOG", log_path)
    log_path.parent.mkdir(parents=True)
    log_path.write_text('{"kind": "ok", "timestamp": "t"}\nnot-json\n')
    import pytest
    with pytest.raises(EventLogCorruption):
        list(read_events())


# ---------------------------------------------------------------------------
# U6b drift tests — KNOWN_KINDS + CANONICAL_FIELDS schema pins
# ---------------------------------------------------------------------------
#
# Per Content Engine v1 U6b: silent removal of any portal-coordinated kind
# or canonical field would un-block downstream features without warning.
# These tests pin the registry so a future edit must be deliberate.


def test_known_kinds_includes_portal_moment_kinds() -> None:
    """U6b R-Schema-1: moment + review_required must stay registered so
    the portal moments timeline + pre-publish review service work."""
    assert "moment" in KNOWN_KINDS
    assert "review_required" in KNOWN_KINDS


def test_known_kinds_includes_review_lifecycle_kinds() -> None:
    """U7 review service emits these four kinds — drift pin so removal
    of any one is caught by CI before U7's portal coupling regresses."""
    for kind in ("review_required", "review_approve", "review_reject", "sla_breach"):
        assert kind in KNOWN_KINDS, f"U7 review kind missing from KNOWN_KINDS: {kind}"


def test_known_kinds_preserves_pre_v1_autoresearch_kinds() -> None:
    """Pre-Content-Engine-v1 callers must keep working — drift pin so
    a v1 cleanup doesn't accidentally remove these."""
    for kind in (
        "judge_unreachable", "judge_abstain", "judge_audit",
        "judge_batch_fallback", "judge_raw", "head_score",
    ):
        assert kind in KNOWN_KINDS, f"pre-v1 kind removed from KNOWN_KINDS: {kind}"


def test_canonical_fields_includes_portal_moment_fields() -> None:
    """U6b R-Schema-3: moment_kind / source_event_ids / title / body must
    stay registered so the portal can render the timeline without
    per-kind transformation."""
    for field in ("moment_kind", "source_event_ids", "title", "body"):
        assert field in CANONICAL_FIELDS, f"R-Schema-3 field missing: {field}"


def test_canonical_fields_includes_top_level_event_fields() -> None:
    """Every event implicitly carries kind + timestamp; client_id +
    actor + action + metadata carry stable cross-kind semantics."""
    for field in ("kind", "timestamp", "client_id", "actor", "action", "metadata"):
        assert field in CANONICAL_FIELDS, f"top-level canonical field missing: {field}"


def test_client_events_path_returns_per_client_route() -> None:
    """U6b: client_events_path(slug) routes to clients/<slug>/audit/events.jsonl,
    so U7 + lane authors can pass it to log_event(path=...) and keep
    portal scoping clean per client."""
    p = client_events_path("klinika-melitus")
    assert p.name == "events.jsonl"
    assert p.parent.name == "audit"
    assert p.parent.parent.name == "klinika-melitus"


def test_log_event_to_per_client_path_writes_jsonl_line(tmp_path, monkeypatch) -> None:
    """Per-client log integration: log_event(path=client_events_path(slug), ...)
    appends to the per-client log without touching the global log."""
    import autoresearch.events as events

    # Redirect both globals so this test cannot pollute the real client
    # tree under repo root.
    fake_repo = tmp_path / "fake-repo"
    fake_repo.mkdir()
    monkeypatch.setattr(events, "_REPO_ROOT", fake_repo)
    monkeypatch.setattr(events, "EVENTS_LOG", tmp_path / ".local/share/gofreddy/events.jsonl")

    per_client = events.client_events_path("klinika-melitus")
    log_event(
        kind="moment", path=per_client,
        client_id="klinika-melitus",
        actor="agent",
        metadata={"moment_kind": "session_start", "title": "Article draft v3 ready"},
    )
    assert per_client.is_file()
    record = json.loads(per_client.read_text().strip())
    assert record["kind"] == "moment"
    assert record["client_id"] == "klinika-melitus"
    # Global log untouched
    assert not (tmp_path / ".local/share/gofreddy/events.jsonl").exists()
