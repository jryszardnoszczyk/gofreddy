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


def test_evaluate_with_klinika_polish_pattern() -> None:
    """Polish-language patterns fire on the right surfaces (Klinika
    archetype). Rule id reflects U16 authoring grouping
    (`naj_novelty` covers `najnowocześniejszy`)."""
    artifact = "Nasza klinika oferuje najnowocześniejszą procedurę liposukcji."
    result = evaluate_compliance(artifact, "medical_pl", lane="article_engine")
    assert result.verdict == "hard_block"
    assert any(f.rule_id == "medical_pl_superlative_naj_novelty" for f in result.flags)


def test_evaluate_with_dwf_polish_pattern() -> None:
    """DWF archetype: outcome-guarantee pattern fires. Rule id reflects
    U17 authoring grouping (`guarantee_win`)."""
    artifact = "Gwarantujemy wygraną w tej sprawie."
    result = evaluate_compliance(artifact, "legal_pl", lane="article_engine")
    assert result.verdict == "hard_block"
    assert any(f.rule_id == "legal_pl_guarantee_win" for f in result.flags)


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
    deliberate — silently downgrading to cheaper-but-permissive
    cyber-filter would degrade reviewer-assist judgment without
    detection."""
    assert COMPLIANCE_JUDGE == ("claude", "opus")


def test_compliance_flag_accepts_future_extension_fields() -> None:
    """Per the 4-agent review (AC-1 T2-A): ComplianceFlag is now
    frozen Pydantic with extra='allow'. v1.5+ can add fields like
    `remediation_hint` without breaking lanes that already serialize
    flag dicts into emails / audit logs / token payloads."""
    from src.compliance.judge import ComplianceFlag
    flag = ComplianceFlag.model_validate({
        "rule_id": "test-rule",
        "severity": "soft_warn",
        "rule_set_name": "test_set",
        "matched_text": "x",
        "prose": "test",
        # Hypothetical v1.5 extension field
        "remediation_hint": "consider rewording with X instead",
    })
    assert flag.rule_id == "test-rule"
    # extra='allow' preserves the additional field
    assert flag.model_dump().get("remediation_hint") == "consider rewording with X instead"


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


def test_redos_pattern_does_not_hang_under_long_artifact(tmp_path: Path, monkeypatch) -> None:
    """Per the 4-agent review (adv-3 + sec-7): a catastrophic-backtracking
    pattern in a YAML rule against a long artifact must not hang the
    worker. The pattern.search call has a wall-clock budget; on
    timeout, the flag is suppressed with a log warning (fail-safe)."""
    import time
    from src.compliance.judge import evaluate_compliance

    # Construct a tmp rule set with a known-ReDoS pattern, point the
    # loader at it via monkeypatching the resolver.
    bad_yaml = tmp_path / "_placeholder_test_redos.yaml"
    bad_yaml.write_text(
        "name: test_redos\n"
        "metadata: {reviewer_assist_posture: true, legal_grade_gate: false}\n"
        "rules:\n"
        "  - id: redos_quadratic\n"
        "    pattern: '^(a+)+b'\n"
        "    severity: soft_warn\n"
        "    prose: Test ReDoS pattern\n"
    )
    from src.compliance import loader as loader_mod
    monkeypatch.setattr(
        loader_mod, "_checklist_yaml_path",
        lambda name: bad_yaml if name == "test_redos" else loader_mod._REPO_ROOT / "missing.yaml",
    )

    # 50K-char artifact of 'a's (no terminating 'b' → catastrophic backtrack)
    pathological = "a" * 50_000

    start = time.time()
    result = evaluate_compliance(pathological, "test_redos", lane="article_engine")
    elapsed = time.time() - start

    # Must complete within ~3s (2s budget + overhead); flag suppressed.
    assert elapsed < 3.5, f"ReDoS protection failed; took {elapsed:.1f}s"
    assert result.verdict == "clean"


def test_artifact_length_capped_to_256kb(tmp_path: Path, monkeypatch, caplog) -> None:
    """Per the 4-agent review (adv-3 + sec-7): artifacts > 256 KB are
    truncated before pattern.search runs. Verifies the cap fires + logs."""
    import logging
    from src.compliance.judge import evaluate_compliance

    huge_artifact = "x" * (300 * 1024)  # 300 KB
    caplog.set_level(logging.WARNING)
    result = evaluate_compliance(huge_artifact, "gdpr_eu", lane="article_engine")
    assert result.verdict == "clean"  # no actual matches in 'x' * N
    assert any(
        "artifact truncated" in rec.message
        for rec in caplog.records
    )


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
