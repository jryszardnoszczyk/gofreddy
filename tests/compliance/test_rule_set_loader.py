"""Reviewer-assist checklist schema + loader (U5)."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from src.compliance.loader import (
    ChecklistNotFoundError,
    load_rule_set,
)
from src.compliance.schema import ComplianceRule, ComplianceRuleSet


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------


def _minimal_rule_dict(**overrides) -> dict:
    base = {
        "id": "fixture_rule",
        "pattern": r"\bfixture\b",
        "severity": "soft_warn",
        "prose": "Test rule for the schema.",
    }
    base.update(overrides)
    return base


def _minimal_rule_set_dict(**overrides) -> dict:
    base = {
        "name": "fixture_rule_set",
        "rules": [_minimal_rule_dict()],
        "metadata": {},
    }
    base.update(overrides)
    return base


def test_minimal_rule_set_constructs() -> None:
    rs = ComplianceRuleSet.model_validate(_minimal_rule_set_dict())
    assert rs.rule_set_name == "fixture_rule_set"
    assert len(rs.rules) == 1
    assert rs.rules[0].id == "fixture_rule"


def test_rule_pattern_validates_compile_at_load() -> None:
    """Schema-level regex validation catches typos at YAML load time
    rather than during artifact evaluation."""
    with pytest.raises(ValidationError) as exc:
        ComplianceRule.model_validate(_minimal_rule_dict(pattern="[unclosed"))
    assert "failed to compile" in str(exc.value)


def test_rule_pattern_accepts_list() -> None:
    rule = ComplianceRule.model_validate(_minimal_rule_dict(
        pattern=["one", "two", "three"],
    ))
    assert rule.pattern == ["one", "two", "three"]


def test_rule_pattern_optional_for_llm_only_rules() -> None:
    rule = ComplianceRule.model_validate(_minimal_rule_dict(pattern=None))
    assert rule.pattern is None


def test_rule_severity_must_be_hard_block_or_soft_warn() -> None:
    with pytest.raises(ValidationError):
        ComplianceRule.model_validate(_minimal_rule_dict(severity="critical"))


def test_rule_set_rejects_duplicate_rule_ids() -> None:
    payload = _minimal_rule_set_dict(rules=[
        _minimal_rule_dict(id="rule_a"),
        _minimal_rule_dict(id="rule_a", pattern=r"\bother\b"),
    ])
    with pytest.raises(ValidationError) as exc:
        ComplianceRuleSet.model_validate(payload)
    assert "duplicate rule ids" in str(exc.value)


def test_rule_set_frozen() -> None:
    rs = ComplianceRuleSet.model_validate(_minimal_rule_set_dict())
    with pytest.raises(ValidationError):
        rs.rule_set_name = "different"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Loader: real YAML files
# ---------------------------------------------------------------------------


def test_load_gdpr_eu_real_checklist() -> None:
    """gdpr_eu is the load-bearing real checklist for Klinika+DWF."""
    rs = load_rule_set("gdpr_eu")
    assert rs.rule_set_name == "gdpr_eu"
    assert rs.metadata.get("reviewer_assist_posture") is True
    assert rs.metadata.get("legal_grade_gate") is False
    assert len(rs.rules) >= 10  # baseline: ~13 rules in v1
    # Spot-check a couple of marquee rules
    rule_ids = {r.id for r in rs.rules}
    assert "gdpr_consent_implicit" in rule_ids
    assert "gdpr_safe_harbor_invalid" in rule_ids


def test_load_medical_pl_authored() -> None:
    """medical_pl is the v1 reviewer-assist checklist (graduated from
    placeholder in U16). Reviewer-assist posture + two-reviewer signoff
    metadata persist; the `placeholder` flag is gone."""
    rs = load_rule_set("medical_pl")
    assert rs.rule_set_name == "medical_pl"
    assert rs.metadata.get("placeholder") is None
    assert rs.metadata.get("two_reviewer_signoff_required") is True
    # Per U16 plan: ~30-50 rules covering Art. 14 + KEL + Medical Devices Act.
    assert 30 <= len(rs.rules) <= 60


def test_load_legal_pl_authored() -> None:
    """legal_pl is the v1 reviewer-assist checklist (graduated from
    placeholder in U17)."""
    rs = load_rule_set("legal_pl")
    assert rs.rule_set_name == "legal_pl"
    assert rs.metadata.get("placeholder") is None
    assert rs.metadata.get("two_reviewer_signoff_required") is True
    # Per U17 plan: ~30-50 rules covering KERP + Zbiór + bar codes.
    assert 30 <= len(rs.rules) <= 60


def test_load_unknown_rule_set_raises() -> None:
    """Per plan U5 error path: unknown checklist name → FileNotFoundError
    pointing at the canonical (non-placeholder) path."""
    with pytest.raises(ChecklistNotFoundError) as exc:
        load_rule_set("does-not-exist")
    assert "does-not-exist" in str(exc.value)


# ---------------------------------------------------------------------------
# Posture pin — reviewer-assist NOT legal-grade compliance gate
# ---------------------------------------------------------------------------


def test_v1_checklists_carry_reviewer_assist_posture_metadata() -> None:
    """Per §Compliance Posture: every v1 reviewer-assist YAML must
    declare reviewer_assist_posture=true + legal_grade_gate=false in
    metadata. Drift pin so a placeholder graduation in U16/U17 doesn't
    accidentally claim legal-grade status without outside-counsel review."""
    for name in ("gdpr_eu", "medical_pl", "legal_pl"):
        rs = load_rule_set(name)
        assert rs.metadata.get("reviewer_assist_posture") is True, (
            f"{name} missing reviewer_assist_posture=true"
        )
        assert rs.metadata.get("legal_grade_gate") is False, (
            f"{name} missing legal_grade_gate=false"
        )
