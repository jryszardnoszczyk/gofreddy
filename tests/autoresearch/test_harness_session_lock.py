"""Regression tests for autoresearch/harness/util.py session locks.

Finding #120 (2026-05-09): parent baseline scoring + candidate scoring of the
same fixture used to share a lock path, causing one of the two concurrent
processes to bail in 0.4s with "Session already running" and produce a
0-deliverable spurious score. The fix partitions lock paths by variant_id
(via the AUTORESEARCH_VARIANT_ID env var, exported by evaluate_variant.py)
in addition to fixture_id.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Path bootstrap matches sibling autoresearch harness tests
_repo_root = Path(__file__).resolve().parents[2]
_autoresearch_dir = _repo_root / "autoresearch"
if str(_autoresearch_dir) in sys.path:
    sys.path.remove(str(_autoresearch_dir))
sys.path.insert(0, str(_autoresearch_dir))
for _mod in [m for m in list(sys.modules) if m == "harness" or m.startswith("harness.")]:
    file_attr = getattr(sys.modules[_mod], "__file__", None) or ""
    if not file_attr.startswith(str(_autoresearch_dir)):
        del sys.modules[_mod]

from harness.util import _lock_path, acquire_lock, release_lock  # noqa: E402


def test_lock_path_partitions_by_variant(monkeypatch):
    """Two variants on the same fixture must yield distinct lock paths."""
    monkeypatch.setenv("AUTORESEARCH_FIXTURE_ID", "geo-mayoclinic-atrial-fibrillation")
    monkeypatch.setenv("AUTORESEARCH_VARIANT_ID", "v007")
    parent = _lock_path("geo", "mayoclinic")
    monkeypatch.setenv("AUTORESEARCH_VARIANT_ID", "v176")
    candidate = _lock_path("geo", "mayoclinic")
    assert parent != candidate, (
        "parent + candidate scoring of the same fixture must use distinct "
        f"lock paths (got {parent} for both)"
    )
    assert "v007" in parent.name
    assert "v176" in candidate.name


def test_lock_path_back_compat_no_variant(monkeypatch):
    """No variant_id → name omits variant token (live operator runs)."""
    monkeypatch.delenv("AUTORESEARCH_VARIANT_ID", raising=False)
    monkeypatch.setenv("AUTORESEARCH_FIXTURE_ID", "fix-1")
    path = _lock_path("geo", "mayoclinic")
    assert path.name == "geo-session-mayoclinic-fix-1.lock"


def test_lock_path_no_fixture_no_variant(monkeypatch):
    """No fixture or variant → original "<domain>-session-<client>.lock" form."""
    monkeypatch.delenv("AUTORESEARCH_VARIANT_ID", raising=False)
    monkeypatch.delenv("AUTORESEARCH_FIXTURE_ID", raising=False)
    path = _lock_path("competitive", "axios")
    assert path.name == "competitive-session-axios.lock"


def test_concurrent_lock_acquire_per_variant(tmp_path, monkeypatch):
    """Both v007 + v176 can hold their respective locks at once."""
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    monkeypatch.setenv("AUTORESEARCH_FIXTURE_ID", "geo-mayo-atrial")

    monkeypatch.setenv("AUTORESEARCH_VARIANT_ID", "v007")
    fd_parent = acquire_lock("geo", "mayoclinic")
    assert fd_parent is not None, "parent (v007) should acquire the lock"

    try:
        monkeypatch.setenv("AUTORESEARCH_VARIANT_ID", "v176")
        fd_candidate = acquire_lock("geo", "mayoclinic")
        assert fd_candidate is not None, (
            "candidate (v176) should acquire its own per-variant lock "
            "while v007's lock is still held — Finding #120 regression"
        )
        release_lock(fd_candidate, "geo", "mayoclinic")
    finally:
        # Reset env to the parent's variant_id before releasing so the
        # release path computes the same lock filename it created.
        monkeypatch.setenv("AUTORESEARCH_VARIANT_ID", "v007")
        release_lock(fd_parent, "geo", "mayoclinic")


def test_concurrent_lock_collision_same_variant(tmp_path, monkeypatch):
    """Same variant + same fixture must still serialize (lock semantics)."""
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    monkeypatch.setenv("AUTORESEARCH_FIXTURE_ID", "geo-mayo-atrial")
    monkeypatch.setenv("AUTORESEARCH_VARIANT_ID", "v007")

    fd_first = acquire_lock("geo", "mayoclinic")
    assert fd_first is not None
    try:
        fd_second = acquire_lock("geo", "mayoclinic")
        assert fd_second is None, (
            "second acquire on the same (domain, client, fixture, variant) "
            "must fail — preserves the original mutual-exclusion guarantee"
        )
    finally:
        release_lock(fd_first, "geo", "mayoclinic")
