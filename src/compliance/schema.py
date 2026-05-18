"""ComplianceRule + ComplianceRuleSet schema.

Internal "compliance" terminology per §Compliance Posture; external
language is "reviewer-assist." The YAML files at
``reviewer_assist/checklists/<name>.yaml`` validate against the
ComplianceRuleSet schema.

Per D20: data-driven YAML (not Python). New rule sets are added by
authoring a YAML file alongside the existing ones; no Python code
changes required for the loader to pick them up.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


Severity = Literal["hard_block", "soft_warn"]


class ComplianceRule(BaseModel):
    """A single rule within a reviewer-assist checklist."""

    model_config = ConfigDict(frozen=True, extra="allow")

    id: str = Field(
        ...,
        description=(
            "Slug-shaped rule identifier. Convention: '<surface>_<pattern>' "
            "(e.g. 'art14_superlative_najlepszy', 'gdpr_consent_implicit')."
        ),
    )
    pattern: str | list[str] | None = Field(
        default=None,
        description=(
            "Regex pattern (or list of patterns; ANY match fires) for "
            "deterministic detection. When None, the rule is LLM-judged "
            "via `prose` only (slop-gate precedent: deterministic regex "
            "separate from LLM judgment)."
        ),
    )
    case_sensitive: bool = Field(
        default=False,
        description="When True, pattern matching is case-sensitive.",
    )
    severity: Severity = Field(
        ...,
        description=(
            "hard_block = score 0 → frontier rejection (D5). "
            "soft_warn = score scaled down + flag persisted to "
            "compliance-meta.json sidecar."
        ),
    )
    prose: str = Field(
        ...,
        description=(
            "Rubric-style description used by the LLM judge (D25 "
            "COMPLIANCE_JUDGE = claude/opus). Operator-readable prose "
            "explaining why this is a flag + how a reviewer should "
            "interpret it. Post-rewrite anchor design (S2): operational "
            "definitions + substitution tests + falsifiability + named "
            "Score-3 failure modes + anti-gaming clauses."
        ),
    )

    @field_validator("id")
    @classmethod
    def _id_is_slug_shaped(cls, v: str) -> str:
        if not v or any(c.isspace() for c in v):
            raise ValueError(f"rule id must be non-empty with no whitespace; got {v!r}")
        return v

    @field_validator("pattern")
    @classmethod
    def _pattern_compiles(cls, v: str | list[str] | None) -> str | list[str] | None:
        """Validate regex patterns at load time so a typo in a YAML rule
        surfaces at startup, not at evaluation time on a real artifact."""
        if v is None:
            return v
        patterns = [v] if isinstance(v, str) else v
        for p in patterns:
            try:
                re.compile(p)
            except re.error as exc:
                raise ValueError(
                    f"pattern {p!r} failed to compile: {exc}"
                )
        return v


class ComplianceRuleSet(BaseModel):
    """A reviewer-assist checklist — a named bundle of rules.

    Per D6 revised + TD-18: ClientConfig.reviewer_assist_checklists has
    length 1 in v1. The schema permits multi-rule-set composition at the
    primitive level so v1.5+ migration is additive (no schema break).
    """

    model_config = ConfigDict(frozen=True, extra="allow", populate_by_name=True)

    rule_set_name: str = Field(
        ...,
        alias="name",
        description=(
            "Slug-shaped checklist name; matches the YAML filename. YAML "
            "keys use `name` for operator-friendliness; the model field "
            "is `rule_set_name` to disambiguate from VoicePersona."
            "persona_slug + ClientConfig.display_name when lanes compose "
            "all three in prompts."
        ),
    )
    rules: list[ComplianceRule] = Field(
        ...,
        description="The rule set's rules. Empty list is allowed (no-op checklist).",
    )
    metadata: dict = Field(
        default_factory=dict,
        description=(
            "Free-form: authoring date, source citations (Art. 14 etc), "
            "legal-review status, placeholder flag. Operator-curated."
        ),
    )

    @field_validator("rule_set_name")
    @classmethod
    def _rule_set_name_is_slug_shaped(cls, v: str) -> str:
        if not v or any(c.isspace() for c in v):
            raise ValueError(f"rule_set_name must be non-empty with no whitespace; got {v!r}")
        return v

    @field_validator("rules")
    @classmethod
    def _rule_ids_are_unique(cls, v: list[ComplianceRule]) -> list[ComplianceRule]:
        seen: set[str] = set()
        dupes: list[str] = []
        for rule in v:
            if rule.id in seen:
                dupes.append(rule.id)
            seen.add(rule.id)
        if dupes:
            raise ValueError(f"duplicate rule ids in rule set: {dupes}")
        return v


__all__ = [
    "ComplianceRule",
    "ComplianceRuleSet",
    "Severity",
]
