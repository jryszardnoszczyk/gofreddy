"""Tests for harness/session_paths.py — per-fixture session directory
resolution (task #97).

The helper exists because x_engine + linkedin_engine all use ``client="jr"``
and distinguish themselves only by ``context`` = angle_id. Pre-fix, all 4
parallel fixtures wrote to the same ``sessions/<lane>/jr/`` and overwrote
each other's results.jsonl. Lane-conditional path nesting fixes that
without touching geo/competitive/etc. (which already have unique clients).
"""
from __future__ import annotations

from pathlib import Path

import pytest

# conftest.py puts autoresearch/harness on sys.path.
from session_paths import (  # noqa: E402
    LANES_NEEDING_CONTEXT_ISOLATION,
    find_variant_root,
    session_dir_for,
)


# ─── session_dir_for ─────────────────────────────────────────────────────────


def test_session_dir_for_x_engine_isolates_by_context(tmp_path: Path):
    """The headline behavior: x_engine fixtures with different angle_ids
    get distinct session_dirs even though they share client='jr'."""
    fixt_121 = session_dir_for(tmp_path, "x_engine", "jr", "121")
    fixt_122 = session_dir_for(tmp_path, "x_engine", "jr", "122")
    assert fixt_121 != fixt_122
    assert fixt_121 == tmp_path / "sessions" / "x_engine" / "jr" / "121"
    assert fixt_122 == tmp_path / "sessions" / "x_engine" / "jr" / "122"


def test_session_dir_for_linkedin_engine_isolates_by_context(tmp_path: Path):
    """linkedin_engine has the same shared-client problem as x_engine
    (per fixture spec) and gets the same isolation treatment."""
    a = session_dir_for(tmp_path, "linkedin_engine", "jr", "201")
    b = session_dir_for(tmp_path, "linkedin_engine", "jr", "202")
    assert a != b
    assert a.parent.name == "jr"  # context is leaf
    assert b.parent.name == "jr"


def test_session_dir_for_geo_keeps_legacy_two_level_path(tmp_path: Path):
    """Geo (and other lanes with unique-per-fixture clients) preserves
    the legacy 2-level path. Backwards-compat with all existing geo
    archives — this is the safety property that lets us avoid changing
    parents[N] arithmetic codebase-wide."""
    result = session_dir_for(tmp_path, "geo", "nubank", "https://nubank.com.br")
    # Even with a non-empty context, geo gets the 2-level shape.
    assert result == tmp_path / "sessions" / "geo" / "nubank"


def test_session_dir_for_x_engine_with_empty_context_falls_back(tmp_path: Path):
    """Cold-start x_engine invocations (no context yet, e.g. operator
    debug runs) get the legacy 2-level path so init_session can't crash
    on a None/empty context. Defensive: better to share the dir than to
    error during a setup call."""
    result = session_dir_for(tmp_path, "x_engine", "jr", "")
    assert result == tmp_path / "sessions" / "x_engine" / "jr"
    result_none = session_dir_for(tmp_path, "x_engine", "jr", None)
    assert result_none == tmp_path / "sessions" / "x_engine" / "jr"


def test_session_dir_for_sanitizes_unsafe_context(tmp_path: Path):
    """Context goes into the filesystem path — sanitize problematic chars
    so a future schema where context contains slashes / shell metachars
    can't break path semantics or create traversal openings."""
    weird = "121/../etc/passwd"
    result = session_dir_for(tmp_path, "x_engine", "jr", weird)
    # Sanitization replaces /, ., etc. with underscores so the leaf is
    # still a single dir name, no path traversal.
    assert result.parent == tmp_path / "sessions" / "x_engine" / "jr"
    assert "/" not in result.name
    assert "../" not in str(result.relative_to(tmp_path))


def test_session_dir_for_caps_long_context(tmp_path: Path):
    """Pathologically long context (e.g. URL accidentally passed as
    context) gets capped at 64 chars so we don't hit ENAMETOOLONG."""
    very_long = "a" * 500
    result = session_dir_for(tmp_path, "x_engine", "jr", very_long)
    assert len(result.name) <= 64


def test_lanes_needing_context_isolation_is_minimal():
    """Only x_engine + linkedin_engine should be in the isolation set.
    Adding more lanes silently changes their archive shape — guard
    against accidental scope expansion."""
    assert LANES_NEEDING_CONTEXT_ISOLATION == frozenset({
        "x_engine", "linkedin_engine",
    })


# ─── find_variant_root ────────────────────────────────────────────────────


def test_find_variant_root_two_level_session(tmp_path: Path):
    """Legacy shape: variant/sessions/<lane>/<client>/. Walk up until
    'sessions/' parent — that's the variant root."""
    session = tmp_path / "v006" / "sessions" / "geo" / "nubank"
    session.mkdir(parents=True)
    assert find_variant_root(session) == tmp_path / "v006"


def test_find_variant_root_three_level_session(tmp_path: Path):
    """New shape (x_engine/linkedin): variant/sessions/<lane>/<client>/
    <context>/. Helper must still return variant root regardless of the
    extra depth — that's the whole point of avoiding parents[2] arithmetic."""
    session = tmp_path / "v192" / "sessions" / "x_engine" / "jr" / "121"
    session.mkdir(parents=True)
    assert find_variant_root(session) == tmp_path / "v192"


def test_find_variant_root_raises_when_no_sessions_ancestor(tmp_path: Path):
    """If session_dir isn't actually under a 'sessions/' folder, surface
    loudly rather than silently returning some arbitrary parent."""
    weird = tmp_path / "scratch" / "foo" / "bar"
    weird.mkdir(parents=True)
    with pytest.raises(ValueError, match="no 'sessions/' ancestor"):
        find_variant_root(weird)
