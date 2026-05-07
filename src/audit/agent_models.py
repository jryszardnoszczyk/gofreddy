"""Pydantic schemas for the v1 marketing audit pipeline.

Authoritative source: the combined spec of
  - docs/plans/2026-04-20-002-feat-automated-audit-pipeline-plan.md
    (Finding schema: 6 required + report_section enum + 8 optional fields)
  - docs/plans/2026-04-22-005-marketing-audit-lens-catalog.md
    (SubSignal → ParentFinding aggregation architecture, locked v2 2026-04-23)
  - docs/plans/2026-04-23-002-marketing-audit-lhr-design.md
    (v1 flat Finding → SubSignal + ParentFinding migration)

Model hierarchy (what flows through v1 stages):

    Stage 2 agent → emits SubSignals (atomic, per-lens) → AgentOutput
                                                             ↓
    Stage 3 synthesis → groups SubSignals by report_section → ParentFindings
                                                                 ↓
                        Python-deterministic arithmetic     → HealthScore
                                                                 ↓
                                                          Deliverable render

Design decisions worth calling out:

- `SubSignal.evidence_urls: list[HttpUrl] = Field(min_length=1)` — Pydantic
  rejects evidence-free findings at construction per R8 R-#9. `HttpUrl` also
  rejects `file://` and other non-http schemes.
- No `min_length` cap on `recommendation` — the plan is explicit that
  quality (strategic-not-tactical, ≥50-word substance) is enforced by the
  critique/judge loop, not by Pydantic. Schema stays a structural floor.
- `ParentFinding.severity` and `.confidence` are computed from children via
  `@model_validator(mode="after")`, so agents/synthesis can't drift them
  against the rollup rule (severity = max of children; confidence = floor).
- Judge schemas (`SubSignalJudgment`, `ParentFindingJudgment`) included so
  the serialization shape is locked before v2 judges get built. v1 doesn't
  invoke them; agents can annotate findings with `quality_warning` directly.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


# ── Enum aliases ──────────────────────────────────────────────────────────
ReportSection = Literal[
    "seo", "geo", "competitive", "monitoring", "conversion",
    "distribution", "lifecycle", "martech_attribution", "brand_narrative",
]
ALL_REPORT_SECTIONS: tuple[str, ...] = (
    "seo", "geo", "competitive", "monitoring", "conversion",
    "distribution", "lifecycle", "martech_attribution", "brand_narrative",
)

Confidence = Literal["H", "M", "L"]
_CONFIDENCE_ORDER: dict[str, int] = {"H": 3, "M": 2, "L": 1}

EffortBand = Literal["S", "M", "L"]
ProposalTier = Literal["fix_it", "build_it", "run_it"]
# Rubric-coverage value can be the simple Literal OR a richer dict
# (some Stage-2 agents emit {"sub_signal_ids": [...], "fired": True}).
# Stage-3 only checks key presence; the value's shape is informational.
RubricCoverage = Literal["covered", "gap_flagged"] | dict[str, Any]
ScoreBand = Literal["red", "yellow", "green"]


# ── SubSignal: atomic per-lens observation ────────────────────────────────
class SubSignal(BaseModel):
    """What a Stage 2 agent emits once per lens firing.

    Kept deliberately thin: one observation, one severity, supporting
    evidence URLs. Stage 3 groups these by `report_section` and synthesizes
    narrative ParentFindings on top.
    """

    # extra="ignore" because Stage-2 agents in production add useful
    # context fields (audit_id, prospect_domain, gap_flagged) that the
    # original strict schema rejected — caused Stage-2→3 data-flow break
    # on Anthropic dry-run 2026-05-07 (all 3 agents' outputs failed
    # AgentOutput.model_validate_json → report.json got parent_findings:[]).
    model_config = ConfigDict(frozen=True, extra="ignore")

    id: str = Field(description="Stable agent-assigned ID, unique within one audit run")
    lens_id: str = Field(description="ID from data/rubrics_<agent>.yaml — ties observation to catalog lens")
    agent: str = Field(description="Emitting agent role (findability/narrative/acquisition/experience)")
    report_section: ReportSection = Field(description="Which deliverable section this feeds (for routing)")

    observation: str = Field(min_length=1, description="One-line factual observation — what was seen")
    # evidence_urls relaxed: agents legitimately emit gap_flagged signals
    # with no URLs (the gap IS the finding). evidence_quotes provides the
    # text-only path. Either or both can be populated.
    # Relaxed from list[HttpUrl] → list[str]. HttpUrl rejected legitimate
    # international URLs (.pl with IDN encoding) on the Anthropic dry run.
    # Stage-3 doesn't depend on URL well-formedness; presentation layer
    # treats them as strings anyway.
    evidence_urls: list[str] = Field(default_factory=list, description="0+ supporting URLs (any string; presentation treats as href)")
    evidence_quotes: list[str] = Field(default_factory=list, description="Optional verbatim quotes lifted from sources")

    # severity allowed null when gap_flagged (signal acknowledges a lens
    # but couldn't evaluate it due to data missing — severity is meaningless).
    severity: int | None = Field(default=None, ge=0, le=3, description="0=positive, 1=minor, 2=moderate, 3=critical, None=gap_flagged")
    confidence: Confidence | None = Field(default=None, description="H/M/L — agent's confidence; None when gap_flagged")

    # Phase-0 meta-frame tag — only set on SubSignals derived from the
    # 9 Phase-0 meta-frames per master plan §2.4. None for tactical lenses.
    phase0_frame: Literal[1, 2, 3, 4, 5, 6, 7, 8, 9] | None = Field(
        default=None,
        description="Set on SubSignals derived from Phase-0 meta-frames (master plan §2.4)",
    )

    # Optional tags — carry through to ParentFinding aggregation.
    category_tags: list[str] = Field(default_factory=list)
    quality_warning: bool = Field(default=False, description="Critique-loop flagged; agent elected to ship anyway")


# ── ParentFinding: strategic aggregation across SubSignals ────────────────
class ParentFinding(BaseModel):
    """Deliverable-level finding: one strategic story per report_section
    cluster, with the underlying SubSignals rendered as evidence rows.

    Stage 3 creates these by grouping SubSignals by `report_section` and
    asking Opus to consolidate them into strategic framings (typically
    25-32 ParentFindings per audit across 9 sections, matching market
    norms per catalog 005 line 44).
    """

    # extra="ignore" mirrors SubSignal — agents add context fields that
    # the strict schema rejected. See SubSignal.model_config note.
    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Stable Stage-3-assigned ID, unique within audit")
    report_section: ReportSection
    headline: str = Field(min_length=1, description="Strategic framing, not a list of sub-issues")
    evidence_summary: str = Field(min_length=1, description="2-3 sentence synthesis explaining the pattern")
    recommendation: str = Field(
        min_length=1,
        description=(
            "Strategic, not tactical — states what would solve this in "
            "terms the engagement delivers, not a DIY execution guide. "
            "≥50-word substance enforced by critique loop, not Pydantic."
        ),
    )

    # Accept either embedded SubSignal objects OR reference IDs (str).
    # Agents in production emit reference-ID style (more normalized,
    # matches DB-relational pattern). Stage 3 resolves IDs against the
    # agent's sibling sub_signals list when triangulation is needed.
    sub_signals: list[SubSignal | str] = Field(min_length=1, description="The atomic observations this parent aggregates (full objects or ID references)")

    # Computed from sub_signals via validator; explicit here so the
    # serialized shape is self-describing without re-deriving on read.
    # severity allowed null — when ParentFinding aggregates exclusively
    # gap_flagged sub_signals (no measured severity exists), the rolled-up
    # severity is meaningfully null rather than an arbitrary 0.
    severity: int | None = Field(default=None, ge=0, le=3, description="max(children.severity) — computed; None if all gap_flagged")
    confidence: Confidence | None = Field(default=None, description="floor(children.confidence); None if all gap_flagged")

    # Optional tagging — populated by Stage 3 / Stage 4.
    reach: int | None = Field(default=None, ge=0, le=3)
    feasibility: int | None = Field(default=None, ge=0, le=3)
    effort_band: EffortBand | None = None
    # Relaxed from Literal["fix_it", "build_it", "run_it"] → str|None.
    # Stage-2 agents in production sometimes use alternate tier vocabularies
    # (do_it_with_you / do_it_for_you / scoped / structural / ongoing). The
    # Stage-4 proposal generator normalizes whatever the agent wrote.
    proposal_tier_mapping: str | None = Field(
        default=None,
        description="Populated in Stage 3 after Stage 4 generates proposal tiers",
    )
    addresses_rubrics: list[str] = Field(
        default_factory=list,
        description="Rubric IDs this finding addresses — Stage 3 validates report_section matches each rubric's declared section",
    )
    quality_warning: bool = Field(
        default=False,
        description="Judge-2 flagged; surfaced to JR at ship-gate",
    )

    @model_validator(mode="after")
    def _recompute_rollup(self) -> "ParentFinding":
        """Enforce severity = max, confidence = floor across sub_signals.

        Writing through a ParentFinding can't drift these against the rule —
        Pydantic re-runs the validator on any .model_copy / reconstruction.

        Handles relaxed schema where sub_signals may be string ID references
        (rather than embedded SubSignal objects) — for those entries, this
        validator can't compute rollup so it preserves the explicitly-set
        severity/confidence on the ParentFinding. Caller-side resolution
        (Stage 3) maps reference IDs to the agent's sibling sub_signals list
        when triangulation is needed.
        """
        embedded = [s for s in self.sub_signals if not isinstance(s, str)]
        if not embedded:
            # All sub_signals are reference IDs — trust ParentFinding's
            # explicit severity/confidence as authored by the agent.
            return self
        rolled_severity = max(s.severity for s in embedded if s.severity is not None)
        confidence_vals = [_CONFIDENCE_ORDER[s.confidence] for s in embedded if s.confidence is not None]
        if not confidence_vals:
            return self
        rolled_confidence_val = min(confidence_vals)
        rolled_confidence: Confidence = {3: "H", 2: "M", 1: "L"}[rolled_confidence_val]  # type: ignore[assignment]

        if self.severity != rolled_severity or self.confidence != rolled_confidence:
            # Rebuild with the computed values — using object.__setattr__ since
            # the model isn't frozen but we want to avoid re-triggering the
            # validator on every attribute assign.
            object.__setattr__(self, "severity", rolled_severity)
            object.__setattr__(self, "confidence", rolled_confidence)
        return self


# ── AgentOutput: what a Stage 2 agent session returns ─────────────────────
class AgentMetadata(BaseModel):
    model_config = ConfigDict(extra="ignore")

    session_id: str = ""
    total_cost_usd: float = Field(default=0.0, ge=0.0)
    duration_ms: int = Field(default=0, ge=0)
    num_turns: int = Field(default=0, ge=0)
    model_usage: dict[str, int] = Field(
        default_factory=dict,
        description="Token counts keyed by model name (e.g. {'claude-sonnet-4-6': 42000})",
    )
    partial: bool = Field(default=False, description="True if the agent didn't complete cleanly")


class AgentOutput(BaseModel):
    """Single Stage-2 agent's deliverable to Stage 3.

    `rubric_coverage` is required and strict: every rubric ID from
    data/rubrics_<agent>.yaml must appear as a key with value
    "covered" (≥1 SubSignal produced) or "gap_flagged" (explicit
    insufficient-signal declaration). A missing key = invariant violation.
    """

    model_config = ConfigDict(extra="ignore")

    agent_name: str
    sub_signals: list[SubSignal] = Field(default_factory=list)
    parent_findings: list[ParentFinding] = Field(
        default_factory=list,
        description=(
            "Per-agent rolled-up ParentFindings. Stage 3 merges across "
            "agents instead of synthesizing from raw SubSignals (master "
            "plan §3.5 — per-agent synthesis simplification)."
        ),
    )
    agent_summary: str = Field(default="", description="Brief agent-authored takeaway")
    rubric_coverage: dict[str, RubricCoverage] = Field(
        default_factory=dict,
        description="Every rubric in agent's YAML must appear here — missing keys raise at Stage 3",
    )
    critique_iterations_used: int = Field(default=0, ge=0, le=3)
    metadata: AgentMetadata = Field(default_factory=AgentMetadata)


# ── HealthScore: Python-deterministic arithmetic + Opus rationale ─────────
class SectionScoreBreakdown(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    section: ReportSection
    findings_counted: int = Field(ge=0)
    arithmetic: str = Field(description="Human-readable computation, e.g. '100 - 20×1 - 10×2 - 5×3 = 45'")


class HealthScore(BaseModel):
    """Stage 3 output: Hero TL;DR numeral + per-section breakdown + rationale.

    The numeric fields are bit-deterministic Python (see
    `compute_health_score`). The `rationale` paragraph is a separate Opus
    call with temperature=0 — may vary stylistically but cannot contradict
    the arithmetic.
    """

    model_config = ConfigDict(extra="forbid")

    overall: int = Field(ge=0, le=100)
    per_section: dict[str, int] = Field(description="9-section map: section → 0-100 score")
    signal_breakdown: list[SectionScoreBreakdown]
    band: ScoreBand = Field(description="Derived from `overall` — red ≤40 / yellow ≤70 / green >70")
    rationale: str = Field(default="", description="≤120-word Opus-written paragraph; empty until rationale call runs")


def compute_health_score(parent_findings: list[ParentFinding]) -> HealthScore:
    """Deterministic arithmetic per plan 002 (R8 R-#7, line 679).

    Formula per section: `max(10, 100 - 20×crit - 10×mod - 5×minor)`
    where crit/mod/minor are severity==3/==2/==1 counts in that section.
    `overall` uses the same formula with counts summed across all sections.
    """
    overall_crit = sum(1 for f in parent_findings if f.severity == 3)
    overall_mod = sum(1 for f in parent_findings if f.severity == 2)
    overall_minor = sum(1 for f in parent_findings if f.severity == 1)
    overall = max(10, 100 - 20 * overall_crit - 10 * overall_mod - 5 * overall_minor)

    per_section: dict[str, int] = {}
    breakdowns: list[SectionScoreBreakdown] = []
    for section in ALL_REPORT_SECTIONS:
        in_section = [f for f in parent_findings if f.report_section == section]
        crit = sum(1 for f in in_section if f.severity == 3)
        mod = sum(1 for f in in_section if f.severity == 2)
        minor = sum(1 for f in in_section if f.severity == 1)
        sub = max(10, 100 - 20 * crit - 10 * mod - 5 * minor)
        per_section[section] = sub
        breakdowns.append(SectionScoreBreakdown(
            section=section,  # type: ignore[arg-type]
            findings_counted=len(in_section),
            arithmetic=f"100 - 20×{crit} - 10×{mod} - 5×{minor} = {sub}" if crit or mod or minor else "baseline (no findings) = 100",
        ))

    if overall <= 40:
        band: ScoreBand = "red"
    elif overall <= 70:
        band = "yellow"
    else:
        band = "green"

    return HealthScore(
        overall=overall,
        per_section=per_section,
        signal_breakdown=breakdowns,
        band=band,
        rationale="",
    )


# ── Judge schemas (v2 — shape locked in v1 for forward compat) ────────────
class SubSignalJudgment(BaseModel):
    """Judge-1: per-SubSignal validator. Not invoked in v1 — shape only."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    subsignal_id: str
    has_evidence_urls: bool
    severity_calibrated: bool = Field(description="0-3 matches severity_anchors for this lens_id")
    observation_specific: bool = Field(description="Not a generic platitude")
    passes: bool = Field(description="All three checks above")
    reason_if_fails: str | None = None


class ParentFindingJudgment(BaseModel):
    """Judge-2: per-ParentFinding strategic-story judge. Not invoked in v1."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    parent_finding_id: str
    tells_strategic_story: bool = Field(description="Not just a list of sub-issues")
    is_actionable: bool = Field(description="JR could scope work from it")
    does_not_repeat_other_sections: bool
    severity_rollup_correct: bool = Field(description="Actually max(children)")
    passes: bool
