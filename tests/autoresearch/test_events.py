import json
import threading
from pathlib import Path

from autoresearch.events import log_event, read_events


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


# Canonical event schema lock (2026-05-13) — see
# docs/brainstorms/2026-05-13-client-portal-telemetry-design.md

def test_known_kinds_contract_locked():
    """KNOWN_KINDS is the contract for canonical event types. Removing entries
    is a breaking change for the portal frontend's kind→colour mapping; adding
    new entries requires updating both KNOWN_KINDS and the frontend."""
    from autoresearch.events import KNOWN_KINDS
    expected = {
        "session_start", "session_end",
        "tool_call", "model_call", "edit",
        "cost", "render", "promotion",
        "review_approve", "review_reject", "review_required", "sla_breach",
        "alert",
        "moment",
    }
    assert KNOWN_KINDS == expected, (
        "KNOWN_KINDS drift detected. If the change is intentional, update "
        "this test AND the portal frontend's kind→colour mapping in "
        "src/api/routers/portal.py."
    )


def test_canonical_fields_contract_locked():
    """CANONICAL_FIELDS documents the canonical event shape consumers can rely
    on. Adding fields is non-breaking; removing them is breaking. Test pins
    the v1 shape."""
    from autoresearch.events import CANONICAL_FIELDS
    expected = {
        "kind", "timestamp",
        "event_id", "session_id", "parent_event_id",
        "source", "client_id", "actor",
        "lane", "variant", "fixture",
        "action", "args", "status",
        "cost_usd", "model", "tokens_in", "tokens_out",
        "metadata",
        "moment_kind", "source_event_ids", "title", "body",
    }
    assert CANONICAL_FIELDS == expected, (
        "CANONICAL_FIELDS drift detected. Adding a field is fine; removing one "
        "breaks consumers. If you removed intentionally, update this test."
    )


def test_client_events_path_operator_internal():
    """No client_id → operator-internal path (the EVENTS_LOG default)."""
    from autoresearch.events import client_events_path, EVENTS_LOG
    assert client_events_path(None) == EVENTS_LOG
    assert client_events_path(None, run_id="ignored") == EVENTS_LOG


def test_client_events_path_per_client_wide():
    """client_id only → client-wide events.jsonl (used by SSE endpoint)."""
    from autoresearch.events import client_events_path
    assert client_events_path("klinika-melitus") == Path(
        "clients/klinika-melitus/audit/events.jsonl"
    )


def test_client_events_path_per_run():
    """client_id + run_id → per-run scoped events.jsonl (used by writers
    during a specific autoresearch run for isolation)."""
    from autoresearch.events import client_events_path
    assert client_events_path("klinika-melitus", "run-abc123") == Path(
        "clients/klinika-melitus/audit/run-abc123/events.jsonl"
    )


def test_log_event_writes_to_per_client_path_via_helper(tmp_path):
    """log_event(path=client_events_path(slug)) is the canonical writer
    invocation for client telemetry. Verifies the path override works
    end-to-end (no monkeypatching of EVENTS_LOG needed for per-client writes)."""
    from autoresearch.events import client_events_path
    # We can't actually write to clients/<slug>/ in the test repo, so we
    # compute the path and assert log_event with path= overrides correctly.
    target = tmp_path / "clients/klinika-melitus/audit/run-test/events.jsonl"
    log_event(
        kind="render",
        path=target,
        source="autoresearch",
        client_id="klinika-melitus",
        lane="site_engine",
        variant="v123",
        fixture="klinika_hero",
        cost_usd=0.045,
        model="gemini-2.5",
        status="complete",
    )
    assert target.exists()
    payload = json.loads(target.read_text().splitlines()[0])
    assert payload["kind"] == "render"
    assert payload["client_id"] == "klinika-melitus"
    assert payload["lane"] == "site_engine"
    assert payload["cost_usd"] == 0.045
    assert payload["model"] == "gemini-2.5"
    assert payload["status"] == "complete"
    assert "timestamp" in payload
