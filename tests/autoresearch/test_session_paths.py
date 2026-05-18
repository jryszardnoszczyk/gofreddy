"""Tests for harness/session_paths.py (#97)."""
from __future__ import annotations

from pathlib import Path

import pytest

from session_paths import (  # noqa: E402
    LANES_NEEDING_CONTEXT_ISOLATION,
    find_variant_root,
    session_dir_for,
)


def test_session_dir_for_x_engine_isolates_by_context(tmp_path: Path):
    a = session_dir_for(tmp_path, "x_engine", "jr", "121")
    b = session_dir_for(tmp_path, "x_engine", "jr", "122")
    assert a == tmp_path / "sessions" / "x_engine" / "jr" / "121"
    assert b == tmp_path / "sessions" / "x_engine" / "jr" / "122"


def test_session_dir_for_linkedin_engine_isolates_by_context(tmp_path: Path):
    a = session_dir_for(tmp_path, "linkedin_engine", "jr", "201")
    b = session_dir_for(tmp_path, "linkedin_engine", "jr", "202")
    assert a != b
    assert a.parent.name == "jr"


def test_session_dir_for_geo_keeps_legacy_two_level_path(tmp_path: Path):
    """Non-isolated lanes ignore context to preserve backwards-compat."""
    result = session_dir_for(tmp_path, "geo", "nubank", "https://nubank.com.br")
    assert result == tmp_path / "sessions" / "geo" / "nubank"


def test_session_dir_for_x_engine_with_empty_context_falls_back(tmp_path: Path):
    assert session_dir_for(tmp_path, "x_engine", "jr", "") == tmp_path / "sessions" / "x_engine" / "jr"
    assert session_dir_for(tmp_path, "x_engine", "jr", None) == tmp_path / "sessions" / "x_engine" / "jr"


def test_session_dir_for_sanitizes_unsafe_context(tmp_path: Path):
    result = session_dir_for(tmp_path, "x_engine", "jr", "121/../etc/passwd")
    assert result.parent == tmp_path / "sessions" / "x_engine" / "jr"
    assert "/" not in result.name


def test_session_dir_for_caps_long_context(tmp_path: Path):
    result = session_dir_for(tmp_path, "x_engine", "jr", "a" * 500)
    assert len(result.name) <= 64


def test_lanes_needing_context_isolation_is_minimal():
    """Guard against accidental scope expansion to other lanes."""
    assert LANES_NEEDING_CONTEXT_ISOLATION == frozenset({"x_engine", "linkedin_engine"})


def test_find_variant_root_two_level_session(tmp_path: Path):
    session = tmp_path / "v006" / "sessions" / "geo" / "nubank"
    session.mkdir(parents=True)
    assert find_variant_root(session) == tmp_path / "v006"


def test_find_variant_root_three_level_session(tmp_path: Path):
    session = tmp_path / "v192" / "sessions" / "x_engine" / "jr" / "121"
    session.mkdir(parents=True)
    assert find_variant_root(session) == tmp_path / "v192"


def test_find_variant_root_raises_when_no_sessions_ancestor(tmp_path: Path):
    weird = tmp_path / "scratch" / "foo" / "bar"
    weird.mkdir(parents=True)
    with pytest.raises(ValueError):
        find_variant_root(weird)
