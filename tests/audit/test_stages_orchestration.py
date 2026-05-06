"""L3 stage orchestration smoke tests.

Mock-based: no real LLM calls. Verifies that each stage:
- Receives a duck-typed runner via ``StageContext``
- Writes its expected artifacts to disk
- Calls ``record_stage_cost`` with its STAGE_KEY

The 4-agent fan-out, schema validation seam, and Stage-5 render
fallbacks (no Jinja, no WeasyPrint) are exercised here. Real provider
fan-out + real LLM dispatch land in L4 first-runnable end-to-end test.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import pytest

from src.audit import stages
from src.audit.cost_observability import read_cost_actual
from src.audit.state import AuditState, AuditStateFile


def _seed_state(audit_dir: Path) -> AuditStateFile:
    audit_dir.mkdir(parents=True, exist_ok=True)
    state = AuditState(
        audit_id="aud_test01",
        client_slug="acme",
        prospect_domain="acme.example",
    )
    sf = AuditStateFile(path=audit_dir / "state.json")
    sf.save(state)
    return sf


def _make_runner_result(text: str = "{}", cost: float = 1.25) -> Any:
    return type("Result", (), {
        "text": text,
        "cost_usd": cost,
        "session_id": "sess-test",
        "duration_ms": 100,
        "backend": "claude",
        "model": "opus",
        "role": "test",
        "transcript_path": None,
        "raw_envelope": None,
        "attempts": 1,
    })()


# ─── Stage 0 ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_stage_0_intake_writes_form_and_records_zero_cost(tmp_path: Path) -> None:
    sf = _seed_state(tmp_path)
    ctx = stages.StageContext(
        audit_dir=tmp_path, state_file=sf,
        intake_data={"prospect_url": "https://acme.example", "vertical": "saas"},
    )

    result = await stages.stage_0_intake(ctx)

    assert result.intake_path.exists()
    form = json.loads(result.intake_path.read_text())
    assert form["vertical"] == "saas"
    cost = read_cost_actual(tmp_path)
    assert stages.STAGE_KEY_INTAKE in cost
    assert cost[stages.STAGE_KEY_INTAKE] == 0.0


# ─── Stage 1b ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_stage_1b_predischarge_invokes_runner_and_records_cost(tmp_path: Path, monkeypatch) -> None:
    sf = _seed_state(tmp_path)
    runner = AsyncMock()
    runner.run.return_value = _make_runner_result(
        text=json.dumps({"signals": [], "gaps": [], "bundles_activated": []}),
        cost=2.50,
    )
    ctx = stages.StageContext(audit_dir=tmp_path, state_file=sf, runner=runner)

    monkeypatch.setattr(stages, "_load_prompt", lambda name: "PROMPT {prospect_domain}")
    result = await stages.stage_1b_predischarge(ctx)

    assert runner.run.await_count == 1
    assert result.signals_path.exists()
    cost = read_cost_actual(tmp_path)
    assert cost[stages.STAGE_KEY_PREDISCO] == 2.50


# ─── Stage 1c ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_stage_1c_brief_synthesis_writes_brief_and_phase0(tmp_path: Path, monkeypatch) -> None:
    sf = _seed_state(tmp_path)
    runner = AsyncMock()
    runner.run.return_value = _make_runner_result(
        text=json.dumps({
            "brief_md": "# Brief\nProspect: acme.example\n",
            "phase0_meta": {"frame_5_traffic_mix": "degraded"},
            "reading_guides": {a: "guide" for a in stages.STAGE_2_AGENTS},
        }),
        cost=0.85,
    )
    ctx = stages.StageContext(audit_dir=tmp_path, state_file=sf, runner=runner)
    (tmp_path / "prediscovery").mkdir(parents=True, exist_ok=True)
    (tmp_path / "prediscovery" / "signals.json").write_text("[]")
    (tmp_path / "prediscovery" / "gaps.jsonl").write_text("")

    monkeypatch.setattr(stages, "_load_prompt", lambda name: "PROMPT {prospect_domain}")
    result = await stages.stage_1c_brief_synthesis(ctx)

    assert result.brief_md_path.exists()
    assert result.phase0_meta_path.exists()
    assert read_cost_actual(tmp_path)[stages.STAGE_KEY_BRIEF] == 0.85


# ─── Stage 2 fan-out ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_stage_2_agents_fans_out_to_all_four_agents(tmp_path: Path, monkeypatch) -> None:
    sf = _seed_state(tmp_path)
    (tmp_path / "prediscovery").mkdir(parents=True, exist_ok=True)
    (tmp_path / "prediscovery" / "brief.md").write_text("# Brief")
    (tmp_path / "prediscovery" / "agent_reading_guides.json").write_text(
        json.dumps({a: f"guide-{a}" for a in stages.STAGE_2_AGENTS})
    )

    runner = AsyncMock()
    runner.run.return_value = _make_runner_result(text="agent text", cost=12.00)
    ctx = stages.StageContext(audit_dir=tmp_path, state_file=sf, runner=runner)

    monkeypatch.setattr(stages, "_load_prompt", lambda name: "PROMPT {prospect_domain}")
    result = await stages.stage_2_agents(ctx)

    assert len(result.agents) == 4
    assert {a.agent_name for a in result.agents} == set(stages.STAGE_2_AGENTS)
    assert runner.run.await_count == 4
    cost = read_cost_actual(tmp_path)
    for agent in stages.STAGE_2_AGENTS:
        assert cost[f"{stages.STAGE_KEY_AGENT_PREFIX}{agent}"] == 12.00
    # total_so_far accumulates 4 × 12.00
    assert cost["total_so_far"] == pytest.approx(48.00)


@pytest.mark.asyncio
async def test_stage_2_agents_isolates_per_agent_failures(tmp_path: Path, monkeypatch) -> None:
    sf = _seed_state(tmp_path)
    (tmp_path / "prediscovery").mkdir(parents=True, exist_ok=True)
    (tmp_path / "prediscovery" / "brief.md").write_text("# Brief")
    (tmp_path / "prediscovery" / "agent_reading_guides.json").write_text("{}")

    async def flaky_run(**kwargs: Any) -> Any:
        if kwargs.get("role") == "stage_2_narrative":
            raise RuntimeError("simulated narrative crash")
        return _make_runner_result(cost=5.0)

    runner = AsyncMock()
    runner.run.side_effect = flaky_run
    ctx = stages.StageContext(audit_dir=tmp_path, state_file=sf, runner=runner)
    monkeypatch.setattr(stages, "_load_prompt", lambda name: "PROMPT {prospect_domain}")

    result = await stages.stage_2_agents(ctx)
    assert len(result.failures) == 1
    assert "narrative" in result.failures[0]
    surviving = [a for a in result.agents if a.error is None]
    assert len(surviving) == 3


# ─── Stage 5 render — fallback paths ──────────────────────────────────────


def test_render_html_uses_template_when_present(tmp_path: Path) -> None:
    report = {"prospect_domain": "acme.example", "health_score": {"overall": 78, "band": "fair", "per_section": {"seo": 80}}, "parent_findings": []}
    proposal = {"narrative_anchor": "test anchor", "entries": []}
    html = stages._render_html(report=report, proposal=proposal, phase0={}, slug="01H...")
    assert "<html" in html
    assert "acme.example" in html
    assert "78" in html


def test_render_pdf_writes_placeholder_when_weasyprint_missing(tmp_path: Path) -> None:
    pdf_path = tmp_path / "deliverable" / "report.pdf"
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    stages._render_pdf("<html>hi</html>", pdf_path)
    assert pdf_path.exists()
    assert pdf_path.read_bytes().startswith(b"%PDF")


# ─── Cost observability invariants ────────────────────────────────────────


@pytest.mark.asyncio
async def test_cost_actual_total_so_far_recomputes_after_each_stage(tmp_path: Path, monkeypatch) -> None:
    sf = _seed_state(tmp_path)
    runner = AsyncMock()
    runner.run.return_value = _make_runner_result(text=json.dumps({"signals": [], "gaps": []}), cost=3.00)
    ctx = stages.StageContext(audit_dir=tmp_path, state_file=sf, runner=runner)
    monkeypatch.setattr(stages, "_load_prompt", lambda name: "PROMPT {prospect_domain}")

    await stages.stage_0_intake(ctx)
    await stages.stage_1b_predischarge(ctx)

    cost = read_cost_actual(tmp_path)
    assert cost[stages.STAGE_KEY_INTAKE] == 0.0
    assert cost[stages.STAGE_KEY_PREDISCO] == 3.00
    assert cost["total_so_far"] == pytest.approx(3.00)
