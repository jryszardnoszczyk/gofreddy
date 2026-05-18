"""evaluate_compliance regex + verdict logic (U5)."""
from __future__ import annotations

import pytest

from src.compliance.judge import (
    COMPLIANCE_JUDGE,
    ComplianceResult,
    evaluate_compliance,
    get_compliance_judge_config,
)


# ---------------------------------------------------------------------------
# evaluate_compliance against real gdpr_eu checklist
# ---------------------------------------------------------------------------


def test_evaluate_clean_artifact_returns_clean_verdict() -> None:
    artifact = (
        "We process your data under Article 6(1)(b) (contract necessity). "
        "Cookie consent is captured via affirmative checkbox before any "
        "non-essential cookies are set. US transfers use SCCs + a Transfer "
        "Impact Assessment per Schrems II."
    )
    result = evaluate_compliance(artifact, "gdpr_eu", lane="article_engine")
    assert result.verdict == "clean"
    assert result.flags == []
    assert result.rule_set_name == "gdpr_eu"
    assert result.lane == "article_engine"


def test_evaluate_hard_block_pattern_fires() -> None:
    """Per D5: hard_block → score 0 → frontier rejection. Test pins
    that the verdict propagates."""
    artifact = "We rely on Safe Harbor for cross-border data transfers."
    result = evaluate_compliance(artifact, "gdpr_eu", lane="article_engine")
    assert result.verdict == "hard_block"
    assert result.has_hard_block is True
    assert any(f.rule_id == "gdpr_safe_harbor_invalid" for f in result.flags)


def test_evaluate_soft_warn_pattern_fires() -> None:
    """Per D5: soft_warn → score scaled + flag persisted, but variant
    NOT auto-rejected (reviewer override is permitted in U7)."""
    artifact = "Our pipeline produces fully anonymous customer data."
    result = evaluate_compliance(artifact, "gdpr_eu", lane="article_engine")
    assert result.verdict == "soft_warn"
    assert result.has_soft_warn is True
    assert result.has_hard_block is False


def test_evaluate_mixed_severity_promotes_to_hard_block() -> None:
    """When both severities fire, the overall verdict is hard_block —
    the most severe outcome wins so the frontier rejects per D5."""
    artifact = (
        "We rely on Safe Harbor for transfers. "
        "Browsing this site implies consent to cookies."
    )
    result = evaluate_compliance(artifact, "gdpr_eu", lane="article_engine")
    assert result.verdict == "hard_block"
    # Both rules' provenance is captured in flags
    rule_ids = {f.rule_id for f in result.flags}
    assert "gdpr_safe_harbor_invalid" in rule_ids


def test_evaluate_with_klinika_placeholder_polish_pattern() -> None:
    """Placeholder Polish-language patterns fire on the right surfaces."""
    artifact = "Nasza klinika oferuje najnowocześniejszą procedurę liposukcji."
    result = evaluate_compliance(artifact, "medical_pl", lane="article_engine")
    assert result.verdict == "hard_block"
    assert any(f.rule_id == "medical_pl_superlative_najlepszy" for f in result.flags)


def test_evaluate_with_dwf_placeholder_polish_pattern() -> None:
    artifact = "Gwarantujemy wygraną w tej sprawie."
    result = evaluate_compliance(artifact, "legal_pl", lane="article_engine")
    assert result.verdict == "hard_block"
    assert any(f.rule_id == "legal_pl_outcome_guarantee" for f in result.flags)


def test_evaluate_matched_text_provenance() -> None:
    """Flags carry the matched substring so reviewers can locate the
    offending text quickly."""
    artifact = "We rely on Safe Harbor here."
    result = evaluate_compliance(artifact, "gdpr_eu", lane="article_engine")
    sh_flag = next(f for f in result.flags if f.rule_id == "gdpr_safe_harbor_invalid")
    assert sh_flag.matched_text is not None
    assert "safe harbor" in sh_flag.matched_text.lower()


# ---------------------------------------------------------------------------
# COMPLIANCE_JUDGE constant + env override (D25)
# ---------------------------------------------------------------------------


def test_compliance_judge_default_is_claude_opus() -> None:
    """D25: single frontier-class judge, claude/opus, for v1's 7
    reviewer-assist-gated lanes. Drift pin so a future edit is
    deliberate."""
    assert COMPLIANCE_JUDGE == ("claude", "opus")


def test_get_compliance_judge_config_returns_default() -> None:
    backend, model = get_compliance_judge_config()
    assert backend == "claude"
    assert model == "opus"


def test_compliance_judge_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """Operator override via COMPLIANCE_JUDGE_BACKEND / _MODEL env vars
    is read at call time."""
    monkeypatch.setenv("COMPLIANCE_JUDGE_BACKEND", "codex")
    monkeypatch.setenv("COMPLIANCE_JUDGE_MODEL", "gpt-5.5")
    backend, model = get_compliance_judge_config()
    assert backend == "codex"
    assert model == "gpt-5.5"


# ---------------------------------------------------------------------------
# D6 revised — single rule_set per call
# ---------------------------------------------------------------------------


def test_evaluate_compliance_api_accepts_single_rule_set_name() -> None:
    """Per D6 revised + TD-18: the API takes a single rule_set_name string
    (not a list). Multi-rule-set merge deferred to first client onboarding
    that needs it.

    ClientConfig.reviewer_assist_checklists is length-1 in v1; call sites
    pass `client.reviewer_assist_checklists[0]`.
    """
    # The function signature itself pins the contract — no list type accepted.
    # `from __future__ import annotations` stringifies the annotation, so we
    # compare to "str" rather than the type object.
    import inspect
    sig = inspect.signature(evaluate_compliance)
    rule_set_param = sig.parameters["rule_set_name"]
    assert rule_set_param.annotation == "str"
