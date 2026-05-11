"""Tests for Stream C C21 — degenerate-cycle detection.

Covers the three pure detectors + the lane-aware wrapper that reads
recent composite scores from lineage.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from autoresearch import cycle_detectors as cd


# --- detect_saturated_metrics ----------------------------------------------
# Defaults assume the gofreddy composite scale (0-10). Tests that
# exercise the upstream 0-1 normalization override via low=/high=.


def test_saturated_all_at_floor_default_scale():
    assert cd.detect_saturated_metrics([0.0, 0.1, 0.5]) is True


def test_saturated_all_at_ceiling_default_scale():
    assert cd.detect_saturated_metrics([9.5, 9.8, 10.0]) is True


def test_saturated_mix_floor_and_ceiling_default_scale():
    """Mixed floor + ceiling (all-or-nothing scoring) — still saturated."""
    assert cd.detect_saturated_metrics([0.0, 10.0, 0.5, 9.7]) is True


def test_saturated_with_intermediate_values_is_not_saturated():
    """Mid-range composites (4-5) signal real progress, not saturation."""
    assert cd.detect_saturated_metrics([4.5, 5.0, 4.8]) is False


def test_saturated_override_for_unit_scale():
    """Operators on a 0-1 rubric can pass scale-appropriate thresholds."""
    assert cd.detect_saturated_metrics(
        [0.0, 0.001, 0.999, 1.0], low=0.001, high=0.999,
    ) is True


def test_saturated_single_value_returns_false():
    """Single observation is insufficient signal — accept-by-default."""
    assert cd.detect_saturated_metrics([0.0]) is False


def test_saturated_filters_none_values():
    """None entries are skipped; what remains must still meet the bar."""
    assert cd.detect_saturated_metrics([None, 0.0, 0.5]) is True


# --- detect_identical_iterations -------------------------------------------


def test_identical_iterations_true():
    assert cd.detect_identical_iterations([4.5, 4.5, 4.5]) is True


def test_identical_iterations_false_with_drift():
    assert cd.detect_identical_iterations([4.5, 4.6, 4.5]) is False


def test_identical_iterations_floating_point_tolerance():
    """Float-noise-level differences (sub-1e-6) should still count as identical."""
    assert cd.detect_identical_iterations([4.5, 4.500000001, 4.5]) is True


def test_identical_iterations_single_value_returns_false():
    assert cd.detect_identical_iterations([4.5]) is False


# --- detect_trivial_ablations ----------------------------------------------


def test_trivial_ablations_majority_trivial():
    ablations = [
        {"delta": 0.001},
        {"delta": -0.002},
        {"delta": 0.5},
    ]
    n_trivial, n_total = cd.detect_trivial_ablations(ablations)
    assert n_trivial == 2
    assert n_total == 3


def test_trivial_ablations_threshold_override():
    ablations = [{"delta": 0.05}, {"delta": -0.04}]
    # Default threshold 0.02 → both non-trivial; bumping to 0.1 → both trivial
    assert cd.detect_trivial_ablations(ablations) == (0, 2)
    assert cd.detect_trivial_ablations(ablations, threshold=0.1) == (2, 2)


def test_trivial_ablations_skips_non_dict_entries():
    ablations = [{"delta": 0.001}, "garbage", {"delta": 0.5}]
    assert cd.detect_trivial_ablations(ablations) == (1, 2)


def test_trivial_ablations_skips_entries_without_numeric_delta():
    ablations = [{"delta": "nope"}, {"delta": 0.001}, {}]
    assert cd.detect_trivial_ablations(ablations) == (1, 1)


def test_trivial_ablations_empty_input():
    assert cd.detect_trivial_ablations([]) == (0, 0)


# --- _coerce_composite ------------------------------------------------------


def test_coerce_composite_canonical_path():
    entry = {"search_metrics": {"domains": {"geo": {"composite": 4.5}}}}
    assert cd._coerce_composite(entry, "geo") == 4.5


def test_coerce_composite_flat_fallback():
    entry = {"search_metrics": {"composite": 5.0}}
    assert cd._coerce_composite(entry, "geo") == 5.0


def test_coerce_composite_returns_none_when_absent():
    entry = {"search_metrics": {"domains": {}}}
    assert cd._coerce_composite(entry, "geo") is None


# --- check_lane_degenerate (end-to-end with mocked lineage) ----------------


def _patched_lineage(monkeypatch, entries):
    monkeypatch.setattr(
        "autoresearch.archive_index.load_lineage_history",
        lambda *a, **k: entries,
    )


def test_check_lane_degenerate_saturated_warns(tmp_path, monkeypatch):
    _patched_lineage(monkeypatch, [
        {"id": f"v{i:03d}", "lane": "geo", "search_metrics": {"composite": 0.0}}
        for i in range(3)
    ])
    is_degen, advisory, meta = cd.check_lane_degenerate(tmp_path, "geo")
    assert is_degen is True
    assert "saturated" in advisory.lower()
    assert meta["saturated"] is True


def test_check_lane_degenerate_identical_warns(tmp_path, monkeypatch):
    _patched_lineage(monkeypatch, [
        {"id": f"v{i:03d}", "lane": "geo", "search_metrics": {"composite": 4.5}}
        for i in range(3)
    ])
    is_degen, advisory, meta = cd.check_lane_degenerate(tmp_path, "geo")
    assert is_degen is True
    assert "identical" in advisory.lower()
    assert meta["identical"] is True


def test_check_lane_degenerate_healthy_signal_no_warning(tmp_path, monkeypatch):
    _patched_lineage(monkeypatch, [
        {"id": "v001", "lane": "geo", "search_metrics": {"composite": 3.5}},
        {"id": "v002", "lane": "geo", "search_metrics": {"composite": 4.2}},
        {"id": "v003", "lane": "geo", "search_metrics": {"composite": 5.0}},
    ])
    is_degen, advisory, _meta = cd.check_lane_degenerate(tmp_path, "geo")
    assert is_degen is False
    assert advisory == ""


def test_check_lane_degenerate_filters_other_lanes(tmp_path, monkeypatch):
    """Composites from other lanes must not poison the detection."""
    _patched_lineage(monkeypatch, [
        {"id": "v001", "lane": "geo", "search_metrics": {"composite": 4.5}},
        {"id": "v002", "lane": "competitive", "search_metrics": {"composite": 0.0}},
        {"id": "v003", "lane": "geo", "search_metrics": {"composite": 4.5}},
        {"id": "v004", "lane": "geo", "search_metrics": {"composite": 4.5}},
    ])
    is_degen, _advisory, meta = cd.check_lane_degenerate(tmp_path, "geo")
    assert is_degen is True
    assert meta["history"] == [4.5, 4.5, 4.5]  # competitive entry filtered out


def test_check_lane_degenerate_empty_lineage(tmp_path, monkeypatch):
    _patched_lineage(monkeypatch, [])
    is_degen, advisory, meta = cd.check_lane_degenerate(tmp_path, "geo")
    assert is_degen is False
    assert advisory == ""
    assert meta["history"] == []
