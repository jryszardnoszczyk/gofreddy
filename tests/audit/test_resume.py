"""Tests for src/audit/resume — viable_resume_id + build_resume_plan."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from harness.sessions import SessionRecord

from src.audit.exceptions import ViableResumeFailed
from src.audit.resume import (
    ResumePlan,
    build_resume_plan,
    viable_resume_id,
)
from src.audit.sessions import open_audit_sessions
from src.audit.state import AuditState


def _record(agent_key: str, status: str, sid: str = "sid-x") -> SessionRecord:
    return SessionRecord(
        agent_key=agent_key,
        session_id=sid,
        engine="claude",
        status=status,
        started_at=1700000000.0,
        finished_at=None if status == "running" else 1700000100.0,
    )


def test_viable_resume_id_returns_none_for_completed():
    record = _record("stage_1b", "complete")
    audit_dir = Path("/tmp/audit-dir-does-not-matter-for-this-test")
    assert viable_resume_id(record, audit_dir) is None


def test_viable_resume_id_returns_none_for_failed():
    record = _record("stage_1b", "failed")
    audit_dir = Path("/tmp/audit-dir-does-not-matter")
    assert viable_resume_id(record, audit_dir) is None


def test_viable_resume_id_returns_none_when_jsonl_missing(tmp_path: Path):
    audit_dir = tmp_path
    record = _record("stage_1b", "running", sid="sid-no-jsonl")
    # No JSONL at ~/.claude/projects/<encoded>/<sid>.jsonl — viable=None
    assert viable_resume_id(record, audit_dir) is None


def test_viable_resume_id_returns_sid_when_jsonl_exists(tmp_path: Path, monkeypatch):
    """Simulate the JSONL existing under a fake HOME so we don't pollute the
    real user's ~/.claude/projects directory."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))

    audit_dir = tmp_path / "audit"
    audit_dir.mkdir()
    sid = "valid-sid-12345"
    encoded = str(audit_dir).replace("/", "-")
    jsonl = fake_home / ".claude" / "projects" / encoded / f"{sid}.jsonl"
    jsonl.parent.mkdir(parents=True)
    jsonl.write_text("{}\n", encoding="utf-8")

    record = _record("stage_1b", "running", sid=sid)
    assert viable_resume_id(record, audit_dir) == sid


# ---------------------------------------------------------------------------
# build_resume_plan
# ---------------------------------------------------------------------------


def test_build_resume_plan_missing_audit_dir_raises():
    state = AuditState(audit_id="a-missing", client_slug="c", prospect_domain="d")
    with pytest.raises(ViableResumeFailed):
        build_resume_plan(
            audit_dir=Path("/nope/does/not/exist"),
            sessions=None,  # type: ignore[arg-type]
            state=state,
        )


def test_build_resume_plan_partitions_sessions(tmp_path: Path, monkeypatch):
    """Three sessions: one complete (skipped), one failed (must_restart),
    one running with viable JSONL (can_resume)."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))

    audit_dir = tmp_path / "audit"
    audit_dir.mkdir()
    sessions = open_audit_sessions(audit_dir)
    sessions.begin("stage_1b", "sid-running", engine="claude")
    sessions.begin("stage_1c", "sid-failed", engine="claude")
    sessions.finish("stage_1c", "failed")
    sessions.begin("stage_3", "sid-complete", engine="claude")
    sessions.finish("stage_3", "complete")

    # Make stage_1b's JSONL exist so it's viable
    encoded = str(audit_dir).replace("/", "-")
    jsonl = fake_home / ".claude" / "projects" / encoded / "sid-running.jsonl"
    jsonl.parent.mkdir(parents=True)
    jsonl.write_text("{}\n", encoding="utf-8")

    state = AuditState(
        audit_id="a-001",
        client_slug="c",
        prospect_domain="d",
        completed_lenses=("L-A-01", "L-A-02"),
    )

    plan = build_resume_plan(audit_dir=audit_dir, sessions=sessions, state=state)
    assert isinstance(plan, ResumePlan)
    assert plan.can_resume == {"stage_1b": "sid-running"}
    assert "stage_1c" in plan.must_restart
    assert "stage_3" not in plan.must_restart
    assert "stage_3" not in plan.can_resume
    assert plan.stage_2_skip == ("L-A-01", "L-A-02")


def test_build_resume_plan_running_without_jsonl_must_restart(tmp_path: Path, monkeypatch):
    """status='running' but JSONL is missing (claude silent-hung pre-token)
    → must_restart, not can_resume."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))

    audit_dir = tmp_path / "audit"
    audit_dir.mkdir()
    sessions = open_audit_sessions(audit_dir)
    sessions.begin("stage_1b", "sid-no-jsonl", engine="claude")

    state = AuditState(audit_id="a", client_slug="c", prospect_domain="d")
    plan = build_resume_plan(audit_dir=audit_dir, sessions=sessions, state=state)
    assert "stage_1b" in plan.must_restart
    assert plan.can_resume == {}
