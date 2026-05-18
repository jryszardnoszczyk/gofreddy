"""Reviewer-assist (internal name: 'compliance') framework — Content Engine v1.

Per §Compliance Posture in the plan: the YAMLs under
``reviewer_assist/checklists/<name>.yaml`` are **reviewer-assist
checklists, NOT legal-grade compliance gates**. The engineering term
"compliance" persists in module names + function names as internal
shorthand; all external / client-facing language uses "reviewer-assist".

Pre-publish human review (U7) is the actual safety mechanism. The
YAML accelerates reviewer pattern-matching (~30-50% per-artifact
reviewer-time reduction); it does NOT substitute for reviewer judgment.

Per D6 revised + TD-18: v1 supports a SINGLE rule set per client.
Multi-rule-set merge logic is deferred to the first client onboarding
that needs two rule sets. ``ClientConfig.reviewer_assist_checklists``
(U2) enforces length 1 at the schema level.
"""

from src.compliance.judge import (
    COMPLIANCE_JUDGE,
    ComplianceResult,
    ComplianceVerdict,
    evaluate_compliance,
    get_compliance_judge_config,
)
from src.compliance.loader import (
    ChecklistNotFoundError,
    load_rule_set,
)
from src.compliance.schema import (
    ComplianceRule,
    ComplianceRuleSet,
    Severity,
)

__all__ = [
    "COMPLIANCE_JUDGE",
    "ChecklistNotFoundError",
    "ComplianceResult",
    "ComplianceRule",
    "ComplianceRuleSet",
    "ComplianceVerdict",
    "Severity",
    "evaluate_compliance",
    "get_compliance_judge_config",
    "load_rule_set",
]
