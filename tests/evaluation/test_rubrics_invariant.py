"""RUBRICS ↔ LaneSpec.rubric_ids derived-count invariant.

The total rubric count is *derived* from the sum of every LaneSpec's
``rubric_ids`` tuple, not a hardcoded magic number. Per-lane increments
update the LaneSpec; the RUBRICS dict gains matching prose. The invariant
is enforced at module load time in ``src/evaluation/rubrics.py``; this
test file exercises the logical invariant independently so that breakage
in *either* direction (lane added without prose, prose without a lane) is
caught by a focused test before it surfaces as an opaque assert at import.
"""
from __future__ import annotations

import pytest


def test_rubrics_module_imports_cleanly() -> None:
    """Sanity: the module-level assertions in ``rubrics.py`` pass under
    the current LANES + RUBRICS state. Any drift on main would surface
    as an ImportError here."""
    from src.evaluation.rubrics import RUBRICS, RUBRIC_VERSION

    assert isinstance(RUBRICS, dict)
    assert len(RUBRICS) > 0
    assert isinstance(RUBRIC_VERSION, str) and len(RUBRIC_VERSION) == 12


def test_rubrics_count_matches_derived_sum_of_lane_rubric_ids() -> None:
    """The derived invariant: ``len(RUBRICS) == sum(len(spec.rubric_ids)
    for spec in LANES.values())``. This is what the module-level assert
    enforces; re-asserting it here pins the contract."""
    from autoresearch.lane_registry import LANES
    from src.evaluation.rubrics import RUBRICS

    expected = sum(len(spec.rubric_ids) for spec in LANES.values())
    assert len(RUBRICS) == expected, (
        f"RUBRICS has {len(RUBRICS)} entries but LANES declares {expected} "
        f"rubric IDs across all LaneSpecs"
    )


def test_every_lane_rubric_id_has_prose_in_rubrics() -> None:
    """Bidirectional invariant, first direction: every ID a LaneSpec
    claims must have matching prose in RUBRICS."""
    from autoresearch.lane_registry import LANES
    from src.evaluation.rubrics import RUBRICS

    declared = {rid for spec in LANES.values() for rid in spec.rubric_ids}
    missing = declared - set(RUBRICS)
    assert not missing, (
        f"LaneSpec(s) declare rubric IDs with no matching RubricTemplate: "
        f"{sorted(missing)}"
    )


def test_no_orphaned_rubrics_without_a_claiming_lane() -> None:
    """Bidirectional invariant, second direction: every RUBRICS entry
    must be claimed by some LaneSpec.rubric_ids. Catches the case where
    prose lands but the LaneSpec wasn't updated."""
    from autoresearch.lane_registry import LANES
    from src.evaluation.rubrics import RUBRICS

    declared = {rid for spec in LANES.values() for rid in spec.rubric_ids}
    orphaned = set(RUBRICS) - declared
    assert not orphaned, (
        f"RUBRICS contains IDs not claimed by any LaneSpec: {sorted(orphaned)}"
    )


def test_invariant_catches_constructed_mismatch() -> None:
    """Falsifiability: the invariant check, applied to a constructed
    LANES-vs-RUBRICS mismatch, produces a clear failure mode. Mirrors
    the module-level assert logic with synthetic inputs."""
    fake_rubrics = {"AE-1": object(), "AE-2": object(), "AE-3": object()}
    fake_lane_rubric_ids = ("AE-1", "AE-2")  # missing AE-3

    declared = set(fake_lane_rubric_ids)
    orphaned = set(fake_rubrics) - declared
    expected = len(fake_lane_rubric_ids)

    assert orphaned == {"AE-3"}, "constructed orphan was not detected"
    assert len(fake_rubrics) != expected, "constructed count mismatch was not detected"
