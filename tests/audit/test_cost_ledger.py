"""Tests for src/audit/cost_ledger — record + accumulate + JSONL log.

Cost-ceiling enforcement (R10) + R29 subscription-window SLA were dropped
in the L1 rebase per master plan §1 Goal 6 + §1 Non-goals 5/6 — those
tests are removed too. v1 is observability-without-enforcement; first 5
paid audits calibrate the empirical baseline.
"""
from __future__ import annotations

import json
from pathlib import Path

from src.audit.claude_subprocess import ResultMessage
from src.audit.cost_ledger import CostLedger
from src.audit.state import AuditState, AuditStateFile


def _result(
    *,
    cost: float = 0.10,
    duration_api_ms: int = 1_000,
    duration_ms: int = 2_000,
    input_tokens: int = 100,
    output_tokens: int = 50,
    subtype: str = "success",
) -> ResultMessage:
    return ResultMessage(
        subtype=subtype,
        session_id="sid",
        is_error=(subtype != "success"),
        duration_ms=duration_ms,
        duration_api_ms=duration_api_ms,
        num_turns=1,
        total_cost_usd=cost,
        stop_reason="end_turn",
        result="ok" if subtype == "success" else None,
        errors=() if subtype == "success" else ("e",),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_creation_input_tokens=0,
        cache_read_input_tokens=0,
    )


def _audit_dir(tmp_path: Path) -> Path:
    d = tmp_path / "clients" / "acme" / "audit" / "a-0001"
    d.mkdir(parents=True)
    return d


def _make_ledger(tmp_path: Path, mode: str = "audit") -> tuple[CostLedger, AuditStateFile]:
    audit_dir = _audit_dir(tmp_path)
    sf = AuditStateFile(audit_dir / "state.json")
    sf.save(AuditState(audit_id="a-0001", client_slug="acme", prospect_domain="acme.test"))
    ledger = CostLedger(state_file=sf, mode=mode, log_path=audit_dir / "cost_log.jsonl")
    return ledger, sf


# ---------------------------------------------------------------------------
# Happy path: record, accumulate, log
# ---------------------------------------------------------------------------


def test_record_appends_jsonl_and_accumulates_state(tmp_path: Path):
    ledger, sf = _make_ledger(tmp_path)
    ledger.record("stage_1b", _result(cost=0.10, duration_api_ms=5000))
    ledger.record("stage_2_lens_L-A-01", _result(cost=0.20, duration_api_ms=7000))
    ledger.record("stage_3", _result(cost=0.30, duration_api_ms=3000))

    rows = (ledger.log_path).read_text(encoding="utf-8").strip().splitlines()
    assert len(rows) == 3
    parsed = [json.loads(r) for r in rows]
    assert [r["role"] for r in parsed] == ["stage_1b", "stage_2_lens_L-A-01", "stage_3"]
    assert all("timestamp" in r for r in parsed)
    assert all("duration_api_ms" in r for r in parsed)

    state = sf.load()
    assert round(state.total_cost_usd, 6) == round(0.10 + 0.20 + 0.30, 6)


def test_record_metadata_is_logged(tmp_path: Path):
    ledger, _ = _make_ledger(tmp_path)
    ledger.record(
        "stage_2_lens_L-A-01",
        _result(),
        metadata={"lens_id": "L-A-01", "phase": "stage_2"},
    )
    row = json.loads(ledger.log_path.read_text(encoding="utf-8").strip())
    assert row["metadata"]["lens_id"] == "L-A-01"


def test_record_zero_cost_does_not_inflate_state(tmp_path: Path):
    """v1 strips the token×rate fallback for zero-cost subscription
    billing — record(cost=0) keeps state.total_cost_usd at 0 (the row
    still lands in the JSONL with cost=0 for observability)."""
    ledger, sf = _make_ledger(tmp_path)
    ledger.record("s1", _result(cost=0.0, input_tokens=1_000_000, output_tokens=1_000_000))
    assert sf.load().total_cost_usd == 0.0
    row = json.loads(ledger.log_path.read_text(encoding="utf-8").strip())
    assert row["total_cost_usd"] == 0.0


# ---------------------------------------------------------------------------
# Crash recovery
# ---------------------------------------------------------------------------


def test_record_does_not_raise_on_log_directory_missing_creates_it(tmp_path: Path):
    """Log path's parent dir is created on first record, not at __init__."""
    audit_dir = tmp_path / "fresh"
    sf = AuditStateFile(audit_dir / "state.json")
    sf.path.parent.mkdir(parents=True)
    sf.save(AuditState(audit_id="a", client_slug="c", prospect_domain="d"))
    log_path = audit_dir / "deep" / "cost_log.jsonl"
    ledger = CostLedger(state_file=sf, mode="audit", log_path=log_path)
    ledger.record("s1", _result())
    assert log_path.is_file()
