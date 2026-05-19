"""U17 legal_pl rule-set integrity + sample-artifact evaluation.

Mirror of test_medical_pl_rule_set.py for the legal_pl reviewer-assist
checklist. See that module's docstring for the test-philosophy framing
(intent over behavior; regulatory surfaces named).
"""
from __future__ import annotations

import pytest

from src.compliance.judge import evaluate_compliance
from src.compliance.loader import load_rule_set


# ---------------------------------------------------------------------------
# Integrity
# ---------------------------------------------------------------------------


def test_legal_pl_loads_with_reviewer_assist_posture() -> None:
    """Per §Compliance Posture: legal_pl is reviewer-assist, NOT
    legal-grade."""
    rs = load_rule_set("legal_pl")
    assert rs.rule_set_name == "legal_pl"
    assert rs.metadata.get("reviewer_assist_posture") is True
    assert rs.metadata.get("legal_grade_gate") is False
    assert rs.metadata.get("two_reviewer_signoff_required") is True


def test_legal_pl_rule_count_within_plan_envelope() -> None:
    """Plan §U17: ~30-50 rules (mirror U16). Tolerated buffer ±10."""
    rs = load_rule_set("legal_pl")
    assert 25 <= len(rs.rules) <= 60, (
        f"legal_pl rule count {len(rs.rules)} outside expected [25, 60] "
        "envelope per U17 plan."
    )


def test_legal_pl_severity_distribution_has_both_classes() -> None:
    rs = load_rule_set("legal_pl")
    hard = sum(1 for r in rs.rules if r.severity == "hard_block")
    soft = sum(1 for r in rs.rules if r.severity == "soft_warn")
    assert hard > 0, "legal_pl has no hard_block rules"
    assert soft > 0, "legal_pl has no soft_warn rules"


def test_legal_pl_has_llm_only_judge_surfaces() -> None:
    """Polish bar codes prohibit solicitation-tone; tone is the load-
    bearing surface. LLM-only flags (pattern=None) must exist."""
    rs = load_rule_set("legal_pl")
    llm_only = [r for r in rs.rules if r.pattern is None]
    assert len(llm_only) >= 2


def test_legal_pl_rule_ids_use_consistent_prefix() -> None:
    rs = load_rule_set("legal_pl")
    for rule in rs.rules:
        assert rule.id.startswith("legal_pl_"), (
            f"legal_pl rule id {rule.id!r} missing 'legal_pl_' prefix"
        )


# ---------------------------------------------------------------------------
# Sample-artifact evaluation — solicitation (HARD BLOCK)
# ---------------------------------------------------------------------------


def test_hire_us_solicitation_fires_hard_block() -> None:
    """Pin: KERP Art. 32 + Zbiór §23 prohibit hire-us solicitation."""
    artifact = "Zatrudnij naszą kancelarię. Wybierz nasz zespół ekspertów."
    result = evaluate_compliance(artifact, "legal_pl", lane="article_engine")
    assert result.has_hard_block
    fired_ids = {f.rule_id for f in result.flags}
    assert "legal_pl_solicitation_hire_us" in fired_ids


def test_call_now_urgency_fires_hard_block() -> None:
    """Pin: urgency-CTA combines solicitation + Art. 24."""
    artifact = "Zadzwoń teraz! Umów spotkanie już dziś."
    result = evaluate_compliance(artifact, "legal_pl", lane="article_engine")
    assert result.has_hard_block


def test_takeover_case_fires_hard_block() -> None:
    """Pin: 'przejmiemy twoją sprawę' violates KERP Art. 32 + Art. 27
    (collegiality)."""
    artifact = "Przejmiemy twoją sprawę od poprzedniej kancelarii."
    result = evaluate_compliance(artifact, "legal_pl", lane="article_engine")
    assert result.has_hard_block


# ---------------------------------------------------------------------------
# Sample-artifact evaluation — fee references (HARD BLOCK)
# ---------------------------------------------------------------------------


def test_explicit_fee_fires_hard_block() -> None:
    """Pin: 'honorarium od 500 zł' violates KERP Art. 33 + Zbiór §23."""
    artifact = "Stawka godzinowa od 300 zł. Cennik usług dostępny online."
    result = evaluate_compliance(artifact, "legal_pl", lane="article_engine")
    assert result.has_hard_block


def test_no_win_no_fee_fires_hard_block() -> None:
    """Pin: contingency marketing violates KERP Art. 36 + Zbiór §50."""
    artifact = "Płatność tylko po wygranej. No win no fee gwarantowane."
    result = evaluate_compliance(artifact, "legal_pl", lane="article_engine")
    assert result.has_hard_block


def test_comparative_fee_fires_hard_block() -> None:
    """Pin: 'najtańsza kancelaria' = KERP Art. 33 + Art. 16."""
    artifact = "Najtańsza kancelaria w Warszawie. Tańsze stawki niż gdziekolwiek."
    result = evaluate_compliance(artifact, "legal_pl", lane="article_engine")
    assert result.has_hard_block


# ---------------------------------------------------------------------------
# Sample-artifact evaluation — outcome guarantees (HARD BLOCK)
# ---------------------------------------------------------------------------


def test_outcome_guarantee_fires_hard_block() -> None:
    """Pin: 'gwarantujemy wygraną' = KERP Art. 31 + Zbiór §23."""
    artifact = "Gwarantujemy wygraną w twojej sprawie. Sukces w 100%."
    result = evaluate_compliance(artifact, "legal_pl", lane="article_engine")
    assert result.has_hard_block


def test_win_rate_puffery_fires_hard_block() -> None:
    """Pin: '95% wygranych spraw' combines guarantee + verifiability."""
    artifact = "Wygrywamy 95% spraw. Skuteczność 90% od początku praktyki."
    result = evaluate_compliance(artifact, "legal_pl", lane="article_engine")
    assert result.has_hard_block


# ---------------------------------------------------------------------------
# Sample-artifact evaluation — competitor comparison (HARD BLOCK)
# ---------------------------------------------------------------------------


def test_competitor_comparison_fires_hard_block() -> None:
    """Pin: 'lepsi niż konkurencja' = KERP Art. 32 + Zbiór §23."""
    artifact = "Jesteśmy lepsi niż konkurencja. Wyższa jakość niż u innych kancelarii."
    result = evaluate_compliance(artifact, "legal_pl", lane="article_engine")
    assert result.has_hard_block


def test_market_leader_fires_hard_block() -> None:
    """Pin: 'lider rynku usług prawnych' = ranking-puffery."""
    artifact = "Jesteśmy liderem rynku usług prawnych. Top 3 kancelarii w Polsce."
    result = evaluate_compliance(artifact, "legal_pl", lane="article_engine")
    assert result.has_hard_block


# ---------------------------------------------------------------------------
# Sample-artifact evaluation — judicial-influence (HARD BLOCK)
# ---------------------------------------------------------------------------


def test_court_connections_fires_hard_block() -> None:
    """Pin: 'nasze znajomości w sądach' = KERP Art. 27 + criminal-law
    overlap."""
    artifact = "Mamy nasze znajomości w sądach. Koneksje w wymiarze sprawiedliwości."
    result = evaluate_compliance(artifact, "legal_pl", lane="article_engine")
    assert result.has_hard_block


# ---------------------------------------------------------------------------
# Sample-artifact evaluation — fear / pressure (HARD BLOCK + soft_warn)
# ---------------------------------------------------------------------------


def test_fear_loss_fires_hard_block() -> None:
    """Pin: 'stracisz wszystko' = KERP Art. 32 + Art. 24."""
    artifact = "Stracisz cały majątek bez naszej pomocy. Grozi ci więzienie."
    result = evaluate_compliance(artifact, "legal_pl", lane="article_engine")
    assert result.has_hard_block


# ---------------------------------------------------------------------------
# Sample-artifact evaluation — celebrity client (HARD BLOCK)
# ---------------------------------------------------------------------------


def test_celebrity_client_fires_hard_block() -> None:
    """Pin: KERP Art. 27 bar-secrecy + Art. 33 dignity."""
    artifact = "Reprezentujemy gwiazdy i celebrytów. Nasi klienci to VIP-y."
    result = evaluate_compliance(artifact, "legal_pl", lane="article_engine")
    assert result.has_hard_block


def test_referral_incentive_fires_hard_block() -> None:
    """Pin: KERP Art. 25-26 prohibit fee-splitting referral arrangements."""
    artifact = "Poleć klienta i otrzymaj prowizję 10%. Program partnerski z wynagrodzeniem."
    result = evaluate_compliance(artifact, "legal_pl", lane="article_engine")
    assert result.has_hard_block


# ---------------------------------------------------------------------------
# Sample-artifact evaluation — clean artifact returns 'clean'
# ---------------------------------------------------------------------------


def test_clean_informational_artifact_returns_clean() -> None:
    """Pin: a KERP-compliant informational artifact returns
    verdict='clean'. Same load-bearing role as the medical_pl
    counterpart."""
    artifact = (
        "Nasza kancelaria prowadzi sprawy z zakresu prawa korporacyjnego "
        "od 2008 roku. Specjalizujemy się w transakcjach M&A oraz "
        "regulacjach giełdowych — w tych obszarach zespół ma "
        "wieloletnie doświadczenie. Jeśli rozważasz konsultację, "
        "skontaktuj się z naszym sekretariatem; zasady współpracy "
        "i warunki finansowe omawiamy w trakcie spotkania, w ramach "
        "umowy zlecenia podpisywanej przed rozpoczęciem prac."
    )
    result = evaluate_compliance(artifact, "legal_pl", lane="article_engine")
    assert result.verdict == "clean", (
        f"Clean informational artifact should return 'clean'; got "
        f"{result.verdict!r} with flags: {[f.rule_id for f in result.flags]}"
    )


# ---------------------------------------------------------------------------
# Severity surfacing — flag.prose carries reviewer guidance
# ---------------------------------------------------------------------------


def test_flags_carry_prose_with_substitution_guidance() -> None:
    """Per §Compliance Posture: rules surface prose with reviewer
    guidance, not just description."""
    artifact = "Najtańsza kancelaria w Warszawie. Gwarantujemy wygraną."
    result = evaluate_compliance(artifact, "legal_pl", lane="article_engine")
    assert len(result.flags) >= 1
    for flag in result.flags:
        prose_lower = flag.prose.lower()
        assert any(
            keyword in prose_lower
            for keyword in ("reviewer:", "replace with", "verify", "remove")
        ), f"Rule {flag.rule_id!r} prose lacks reviewer guidance: {flag.prose[:200]!r}"
