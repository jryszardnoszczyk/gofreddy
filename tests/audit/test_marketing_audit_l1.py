"""Layer L1 (Foundation) tests for marketing_audit lane wiring.

Master plan 2026-05-06-001 §7.2 work item 11.

Coverage:
1. Schema additions — Pydantic validates ``phase0_frame`` on SubSignal
   and ``parent_findings`` on AgentOutput.
2. Lane registration — LaneSpec is registered + serializes against
   ``lane_registry.compute_manifest`` cleanly.
3. Preflight runner wiring — ``stages.stage_1_warmup`` invokes the
   preflight runner without RuntimeError.
4. Structural validator — ``_validate_marketing_audit`` accepts
   well-shaped findings/proposal docs and rejects missing/wrong-order
   ones.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest


# ─── Schema additions (master plan §2.5) ─────────────────────────────────


def test_subsignal_phase0_frame_optional() -> None:
    """phase0_frame is None by default (tactical lens) and accepts 1..9."""
    from src.audit.agent_models import SubSignal

    s = SubSignal(
        id="s1",
        lens_id="L-A-01",
        agent="findability",
        report_section="seo",
        observation="o",
        evidence_urls=["https://example.com/"],
        severity=1,
        confidence="H",
    )
    assert s.phase0_frame is None

    s_phase0 = SubSignal(
        id="s2",
        lens_id="L-PHASE0-1",
        agent="findability",
        report_section="seo",
        observation="o",
        evidence_urls=["https://example.com/"],
        severity=1,
        confidence="H",
        phase0_frame=3,
    )
    assert s_phase0.phase0_frame == 3


def test_subsignal_phase0_frame_rejects_out_of_range() -> None:
    """Literal[1..9] rejects 0 and 10."""
    from pydantic import ValidationError

    from src.audit.agent_models import SubSignal

    base_kwargs = dict(
        id="s1",
        lens_id="L1",
        agent="findability",
        report_section="seo",
        observation="o",
        evidence_urls=["https://example.com/"],
        severity=1,
        confidence="H",
    )
    with pytest.raises(ValidationError):
        SubSignal(**base_kwargs, phase0_frame=0)
    with pytest.raises(ValidationError):
        SubSignal(**base_kwargs, phase0_frame=10)


def test_agent_output_parent_findings_default_empty() -> None:
    """AgentOutput.parent_findings is an empty list by default."""
    from src.audit.agent_models import AgentMetadata, AgentOutput

    out = AgentOutput(
        agent_name="findability",
        rubric_coverage={"L-A-01": "covered"},
        metadata=AgentMetadata(
            session_id="sid",
            total_cost_usd=0.1,
            duration_ms=1000,
            num_turns=1,
        ),
    )
    assert out.parent_findings == []


def test_agent_output_parent_findings_round_trip() -> None:
    """ParentFinding round-trips through AgentOutput.parent_findings."""
    from src.audit.agent_models import (
        AgentMetadata,
        AgentOutput,
        ParentFinding,
        SubSignal,
    )

    sub = SubSignal(
        id="s1",
        lens_id="L1",
        agent="findability",
        report_section="seo",
        observation="o",
        evidence_urls=["https://example.com/"],
        severity=2,
        confidence="H",
    )
    pf = ParentFinding(
        id="pf1",
        report_section="seo",
        headline="Headline",
        evidence_summary="Summary",
        recommendation="Strategic recommendation here",
        sub_signals=[sub],
        severity=2,
        confidence="H",
    )
    out = AgentOutput(
        agent_name="findability",
        sub_signals=[sub],
        parent_findings=[pf],
        rubric_coverage={"L1": "covered"},
        metadata=AgentMetadata(
            session_id="sid",
            total_cost_usd=0.1,
            duration_ms=1000,
            num_turns=1,
        ),
    )
    assert len(out.parent_findings) == 1
    assert out.parent_findings[0].id == "pf1"


# ─── Lane registration (master plan §3.1) ────────────────────────────────


def test_marketing_audit_lane_registered() -> None:
    """marketing_audit appears in LANES + workflow_lane_names."""
    from autoresearch.lane_registry import LANES, workflow_lane_names

    assert "marketing_audit" in LANES
    spec = LANES["marketing_audit"]
    assert spec.is_workflow_lane is True
    assert spec.rubric_ids == (
        "MA-1", "MA-2", "MA-3", "MA-4", "MA-5", "MA-6", "MA-7", "MA-8",
    )
    assert spec.session_md_filename == "marketing_audit-session.md"
    assert "marketing_audit" in workflow_lane_names()


def test_marketing_audit_lanespec_callables_wired() -> None:
    """custom_score + custom_validate are wired; custom_promote stays None."""
    from autoresearch.lane_registry import LANES

    spec = LANES["marketing_audit"]
    assert spec.custom_score is not None
    assert spec.custom_validate is not None
    assert spec.custom_promote is None
    assert spec.custom_objective_score_from_entry is None


def test_marketing_audit_score_stub_returns_dict() -> None:
    """L1 stub: score returns sane defaults so the lane registers."""
    from src.audit.score import marketing_audit_score

    result = marketing_audit_score(None, None)
    assert isinstance(result, dict)
    assert result["score"] == 0.0
    assert result["rubric_breakdown"] == {}
    assert result["stub"] is True


def test_marketing_audit_validate_stub_returns_pass_tuple() -> None:
    """L1 stub: validate returns (True, []) so variants pass through."""
    from src.audit.validate import marketing_audit_validate

    passed, failures = marketing_audit_validate(None)
    assert passed is True
    assert failures == []


def test_compute_manifest_serializes_marketing_audit_files(tmp_path: Path) -> None:
    """LaneSpec validates against lane_registry.compute_manifest — i.e.
    paths produced by the manifest are hash-stable bytes-equal across
    runs. This is the contract custom_validate depends on at runtime."""
    from autoresearch.lane_registry import compute_manifest

    # Synthesize a fake prompt file at the lane-owned path.
    fake_root = tmp_path
    fake_prompt = fake_root / "programs" / "marketing_audit" / "prompts" / "stage_1b.md"
    fake_prompt.parent.mkdir(parents=True)
    fake_prompt.write_text("# stage 1b pre-discovery\n", encoding="utf-8")

    manifest = compute_manifest([fake_prompt], fake_root)
    assert "programs/marketing_audit/prompts/stage_1b.md" in manifest
    # Re-running over the same bytes returns the same hash.
    manifest2 = compute_manifest([fake_prompt], fake_root)
    assert manifest == manifest2


def test_evaluate_request_domain_literal_includes_marketing_audit() -> None:
    """src/evaluation/models.py:EvaluateRequest.domain Literal must include
    marketing_audit so _assert_models_literal_matches() in lane_registry
    passes — failure here means the Literal drifted from LANES."""
    from autoresearch.lane_registry import _assert_models_literal_matches

    # Should not raise.
    _assert_models_literal_matches()


# ─── Preflight runner wiring (master plan §4.8) ──────────────────────────


def test_stage_1_warmup_invokes_preflight_runner(tmp_path: Path, monkeypatch) -> None:
    """stage_1_warmup is callable + invokes the preflight runner against
    state.prospect_domain. We don't network-fetch here; we monkeypatch
    the runner to verify it gets called with the expected domain."""
    from src.audit import stages
    from src.audit.preflight.runner import PreflightResult
    from src.audit.state import AuditState, AuditStateFile

    audit_dir = tmp_path / "clients" / "test" / "audit" / "a-0001"
    audit_dir.mkdir(parents=True)
    sf = AuditStateFile(audit_dir / "state.json")
    sf.save(AuditState(
        audit_id="a-0001",
        client_slug="test",
        prospect_domain="example.com",
    ))

    captured: dict = {}

    async def fake_run(domain, *, config=None):
        captured["domain"] = domain
        captured["config"] = config
        return PreflightResult(domain=domain, started_at=0.0, elapsed_s=0.1)

    monkeypatch.setattr("src.audit.stages.preflight_runner.run", fake_run)

    result = asyncio.run(stages.stage_1_warmup(sf))

    assert captured["domain"] == "example.com"
    assert isinstance(result, PreflightResult)
    assert result.domain == "example.com"


# ─── Structural validator (master plan §3.6) ─────────────────────────────


def _build_findings_with_all_sections() -> str:
    from src.evaluation.structural import NINE_SECTIONS_MARKETING_AUDIT
    return "\n".join(f"## {s.title()}" for s in NINE_SECTIONS_MARKETING_AUDIT)


def test_validate_marketing_audit_happy_path() -> None:
    from src.evaluation.structural import _validate_marketing_audit

    res = _validate_marketing_audit({"findings.md": _build_findings_with_all_sections()})
    assert res.passed is True
    assert res.failures == []


def test_validate_marketing_audit_missing_findings() -> None:
    from src.evaluation.structural import _validate_marketing_audit

    res = _validate_marketing_audit({})
    assert res.passed is False
    assert any("findings.md" in f for f in res.failures)


def test_validate_marketing_audit_missing_sections() -> None:
    from src.evaluation.structural import _validate_marketing_audit

    res = _validate_marketing_audit({"findings.md": "## Seo\n## Geo"})
    assert res.passed is False
    assert any("missing required sections" in f for f in res.failures)


def test_validate_marketing_audit_proposal_three_tiers_in_order() -> None:
    from src.evaluation.structural import _validate_marketing_audit

    findings = _build_findings_with_all_sections()
    res = _validate_marketing_audit({
        "findings.md": findings,
        "proposal.md": "# fix_it\n# build_it\n# run_it",
    })
    assert res.passed is True


def test_validate_marketing_audit_proposal_wrong_order_fails() -> None:
    from src.evaluation.structural import _validate_marketing_audit

    findings = _build_findings_with_all_sections()
    res = _validate_marketing_audit({
        "findings.md": findings,
        "proposal.md": "# build_it\n# fix_it\n# run_it",
    })
    assert res.passed is False
    assert any("fixed order" in f for f in res.failures)


def test_validate_marketing_audit_proposal_missing_tier_fails() -> None:
    from src.evaluation.structural import _validate_marketing_audit

    findings = _build_findings_with_all_sections()
    res = _validate_marketing_audit({
        "findings.md": findings,
        "proposal.md": "# fix_it\n# build_it",  # run_it missing
    })
    assert res.passed is False
    assert any("run_it" in f for f in res.failures)


def test_structural_gate_dispatches_marketing_audit() -> None:
    from src.evaluation.structural import structural_gate

    findings = _build_findings_with_all_sections()
    res = asyncio.run(structural_gate("marketing_audit", {"findings.md": findings}))
    assert res.passed is True


# ─── Operator script (master plan §6.6) ──────────────────────────────────


def test_regen_marketing_audit_manifest_empty_writes_empty_dict(tmp_path: Path) -> None:
    """When no prompt files exist, the operator script writes an empty
    manifest (signals 'authoring not yet done')."""
    from autoresearch.scripts import regen_marketing_audit_manifest

    out = tmp_path / "marketing_audit_manifest.json"
    count = regen_marketing_audit_manifest.regen(tmp_path, out)
    assert count == 0
    assert out.exists()
    assert json.loads(out.read_text()) == {}


def test_regen_marketing_audit_manifest_freezes_present_files(tmp_path: Path) -> None:
    """When prompt files exist, the script hashes them all into the manifest."""
    from autoresearch.scripts import regen_marketing_audit_manifest

    rubric = tmp_path / "programs" / "marketing_audit" / "prompts" / "rubrics" / "MA-1.md"
    rubric.parent.mkdir(parents=True)
    rubric.write_text("# MA-1\n", encoding="utf-8")

    judge = tmp_path / "programs" / "marketing_audit" / "prompts" / "judges" / "MA-1-judge.md"
    judge.parent.mkdir(parents=True)
    judge.write_text("# MA-1 judge\n", encoding="utf-8")

    stage = tmp_path / "programs" / "marketing_audit" / "prompts" / "stage_1b.md"
    stage.write_text("# stage 1b\n", encoding="utf-8")

    out = tmp_path / "marketing_audit_manifest.json"
    count = regen_marketing_audit_manifest.regen(tmp_path, out)
    assert count == 3
    manifest = json.loads(out.read_text())
    assert "programs/marketing_audit/prompts/rubrics/MA-1.md" in manifest
    assert "programs/marketing_audit/prompts/judges/MA-1-judge.md" in manifest
    assert "programs/marketing_audit/prompts/stage_1b.md" in manifest
    # Hashes are SHA256 hex strings (64 chars).
    for h in manifest.values():
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)
