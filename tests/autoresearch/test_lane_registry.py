"""Unit 1 tests for `autoresearch/lane_registry.py`.

Covers the 18 test scenarios from the bare-bones lane registry plan
(`docs/plans/2026-04-27-002-feat-autoresearch-lane-registry-plan.md` Unit 1):
LaneSpec accessors, default_objective_score_from_entry parity with frontier,
runtime assertion against models.py:160 Literal, and the file-bytes manifest
toolkit (file_hash + compute_manifest + verify_manifest).
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

# `_assert_models_literal_matches` imports `src.evaluation.models`; conftest only
# puts `autoresearch/` on sys.path, so add the repo root for that one test.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from autoresearch.lane_registry import (  # noqa: E402
    LANES,
    LaneSpec,
    _assert_models_literal_matches,
    all_lane_names,
    compute_manifest,
    default_objective_score_from_entry,
    file_hash,
    get_spec,
    verify_manifest,
    workflow_lane_names,
)


# ─── Accessors ───────────────────────────────────────────────────────────


def test_all_lane_names_in_insertion_order():
    assert all_lane_names() == ("core", "geo", "competitive", "monitoring", "storyboard")


def test_workflow_lane_names_excludes_core():
    assert workflow_lane_names() == ("geo", "competitive", "monitoring", "storyboard")


def test_get_spec_geo_rubric_ids():
    assert get_spec("geo").rubric_ids == (
        "GEO-1", "GEO-2", "GEO-3", "GEO-4", "GEO-5", "GEO-6", "GEO-7", "GEO-8",
    )


def test_get_spec_unknown_lane_raises_key_error():
    with pytest.raises(KeyError):
        get_spec("bogus")


def test_lanespec_is_frozen():
    spec = get_spec("geo")
    with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
        spec.name = "mutated"  # type: ignore[misc]


def test_core_lane_has_no_workflow_state():
    core = get_spec("core")
    assert core.is_workflow_lane is False
    assert core.rubric_ids == ()
    assert core.deliverables == ()
    assert core.session_md_filename == ""
    assert core.custom_mutate is None
    assert core.custom_score is None
    assert core.custom_validate is None
    assert core.custom_promote is None
    assert core.custom_objective_score_from_entry is None


def test_workflow_lanes_have_eight_rubric_ids_each():
    for name in workflow_lane_names():
        assert len(get_spec(name).rubric_ids) == 8, name


# ─── default_objective_score_from_entry parity with frontier ────────────


def test_objective_score_core_uses_composite():
    entry = {"search_metrics": {"composite": 0.77}}
    # Mirrors `frontier.composite_score(entry) -> 0.77`
    assert default_objective_score_from_entry(entry, "core") == 0.77


def test_objective_score_workflow_uses_domain_score():
    entry = {"search_metrics": {"domains": {"geo": {"score": 0.42}}}}
    # Mirrors `frontier.domain_score(entry, "geo") -> 0.42`
    assert default_objective_score_from_entry(entry, "geo") == 0.42


def test_objective_score_returns_none_when_search_metrics_missing():
    assert default_objective_score_from_entry({}, "core") is None
    assert default_objective_score_from_entry({}, "geo") is None


def test_objective_score_returns_none_when_workflow_domains_missing():
    entry = {"search_metrics": {"composite": 0.5}}  # no "domains" key
    assert default_objective_score_from_entry(entry, "geo") is None


def test_objective_score_returns_none_when_workflow_lane_payload_absent():
    entry = {"search_metrics": {"domains": {"geo": {"score": 0.5}}}}
    # Asking for "competitive" — not in the domains dict
    assert default_objective_score_from_entry(entry, "competitive") is None


def test_objective_score_uses_custom_callable_when_set():
    captured: dict[str, object] = {}

    def custom(entry):
        captured["entry"] = entry
        return 99.0

    fake = LaneSpec(name="fake", is_workflow_lane=True, custom_objective_score_from_entry=custom)
    LANES["fake"] = fake
    try:
        result = default_objective_score_from_entry({"x": 1}, "fake")
        assert result == 99.0
        assert captured["entry"] == {"x": 1}
    finally:
        del LANES["fake"]


# ─── Runtime assertion against models.py Literal ─────────────────────────


def test_assert_models_literal_matches_passes():
    # Should not raise — current models.py:160 Literal matches workflow lanes.
    _assert_models_literal_matches()


# ─── file_hash ────────────────────────────────────────────────────────────


def test_file_hash_matches_known_sha256(tmp_path: Path):
    target = tmp_path / "fixture.txt"
    target.write_text("hello world")
    expected = hashlib.sha256(b"hello world").hexdigest()
    assert file_hash(target) == expected


def test_file_hash_missing_file_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        file_hash(tmp_path / "does-not-exist")


def test_file_hash_is_idempotent(tmp_path: Path):
    target = tmp_path / "fixture.txt"
    target.write_text("repeatable input")
    assert file_hash(target) == file_hash(target)


# ─── compute_manifest ────────────────────────────────────────────────────


def test_compute_manifest_two_files(tmp_path: Path):
    a = tmp_path / "a.md"
    a.write_text("content-a")
    b = tmp_path / "sub" / "b.md"
    b.parent.mkdir()
    b.write_text("content-b")
    manifest = compute_manifest([a, b], tmp_path)
    assert set(manifest.keys()) == {"a.md", "sub/b.md"}
    assert manifest["a.md"] == hashlib.sha256(b"content-a").hexdigest()
    assert manifest["sub/b.md"] == hashlib.sha256(b"content-b").hexdigest()


def test_compute_manifest_empty_paths(tmp_path: Path):
    assert compute_manifest([], tmp_path) == {}


# ─── verify_manifest ─────────────────────────────────────────────────────


def test_verify_manifest_passes_when_files_unchanged(tmp_path: Path):
    target = tmp_path / "stable.md"
    target.write_text("untouched")
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(compute_manifest([target], tmp_path)))
    passed, failures = verify_manifest(manifest_path, tmp_path)
    assert passed is True
    assert failures == []


def test_verify_manifest_reports_missing_file(tmp_path: Path):
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps({"missing.md": "0" * 64}))
    passed, failures = verify_manifest(manifest_path, tmp_path)
    assert passed is False
    assert failures == ["missing: missing.md"]


def test_verify_manifest_reports_hash_mismatch(tmp_path: Path):
    target = tmp_path / "drift.md"
    target.write_text("original")
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(compute_manifest([target], tmp_path)))
    target.write_text("tampered")
    passed, failures = verify_manifest(manifest_path, tmp_path)
    assert passed is False
    assert len(failures) == 1
    assert failures[0].startswith("hash mismatch: drift.md")


def test_compute_then_verify_manifest_round_trip(tmp_path: Path):
    a = tmp_path / "one.txt"
    a.write_text("alpha")
    b = tmp_path / "nested" / "two.txt"
    b.parent.mkdir()
    b.write_text("beta")
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(compute_manifest([a, b], tmp_path)))
    passed, failures = verify_manifest(manifest_path, tmp_path)
    assert (passed, failures) == (True, [])
