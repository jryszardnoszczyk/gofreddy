"""L5 resume-by-session-id: idempotent stages skip when already complete.

Each stage at its top checks ``is_stage_complete(state, key) and outputs
exist`` → reconstructs Result from disk and returns without re-firing
the runner. Verifies that calling a stage twice fires runner.run() once.
"""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from src.audit import stages
from src.audit.state import AuditState, AuditStateFile


def _seed(audit_dir: Path) -> AuditStateFile:
    audit_dir.mkdir(parents=True, exist_ok=True)
    sf = AuditStateFile(path=audit_dir / "state.json")
    sf.save(AuditState(
        audit_id="aud_resume01",
        client_slug="acme",
        prospect_domain="acme.example",
    ))
    return sf


def _runner_result(text: str = "", cost: float = 1.0) -> Any:
    return type("R", (), {
        "text": text, "cost_usd": cost, "session_id": "sess-resume",
        "duration_ms": 100, "backend": "claude", "model": "opus",
        "role": "smoke", "transcript_path": None, "raw_envelope": None,
        "attempts": 1,
    })()


# ─── completed_stages helpers ────────────────────────────────────────


def test_mark_stage_complete_appends_once(tmp_path: Path):
    sf = _seed(tmp_path)
    stages.mark_stage_complete(sf, "stage_0_intake", session_id="s1", cost_usd=0.5)
    assert sf.load().completed_stages == ("stage_0_intake",)
    # Second call is idempotent — no duplicate
    stages.mark_stage_complete(sf, "stage_0_intake", session_id="s1", cost_usd=0.5)
    assert sf.load().completed_stages == ("stage_0_intake",)


def test_mark_stage_complete_records_session_id(tmp_path: Path):
    sf = _seed(tmp_path)
    stages.mark_stage_complete(sf, "stage_1b_predischarge", session_id="abc-123", cost_usd=2.5)
    s = sf.load()
    assert s.sessions["stage_1b_predischarge"]["session_id"] == "abc-123"
    assert s.sessions["stage_1b_predischarge"]["cost_usd"] == 2.5
    assert "completed_at" in s.sessions["stage_1b_predischarge"]


def test_is_stage_complete_returns_true_after_mark(tmp_path: Path):
    sf = _seed(tmp_path)
    assert not stages.is_stage_complete(sf, "stage_0_intake")
    stages.mark_stage_complete(sf, "stage_0_intake")
    assert stages.is_stage_complete(sf, "stage_0_intake")


# ─── Stage 0 idempotency ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_stage_0_skips_when_complete_and_intake_exists(tmp_path: Path):
    sf = _seed(tmp_path)
    ctx = stages.StageContext(
        audit_dir=tmp_path, state_file=sf, intake_data={"vertical": "saas"},
    )
    await stages.stage_0_intake(ctx)
    intake_path = tmp_path / "intake" / "form.json"
    assert intake_path.exists()
    intake_path.write_text(json.dumps({"sentinel": True}))  # mutate to detect overwrite

    # Second call: stage is complete + form.json exists → no overwrite
    await stages.stage_0_intake(ctx)
    data = json.loads(intake_path.read_text())
    assert data == {"sentinel": True}, "stage_0 must not overwrite on resume"


@pytest.mark.asyncio
async def test_stage_0_reruns_if_intake_file_missing(tmp_path: Path):
    """If completed_stages says done but the file is gone, re-run."""
    sf = _seed(tmp_path)
    stages.mark_stage_complete(sf, stages.STAGE_KEY_INTAKE)
    ctx = stages.StageContext(
        audit_dir=tmp_path, state_file=sf, intake_data={"vertical": "saas"},
    )
    await stages.stage_0_intake(ctx)
    assert (tmp_path / "intake" / "form.json").exists()


# ─── Stage 1b idempotency ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_stage_1b_skips_runner_when_complete(tmp_path: Path, monkeypatch):
    sf = _seed(tmp_path)
    runner = AsyncMock()
    runner.run.return_value = _runner_result(cost=2.0)
    ctx = stages.StageContext(audit_dir=tmp_path, state_file=sf, runner=runner)
    monkeypatch.setattr(stages, "_load_prompt", lambda name: "PROMPT")

    await stages.stage_1b_predischarge(ctx)
    assert runner.run.await_count == 1

    # Second call: skip
    await stages.stage_1b_predischarge(ctx)
    assert runner.run.await_count == 1, "runner.run must not fire on resume"


# ─── Stage 1c idempotency ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_stage_1c_skips_runner_when_complete(tmp_path: Path, monkeypatch):
    sf = _seed(tmp_path)
    runner = AsyncMock()
    runner.run.return_value = _runner_result(cost=0.85)
    ctx = stages.StageContext(audit_dir=tmp_path, state_file=sf, runner=runner)
    monkeypatch.setattr(stages, "_load_prompt", lambda name: "PROMPT")

    # 1c reads from prediscovery/, seed minimum
    (tmp_path / "prediscovery").mkdir(parents=True, exist_ok=True)
    (tmp_path / "prediscovery" / "signals.md").write_text("x")
    (tmp_path / "prediscovery" / "gaps.jsonl").write_text("")
    (tmp_path / "prediscovery" / "bundles_active.json").write_text("{}")

    await stages.stage_1c_brief_synthesis(ctx)
    assert runner.run.await_count == 1
    await stages.stage_1c_brief_synthesis(ctx)
    assert runner.run.await_count == 1


# ─── Stage 2 per-agent idempotency ───────────────────────────────────


@pytest.mark.asyncio
async def test_stage_2_skips_completed_agents(tmp_path: Path, monkeypatch):
    sf = _seed(tmp_path)
    runner = AsyncMock()
    runner.run.return_value = _runner_result(cost=12.0)
    ctx = stages.StageContext(audit_dir=tmp_path, state_file=sf, runner=runner)
    monkeypatch.setattr(stages, "_load_prompt", lambda name: "PROMPT")

    (tmp_path / "prediscovery").mkdir(parents=True, exist_ok=True)
    (tmp_path / "prediscovery" / "brief.md").write_text("# Brief")
    (tmp_path / "prediscovery" / "agent_reading_guides.json").write_text(
        json.dumps({a: "" for a in stages.STAGE_2_AGENTS})
    )

    await stages.stage_2_agents(ctx)
    assert runner.run.await_count == 4
    # Resume: each agent's stage_key is complete → 0 new calls
    await stages.stage_2_agents(ctx)
    assert runner.run.await_count == 4


# ─── Stage 3 idempotency ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_stage_3_skips_runner_when_complete(tmp_path: Path, monkeypatch):
    """Stage 3 fires 2 Opus calls (cross-cutting + narrative). On
    resume: 0 calls when synthesis dir + completed_stages set."""
    sf = _seed(tmp_path)
    runner = AsyncMock()
    runner.run.return_value = _runner_result(cost=5.0)
    ctx = stages.StageContext(audit_dir=tmp_path, state_file=sf, runner=runner)

    # Pre-seed prediscovery so the cross_cutting prompt has phase0_meta
    (tmp_path / "prediscovery").mkdir(parents=True, exist_ok=True)
    (tmp_path / "prediscovery" / "phase0_meta.json").write_text("{}")

    # Stage 3 takes a Stage2Result — empty fan-out is fine
    empty_stage2 = stages.Stage2Result(agents=[], failures=[])

    await stages.stage_3_synthesis(ctx, empty_stage2)
    first_pass = runner.run.await_count
    assert first_pass == 2  # cross-cutting + narrative

    # Resume — runner should NOT fire
    await stages.stage_3_synthesis(ctx, empty_stage2)
    assert runner.run.await_count == first_pass, "stage_3 must not re-fire on resume"


# ─── Stage 4 idempotency ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_stage_4_skips_runner_when_complete(tmp_path: Path, monkeypatch):
    sf = _seed(tmp_path)
    runner = AsyncMock()
    runner.run.return_value = _runner_result(cost=3.0)
    ctx = stages.StageContext(audit_dir=tmp_path, state_file=sf, runner=runner)
    monkeypatch.setattr(stages, "_load_prompt", lambda name: "PROMPT")

    # Synthesis result requires report.json on disk
    synth_dir = tmp_path / "synthesis"
    synth_dir.mkdir(parents=True, exist_ok=True)
    report_json = synth_dir / "report.json"
    report_json.write_text(json.dumps({"audit_id": "aud_resume01"}))
    synthesis = stages.SynthesisResult(
        findings_md_path=synth_dir / "findings.md",
        report_md_path=synth_dir / "report.md",
        report_json_path=report_json,
        surprises_md_path=synth_dir / "surprises.md",
        gap_report_md_path=synth_dir / "gap_report.md",
        health_score=stages.compute_health_score([]),
        parent_findings=[],
    )

    await stages.stage_4_proposal(ctx, synthesis)
    assert runner.run.await_count == 1
    await stages.stage_4_proposal(ctx, synthesis)
    assert runner.run.await_count == 1


# ─── Stage 5 idempotency ─────────────────────────────────────────────


def _seed_synthesis_proposal(audit_dir: Path) -> tuple[Any, Any]:
    """Minimal disk shape for stage_5 to render."""
    synth_dir = audit_dir / "synthesis"
    synth_dir.mkdir(parents=True, exist_ok=True)
    report_json_path = synth_dir / "report.json"
    report_json_path.write_text(json.dumps({
        "audit_id": "aud_resume01",
        "prospect_domain": "acme.example",
        "health_score": {"overall": 100, "band": "green", "per_section": {}},
        "parent_findings": [], "sources": [],
    }))
    proposal_dir = audit_dir / "proposal"
    proposal_dir.mkdir(parents=True, exist_ok=True)
    proposal_json_path = proposal_dir / "proposal.json"
    proposal_json_path.write_text(json.dumps({"narrative_anchor": "test", "entries": []}))
    (audit_dir / "prediscovery").mkdir(parents=True, exist_ok=True)
    (audit_dir / "prediscovery" / "phase0_meta.json").write_text("{}")
    synthesis = stages.SynthesisResult(
        findings_md_path=synth_dir / "findings.md",
        report_md_path=synth_dir / "report.md",
        report_json_path=report_json_path,
        surprises_md_path=synth_dir / "surprises.md",
        gap_report_md_path=synth_dir / "gap_report.md",
        health_score=stages.compute_health_score([]),
        parent_findings=[],
    )
    proposal = stages.ProposalResult(
        proposal_md_path=proposal_dir / "proposal.md",
        proposal_json_path=proposal_json_path,
    )
    return synthesis, proposal


@pytest.mark.asyncio
async def test_stage_5_idempotent_resume_returns_same_slug(tmp_path: Path):
    sf = _seed(tmp_path)
    ctx = stages.StageContext(audit_dir=tmp_path, state_file=sf)
    synthesis, proposal = _seed_synthesis_proposal(tmp_path)

    r1 = await stages.stage_5_deliverable(ctx, synthesis, proposal)
    r2 = await stages.stage_5_deliverable(ctx, synthesis, proposal)
    # Resume must return the SAME slug (recovered from sessions[stage_5_deliverable])
    assert r1.slug == r2.slug


# ─── End-to-end resume ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_full_pipeline_resume_no_double_calls(tmp_path: Path, monkeypatch):
    """Two full passes through stages 0→1c — runner must fire 3 times
    (1b + 1c — Stage 0 has no runner; warmup has no runner) on first
    pass and 0 times on resume."""
    audit_dir = tmp_path / "audit"
    sf = _seed(audit_dir)
    runner = AsyncMock()
    runner.run.return_value = _runner_result(cost=1.0)
    ctx = stages.StageContext(
        audit_dir=audit_dir, state_file=sf, runner=runner,
        intake_data={"vertical": "saas"},
    )
    monkeypatch.setattr(stages, "_load_prompt", lambda name: "PROMPT")

    from src.audit.preflight.runner import PreflightResult
    stub = PreflightResult(domain="x", started_at=0.0, elapsed_s=0.0, signals={}, failures={})
    with patch("src.audit.stages.preflight_runner.run", AsyncMock(return_value=stub)):
        # Pass 1
        await stages.stage_0_intake(ctx)
        await stages.stage_1_warmup(ctx)
        await stages.stage_1b_predischarge(ctx)
        await stages.stage_1c_brief_synthesis(ctx)
        first_pass = runner.run.await_count
        assert first_pass == 2  # 1b + 1c

        # Pass 2 (resume) — runner should NOT fire again
        await stages.stage_0_intake(ctx)
        await stages.stage_1_warmup(ctx)
        await stages.stage_1b_predischarge(ctx)
        await stages.stage_1c_brief_synthesis(ctx)
        assert runner.run.await_count == first_pass, "resume must not re-fire runner"
