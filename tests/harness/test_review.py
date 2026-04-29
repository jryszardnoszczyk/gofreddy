"""Tests for harness.review — pr_body and compose output shape."""
from __future__ import annotations

from pathlib import Path

from harness.review import CommitRecord, pr_body


def _commit(track: str, fid: str, summary: str = "real fix") -> CommitRecord:
    return CommitRecord(
        sha="a" * 40, finding_id=fid, summary=summary, track=track,
        files=("cli/freddy/x.py",), reproduction="", adjacent_checked=(),
    )


def test_pr_body_excludes_no_op_markers_from_headline_count(tmp_path):
    """NO-OP markers (cascade-resolved findings) live in state.commits so
    resume can skip them, but they are NOT verified fixes. The pr-body
    headline must reflect only real, code-changing fixes."""
    commits = [
        _commit("a", "F-a-1", "real fix one"),
        _commit("a", "F-a-2", "NO-OP cascade-resolved by F-a-1"),
        _commit("b", "F-b-1", "real fix two"),
    ]
    body = pr_body(tmp_path, commits, tip_smoke_ok=True)
    assert "2 verified fixes" in body
    assert "3 verified fixes" not in body


def test_pr_body_per_track_count_excludes_no_ops(tmp_path):
    """Per-track counts must also exclude NO-OPs."""
    commits = [
        _commit("a", "F-a-1", "real fix one"),
        _commit("a", "F-a-2", "NO-OP cascade-resolved"),
        _commit("a", "F-a-3", "real fix two"),
    ]
    body = pr_body(tmp_path, commits, tip_smoke_ok=True)
    assert "Track A (2 fixes)" in body
    assert "Track A (3 fixes)" not in body


def test_pr_body_renders_no_ops_in_dedicated_section(tmp_path):
    """NO-OPs stay visible to reviewers — just under a separate header that
    doesn't inflate the verified-fix metric."""
    commits = [
        _commit("a", "F-a-1", "real fix one"),
        _commit("a", "F-a-2", "NO-OP cascade-resolved by F-a-1"),
    ]
    body = pr_body(tmp_path, commits, tip_smoke_ok=True)
    assert "Cascade-resolved (no code change) — 1" in body
    assert "F-a-2" in body


def test_pr_body_no_op_only_run_reports_zero_verified(tmp_path):
    """Edge case: a run that produced only NO-OP markers."""
    commits = [
        _commit("a", "F-a-1", "NO-OP cascade-resolved"),
        _commit("a", "F-a-2", "NO-OP cascade-resolved"),
    ]
    body = pr_body(tmp_path, commits, tip_smoke_ok=True)
    assert "0 verified fixes" in body
    assert "Cascade-resolved (no code change) — 2" in body
    assert "Track A" not in body  # no per-track section when no real fixes


def test_pr_body_no_no_ops_omits_cascade_section(tmp_path):
    """Clean run — no cascade section emitted."""
    commits = [_commit("a", "F-a-1", "real fix")]
    body = pr_body(tmp_path, commits, tip_smoke_ok=True)
    assert "1 verified fixes" in body
    assert "Cascade-resolved" not in body
