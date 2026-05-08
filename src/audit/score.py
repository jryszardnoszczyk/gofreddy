"""marketing_audit lane fitness scoring — L1 stub.

Wired into ``autoresearch/lane_registry.py:LANES["marketing_audit"]``
as ``custom_score``. Default substrate ``_score_variant_search``
(``evaluate_variant.py``) emits ``mean_inner_pass_rate`` /
``mean_outer_pass_rate`` / ``mean_pass_rate_delta`` assuming an
inner critique loop; v1 has no inner critique loop (LHR D2) so
the default emits null/wrong metrics. Hence custom_score per
master plan §6.2 + §6.5.

L1 stub returns sane defaults (0.0 score, empty rubric breakdown)
so the lane registers + LaneSpec validates against compute_manifest
without RuntimeErrors. Full implementation lands in L3 (Phase 2)
once MA-1..MA-8 rubrics + judges + holdout fixtures exist.

Full L3 contract (master plan §6.5):
    score = geometric_mean([MA_1..MA_8]) / 10.0 + engagement_bonus
    where engagement_bonus = 0.05 if T+60d engagement_converted else 0.0
    score range [0, 1.05] — keeps 4 peer lanes' [0, 1] selection-space
    calibrated.
"""
from __future__ import annotations

from typing import Any


def marketing_audit_score(
    config: Any,
    variant_dir: Any,
    parent_id: str | None = None,
) -> dict[str, Any]:
    """L1 stub. Returns sane defaults so the lane registers without
    raising; L3 implements the geometric-mean MA-1..MA-8 rollup +
    engagement bonus per master plan §6.5.

    Signature mirrors substrate's ``_score_variant_search`` so the
    L3 swap-in is a body-only change.
    """
    return {
        "score": 0.0,
        "rubric_breakdown": {},
        "engagement_bonus": 0.0,
        "fixtures_detail": [],
        "stub": True,
    }


__all__ = ["marketing_audit_score"]
