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
    _persist_monitoring_dqs_score,
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
    assert all_lane_names() == (
        "core", "geo", "competitive", "monitoring", "storyboard",
        "marketing_audit", "x_engine", "linkedin_engine",
        "article_engine", "image_engine", "ad_engine",
    )


def test_workflow_lane_names_excludes_core():
    assert workflow_lane_names() == (
        "geo", "competitive", "monitoring", "storyboard",
        "marketing_audit", "x_engine", "linkedin_engine",
        "article_engine", "image_engine", "ad_engine",
    )


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


def test_workflow_lanes_have_expected_rubric_id_counts():
    """Per master plan v13 §1.5 D3: x_engine + linkedin_engine inline tuples
    instead of using `_rubric_ids("X")` which hardcodes range(1, 9) = 8 IDs.
    x_engine grew to 7 IDs (X-1..X-6 + X-9 added by judge plan v3 kernel
    expansion 2026-05-13). linkedin_engine stayed at 6. Other lanes keep
    the original 8 each, except storyboard which gained 3 compliance
    rubric IDs in Content Engine v1 U8 (one per active v1 rule set:
    gdpr_eu, medical_pl, legal_pl)."""
    expected: dict[str, int] = {
        "geo": 8,
        "competitive": 8,
        "monitoring": 8,
        "storyboard": 11,  # 8 SB + 3 reviewer-assist compliance per U8
        "marketing_audit": 8,
        "x_engine": 7,
        "linkedin_engine": 6,
        "article_engine": 11,  # 8 AE + 3 reviewer-assist compliance per U13
        "image_engine": 11,    # 8 IE + 3 reviewer-assist compliance per U14
        "ad_engine": 11,       # 8 AD + 3 reviewer-assist compliance per U15
    }
    for name in workflow_lane_names():
        assert len(get_spec(name).rubric_ids) == expected[name], name


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


# ─── _persist_monitoring_dqs_score (D3 hook — audit 2026-05-07) ─────────────


def test_persist_monitoring_dqs_score_writes_sidecar(tmp_path: Path):
    """Happy path: payload carries dqs_score, session_dir exists, sidecar written."""
    _persist_monitoring_dqs_score({"dqs_score": 4.21}, tmp_path, "fixture-x")
    payload = json.loads((tmp_path / "digest-meta.json").read_text())
    assert payload == {"dqs_score": 4.21}


def test_persist_monitoring_dqs_score_noop_when_score_missing(tmp_path: Path):
    """No-op when payload has no dqs_score — must not write a sidecar."""
    _persist_monitoring_dqs_score({}, tmp_path, "fixture-x")
    _persist_monitoring_dqs_score({"dqs_score": None}, tmp_path, "fixture-x")
    assert not (tmp_path / "digest-meta.json").exists()


def test_persist_monitoring_dqs_score_noop_when_session_dir_none(tmp_path: Path):
    """No-op when session_dir is None — defends against pre-evaluation
    fixtures (run.session_dir defaults to None until the run lands)."""
    _persist_monitoring_dqs_score({"dqs_score": 1.0}, None, "fixture-x")
    assert list(tmp_path.iterdir()) == []


def test_persist_monitoring_dqs_score_merges_into_existing_sidecar(tmp_path: Path):
    """Existing digest-meta.json keys are preserved; only dqs_score is updated."""
    existing = tmp_path / "digest-meta.json"
    existing.write_text(json.dumps({"week": "2026-W19", "source_count": 12}))
    _persist_monitoring_dqs_score({"dqs_score": 3.7}, tmp_path, "fixture-x")
    payload = json.loads(existing.read_text())
    assert payload == {"week": "2026-W19", "source_count": 12, "dqs_score": 3.7}


def test_persist_monitoring_dqs_score_recovers_from_malformed_sidecar(tmp_path: Path):
    """Existing digest-meta.json that is non-JSON or non-dict is replaced
    cleanly with a fresh {dqs_score} payload (instead of crashing)."""
    (tmp_path / "digest-meta.json").write_text("not-json")
    _persist_monitoring_dqs_score({"dqs_score": 2.0}, tmp_path, "fixture-x")
    payload = json.loads((tmp_path / "digest-meta.json").read_text())
    assert payload == {"dqs_score": 2.0}


def test_monitoring_lane_wires_persist_hook():
    """Registry consistency: monitoring's LaneSpec carries the hook; the other
    3 workflow lanes do NOT (they have no judge-side sidecar to persist)."""
    assert LANES["monitoring"].custom_persist_judge_payload is _persist_monitoring_dqs_score
    for lane in ("geo", "competitive", "storyboard", "core",
                 "x_engine", "linkedin_engine"):
        assert LANES[lane].custom_persist_judge_payload is None
