"""R22 gate-1: in-loop reviewer-assist compliance check, fires before
variant scoring.

Plan §R22 names the dual-gate compliance architecture:
  - Gate-1 (this module): in-loop fitness penalty — runs during
    evolution scoring so the loop can systematically optimize away
    from regulatory violations.
  - Gate-2 (src.review.service): pre-publish human review — runs at
    publication time so a real reviewer signs off on each artifact.

Before this module, gate-1 was library-only: `evaluate_compliance`
was importable + tested but never invoked by any lane's scoring
path. Variants could pass through evolution with Art. 14 hard-block
prose intact because no production code called the gate. CE-review
adversarial finding ADV-001 surfaced the orphan.

This module is the integration point. It is invoked from
`autoresearch/evolve.py` once per variant, AFTER structural-gate
validation + BEFORE scoring. The lane (or harness) opts in by
setting `EVOLUTION_RULE_SET` to the name of a reviewer-assist
checklist YAML (e.g., `medical_pl`); when unset, the gate is a
no-op and the substrate falls through to the prior behavior.

Semantics per plan §D5 + §Compliance Posture:
  - verdict='hard_block' → discard variant (frontier rejection)
  - verdict='soft_warn'  → write compliance-meta.json sidecar so the
    pre-publish reviewer (gate-2 at U18) sees the flag at sign-off;
    the variant's score is NOT discounted by gate-1 (per §Compliance
    Posture: gate-1 is fitness only; the actual safety weight lives
    at gate-2)
  - verdict='clean'      → no-op (sidecar still written for the
    audit trail)

The gate is opt-in by design: lanes that don't have a configured
rule_set (or operators running ad-hoc fixtures without the env set)
see no behavior change. v1 production wiring is parallel-track per
plan §Parallel-Track Risks (Klinika consent + DWF engagement letter
+ outside-counsel YAML review).
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict
from pathlib import Path

from src.compliance.judge import ComplianceResult, evaluate_compliance
from src.compliance.loader import ChecklistNotFoundError

logger = logging.getLogger(__name__)


# Env var the lane harness / fixture sets to opt in to gate-1.
# Convention mirrors the existing EVOLUTION_* env namespace
# (EVOLUTION_LANE, EVOLUTION_INNER_BACKEND, etc.).
_RULE_SET_ENV = "EVOLUTION_RULE_SET"


# Per-lane deliverable glob convention. Each new content lane writes
# its variant outputs under a known subdirectory of the variant_dir
# per its WorkflowSpec.deliverables tuple. Gate-1 concatenates the
# text of every deliverable matched by these globs and evaluates as a
# single artifact.
#
# When a lane is missing from this map, gate-1 is a no-op for that
# lane (returns None). This keeps the gate's blast radius bounded:
# adding a lane to gate-1 coverage is an explicit dict-edit, not an
# accident-of-grep that fires on adjacent lane output shapes.
_LANE_DELIVERABLE_GLOBS: dict[str, tuple[str, ...]] = {
    "article_engine": ("drafts/*.md", "drafts/*.txt"),
    "image_engine":   ("drafts/*.md",),     # captions + alt text + fal prompts
    "ad_engine":      ("drafts/*.json", "drafts/*.md"),
    "site_engine":    ("drafts/*.html",),
    "storyboard":     ("stories/*.json", "storyboards/*.json"),
    "linkedin_engine": ("drafts/*.md",),
    "x_engine":       ("drafts/*.md",),
}


class ComplianceGateOutcome:
    """Marker for the three possible gate outcomes.

    Lighter-weight than a Pydantic model: this module emits one of three
    behavioral signals (None / soft_warn-passthrough / hard_block-discard)
    + persists a sidecar. The richer ComplianceResult is what gets
    serialized to the sidecar; callers in evolve.py care only about
    'should I discard?' which is a bool returned alongside.
    """

    SKIPPED = "skipped"        # no rule_set configured; opt-out
    CLEAN = "clean"            # gate fired, no flags
    SOFT_WARN = "soft_warn"    # gate fired, warn flags persisted
    HARD_BLOCK = "hard_block"  # gate fired, hard-block flags persisted → discard


def _collect_deliverable_text(variant_dir: Path, lane: str) -> str:
    """Concatenate all deliverable text matched by the lane's globs.

    Returns empty string when no deliverables exist (variant produced
    no output) or when the lane has no glob convention. Callers
    treat empty as 'nothing to evaluate' → gate skip with logged
    warning.
    """
    globs = _LANE_DELIVERABLE_GLOBS.get(lane)
    if not globs:
        return ""
    parts: list[str] = []
    for glob in globs:
        for path in sorted(variant_dir.glob(glob)):
            try:
                parts.append(path.read_text(encoding="utf-8", errors="replace"))
            except OSError as exc:
                logger.warning(
                    "gate-1: skipping unreadable deliverable %s: %s", path, exc,
                )
    return "\n\n---\n\n".join(parts)


def apply_compliance_gate(
    variant_dir: Path,
    lane: str,
    rule_set_name: str | None = None,
) -> tuple[str, ComplianceResult | None]:
    """Run gate-1 against the variant's deliverable text.

    Args:
        variant_dir: per-variant output dir written by the lane workflow.
        lane: lane name (e.g., 'article_engine'). Determines deliverable
            globs.
        rule_set_name: explicit rule_set override. When None, reads
            from `EVOLUTION_RULE_SET` env. When that's also unset,
            the gate is a no-op (returns ("skipped", None)).

    Returns:
        A tuple `(outcome, result)` where:
          - outcome is one of `ComplianceGateOutcome.{SKIPPED, CLEAN,
            SOFT_WARN, HARD_BLOCK}`
          - result is the ComplianceResult when the gate fired, else None

    Side effect: when the gate fires (i.e., not SKIPPED), writes a
    `compliance-meta.json` sidecar to `variant_dir` carrying the
    full ComplianceResult for the pre-publish reviewer (gate-2 at
    U18). The sidecar is the audit trail; no PII beyond what was
    in the artifact + the matched flag prose.

    Per plan §D5: hard_block → score 0 → frontier rejection. The
    caller in evolve.py is responsible for the actual discard
    (this function reports the verdict; it does not mutate the
    archive). soft_warn → no score discount at gate-1 (passes
    through); the flag is for the reviewer at gate-2.
    """
    if rule_set_name is None:
        rule_set_name = os.environ.get(_RULE_SET_ENV, "").strip() or None
    if rule_set_name is None:
        logger.debug(
            "gate-1: skipped for %s (no rule_set configured via "
            "%s env or explicit param)", lane, _RULE_SET_ENV,
        )
        return ComplianceGateOutcome.SKIPPED, None

    text = _collect_deliverable_text(variant_dir, lane)
    if not text:
        logger.warning(
            "gate-1: no deliverable text to evaluate for %s in %s "
            "(lane glob: %s). Skipping.",
            lane, variant_dir, _LANE_DELIVERABLE_GLOBS.get(lane, "<unmapped>"),
        )
        return ComplianceGateOutcome.SKIPPED, None

    try:
        result = evaluate_compliance(text, rule_set_name, lane=lane)
    except ChecklistNotFoundError as exc:
        logger.error(
            "gate-1: rule_set %r not found: %s. Treating as SKIPPED — operator "
            "must verify %s env vs reviewer_assist/checklists/<name>.yaml.",
            rule_set_name, exc, _RULE_SET_ENV,
        )
        return ComplianceGateOutcome.SKIPPED, None

    # Sidecar: full ComplianceResult for the reviewer + audit trail.
    sidecar_path = variant_dir / "compliance-meta.json"
    try:
        sidecar_path.write_text(
            json.dumps(result.model_dump(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except OSError as exc:
        logger.warning(
            "gate-1: could not write %s: %s. The gate outcome is unaffected; "
            "the reviewer audit trail will be missing this entry.",
            sidecar_path, exc,
        )

    if result.verdict == "hard_block":
        return ComplianceGateOutcome.HARD_BLOCK, result
    if result.verdict == "soft_warn":
        return ComplianceGateOutcome.SOFT_WARN, result
    return ComplianceGateOutcome.CLEAN, result


__all__ = [
    "ComplianceGateOutcome",
    "apply_compliance_gate",
]
