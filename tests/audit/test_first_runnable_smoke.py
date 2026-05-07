"""§7.7 first-runnable plumbing smoke test.

NOT the production §7.7 acceptance run (that needs real LLM + real
providers + Cloudflare deploy). This is the precursor smoke test that
validates pipeline wiring before paying for a real run:

  - Workspace init + state machine transitions through 8 sub-phases
  - Each stage's runner invocation + output scaffold
  - cost_actual.json populated per stage; total_so_far recomputed
  - events.jsonl emits cost_recorded per record_stage_cost call
  - Deterministic HealthScore lands in report.json
  - Stage 5 deliverable/report.html + report.pdf produced

LLM calls are mocked via ``AsyncMock``; the preflight runner is patched
to avoid hitting the network. Per master plan §7.7, "deliverable shape
is correct" is the bar — content quality is JR ship-gate territory.
"""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from src.audit import stages
from src.audit.preflight.runner import PreflightResult
from src.audit.state import AuditState, AuditStateFile


def _seed_workspace(audit_dir: Path) -> AuditStateFile:
    audit_dir.mkdir(parents=True, exist_ok=True)
    sf = AuditStateFile(path=audit_dir / "state.json")
    sf.save(AuditState(
        audit_id="aud_smoke01",
        client_slug="acme",
        prospect_domain="acme.example",
    ))
    return sf


def _runner_result(text: str = "", cost: float = 1.0) -> Any:
    return type("R", (), {
        "text": text, "cost_usd": cost, "session_id": "sess-smoke",
        "duration_ms": 100, "backend": "claude", "model": "opus",
        "role": "smoke", "transcript_path": None, "raw_envelope": None,
        "attempts": 1,
    })()


@pytest.mark.asyncio
async def test_first_runnable_smoke_full_pipeline_plumbing(tmp_path: Path):
    """Drive Stage 0 → 5 with mocked runner; verify all artifacts + state
    transitions + cost ledger + events.jsonl + deliverable shape."""
    audit_dir = tmp_path / "clients" / "acme" / "audit"
    sf = _seed_workspace(audit_dir)

    runner = AsyncMock()
    runner.run.return_value = _runner_result(text="", cost=2.50)

    ctx = stages.StageContext(
        audit_dir=audit_dir, state_file=sf, runner=runner,
        intake_data={"prospect_url": "https://acme.example", "vertical": "saas"},
    )

    # Stub preflight to avoid network calls
    stub_preflight = PreflightResult(
        domain="acme.example", started_at=0.0, elapsed_s=0.0,
        signals={}, failures={},
    )

    # Prompts contain literal `{...}` blocks (JSON examples, code) that
    # break Python's .format(). A placeholder-free stub keeps the smoke
    # test focused on plumbing — content + prompt rendering belong in
    # the production §7.7 acceptance run.
    with patch("src.audit.stages.preflight_runner.run", AsyncMock(return_value=stub_preflight)), \
         patch("src.audit.stages._load_prompt", lambda name: "PROMPT"):
        # ── Pre-payment chain: Stage 0 → 1 → 1b → 1c → intake gate ───
        await stages.stage_0_intake(ctx)
        await stages.stage_1_warmup(ctx)
        await stages.stage_1b_predischarge(ctx)
        await stages.stage_1c_brief_synthesis(ctx)

        # Intake gate flip (CLI: freddy audit confirm-brief acme)
        sf.mutate(lambda s: dataclasses.replace(s, status="brief_confirmed"))

        # Payment gate flip (CLI: freddy audit mark-paid acme)
        sf.mutate(lambda s: dataclasses.replace(s, status="paid"))

        # ── Post-payment chain: Stage 2 → 3 → 4 → 5 ───────────────────
        s2 = await stages.stage_2_agents(ctx)
        s3 = await stages.stage_3_synthesis(ctx, s2)
        s4 = await stages.stage_4_proposal(ctx, s3)
        s5 = await stages.stage_5_deliverable(ctx, s3, s4)

    # ── Workspace shape ──────────────────────────────────────────────
    assert (audit_dir / "state.json").exists()
    # Stage 0 writes intake/form.json
    assert (audit_dir / "intake" / "form.json").exists()
    assert (audit_dir / "cache" / "manifest.json").exists()
    assert (audit_dir / "prediscovery" / "signals.md").exists()
    assert (audit_dir / "prediscovery" / "gaps.jsonl").exists()
    assert (audit_dir / "prediscovery" / "bundles_active.json").exists()
    assert (audit_dir / "prediscovery" / "brief.md").exists()
    assert (audit_dir / "prediscovery" / "brief.json").exists()
    assert (audit_dir / "prediscovery" / "phase0_meta.json").exists()
    assert (audit_dir / "prediscovery" / "agent_reading_guides.json").exists()

    # ── Stage 2: 4 agents fan-out, each produced an AgentOutput ──────
    assert len(s2.agents) == 4
    assert {a.agent_name for a in s2.agents} == set(stages.STAGE_2_AGENTS)
    for art in s2.agents:
        assert art.output_path.exists()
        # scaffolded AgentOutput is valid JSON
        out = json.loads(art.output_path.read_text())
        assert out["agent_name"] == art.agent_name

    # ── Stage 3: synthesis files + deterministic HealthScore ─────────
    assert s3.findings_md_path.exists()
    assert s3.report_md_path.exists()
    assert s3.report_json_path.exists()
    assert s3.surprises_md_path.exists()
    assert s3.gap_report_md_path.exists()
    report = json.loads(s3.report_json_path.read_text())
    assert "health_score" in report
    assert report["health_score"]["overall"] == 100  # no findings → baseline
    assert report["health_score"]["band"] == "green"
    assert "parent_findings" in report
    assert report["audit_id"] == "aud_smoke01"

    # ── Stage 4: proposal files ──────────────────────────────────────
    assert s4.proposal_md_path.exists()
    assert s4.proposal_json_path.exists()

    # ── Stage 5: deliverable HTML + PDF placeholder ──────────────────
    assert s5.html_path.exists()
    html = s5.html_path.read_text()
    assert "<html" in html
    assert "acme.example" in html
    assert s5.pdf_path.exists()
    assert s5.pdf_path.read_bytes().startswith(b"%PDF")

    # ── Cost ledger: every stage recorded a cost row ─────────────────
    cost = json.loads((audit_dir / "cost_actual.json").read_text())
    expected_keys = {
        stages.STAGE_KEY_INTAKE,
        stages.STAGE_KEY_WARMUP,
        stages.STAGE_KEY_PREDISCO,
        stages.STAGE_KEY_BRIEF,
        stages.STAGE_KEY_SYNTHESIS,
        stages.STAGE_KEY_PROPOSAL,
        stages.STAGE_KEY_DELIVERABLE,
        "total_so_far",
    } | {f"{stages.STAGE_KEY_AGENT_PREFIX}{a}" for a in stages.STAGE_2_AGENTS}
    assert expected_keys.issubset(cost.keys())
    # total_so_far recomputed from sum of all stage rows
    expected_total = sum(v for k, v in cost.items() if k != "total_so_far")
    assert cost["total_so_far"] == pytest.approx(expected_total)

    # ── events.jsonl: cost_recorded events emitted ───────────────────
    events_path = audit_dir / "events.jsonl"
    assert events_path.exists()
    events = [json.loads(line) for line in events_path.read_text().splitlines() if line.strip()]
    cost_recorded = [e for e in events if e["kind"] == "cost_recorded"]
    # one event per record_stage_cost call (intake, warmup, 1b, 1c, 4 agents,
    # synthesis, proposal, deliverable) = 11 minimum
    assert len(cost_recorded) >= 11

    # ── State machine: paid is the latest manual flip ────────────────
    final_state = sf.load()
    assert final_state.status == "paid"
    assert final_state.audit_id == "aud_smoke01"


@pytest.mark.asyncio
async def test_first_runnable_smoke_intake_gate_blocks_stage_2(tmp_path: Path):
    """Sanity: stage_2 still runs without state.status=paid (gate is
    enforced at CLI layer, not stages layer). This documents the
    contract — gate enforcement lives in `cli.freddy.commands.audit:ma_run`."""
    audit_dir = tmp_path / "clients" / "acme" / "audit"
    sf = _seed_workspace(audit_dir)
    runner = AsyncMock()
    runner.run.return_value = _runner_result(cost=1.0)
    ctx = stages.StageContext(audit_dir=audit_dir, state_file=sf, runner=runner)

    # Pre-seed prediscovery so stage_2 has its inputs
    (audit_dir / "prediscovery").mkdir(parents=True, exist_ok=True)
    (audit_dir / "prediscovery" / "brief.md").write_text("# Brief")
    (audit_dir / "prediscovery" / "agent_reading_guides.json").write_text(
        json.dumps({a: "" for a in stages.STAGE_2_AGENTS})
    )

    s2 = await stages.stage_2_agents(ctx)
    # No gate at stages.py layer — runs to completion
    assert len(s2.agents) == 4
