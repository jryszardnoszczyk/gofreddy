"""U16 medical_pl rule-set integrity + sample-artifact evaluation.

These tests pin the reviewer-assist substrate for the medical_pl
checklist. They are NOT validation that the patterns capture every
Polish medical-advertising violation — that's the reviewer's job at
U7 pre-publish review (§Compliance Posture). They DO validate:

  1. The YAML loads and matches the schema.
  2. Marquee patterns fire on representative trigger text.
  3. Clean text returns verdict='clean'.
  4. Severity distribution is sensible (some hard_block, some soft_warn).

Per Rule 9 (tests verify intent, not just behavior): each test names the
regulatory surface it pins, so a future change that quietly removes a
rule fails a test that documents WHY the rule was added.
"""
from __future__ import annotations

import pytest

from src.compliance.judge import evaluate_compliance
from src.compliance.loader import load_rule_set


# ---------------------------------------------------------------------------
# Integrity
# ---------------------------------------------------------------------------


def test_medical_pl_loads_with_reviewer_assist_posture() -> None:
    """Per §Compliance Posture: medical_pl is reviewer-assist, NOT
    legal-grade. Future drift away from this stance must fail."""
    rs = load_rule_set("medical_pl")
    assert rs.rule_set_name == "medical_pl"
    assert rs.metadata.get("reviewer_assist_posture") is True
    assert rs.metadata.get("legal_grade_gate") is False
    assert rs.metadata.get("two_reviewer_signoff_required") is True


def test_medical_pl_rule_count_within_plan_envelope() -> None:
    """Plan §U16: ~30-50 rules. Buffer is tolerated; a sub-20 rule
    count or runaway 100+ count indicates a regression worth surfacing."""
    rs = load_rule_set("medical_pl")
    assert 30 <= len(rs.rules) <= 60, (
        f"medical_pl rule count {len(rs.rules)} outside expected [30, 60] "
        "envelope per U16 plan."
    )


def test_medical_pl_severity_distribution_has_both_classes() -> None:
    """A reviewer-assist checklist that's all-hard-block would over-
    block; all-soft-warn would under-block. Both classes must be
    represented."""
    rs = load_rule_set("medical_pl")
    hard = sum(1 for r in rs.rules if r.severity == "hard_block")
    soft = sum(1 for r in rs.rules if r.severity == "soft_warn")
    assert hard > 0, "medical_pl has no hard_block rules"
    assert soft > 0, "medical_pl has no soft_warn rules"


def test_medical_pl_has_llm_only_judge_surfaces() -> None:
    """Some surfaces (tone-pressure, unsubstantiated authority) cannot be
    captured by regex and need LLM-judged prose. The checklist must
    carry such rules with pattern=None."""
    rs = load_rule_set("medical_pl")
    llm_only = [r for r in rs.rules if r.pattern is None]
    assert len(llm_only) >= 2, (
        "medical_pl should include LLM-only judge surfaces (e.g. tone-"
        "pressure, vague-authority). Found "
        f"{len(llm_only)} pattern=None rules."
    )


def test_medical_pl_rule_ids_use_consistent_prefix() -> None:
    """Drift pin: every rule id starts with 'medical_pl_' so a grep
    over compliance-meta logs filters by rule set without joining."""
    rs = load_rule_set("medical_pl")
    for rule in rs.rules:
        assert rule.id.startswith("medical_pl_"), (
            f"medical_pl rule id {rule.id!r} missing 'medical_pl_' prefix"
        )


# ---------------------------------------------------------------------------
# Sample-artifact evaluation — Art. 14 superlatives (HARD BLOCK)
# ---------------------------------------------------------------------------


def test_superlative_najlepszy_inflected_fires_hard_block() -> None:
    """Pin: Art. 14 superlative prohibition. Polish inflection means
    'najlepszy' (nom.), 'najlepszego' (gen.), 'najlepszą' (acc.f.),
    'najlepszej' (loc.f.) all must fire."""
    for form in ("najlepszy", "najlepszego", "najlepszą", "najlepszej", "najlepsi"):
        artifact = f"Naszą klinikę charakteryzuje {form} sprzęt w Warszawie."
        result = evaluate_compliance(artifact, "medical_pl", lane="article_engine")
        assert result.has_hard_block, (
            f"medical_pl_superlative_naj_quality did not fire on inflection "
            f"{form!r}; pattern needs stem+\\w* coverage."
        )


def test_superlative_najnowoczesniejszy_fires_hard_block() -> None:
    """Pin: novelty-superlative (najnowocześniejszy). Stem-anchored \\w*
    captures inflection."""
    artifact = "Wykorzystujemy najnowocześniejszy laser na rynku."
    result = evaluate_compliance(artifact, "medical_pl", lane="article_engine")
    assert result.has_hard_block


def test_market_leader_fires_hard_block() -> None:
    """Pin: 'lider rynku medycyny estetycznej' is hard-block puffery."""
    artifact = "Jesteśmy liderem rynku medycyny estetycznej w Polsce."
    result = evaluate_compliance(artifact, "medical_pl", lane="article_engine")
    assert result.has_hard_block


# ---------------------------------------------------------------------------
# Sample-artifact evaluation — Art. 14 CTAs (HARD BLOCK)
# ---------------------------------------------------------------------------


def test_book_visit_cta_fires_hard_block() -> None:
    """Pin: 'umów się na wizytę' is direct-booking CTA → Art. 14."""
    artifact = "Umów się na wizytę już dziś. Mamy wolne terminy."
    result = evaluate_compliance(artifact, "medical_pl", lane="article_engine")
    assert result.has_hard_block
    fired_ids = {f.rule_id for f in result.flags}
    assert "medical_pl_cta_book_visit" in fired_ids


def test_urgency_today_fires_hard_block() -> None:
    """Pin: 'tylko dziś' on a medical artifact = Art. 14 + Art. 24."""
    artifact = "Promocja tylko dziś! Skontaktuj się z naszą kliniką."
    result = evaluate_compliance(artifact, "medical_pl", lane="article_engine")
    assert result.has_hard_block


# ---------------------------------------------------------------------------
# Sample-artifact evaluation — Art. 14 prices (HARD BLOCK)
# ---------------------------------------------------------------------------


def test_explicit_price_fires_hard_block() -> None:
    """Pin: explicit price in health-services advertising = Art. 14."""
    artifact = "Zabieg laserowy tylko 500 zł. Najlepsza cena w Warszawie."
    result = evaluate_compliance(artifact, "medical_pl", lane="article_engine")
    assert result.has_hard_block
    fired_ids = {f.rule_id for f in result.flags}
    # Both price rule + superlative rule should fire (best-price comparison)
    assert "medical_pl_price_explicit" in fired_ids


def test_discount_promotion_fires_hard_block() -> None:
    """Pin: 'rabat 20%' on aesthetic procedure = Art. 14 + KEL."""
    artifact = "Rabat 20% na zabieg botoxu. Zniżka tylko w tym tygodniu."
    result = evaluate_compliance(artifact, "medical_pl", lane="article_engine")
    assert result.has_hard_block


def test_financing_for_procedure_fires_hard_block() -> None:
    """Pin: 'kredyt na zabieg' is hard-blocked under Art. 14 + Art. 24."""
    artifact = "Skorzystaj z finansowania zabiegu — raty 12x bez odsetek."
    result = evaluate_compliance(artifact, "medical_pl", lane="article_engine")
    assert result.has_hard_block


# ---------------------------------------------------------------------------
# Sample-artifact evaluation — Outcome guarantees (HARD BLOCK)
# ---------------------------------------------------------------------------


def test_outcome_guarantee_fires_hard_block() -> None:
    """Pin: 'gwarantujemy wyleczenie' = Art. 14 + Medical Devices Act."""
    artifact = "Gwarantujemy 100% skuteczności naszego programu odchudzania."
    result = evaluate_compliance(artifact, "medical_pl", lane="article_engine")
    assert result.has_hard_block


def test_complete_cure_fires_hard_block() -> None:
    """Pin: 'całkowite wyleczenie' + 'raz na zawsze' both hard-block."""
    artifact = "Trwały efekt na zawsze. Raz na zawsze pozbędziesz się problemu."
    result = evaluate_compliance(artifact, "medical_pl", lane="article_engine")
    assert result.has_hard_block


def test_no_side_effects_fires_hard_block() -> None:
    """Pin: 'bez skutków ubocznych' violates Art. 14 + Medical Devices Act."""
    artifact = "Zabieg całkowicie bezpieczny, bez skutków ubocznych."
    result = evaluate_compliance(artifact, "medical_pl", lane="article_engine")
    assert result.has_hard_block


# ---------------------------------------------------------------------------
# Sample-artifact evaluation — Off-label / unapproved claims (HARD BLOCK)
# ---------------------------------------------------------------------------


def test_unapproved_disease_cure_fires_hard_block() -> None:
    """Pin: aesthetic clinic claiming to 'leczyć raka' violates everything."""
    artifact = "Nasz program leczy raka piersi i HIV jednocześnie."
    result = evaluate_compliance(artifact, "medical_pl", lane="article_engine")
    assert result.has_hard_block


# ---------------------------------------------------------------------------
# Sample-artifact evaluation — Celebrity / referral (HARD BLOCK)
# ---------------------------------------------------------------------------


def test_celebrity_endorsement_fires_hard_block() -> None:
    """Pin: 'gwiazdy wybierają' = Art. 14 + KEL + GDPR surface."""
    artifact = "Gwiazdy wybierają naszą klinikę. Ulubiony zabieg celebrytów."
    result = evaluate_compliance(artifact, "medical_pl", lane="article_engine")
    assert result.has_hard_block


def test_referral_incentive_fires_hard_block() -> None:
    """Pin: 'poleć znajomego i otrzymaj' = Art. 14 encouragement-to-use."""
    artifact = "Poleć znajomego i otrzymaj zniżkę 100 zł na kolejny zabieg."
    result = evaluate_compliance(artifact, "medical_pl", lane="article_engine")
    assert result.has_hard_block


# ---------------------------------------------------------------------------
# Sample-artifact evaluation — Clean artifact returns 'clean'
# ---------------------------------------------------------------------------


def test_clean_informational_artifact_returns_clean() -> None:
    """Pin: an Art. 14-compliant informational artifact returns
    verdict='clean'. This is the most important test — without a clean
    signal, the framework over-flags and reviewer ignores all output."""
    artifact = (
        "Mezoterapia to zabieg polegający na wprowadzeniu pod skórę "
        "preparatów rewitalizujących. Procedura wykonywana jest przez "
        "lekarza specjalistę dermatologii estetycznej. Konsultacja "
        "wstępna pozwala określić, czy zabieg jest wskazany dla "
        "Pana / Pani sytuacji. Okres gojenia trwa 3-5 dni; pełne "
        "wygojenie obserwujemy po 2-3 tygodniach. Reakcja na zabieg "
        "może się różnić indywidualnie."
    )
    result = evaluate_compliance(artifact, "medical_pl", lane="article_engine")
    assert result.verdict == "clean", (
        f"Clean informational artifact should return 'clean'; got "
        f"{result.verdict!r} with flags: {[f.rule_id for f in result.flags]}"
    )


# ---------------------------------------------------------------------------
# Sample-artifact evaluation — case-insensitive matching
# ---------------------------------------------------------------------------


def test_patterns_default_case_insensitive() -> None:
    """Pin: default case-insensitive matches per ComplianceRule schema —
    Polish copy mixes capitalised + lowercase versions ("Najlepszy" at
    sentence start, "najlepszy" mid-sentence)."""
    for form in ("najlepszy", "Najlepszy", "NAJLEPSZY"):
        artifact = f"{form} zabieg w naszej klinice."
        result = evaluate_compliance(artifact, "medical_pl", lane="article_engine")
        assert result.has_hard_block, f"case {form!r} did not fire"


# ---------------------------------------------------------------------------
# Severity surfacing — flag.prose carries reviewer guidance
# ---------------------------------------------------------------------------


def test_flags_carry_prose_with_substitution_guidance() -> None:
    """Per §Compliance Posture: rules surface prose that helps the
    reviewer act, not just flag. Verify the prose carries
    substitution / framing guidance, not just descriptions."""
    artifact = "Najlepszy zabieg w Warszawie. Gwarantujemy efekt."
    result = evaluate_compliance(artifact, "medical_pl", lane="article_engine")
    assert len(result.flags) >= 2
    for flag in result.flags:
        prose_lower = flag.prose.lower()
        # Each rule's prose should explain what the reviewer should DO,
        # not just say "this is bad."
        assert any(
            keyword in prose_lower
            for keyword in ("reviewer:", "replace with", "verify", "remove")
        ), f"Rule {flag.rule_id!r} prose lacks reviewer guidance: {flag.prose[:200]!r}"
