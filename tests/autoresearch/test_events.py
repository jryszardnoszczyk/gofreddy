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
