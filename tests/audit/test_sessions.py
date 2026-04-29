"""Audit-scoped sessions wrapper tests — thin adapter around harness.sessions.SessionsFile."""
from __future__ import annotations

from pathlib import Path

from harness.sessions import SessionRecord, SessionsFile

from src.audit.sessions import open_audit_sessions


def test_open_audit_sessions_returns_sessions_file(tmp_path: Path):
    audit_dir = tmp_path / "clients" / "acme" / "audit" / "a-0001"
    audit_dir.mkdir(parents=True)
    sf = open_audit_sessions(audit_dir)
    assert isinstance(sf, SessionsFile)
    assert sf.path == audit_dir / "sessions.json"


def test_begin_then_finish_status_transitions(tmp_path: Path):
    audit_dir = tmp_path
    sf = open_audit_sessions(audit_dir)
    record = sf.begin("stage_1b", "session-uuid-1", engine="claude")
    assert isinstance(record, SessionRecord)
    assert record.status == "running"
    assert record.session_id == "session-uuid-1"
    assert record.engine == "claude"

    sf.finish("stage_1b", "complete")
    final = sf.get("stage_1b")
    assert final is not None
    assert final.status == "complete"
    assert final.finished_at is not None


def test_creates_sessions_file_under_audit_dir(tmp_path: Path):
    audit_dir = tmp_path
    sf = open_audit_sessions(audit_dir)
    sf.begin("stage_0", "sid-0", engine="claude")
    assert (audit_dir / "sessions.json").is_file()
