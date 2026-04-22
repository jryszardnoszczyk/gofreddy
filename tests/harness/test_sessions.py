"""Tests for harness.sessions — sessions.json read/write + resume semantics."""
from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

from harness.sessions import SessionRecord, SessionsFile


def test_load_returns_empty_when_file_missing(tmp_path):
    sessions = SessionsFile(tmp_path / "sessions.json")
    assert sessions.all() == {}


def test_begin_writes_record_and_creates_file(tmp_path):
    path = tmp_path / "sessions.json"
    sessions = SessionsFile(path)
    sessions.begin("eval-a-c1", "sid-123", engine="claude")
    assert path.is_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "eval-a-c1" in data
    assert data["eval-a-c1"]["session_id"] == "sid-123"
    assert data["eval-a-c1"]["status"] == "running"
    assert data["eval-a-c1"]["engine"] == "claude"


def test_finish_transitions_status(tmp_path):
    sessions = SessionsFile(tmp_path / "sessions.json")
    sessions.begin("fix-F-a-1-1", "sid-x", engine="claude")
    sessions.finish("fix-F-a-1-1", "complete")
    record = sessions.get("fix-F-a-1-1")
    assert record is not None
    assert record.status == "complete"
    assert record.finished_at is not None


def test_finish_unknown_key_is_noop(tmp_path, caplog):
    sessions = SessionsFile(tmp_path / "sessions.json")
    with caplog.at_level("WARNING", logger="harness.sessions"):
        sessions.finish("ghost", "complete")
    assert "unknown agent_key ghost" in caplog.text


def test_reopen_loads_prior_state(tmp_path):
    """After a crash/SIGTERM, a fresh SessionsFile over the same path must see
    the prior records so resume logic can make skip/resume decisions."""
    path = tmp_path / "sessions.json"
    first = SessionsFile(path)
    first.begin("eval-a-c1", "sid-1", engine="claude")
    first.finish("eval-a-c1", "complete")
    first.begin("fix-F-a-1-1", "sid-2", engine="claude")
    # Simulate SIGTERM: second SessionsFile reads what first wrote.

    second = SessionsFile(path)
    eval_rec = second.get("eval-a-c1")
    fix_rec = second.get("fix-F-a-1-1")
    assert eval_rec is not None and eval_rec.status == "complete"
    # Interrupted fix must stay "running" so --resume-branch picks it up.
    assert fix_rec is not None and fix_rec.status == "running"


def test_corrupt_json_starts_empty_with_warning(tmp_path, caplog):
    path = tmp_path / "sessions.json"
    path.write_text("not json at all", encoding="utf-8")
    with caplog.at_level("WARNING", logger="harness.sessions"):
        sessions = SessionsFile(path)
    assert sessions.all() == {}
    assert "corrupted" in caplog.text


def test_malformed_entry_is_skipped_not_fatal(tmp_path, caplog):
    path = tmp_path / "sessions.json"
    path.write_text(json.dumps({
        "good": {"agent_key": "good", "session_id": "s", "engine": "claude",
                 "status": "complete", "started_at": 1.0, "finished_at": 2.0},
        "bad": {"session_id": "s"},  # missing required fields
    }), encoding="utf-8")
    with caplog.at_level("WARNING", logger="harness.sessions"):
        sessions = SessionsFile(path)
    assert "good" in sessions.all()
    assert "bad" not in sessions.all()
    assert "malformed" in caplog.text


def test_concurrent_begin_and_finish_is_safe(tmp_path):
    """Parallel tracks write to sessions.json concurrently; lock must serialize."""
    sessions = SessionsFile(tmp_path / "sessions.json")
    barrier = threading.Barrier(6)

    def write_one(key: str, sid: str) -> None:
        barrier.wait()
        sessions.begin(key, sid, engine="claude")
        sessions.finish(key, "complete")

    threads = [
        threading.Thread(target=write_one, args=(f"eval-{t}-c1", f"sid-{t}"))
        for t in ("a", "b", "c")
    ] + [
        threading.Thread(target=write_one, args=(f"fix-F-{t}-1-1", f"sid-fix-{t}"))
        for t in ("a", "b", "c")
    ]
    for th in threads:
        th.start()
    for th in threads:
        th.join()

    # All 6 records present and marked complete — no lost writes from interleaving.
    all_records = sessions.all()
    assert len(all_records) == 6
    for record in all_records.values():
        assert record.status == "complete"


def test_atomic_write_no_partial_file_on_midwrite_crash(tmp_path, monkeypatch):
    """If the write crashes mid-flight, the target file must either be the prior
    good state or not modified — never a half-written JSON. os.replace is atomic."""
    sessions = SessionsFile(tmp_path / "sessions.json")
    sessions.begin("eval-a-c1", "sid-1", engine="claude")
    prior = (tmp_path / "sessions.json").read_text(encoding="utf-8")

    # Simulate os.replace blowing up on the next write.
    from harness import sessions as sessions_mod
    real_replace = sessions_mod.os.replace

    def boom(*args, **kwargs):
        raise OSError("simulated disk full")
    monkeypatch.setattr(sessions_mod.os, "replace", boom)

    with pytest.raises(OSError):
        sessions.begin("fix-F-a-1-1", "sid-x", engine="claude")

    # Target file is still the prior good state. No orphaned .sessions-*.tmp.
    monkeypatch.setattr(sessions_mod.os, "replace", real_replace)
    current = (tmp_path / "sessions.json").read_text(encoding="utf-8")
    assert current == prior
    leftovers = list(tmp_path.glob(".sessions-*.tmp"))
    assert leftovers == [], f"tmp file leaked: {leftovers}"


def test_session_record_dataclass_is_immutable():
    """Frozen dataclass: callers can't mutate a record fetched via get()."""
    record = SessionRecord(
        agent_key="k", session_id="s", engine="claude",
        status="running", started_at=1.0,
    )
    with pytest.raises(Exception):  # FrozenInstanceError
        record.status = "complete"  # type: ignore[misc]
