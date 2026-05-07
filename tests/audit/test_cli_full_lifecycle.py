"""§7.7 precursor — CLI-driven full lifecycle integration test.

Runs the complete user-facing flow:

    freddy audit init <slug>
    freddy audit run <slug>             → halts at intake gate
    freddy audit confirm-brief <slug>
    freddy audit run <slug>             → halts at payment gate
    freddy audit mark-paid <slug>
    freddy audit run <slug>             → produces deliverable
    freddy audit publish <slug> --dry-run
    freddy audit close-engagement <slug> --converted Y

with the AgentRunner + preflight runner mocked. Catches CLI-level
regressions (missing args, wrong gate ordering) that the
stage-level smoke test cannot see.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from typer.testing import CliRunner

from cli.freddy.commands import audit as audit_cli


def _seed_workspace(tmp_path: Path, slug: str = "acme") -> Path:
    clients_dir = tmp_path / "clients"
    (clients_dir / slug).mkdir(parents=True, exist_ok=True)
    (clients_dir / slug / "config.json").write_text(json.dumps({"slug": slug}))
    return clients_dir


def _patch_config(clients_dir: Path):
    cfg = type("Cfg", (), {"clients_dir": clients_dir})()
    return patch("cli.freddy.commands.audit.load_config", return_value=cfg)


def _runner_result(text: str = "", cost: float = 1.0) -> Any:
    return type("R", (), {
        "text": text, "cost_usd": cost, "session_id": "sess-cli",
        "duration_ms": 100, "backend": "claude", "model": "opus",
        "role": "smoke", "transcript_path": None, "raw_envelope": None,
        "attempts": 1,
    })()


@pytest.fixture
def runner_patches(monkeypatch):
    """All the patches needed to make freddy audit run work without a real
    LLM or real preflight network calls."""
    fake_runner = AsyncMock()
    fake_runner.run.return_value = _runner_result(cost=2.0)

    from src.audit.preflight.runner import PreflightResult
    stub_preflight = PreflightResult(
        domain="acme.example", started_at=0.0, elapsed_s=0.0,
        signals={}, failures={},
    )

    patches = [
        # Replace AgentRunner constructor with a factory that returns our mock
        patch("src.audit.agent_runner.AgentRunner", return_value=fake_runner),
        patch("src.audit.stages.preflight_runner.run", AsyncMock(return_value=stub_preflight)),
        patch("src.audit.stages._load_prompt", lambda name: "PROMPT"),
    ]
    for p in patches:
        p.start()
    yield fake_runner
    for p in patches:
        p.stop()


def test_full_cli_lifecycle_init_to_close(tmp_path: Path, runner_patches):
    clients_dir = _seed_workspace(tmp_path, "acme")
    cli = CliRunner()

    with _patch_config(clients_dir):
        # 1. init
        r = cli.invoke(audit_cli.app, ["init", "acme", "--domain", "acme.example"])
        assert r.exit_code == 0, r.output
        state_path = clients_dir / "acme" / "audit" / "state.json"
        assert state_path.exists()
        assert json.loads(state_path.read_text())["status"] == "pending"

        # 2. first run → halts at intake gate
        r = cli.invoke(audit_cli.app, ["run", "acme"])
        assert r.exit_code == 0, r.output
        assert "confirm-brief" in r.output
        # Stages 0/1/1b/1c artifacts on disk
        for sub in ["intake/form.json", "cache/manifest.json",
                    "prediscovery/brief.md", "prediscovery/agent_reading_guides.json"]:
            assert (clients_dir / "acme" / "audit" / sub).exists(), f"missing {sub}"

        # 3. confirm-brief
        r = cli.invoke(audit_cli.app, ["confirm-brief", "acme"])
        assert r.exit_code == 0
        assert json.loads(state_path.read_text())["status"] == "brief_confirmed"

        # 4. second run → halts at payment gate
        r = cli.invoke(audit_cli.app, ["run", "acme"])
        assert r.exit_code == 0, r.output
        assert "mark-paid" in r.output

        # 5. mark-paid
        r = cli.invoke(audit_cli.app, ["mark-paid", "acme", "--stripe-event-id", "evt_test"])
        assert r.exit_code == 0
        assert json.loads(state_path.read_text())["status"] == "paid"

        # 6. third run → produces deliverable, halts at ship gate
        r = cli.invoke(audit_cli.app, ["run", "acme"])
        assert r.exit_code == 0, r.output
        assert "publish" in r.output
        # Stage 2/3/4/5 artifacts
        audit_dir = clients_dir / "acme" / "audit"
        for sub in [
            "agents/findability/agent_output.json",
            "agents/narrative/agent_output.json",
            "agents/acquisition/agent_output.json",
            "agents/experience/agent_output.json",
            "synthesis/report.json",
            "proposal/proposal.json",
            "deliverable/report.html",
            "deliverable/report.pdf",
        ]:
            assert (audit_dir / sub).exists(), f"missing {sub}"

        # report.json carries deterministic HealthScore
        report = json.loads((audit_dir / "synthesis" / "report.json").read_text())
        assert report["health_score"]["overall"] == 100
        assert report["health_score"]["band"] == "green"

        # cost_actual.json populated, total_so_far set
        cost = json.loads((audit_dir / "cost_actual.json").read_text())
        assert cost["total_so_far"] > 0
        # Every stage represented
        for k in ["stage_0_intake", "stage_1a_warmup", "stage_1b_predischarge",
                  "stage_1c_brief", "stage_3_synthesis",
                  "stage_4_proposal", "stage_5_deliverable"]:
            assert k in cost, f"missing cost key {k}"

        # events.jsonl populated
        events_path = audit_dir / "events.jsonl"
        assert events_path.exists()
        kinds = {json.loads(line)["kind"]
                 for line in events_path.read_text().splitlines() if line.strip()}
        assert "cost_recorded" in kinds

        # 7. publish (dry-run — skips R2 upload, just flips state)
        r = cli.invoke(audit_cli.app, ["publish", "acme", "--dry-run"])
        assert r.exit_code == 0, r.output
        assert json.loads(state_path.read_text())["status"] == "published"

        # 8. close-engagement (T+60d signal) → lineage row written
        r = cli.invoke(audit_cli.app, ["close-engagement", "acme", "--converted", "Y"])
        assert r.exit_code == 0, r.output
        assert json.loads(state_path.read_text())["status"] == "engagement_closed"
        lineage = (clients_dir.parent / "audits" / "lineage.jsonl").read_text().strip().splitlines()
        assert len(lineage) == 1
        row = json.loads(lineage[0])
        assert row["slug"] == "acme"
        assert row["engagement_converted"] is True


def test_resume_from_intake_gate_skips_completed_stages(tmp_path: Path, runner_patches):
    """After first run halts at intake gate, a second run BEFORE
    confirm-brief should NOT re-fire the runner (stages are idempotent)."""
    clients_dir = _seed_workspace(tmp_path, "acme")
    cli = CliRunner()

    with _patch_config(clients_dir):
        cli.invoke(audit_cli.app, ["init", "acme", "--domain", "acme.example"])
        cli.invoke(audit_cli.app, ["run", "acme"])
        first_call_count = runner_patches.run.await_count
        # Second run before confirm-brief — runner should NOT fire again
        cli.invoke(audit_cli.app, ["run", "acme"])
        assert runner_patches.run.await_count == first_call_count, (
            "resume must not re-fire runner before gate transitions"
        )
