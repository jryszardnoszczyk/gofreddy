"""Tests for autoresearch.sessions — restored 2026-05-12 after Plan B U10
had gutted it to a no-op shim. See sessions.py docstring for context."""

from __future__ import annotations

import json
from pathlib import Path
from unittest import mock

import pytest

from sessions import SessionsFile, SessionRecord, viable_resume_id


def test_begin_then_get_round_trip(tmp_path: Path) -> None:
    sf = SessionsFile(tmp_path / ".session_ids.json")
    record = sf.begin("meta-v013", "abc-123-uuid", engine="claude")
    assert record.session_id == "abc-123-uuid"
    assert record.status == "running"
    assert record.engine == "claude"

    fresh = SessionsFile(tmp_path / ".session_ids.json")
    fetched = fresh.get("meta-v013")
    assert fetched is not None
    assert fetched.session_id == "abc-123-uuid"
    assert fetched.status == "running"


def test_finish_updates_status_to_complete(tmp_path: Path) -> None:
    sf = SessionsFile(tmp_path / ".session_ids.json")
    sf.begin("fixture-geo-semrush", "sid-1", engine="claude")
    sf.finish("fixture-geo-semrush", "complete")

    fresh = SessionsFile(tmp_path / ".session_ids.json")
    record = fresh.get("fixture-geo-semrush")
    assert record is not None
    assert record.status == "complete"
    assert record.finished_at is not None


def test_finish_unknown_key_is_noop(tmp_path: Path) -> None:
    sf = SessionsFile(tmp_path / ".session_ids.json")
    # Should warn + not raise.
    sf.finish("never-began", "complete")
    assert sf.get("never-began") is None


def test_running_filters_to_running_only(tmp_path: Path) -> None:
    sf = SessionsFile(tmp_path / ".session_ids.json")
    sf.begin("meta-v100", "sid-meta", engine="claude")
    sf.begin("fixture-a", "sid-a", engine="claude")
    sf.begin("fixture-b", "sid-b", engine="claude")
    sf.finish("fixture-a", "complete")

    running = sf.running()
    assert set(running.keys()) == {"meta-v100", "fixture-b"}


def test_update_session_id_patches_codex_post_capture(tmp_path: Path) -> None:
    """Codex doesn't accept pre-minted session-id, so the orchestrator
    begins with empty sid and patches via update_session_id once it scrapes
    the 'session id: <uuid>' line from the codex stdout."""
    sf = SessionsFile(tmp_path / ".session_ids.json")
    sf.begin("meta-v200", "", engine="codex")
    assert sf.get("meta-v200").session_id == ""

    sf.update_session_id("meta-v200", "019e1c79-1443-7cd1-8808-a3e7ba510169")
    assert sf.get("meta-v200").session_id == "019e1c79-1443-7cd1-8808-a3e7ba510169"
    # Status preserved (still running).
    assert sf.get("meta-v200").status == "running"


def test_update_session_id_unknown_key_is_noop(tmp_path: Path) -> None:
    sf = SessionsFile(tmp_path / ".session_ids.json")
    sf.update_session_id("never-began", "some-sid")
    assert sf.get("never-began") is None


def test_atomic_write_survives_corrupt_file(tmp_path: Path) -> None:
    """If .session_ids.json is corrupted (mid-write crash), starting a fresh
    SessionsFile should warn and start with empty state, not crash."""
    bad = tmp_path / ".session_ids.json"
    bad.write_text("{this is not valid json")
    sf = SessionsFile(bad)
    assert sf.all() == {}

    # And it should still be writable after the load failure.
    sf.begin("meta-v300", "sid-x", engine="claude")
    assert sf.get("meta-v300").session_id == "sid-x"


def test_load_skips_malformed_records(tmp_path: Path) -> None:
    """Records with missing required fields should be skipped, not crash
    the load."""
    path = tmp_path / ".session_ids.json"
    path.write_text(json.dumps({
        "good": {
            "agent_key": "good", "session_id": "sid-1", "engine": "claude",
            "status": "running", "started_at": 1234.5,
        },
        "missing_engine": {
            "agent_key": "missing_engine", "session_id": "sid-2",
            "status": "running", "started_at": 1234.5,
        },
    }))
    sf = SessionsFile(path)
    assert "good" in sf.all()
    assert "missing_engine" not in sf.all()


# ---------------------------------------------------------------------------
# viable_resume_id
# ---------------------------------------------------------------------------


def _make_record(engine: str, sid: str = "abc-uuid") -> SessionRecord:
    return SessionRecord(
        agent_key="test", session_id=sid, engine=engine,
        status="running", started_at=0.0,
    )


def test_viable_resume_id_claude_with_existing_jsonl(tmp_path: Path) -> None:
    """Claude rollout exists at ~/.claude/projects/<encoded-cwd>/<sid>.jsonl."""
    record = _make_record("claude", "claude-sid-1")
    cwd = Path("/some/workdir")
    # Mock Path.home() to point at tmp_path so the test doesn't touch real ~.
    encoded = str(cwd).replace("/", "-")
    fake_home = tmp_path / "home"
    jsonl = fake_home / ".claude" / "projects" / encoded / "claude-sid-1.jsonl"
    jsonl.parent.mkdir(parents=True)
    jsonl.write_text("")  # presence is enough; viability check only stats

    with mock.patch("sessions.Path.home", return_value=fake_home):
        result = viable_resume_id(record, claude_cwd=cwd)
    assert result == "claude-sid-1"


def test_viable_resume_id_claude_returns_none_when_jsonl_missing(tmp_path: Path) -> None:
    record = _make_record("claude", "claude-sid-2")
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    with mock.patch("sessions.Path.home", return_value=fake_home):
        result = viable_resume_id(record, claude_cwd=Path("/nope"))
    assert result is None


def test_viable_resume_id_claude_returns_none_when_no_cwd_supplied() -> None:
    record = _make_record("claude")
    assert viable_resume_id(record, claude_cwd=None) is None


def test_viable_resume_id_codex_with_existing_rollout(tmp_path: Path) -> None:
    """Codex rollout exists at ~/.codex/sessions/YYYY/MM/DD/rollout-<ts>-<sid>.jsonl."""
    record = _make_record("codex", "codex-sid-1")
    fake_home = tmp_path / "home"
    rollout_dir = fake_home / ".codex" / "sessions" / "2026" / "05" / "12"
    rollout_dir.mkdir(parents=True)
    rollout = rollout_dir / "rollout-1234567890-codex-sid-1.jsonl"
    rollout.write_text("")
    with mock.patch("sessions.Path.home", return_value=fake_home):
        result = viable_resume_id(record, claude_cwd=None)
    assert result == "codex-sid-1"


def test_viable_resume_id_codex_returns_none_when_rollout_missing(tmp_path: Path) -> None:
    record = _make_record("codex", "codex-sid-2")
    fake_home = tmp_path / "home"
    (fake_home / ".codex" / "sessions").mkdir(parents=True)  # exists but empty
    with mock.patch("sessions.Path.home", return_value=fake_home):
        result = viable_resume_id(record, claude_cwd=None)
    assert result is None


def test_viable_resume_id_unknown_engine_returns_none() -> None:
    """opencode (or any unknown engine) returns None — caller falls back to fresh."""
    record = _make_record("opencode")
    assert viable_resume_id(record) is None
