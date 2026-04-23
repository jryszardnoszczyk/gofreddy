"""Lock the v1 audit schema shape.

Tests cover the Pydantic floors the plan requires (evidence_urls min_length,
HttpUrl scheme rejection, enum enforcement) + the rollup invariants on
ParentFinding (severity = max of children, confidence = floor of children)
+ the deterministic health-score arithmetic. Thin coverage by design — this
is schema, not business logic.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.audit.agent_models import (
    ALL_REPORT_SECTIONS,
    AgentMetadata,
    AgentOutput,
    ParentFinding,
    SubSignal,
    compute_health_score,
)


# ── Fixtures ──────────────────────────────────────────────────────────────
def make_subsignal(
    *,
    id: str = "s1",
    lens_id: str = "tech_seo_health",
    agent: str = "findability",
    report_section: str = "seo",
    observation: str = "Homepage lacks HSTS header.",
    severity: int = 1,
    confidence: str = "M",
    evidence_urls: list[str] | None = None,
) -> SubSignal:
    return SubSignal(
        id=id,
        lens_id=lens_id,
        agent=agent,
        report_section=report_section,  # type: ignore[arg-type]
        observation=observation,
        evidence_urls=["https://example.com/"] if evidence_urls is None else evidence_urls,
        severity=severity,
        confidence=confidence,  # type: ignore[arg-type]
    )


def make_parent(sub_signals: list[SubSignal]) -> ParentFinding:
    return ParentFinding(
        id="p1",
        report_section=sub_signals[0].report_section,
        headline="Technical SEO hygiene is below market baseline",
        evidence_summary="Canonicalization, HSTS, and mixed-content posture all lag.",
        recommendation=(
            "Technical SEO engagement at Fix-it tier covering HSTS deployment, "
            "canonical-tag policy, and mixed-content remediation."
        ),
        sub_signals=sub_signals,
        # Deliberately wrong — validator should overwrite.
        severity=0,
        confidence="H",  # type: ignore[arg-type]
    )


# ── SubSignal validation floors ───────────────────────────────────────────
class TestSubSignalFloors:
    def test_empty_evidence_urls_rejected(self) -> None:
        with pytest.raises(ValidationError):
            make_subsignal(evidence_urls=[])

    def test_file_scheme_url_rejected(self) -> None:
        with pytest.raises(ValidationError):
            make_subsignal(evidence_urls=["file:///etc/passwd"])

    def test_invalid_report_section_rejected(self) -> None:
        with pytest.raises(ValidationError):
            make_subsignal(report_section="not_a_real_section")

    def test_severity_out_of_range_rejected(self) -> None:
        with pytest.raises(ValidationError):
            make_subsignal(severity=99)
        with pytest.raises(ValidationError):
            make_subsignal(severity=-1)

    def test_confidence_invalid_letter_rejected(self) -> None:
        with pytest.raises(ValidationError):
            make_subsignal(confidence="X")

    def test_empty_observation_rejected(self) -> None:
        with pytest.raises(ValidationError):
            make_subsignal(observation="")

    def test_all_nine_report_sections_accepted(self) -> None:
        for section in ALL_REPORT_SECTIONS:
            sig = make_subsignal(report_section=section)
            assert sig.report_section == section


# ── ParentFinding rollup invariants ───────────────────────────────────────
class TestParentRollup:
    def test_severity_rolls_up_to_max_of_children(self) -> None:
        children = [
            make_subsignal(id="a", severity=1),
            make_subsignal(id="b", severity=3),
            make_subsignal(id="c", severity=2),
        ]
        parent = make_parent(children)
        assert parent.severity == 3

    def test_confidence_rolls_up_to_floor_of_children(self) -> None:
        children = [
            make_subsignal(id="a", confidence="H"),
            make_subsignal(id="b", confidence="L"),  # floor
            make_subsignal(id="c", confidence="M"),
        ]
        parent = make_parent(children)
        assert parent.confidence == "L"

    def test_uniform_children_rollup_matches(self) -> None:
        children = [
            make_subsignal(id="a", severity=2, confidence="M"),
            make_subsignal(id="b", severity=2, confidence="M"),
        ]
        parent = make_parent(children)
        assert parent.severity == 2
        assert parent.confidence == "M"

    def test_empty_sub_signals_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ParentFinding(
                id="p1",
                report_section="seo",
                headline="x",
                evidence_summary="x",
                recommendation="x",
                sub_signals=[],
                severity=0,
                confidence="H",
            )


# ── HealthScore arithmetic ────────────────────────────────────────────────
class TestHealthScore:
    def test_empty_findings_scores_100_green(self) -> None:
        score = compute_health_score([])
        assert score.overall == 100
        assert score.band == "green"
        for section in ALL_REPORT_SECTIONS:
            assert score.per_section[section] == 100

    def test_one_critical_docks_20(self) -> None:
        parent = make_parent([make_subsignal(severity=3)])
        score = compute_health_score([parent])
        assert score.overall == 80
        assert score.band == "green"

    def test_band_red_at_40_yellow_at_70_green_above(self) -> None:
        # overall <= 40 → red
        five_crits = [make_parent([make_subsignal(id=f"s{i}", severity=3)]) for i in range(4)]
        for i, p in enumerate(five_crits):
            object.__setattr__(p, "id", f"p{i}")
        # 4 critical findings = 100 - 80 = 20 → red
        score = compute_health_score(five_crits)
        assert score.overall == 20
        assert score.band == "red"

    def test_overall_floors_at_10(self) -> None:
        many_crits = [
            make_parent([make_subsignal(id=f"s{i}", severity=3)])
            for i in range(20)
        ]
        for i, p in enumerate(many_crits):
            object.__setattr__(p, "id", f"p{i}")
        score = compute_health_score(many_crits)
        assert score.overall == 10  # formula would go negative; floor clamps to 10

    def test_per_section_isolated(self) -> None:
        seo_parent = make_parent([make_subsignal(severity=3, report_section="seo")])
        score = compute_health_score([seo_parent])
        assert score.per_section["seo"] == 80
        assert score.per_section["brand_narrative"] == 100  # untouched

    def test_signal_breakdown_has_all_nine_sections(self) -> None:
        score = compute_health_score([])
        seen = {b.section for b in score.signal_breakdown}
        assert seen == set(ALL_REPORT_SECTIONS)


# ── AgentOutput shape ─────────────────────────────────────────────────────
class TestAgentOutput:
    def test_minimal_output_valid(self) -> None:
        out = AgentOutput(
            agent_name="findability",
            rubric_coverage={"tech_seo_health": "covered"},
            metadata=AgentMetadata(
                session_id="sess-1",
                total_cost_usd=1.50,
                duration_ms=30_000,
                num_turns=8,
            ),
        )
        assert out.agent_name == "findability"
        assert out.sub_signals == []
        assert out.critique_iterations_used == 0

    def test_rubric_coverage_rejects_invalid_value(self) -> None:
        with pytest.raises(ValidationError):
            AgentOutput(
                agent_name="findability",
                rubric_coverage={"tech_seo_health": "maybe"},  # not covered/gap_flagged
                metadata=AgentMetadata(
                    session_id="s", total_cost_usd=0, duration_ms=0, num_turns=0,
                ),
            )

    def test_critique_iterations_bounded_zero_to_three(self) -> None:
        meta = AgentMetadata(session_id="s", total_cost_usd=0, duration_ms=0, num_turns=0)
        AgentOutput(agent_name="x", rubric_coverage={}, critique_iterations_used=0, metadata=meta)
        AgentOutput(agent_name="x", rubric_coverage={}, critique_iterations_used=3, metadata=meta)
        with pytest.raises(ValidationError):
            AgentOutput(agent_name="x", rubric_coverage={}, critique_iterations_used=4, metadata=meta)
