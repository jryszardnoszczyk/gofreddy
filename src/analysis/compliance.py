"""Deterministic compliance scoring for sponsored content disclosures.

Scores are informational assessments only. Not legal or regulatory advice.
Not a determination of FTC compliance.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.schemas import SponsoredContent

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

COMPLIANCE_DISCLAIMER = (
    "Informational assessment only. Not legal or regulatory advice. "
    "Not a determination of FTC compliance."
)

PLACEMENT_SCORES: dict[str, float] = {
    "first_3_seconds": 1.0,
    "middle": 0.5,
    "end": 0.2,
    "absent": 0.0,
}

VISIBILITY_SCORES: dict[str, float] = {
    "verbal": 1.0,
    "text_overlay": 0.6,
    "hashtag_only": 0.3,
    "none": 0.0,
}

# Weights must sum to 1.0
_PLACEMENT_WEIGHT = 0.40
_VISIBILITY_WEIGHT = 0.35
_TIMING_WEIGHT = 0.25


def compute_compliance(sponsored: SponsoredContent) -> SponsoredContent:
    """Compute compliance sub-scores, grade, and suggestions from raw Gemini signals.

    Uses compute-then-assign pattern: all values computed into locals first,
    then assigned atomically. Prevents partial mutation on exception.
    Non-sponsored content is returned unchanged (all compliance fields stay None).
    """
    if not sponsored.is_sponsored:
        return sponsored

    # ── Phase 1: Compute all values into locals ──
    placement = PLACEMENT_SCORES.get(sponsored.disclosure_placement or "", 0.0)
    visibility = VISIBILITY_SCORES.get(sponsored.disclosure_visibility or "", 0.0)
    timing = 1.0 if sponsored.disclosure_before_product else 0.0

    weighted_avg = (
        placement * _PLACEMENT_WEIGHT
        + visibility * _VISIBILITY_WEIGHT
        + timing * _TIMING_WEIGHT
    )
    score_100 = weighted_avg * 100

    if score_100 >= 90:
        grade = "A"
    elif score_100 >= 80:
        grade = "B"
    elif score_100 >= 70:
        grade = "C"
    elif score_100 >= 60:
        grade = "D"
    else:
        grade = "F"

    # Rule-based improvement suggestions (plain if/elif — 5 static rules)
    suggestions: list[str] = []
    if placement == 0.0:
        suggestions.append("Add a disclosure — none was detected")
    elif placement < 0.5:
        suggestions.append("Move disclosure to the first 3 seconds of the video")
    if visibility <= 0.3:
        suggestions.append("Use a visible text overlay instead of hashtag-only disclosure")
    elif visibility < 0.5:
        suggestions.append("Add a verbal disclosure alongside any text or hashtag")
    if timing < 0.5:
        suggestions.append("Place disclosure before the first product mention or demonstration")

    # ── Phase 2: Assign atomically (all-or-nothing) ──
    sponsored.placement_score = placement
    sponsored.visibility_score = visibility
    sponsored.timing_score = timing
    sponsored.compliance_grade = grade
    sponsored.improvement_suggestions = suggestions

    return sponsored


def _reset_compliance_fields(sponsored: SponsoredContent) -> None:
    """Reset all computed compliance fields to None/defaults."""
    sponsored.placement_score = None
    sponsored.visibility_score = None
    sponsored.timing_score = None
    sponsored.compliance_grade = None
    sponsored.improvement_suggestions = []
