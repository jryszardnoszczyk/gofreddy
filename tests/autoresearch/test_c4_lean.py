"""Tests for Stream C C4-lean: rubric-hash propagation + extractive
evidence cap + parent-score cache invalidation (in ``evaluate_variant``).

Covers four helpers added to ``autoresearch.evaluate_variant``:
- ``_check_rubric_hash`` (raises ``JudgeRubricMismatch`` on disagreement)
- ``_apply_evidence_cap`` (env-gated; clips scores missing evidence)
- ``_current_rubric_version`` (best-effort import; soft-fails None)
- ``_load_parent_scores`` (returns None when stored ``rubric_hash`` is stale)
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from autoresearch import evaluate_variant as ev


# --- _check_rubric_hash -----------------------------------------------------


def test_rubric_check_skipped_when_version_unavailable(monkeypatch):
    monkeypatch.setattr(ev, "_current_rubric_version", lambda: None)
    ev._check_rubric_hash({"rubric_hash": "anything"})  # must not raise


def test_rubric_check_passes_on_match(monkeypatch):
    monkeypatch.setattr(ev, "_current_rubric_version", lambda: "abc123")
    ev._check_rubric_hash({"rubric_hash": "abc123"})  # must not raise


def test_rubric_check_raises_on_mismatch(monkeypatch):
    monkeypatch.setattr(ev, "_current_rubric_version", lambda: "abc123")
    with pytest.raises(ev.JudgeRubricMismatch):
        ev._check_rubric_hash({"rubric_hash": "different"})


def test_rubric_check_legacy_response_without_hash(monkeypatch):
    """Older judges that don't echo ``rubric_hash`` flow through unchanged."""
    monkeypatch.setattr(ev, "_current_rubric_version", lambda: "abc123")
    ev._check_rubric_hash({"score": 4.5})  # must not raise


# --- _apply_evidence_cap helpers --------------------------------------------


def _judge_response(
    primary_per_criterion: list[dict],
    secondary_per_criterion: list[dict] | None = None,
    primary_aggregate: float = 7.0,
    secondary_aggregate: float = 7.0,
) -> dict:
    if secondary_per_criterion is None:
        # deepcopy so the two families don't share dict refs — otherwise
        # mutating primary's per_criterion would silently rewrite secondary's.
        secondary_per_criterion = copy.deepcopy(primary_per_criterion)
    return {
        "primary": {
            "per_criterion": primary_per_criterion,
            "aggregate_score": primary_aggregate,
        },
        "secondary": {
            "per_criterion": secondary_per_criterion,
            "aggregate_score": secondary_aggregate,
        },
        "aggregate": {
            "aggregate_score": (primary_aggregate + secondary_aggregate) / 2,
            "structural_passed": True,
            "grounding_passed": True,
        },
    }


def test_evidence_cap_inert_when_env_unset(monkeypatch):
    monkeypatch.delenv("AUTORESEARCH_RUBRIC_HASH_ENFORCEMENT", raising=False)
    data = _judge_response([{"criterion": "X-1", "score": 9.0, "evidence": []}])
    ev._apply_evidence_cap(data)
    assert data["primary"]["per_criterion"][0]["score"] == 9.0
    assert "capped_no_evidence" not in data["primary"]["per_criterion"][0]
    assert "capped_no_evidence" not in data["aggregate"]


def test_evidence_cap_fires_when_evidence_empty(monkeypatch):
    monkeypatch.setenv("AUTORESEARCH_RUBRIC_HASH_ENFORCEMENT", "1")
    data = _judge_response(
        [
            {"criterion": "X-1", "score": 9.0, "evidence": []},
            {"criterion": "X-2", "score": 7.0, "evidence": [{"quote": "q", "source_anchor": "a.md"}]},
        ],
        primary_aggregate=8.0,
        secondary_aggregate=8.0,
    )
    ev._apply_evidence_cap(data)

    primary = data["primary"]["per_criterion"]
    assert primary[0]["score"] == 2.0
    assert primary[0]["capped_no_evidence"] is True
    assert primary[1]["score"] == 7.0
    assert "capped_no_evidence" not in primary[1]

    # Family aggregate = mean of (capped) per_criterion
    assert pytest.approx(data["primary"]["aggregate_score"]) == (2.0 + 7.0) / 2
    # Cross-family aggregate = mean of family means (both deep-copied)
    expected_cross = ((2.0 + 7.0) / 2 + (2.0 + 7.0) / 2) / 2
    assert pytest.approx(data["aggregate"]["aggregate_score"]) == expected_cross
    assert data["aggregate"]["capped_no_evidence"] is True


def test_evidence_cap_skipped_when_evidence_present(monkeypatch):
    monkeypatch.setenv("AUTORESEARCH_RUBRIC_HASH_ENFORCEMENT", "1")
    data = _judge_response([
        {"criterion": "X-1", "score": 9.5, "evidence": [{"quote": "q", "source_anchor": "a.md"}]},
        {"criterion": "X-2", "score": 8.0, "evidence": [{"quote": "q2", "source_anchor": "b.md"}]},
    ])
    ev._apply_evidence_cap(data)
    assert data["primary"]["per_criterion"][0]["score"] == 9.5
    assert "capped_no_evidence" not in data["aggregate"]


def test_evidence_cap_score_below_cap_not_clipped(monkeypatch):
    """A criterion already at/below the cap isn't flagged — the rule clips,
    not flags. Score 1.5 < 2.0 (default cap), so no change."""
    monkeypatch.setenv("AUTORESEARCH_RUBRIC_HASH_ENFORCEMENT", "1")
    data = _judge_response([{"criterion": "X-1", "score": 1.5, "evidence": []}])
    ev._apply_evidence_cap(data)
    assert data["primary"]["per_criterion"][0]["score"] == 1.5
    assert "capped_no_evidence" not in data["primary"]["per_criterion"][0]
    assert "capped_no_evidence" not in data["aggregate"]


def test_evidence_cap_handles_missing_per_criterion(monkeypatch):
    monkeypatch.setenv("AUTORESEARCH_RUBRIC_HASH_ENFORCEMENT", "1")
    data = {"score": 4.5, "aggregate": {"aggregate_score": 4.5}}
    ev._apply_evidence_cap(data)
    assert data == {"score": 4.5, "aggregate": {"aggregate_score": 4.5}}


def test_evidence_cap_env_override_score(monkeypatch):
    monkeypatch.setenv("AUTORESEARCH_RUBRIC_HASH_ENFORCEMENT", "1")
    monkeypatch.setenv("AUTORESEARCH_EVIDENCE_CAP_SCORE", "4.0")
    data = _judge_response([{"criterion": "X-1", "score": 9.0, "evidence": []}])
    ev._apply_evidence_cap(data)
    assert data["primary"]["per_criterion"][0]["score"] == 4.0


def test_evidence_cap_env_override_min_relaxes_requirement(monkeypatch):
    monkeypatch.setenv("AUTORESEARCH_RUBRIC_HASH_ENFORCEMENT", "1")
    monkeypatch.setenv("AUTORESEARCH_EVIDENCE_MIN", "0")
    data = _judge_response([{"criterion": "X-1", "score": 9.0, "evidence": []}])
    ev._apply_evidence_cap(data)
    assert data["primary"]["per_criterion"][0]["score"] == 9.0
    assert "capped_no_evidence" not in data["aggregate"]


def test_evidence_cap_partial_only_one_family_capped(monkeypatch):
    monkeypatch.setenv("AUTORESEARCH_RUBRIC_HASH_ENFORCEMENT", "1")
    data = _judge_response(
        primary_per_criterion=[
            {"criterion": "X-1", "score": 9.0, "evidence": [{"quote": "q", "source_anchor": "a.md"}]},
        ],
        secondary_per_criterion=[
            {"criterion": "X-1", "score": 9.0, "evidence": []},
        ],
        primary_aggregate=9.0,
        secondary_aggregate=9.0,
    )
    ev._apply_evidence_cap(data)
    assert data["primary"]["aggregate_score"] == 9.0  # untouched (LLM value)
    assert data["secondary"]["aggregate_score"] == 2.0  # capped + recomputed
    assert pytest.approx(data["aggregate"]["aggregate_score"]) == (9.0 + 2.0) / 2
    assert data["aggregate"]["capped_no_evidence"] is True


# --- _load_parent_scores cache invalidation --------------------------------


def _write_scores(archive_dir: Path, parent_id: str, payload: dict) -> Path:
    parent_dir = archive_dir / parent_id
    parent_dir.mkdir(parents=True, exist_ok=True)
    scores_path = parent_dir / "scores.json"
    scores_path.write_text(json.dumps(payload))
    return scores_path


@pytest.fixture
def real_load_json(monkeypatch):
    """The autoresearch conftest stubs ``load_json`` to return ``{}`` to
    keep evaluate_variant importable; these tests need the real version so
    on-disk scores.json content is actually read back."""
    def _impl(path: Path, default=None):
        if not path.exists():
            return default
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return default
    monkeypatch.setattr(ev, "load_json", _impl)


def test_load_parent_scores_missing_file(tmp_path, real_load_json):
    assert ev._load_parent_scores(tmp_path, "v007") is None


def test_load_parent_scores_returns_results_when_hash_matches(
    tmp_path, monkeypatch, real_load_json,
):
    monkeypatch.setattr(ev, "_current_rubric_version", lambda: "abc123")
    _write_scores(tmp_path, "v007", {
        "rubric_hash": "abc123",
        "domains": {
            "geo": {"results": [{"fixture_id": "geo-1", "score": 4.5}]},
        },
    })
    result = ev._load_parent_scores(tmp_path, "v007")
    assert result is not None
    assert result["geo"][0]["fixture_id"] == "geo-1"


def test_load_parent_scores_rejects_when_hash_differs(
    tmp_path, monkeypatch, real_load_json,
):
    """Cache invalidation: stale rubric → caller re-judges."""
    monkeypatch.setattr(ev, "_current_rubric_version", lambda: "newhash")
    _write_scores(tmp_path, "v007", {
        "rubric_hash": "oldhash",
        "domains": {"geo": {"results": [{"fixture_id": "geo-1", "score": 4.5}]}},
    })
    assert ev._load_parent_scores(tmp_path, "v007") is None


def test_load_parent_scores_legacy_without_hash_kept(
    tmp_path, monkeypatch, real_load_json,
):
    """Pre-C4-lean scores.json has no ``rubric_hash`` field — back-compat."""
    monkeypatch.setattr(ev, "_current_rubric_version", lambda: "abc123")
    _write_scores(tmp_path, "v007", {
        "domains": {"geo": {"results": [{"fixture_id": "geo-1", "score": 4.5}]}},
    })
    result = ev._load_parent_scores(tmp_path, "v007")
    assert result is not None
    assert "geo" in result


def test_load_parent_scores_skips_check_when_rubrics_module_missing(
    tmp_path, monkeypatch, real_load_json,
):
    """If the rubrics module isn't importable, the check is skipped even
    when the stored payload has a ``rubric_hash`` field."""
    monkeypatch.setattr(ev, "_current_rubric_version", lambda: None)
    _write_scores(tmp_path, "v007", {
        "rubric_hash": "whatever",
        "domains": {"geo": {"results": [{"fixture_id": "geo-1", "score": 4.5}]}},
    })
    result = ev._load_parent_scores(tmp_path, "v007")
    assert result is not None


# --- C5 RaR weighted-composite aggregation ---------------------------------


def test_tier_weights_inert_when_env_unset(monkeypatch):
    monkeypatch.delenv("AUTORESEARCH_RAR_TIER_WEIGHTS", raising=False)
    data = _judge_response([
        {"criterion": "GEO-1", "score": 10.0},
        {"criterion": "GEO-2", "score": 0.0},
    ], primary_aggregate=5.0, secondary_aggregate=5.0)
    ev._apply_tier_weights(data, "geo")
    # Aggregate untouched (LLM value 5.0 stays).
    assert data["aggregate"]["aggregate_score"] == 5.0
    assert "tier_weighted" not in data["aggregate"]


def test_tier_weights_recomputes_aggregate_when_env_set(monkeypatch):
    """All 8 GEO scores at 10.0 → weighted composite is 10.0 regardless of
    tier mix (weighted mean of identical values equals the value)."""
    monkeypatch.setenv("AUTORESEARCH_RAR_TIER_WEIGHTS", "1")
    per_criterion = [
        {"criterion": f"GEO-{i}", "score": 10.0} for i in range(1, 9)
    ]
    data = _judge_response(per_criterion, primary_aggregate=7.5, secondary_aggregate=7.5)
    ev._apply_tier_weights(data, "geo")
    assert data["primary"]["aggregate_score"] == 10.0
    assert data["secondary"]["aggregate_score"] == 10.0
    assert data["aggregate"]["aggregate_score"] == 10.0
    assert data["aggregate"]["tier_weighted"] is True


def test_tier_weights_essential_dominates_optional(monkeypatch):
    """When essential criteria pass (10) and optional fail (0), the
    weighted aggregate skews toward essential — higher than the uniform
    mean of the same scores."""
    monkeypatch.setenv("AUTORESEARCH_RAR_TIER_WEIGHTS", "1")
    # GEO-1 (essential, 1.0) = 10
    # GEO-4 (optional, 0.3) = 0
    # uniform mean = 5.0
    # weighted = (1.0*10 + 0.3*0) / (1.0 + 0.3) = 10 / 1.3 ≈ 7.69
    per_criterion = [
        {"criterion": "GEO-1", "score": 10.0},
        {"criterion": "GEO-4", "score": 0.0},
    ]
    data = _judge_response(per_criterion)
    ev._apply_tier_weights(data, "geo")
    assert pytest.approx(data["primary"]["aggregate_score"], abs=0.01) == 10.0 / 1.3


def test_tier_weights_pitfall_violation_pulls_aggregate_down(monkeypatch):
    """GEO-8 is tagged ``pitfall`` (weight 0.8). When pitfall is violated
    (score 0) and other scores are 10, the pitfall's contribution to the
    numerator is 0 — pulling the weighted mean below uniform 10."""
    monkeypatch.setenv("AUTORESEARCH_RAR_TIER_WEIGHTS", "1")
    per_criterion = [
        {"criterion": "GEO-1", "score": 10.0},  # essential 1.0
        {"criterion": "GEO-8", "score": 0.0},   # pitfall 0.8
    ]
    data = _judge_response(per_criterion)
    ev._apply_tier_weights(data, "geo")
    # (1.0*10 + 0.8*0) / (1.0 + 0.8) = 10 / 1.8 ≈ 5.56
    assert pytest.approx(data["primary"]["aggregate_score"], abs=0.01) == 10.0 / 1.8


def test_tier_weights_falls_back_to_position_when_id_missing(monkeypatch):
    """When per_criterion entries lack rubric IDs in the ``criterion``
    field, _resolve_tier falls back to position-based mapping against
    domain rubrics sorted alphabetically."""
    monkeypatch.setenv("AUTORESEARCH_RAR_TIER_WEIGHTS", "1")
    # 8 entries with generic names → positions 0..7 map to GEO-1..GEO-8
    per_criterion = [
        {"criterion": f"axis {i}", "score": 10.0 if i == 0 else 0.0}
        for i in range(8)
    ]
    data = _judge_response(per_criterion)
    ev._apply_tier_weights(data, "geo")
    assert data["aggregate"]["tier_weighted"] is True
    # Position 0 → GEO-1 (essential 1.0); positions 1-7 → other tiers (all 0)
    # Weight sum for GEO 1..8 = 1.0 + 1.0 + 0.7 + 0.3 + 0.7 + 0.7 + 1.0 + 0.8 = 6.2
    # Numerator = 1.0 * 10 + 0 = 10
    # Weighted = 10 / 6.2 ≈ 1.613
    assert pytest.approx(data["primary"]["aggregate_score"], abs=0.01) == 10.0 / 6.2


def test_tier_weights_unknown_domain_falls_through(monkeypatch):
    """If domain has no rubrics, _apply_tier_weights is a no-op."""
    monkeypatch.setenv("AUTORESEARCH_RAR_TIER_WEIGHTS", "1")
    data = _judge_response([{"criterion": "X", "score": 5.0}],
                            primary_aggregate=3.3, secondary_aggregate=3.3)
    ev._apply_tier_weights(data, "no_such_domain")
    assert data["aggregate"]["aggregate_score"] == 3.3
    assert "tier_weighted" not in data["aggregate"]


def test_tier_weights_pairs_with_evidence_cap(monkeypatch):
    """Cap+weight chain: when both flags are set, the evidence cap clips
    per_criterion scores first, then the weighted composite uses the
    capped values."""
    monkeypatch.setenv("AUTORESEARCH_RUBRIC_HASH_ENFORCEMENT", "1")
    monkeypatch.setenv("AUTORESEARCH_RAR_TIER_WEIGHTS", "1")
    per_criterion = [
        # GEO-1 essential 1.0 — score 10 but no evidence → capped to 2.0
        {"criterion": "GEO-1", "score": 10.0, "evidence": []},
        # GEO-2 essential 1.0 — has evidence → stays at 10
        {"criterion": "GEO-2", "score": 10.0, "evidence": [{"quote": "q", "source_anchor": "a.md"}]},
    ]
    data = _judge_response(per_criterion)
    ev._apply_evidence_cap(data)
    ev._apply_tier_weights(data, "geo")
    # GEO-1 capped to 2.0, GEO-2 stays at 10.0; both essential weight 1.0
    # weighted = (1.0 * 2.0 + 1.0 * 10.0) / 2.0 = 6.0
    assert pytest.approx(data["primary"]["aggregate_score"]) == 6.0
    assert data["aggregate"]["tier_weighted"] is True
    assert data["aggregate"]["capped_no_evidence"] is True
