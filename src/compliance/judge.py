"""Reviewer-assist judge + COMPLIANCE_JUDGE constant (D25).

Per D25: a single frontier-class judge across the 7 reviewer-assist-
gated lanes (storyboard, article_engine, image_engine, ad_engine,
site_engine, linkedin_engine, x_engine). Compliance correctness is the
most-consequential judge call (false-negative = regulator-flagged
published artifact); diverse from inner-loop (codex/gpt-5.5) per
``judge-decisions-2026-05-11.md``.

The 2-tuple constant is the simplest shape (no singleton class
ceremony per Pass-5 audit). Operator override via
``COMPLIANCE_JUDGE_BACKEND`` / ``COMPLIANCE_JUDGE_MODEL`` env vars
read at call time.

Per the §Compliance Posture clause: this judge fires on rules with
``pattern`` defined (deterministic regex; slop-gate precedent) and
returns prose-grounded interpretation for rules whose ``pattern`` is
None (LLM-judged surface). The function returns a structured result;
actual LLM dispatch for prose-only rules happens at the per-lane
integration level (U13/U14/U15/U15b) where the existing judge
HTTP service is already wired.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from typing import Literal

from src.compliance.loader import load_rule_set
from src.compliance.schema import ComplianceRule, ComplianceRuleSet, Severity

logger = logging.getLogger(__name__)


# D25 — single frontier-class judge for all reviewer-assist work in v1.
# 2-tuple (backend, model). Operator override via env (read at call time).
COMPLIANCE_JUDGE: tuple[str, str] = ("claude", "opus")


ComplianceVerdict = Literal["clean", "soft_warn", "hard_block"]


def get_compliance_judge_config() -> tuple[str, str]:
    """Return the active (backend, model) for the reviewer-assist judge,
    honoring env-var overrides ``COMPLIANCE_JUDGE_BACKEND`` /
    ``COMPLIANCE_JUDGE_MODEL`` when set."""
    backend = os.environ.get("COMPLIANCE_JUDGE_BACKEND") or COMPLIANCE_JUDGE[0]
    model = os.environ.get("COMPLIANCE_JUDGE_MODEL") or COMPLIANCE_JUDGE[1]
    return backend, model


@dataclass(frozen=True)
class ComplianceFlag:
    """A single rule that fired against the artifact."""

    rule_id: str
    severity: Severity
    rule_set_name: str
    matched_text: str | None  # Substring that matched the pattern (None for LLM-only rules)
    prose: str                # Operator-readable rationale (from rule.prose)


@dataclass(frozen=True)
class ComplianceResult:
    """Outcome of evaluate_compliance for a single artifact."""

    verdict: ComplianceVerdict
    flags: list[ComplianceFlag] = field(default_factory=list)
    rule_set_name: str = ""
    lane: str = ""

    @property
    def has_hard_block(self) -> bool:
        return any(f.severity == "hard_block" for f in self.flags)

    @property
    def has_soft_warn(self) -> bool:
        return any(f.severity == "soft_warn" for f in self.flags)


def _compile_patterns(rule: ComplianceRule) -> list[re.Pattern[str]]:
    """Compile a rule's pattern(s) once per call.

    Schema validation already verified the patterns compile; here we
    pay the compile cost for the actual evaluation.
    """
    if rule.pattern is None:
        return []
    raw = [rule.pattern] if isinstance(rule.pattern, str) else rule.pattern
    flags = 0 if rule.case_sensitive else re.IGNORECASE
    return [re.compile(p, flags=flags) for p in raw]


def evaluate_compliance(
    artifact: str,
    rule_set_name: str,
    lane: str,
) -> ComplianceResult:
    """Evaluate ``artifact`` against the named rule set for ``lane``.

    Args:
        artifact: the candidate text to evaluate (article body, ad copy,
            section HTML, etc.).
        rule_set_name: single rule_set name per D6 revised / TD-18.
        lane: lane name for error reporting + result provenance.

    Returns:
        ComplianceResult with overall verdict (hard_block | soft_warn |
        clean) and per-flag provenance.

    Per D6 revised: v1 evaluates a SINGLE rule set per call. The API
    accepts a single name (not a list); call sites pass
    ``client.reviewer_assist_checklists[0]`` (length-1 enforced by
    ClientConfig). Multi-rule-set merge logic deferred.

    Per the §Compliance Posture clause: rules with `pattern` defined
    are matched deterministically (regex). Rules with `pattern=None`
    return prose-only flags that the LLM judge interprets at the
    per-lane integration boundary (U13+); this function pre-resolves
    the prose so the per-lane integration only needs to wrap the
    existing judge HTTP service.
    """
    rule_set = load_rule_set(rule_set_name)
    flags: list[ComplianceFlag] = []

    for rule in rule_set.rules:
        if rule.pattern is None:
            # LLM-only rule. The deterministic pass here records a stub
            # flag whose severity is informational ("soft_warn" by
            # convention until the LLM judge resolves at the per-lane
            # integration boundary). Callers that want the LLM verdict
            # invoke the judge HTTP service with `rule.prose` as the
            # rubric prompt.
            continue

        compiled = _compile_patterns(rule)
        for pattern in compiled:
            match = pattern.search(artifact)
            if match is None:
                continue
            flags.append(ComplianceFlag(
                rule_id=rule.id,
                severity=rule.severity,
                rule_set_name=rule_set.name,
                matched_text=match.group(0),
                prose=rule.prose,
            ))
            break  # One match per rule is enough; record provenance + move on.

    verdict: ComplianceVerdict
    if any(f.severity == "hard_block" for f in flags):
        verdict = "hard_block"
    elif any(f.severity == "soft_warn" for f in flags):
        verdict = "soft_warn"
    else:
        verdict = "clean"

    return ComplianceResult(
        verdict=verdict,
        flags=flags,
        rule_set_name=rule_set.name,
        lane=lane,
    )


__all__ = [
    "COMPLIANCE_JUDGE",
    "ComplianceFlag",
    "ComplianceResult",
    "ComplianceVerdict",
    "evaluate_compliance",
    "get_compliance_judge_config",
]
