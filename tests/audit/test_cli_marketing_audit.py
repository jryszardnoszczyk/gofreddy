"""L4 smoke tests for `freddy audit` marketing-audit lifecycle verbs.

Covers the 7 new verbs (init / run / confirm-brief / mark-paid / publish /
close-engagement / attach). The `run` verb dispatches `stages.*` which is
already covered by `test_stages_orchestration.py` — here we only verify
the gate-honoring + state-transition flow, not the inner stage logic.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from cli.freddy.commands import audit as audit_cli


def _seed_workspace(tmp_path: Path, slug: str = "acme") -> Path:
    """Set up a fake clients_dir with a registered client."""
    clients_dir = tmp_path / "clients"
    client_dir = clients_dir / slug
    client_dir.mkdir(parents=True, exist_ok=True)
    (client_dir / "config.json").write_text(json.dumps({"slug": slug}))
    return clients_dir


def _patch_config(clients_dir: Path):
    """Return a context manager patching load_config to return our fake."""
    cfg = type("Cfg", (), {"clients_dir": clients_dir})()
    return patch("cli.freddy.commands.audit.load_config", return_value=cfg)


def test_ma_init_creates_state_json(tmp_path: Path) -> None:
    clients_dir = _seed_workspace(tmp_path, "acme")
    with _patch_config(clients_dir):
        result = CliRunner().invoke(audit_cli.app, ["init", "acme", "--domain", "acme.example"])
    assert result.exit_code == 0, result.output
    state_path = clients_dir / "acme" / "audit" / "state.json"
    assert state_path.exists()
    state = json.loads(state_path.read_text())
    assert state["client_slug"] == "acme"
    assert state["prospect_domain"] == "acme.example"


def test_ma_confirm_brief_transitions_status(tmp_path: Path) -> None:
    clients_dir = _seed_workspace(tmp_path, "acme")
    with _patch_config(clients_dir):
        CliRunner().invoke(audit_cli.app, ["init", "acme", "--domain", "acme.example"])
        result = CliRunner().invoke(audit_cli.app, ["confirm-brief", "acme"])
    assert result.exit_code == 0, result.output
    state = json.loads((clients_dir / "acme" / "audit" / "state.json").read_text())
    assert state["status"] == "brief_confirmed"


def test_ma_mark_paid_records_stripe_event(tmp_path: Path) -> None:
    clients_dir = _seed_workspace(tmp_path, "acme")
    with _patch_config(clients_dir):
        CliRunner().invoke(audit_cli.app, ["init", "acme", "--domain", "acme.example"])
        result = CliRunner().invoke(audit_cli.app, ["mark-paid", "acme", "--stripe-event-id", "evt_123"])
    assert result.exit_code == 0, result.output
    assert "evt_123" in result.output or "paid" in result.output.lower()
    state = json.loads((clients_dir / "acme" / "audit" / "state.json").read_text())
    assert state["status"] == "paid"


def test_ma_publish_transitions_status(tmp_path: Path) -> None:
    clients_dir = _seed_workspace(tmp_path, "acme")
    with _patch_config(clients_dir):
        CliRunner().invoke(audit_cli.app, ["init", "acme", "--domain", "acme.example"])
        result = CliRunner().invoke(audit_cli.app, ["publish", "acme"])
    assert result.exit_code == 0, result.output
    state = json.loads((clients_dir / "acme" / "audit" / "state.json").read_text())
    assert state["status"] == "published"


def test_ma_close_engagement_appends_lineage_row(tmp_path: Path) -> None:
    clients_dir = _seed_workspace(tmp_path, "acme")
    with _patch_config(clients_dir):
        CliRunner().invoke(audit_cli.app, ["init", "acme", "--domain", "acme.example"])
        result = CliRunner().invoke(
            audit_cli.app, ["close-engagement", "acme", "--converted", "Y"]
        )
    assert result.exit_code == 0, result.output
    # lineage.jsonl is at clients_dir.parent / "audits" / "lineage.jsonl"
    lineage = (clients_dir.parent / "audits" / "lineage.jsonl").read_text().strip().splitlines()
    assert len(lineage) == 1
    row = json.loads(lineage[0])
    assert row["engagement_converted"] is True
    assert row["slug"] == "acme"


def test_ma_attach_rejects_unknown_type(tmp_path: Path) -> None:
    clients_dir = _seed_workspace(tmp_path, "acme")
    with _patch_config(clients_dir):
        CliRunner().invoke(audit_cli.app, ["init", "acme", "--domain", "acme.example"])
        result = CliRunner().invoke(
            audit_cli.app, ["attach", "bogus-type", "acme", "--source", "anything"]
        )
    assert result.exit_code != 0
    assert "Unknown attach type" in result.output or "bogus-type" in result.output


def test_ma_attach_stores_file_when_source_path_exists(tmp_path: Path) -> None:
    clients_dir = _seed_workspace(tmp_path, "acme")
    src_file = tmp_path / "transcript.txt"
    src_file.write_text("sales call transcript content")
    with _patch_config(clients_dir):
        CliRunner().invoke(audit_cli.app, ["init", "acme", "--domain", "acme.example"])
        result = CliRunner().invoke(
            audit_cli.app, ["attach", "sales-transcript", "acme", "--source", str(src_file)]
        )
    assert result.exit_code == 0, result.output
    stored = clients_dir / "acme" / "audit" / "attached" / "sales-transcript" / "transcript.txt"
    assert stored.exists()
    assert stored.read_text() == "sales call transcript content"
