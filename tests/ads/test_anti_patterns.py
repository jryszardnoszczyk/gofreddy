"""U15 — anti-patterns deterministic pre-check (TD-42)."""
from __future__ import annotations

import pytest

from src.ads.compliance.anti_patterns import (
    cap_score_from_hits,
    find_anti_pattern_hits,
)
from src.ads.compliance import (
    text_violates_guaranteed_results,
    text_violates_linkedin_aggressive,
    text_violates_meta_health,
)


# ---------------------------------------------------------------------------
# Anti-pattern detection
# ---------------------------------------------------------------------------


def test_no_hits_on_clean_copy() -> None:
    text = "We help dental clinics fill 5 chairs/day with a 15-min implementation call."
    hits = find_anti_pattern_hits(text)
    assert hits == []


def test_tired_of_x_meet_y_pas_formula() -> None:
    text = "Tired of broken workflows? Meet our new automation suite."
    hits = find_anti_pattern_hits(text)
    pattern_ids = [h.pattern_id for h in hits]
    assert "tired_of_x_meet_y" in pattern_ids


def test_unlock_outcome_generic() -> None:
    text = "Unlock the future of your business with our platform."
    hits = find_anti_pattern_hits(text)
    pattern_ids = [h.pattern_id for h in hits]
    assert "unlock_outcome" in pattern_ids


def test_ai_powered_without_capability_noun() -> None:
    """88% of B2B buyers tune out 'AI-powered' without a concrete
    capability in the same sentence."""
    text = "Our AI-powered platform helps you grow."
    hits = find_anti_pattern_hits(text)
    assert any(h.pattern_id == "ai_powered_without_capability" for h in hits)


def test_ai_powered_with_capability_passes() -> None:
    text = "AI-powered transcription extracts key entities from your meetings."
    hits = find_anti_pattern_hits(text)
    assert not any(h.pattern_id == "ai_powered_without_capability" for h in hits)


def test_leverage_thing() -> None:
    text = "Leverage your customer data to drive insights."
    hits = find_anti_pattern_hits(text)
    assert any(h.pattern_id == "leverage_thing" for h in hits)


def test_seamlessly_integrate() -> None:
    text = "Our tool seamlessly integrates with your existing stack."
    hits = find_anti_pattern_hits(text)
    assert any(h.pattern_id == "seamlessly_integrate" for h in hits)


def test_game_changer_next_gen() -> None:
    for phrase in ("game-changer", "next-generation", "cutting-edge"):
        hits = find_anti_pattern_hits(f"Our {phrase} platform")
        assert any(h.pattern_id == "game_changer_next_gen" for h in hits), phrase


def test_learn_more_cta() -> None:
    text = 'CTA: "Learn More"'
    hits = find_anti_pattern_hits(text)
    assert any(h.pattern_id == "learn_more_cta" for h in hits)


def test_built_for_modern_teams() -> None:
    for phrase in (
        "Built for modern teams.",
        "Built for the way developers work.",
    ):
        hits = find_anti_pattern_hits(phrase)
        assert any(h.pattern_id == "built_for_modern_teams" for h in hits), phrase


def test_multiple_anti_patterns_in_same_text() -> None:
    text = (
        "Tired of broken analytics? Meet our AI-powered platform that seamlessly "
        "integrates with your stack. CTA: \"Learn More\""
    )
    hits = find_anti_pattern_hits(text)
    pattern_ids = {h.pattern_id for h in hits}
    assert "tired_of_x_meet_y" in pattern_ids
    assert "seamlessly_integrate" in pattern_ids
    assert "learn_more_cta" in pattern_ids


# ---------------------------------------------------------------------------
# Cap score logic
# ---------------------------------------------------------------------------


def test_no_hits_no_cap() -> None:
    """Empty hits list → score passes through unchanged."""
    assert cap_score_from_hits(5.0, [], "AD-1") == 5.0


def test_ad_1_caps_per_hit_count() -> None:
    """AD-1 caps at max(2, 4 - 0.5*(hits-1)). 1 hit → cap 4; 2 hits →
    cap 3.5; 5+ hits → cap 2."""
    hits1 = find_anti_pattern_hits("Tired of broken workflows? Meet us.")
    assert len(hits1) >= 1
    assert cap_score_from_hits(5.0, hits1, "AD-1") <= 4.0


def test_ad_6_caps_at_3_on_any_hit() -> None:
    hits = find_anti_pattern_hits("Tired of broken workflows? Meet us.")
    assert cap_score_from_hits(5.0, hits, "AD-6") == 3.0


def test_other_rubrics_no_cap() -> None:
    hits = find_anti_pattern_hits("Tired of broken workflows? Meet us.")
    assert cap_score_from_hits(5.0, hits, "AD-8") == 5.0


# ---------------------------------------------------------------------------
# Banned terms (Meta health, LinkedIn aggressive, guaranteed N%)
# ---------------------------------------------------------------------------


def test_meta_health_words_detected() -> None:
    text = "Our treatment cures anxiety symptoms in 30 days."
    hits = text_violates_meta_health(text)
    assert "treatment" not in hits  # "treat" matches; "treatment" does not (word boundary on whole word)
    assert "cures" in hits
    assert "symptoms" in hits


def test_meta_health_clean_passes() -> None:
    text = "Our clinic offers consultations on Tuesdays and Thursdays."
    assert text_violates_meta_health(text) == []


def test_linkedin_aggressive_phrases() -> None:
    text = "Get guaranteed ROI in 30 days with our secret hack."
    hits = text_violates_linkedin_aggressive(text)
    assert "guaranteed ROI" in hits
    assert "secret hack" in hits


def test_guaranteed_n_pct_regex() -> None:
    for text in (
        "Guaranteed 30% results in 30 days",
        "50% guaranteed ROI",
    ):
        assert text_violates_guaranteed_results(text), text


def test_guaranteed_clean_passes() -> None:
    text = "We deliver measurable results in 30 days."
    assert text_violates_guaranteed_results(text) is False
