"""Tests for src/audit/cost_ledger — record + ceilings + R29 SLA + JSONL log."""
from __future__ import annotations

import json
import os
from dataclasses import replace
from pathlib import Path

import pytest

from src.audit.claude_subprocess import ResultMessage
from src.audit.cost_ledger import (
    AUDIT_HARD_USD,
    AUDIT_SOFT_USD,
    R29_HARD_API_MS,
    R29_SOFT_API_MS,
    SCAN_HARD_USD,
    CostLedger,
    claude_rates,
)
from src.audit.exceptions import (
    CostCeilingReached,
    MissingSubscriptionToken,
    SubscriptionWindowExceeded,
)
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
# Subscription token enforcement
# ---------------------------------------------------------------------------


def test_assert_subscription_token_present(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "tok-abc")
    ledger, _ = _make_ledger(tmp_path)
    ledger.assert_subscription_token()  # no raise


def test_assert_subscription_token_missing_raises(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("CLAUDE_CODE_OAUTH_TOKEN", raising=False)
    ledger, _ = _make_ledger(tmp_path)
    with pytest.raises(MissingSubscriptionToken):
        ledger.assert_subscription_token()


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
    assert state.total_duration_api_ms == 5000 + 7000 + 3000


def test_record_metadata_is_logged(tmp_path: Path):
    ledger, _ = _make_ledger(tmp_path)
    ledger.record(
        "stage_2_lens_L-A-01",
        _result(),
        metadata={"lens_id": "L-A-01", "phase": "stage_2"},
    )
    row = json.loads(ledger.log_path.read_text(encoding="utf-8").strip())
    assert row["metadata"]["lens_id"] == "L-A-01"


# ---------------------------------------------------------------------------
# Cost ceilings (R10)
# ---------------------------------------------------------------------------


def test_audit_mode_hard_breaker(tmp_path: Path):
    ledger, sf = _make_ledger(tmp_path, mode="audit")
    # Below ceiling — no raise.
    ledger.record("s1", _result(cost=AUDIT_HARD_USD - 1.0))
    # Crossing ceiling — raise + state captures pause_reason.
    with pytest.raises(CostCeilingReached):
        ledger.record("s2", _result(cost=2.0))  # pushes total above $150
    state = sf.load()
    assert state.pause_reason == "cost_ceiling"


def test_audit_mode_soft_warn_does_not_raise(tmp_path: Path, capsys):
    ledger, _ = _make_ledger(tmp_path, mode="audit")
    ledger.record("s1", _result(cost=AUDIT_SOFT_USD - 1.0))
    # Crossing soft warn at $100 — proceeds, but emits stderr warning.
    ledger.record("s2", _result(cost=2.0))
    captured = capsys.readouterr()
    assert "soft" in captured.err.lower() or "warn" in captured.err.lower()


def test_scan_mode_hard_breaker(tmp_path: Path):
    ledger, sf = _make_ledger(tmp_path, mode="scan")
    ledger.record("s1", _result(cost=SCAN_HARD_USD - 0.5))
    with pytest.raises(CostCeilingReached):
        ledger.record("s2", _result(cost=1.0))  # pushes above $2
    state = sf.load()
    assert state.pause_reason == "cost_ceiling"


# ---------------------------------------------------------------------------
# R29 subscription-window SLA — duration_api_ms NOT duration_ms
# ---------------------------------------------------------------------------


def test_r29_hard_breaker_uses_duration_api_ms(tmp_path: Path):
    ledger, sf = _make_ledger(tmp_path)
    # Spend just under the hard limit — fine.
    ledger.record("s1", _result(cost=0.0, duration_api_ms=R29_HARD_API_MS - 1000))
    # Crossing 50% of 5h API-time — raise + pause_reason.
    with pytest.raises(SubscriptionWindowExceeded):
        ledger.record("s2", _result(cost=0.0, duration_api_ms=2000))
    state = sf.load()
    assert state.pause_reason == "subscription_window_ceiling"


def test_r29_uses_duration_api_ms_not_wall_clock(tmp_path: Path):
    """A stage with huge wall-clock (duration_ms) but small duration_api_ms
    must NOT trip R29 — wall-clock is observability only."""
    ledger, _ = _make_ledger(tmp_path)
    # Massive wall-clock (5h) but tiny API time — fine.
    ledger.record(
        "s1",
        _result(cost=0.0, duration_api_ms=10_000, duration_ms=5 * 60 * 60 * 1000),
    )
    # No raise; total_duration_api_ms only 10k.


def test_r29_soft_warn_does_not_raise(tmp_path: Path, capsys):
    ledger, _ = _make_ledger(tmp_path)
    # Below soft (40% of 5h API-time) — silent.
    ledger.record("s1", _result(cost=0.0, duration_api_ms=R29_SOFT_API_MS - 1000))
    # Crossing soft warn — stderr but no raise.
    ledger.record("s2", _result(cost=0.0, duration_api_ms=2000))
    captured = capsys.readouterr()
    assert "subscription" in captured.err.lower() or "r29" in captured.err.lower()


# ---------------------------------------------------------------------------
# Subscription billing with total_cost_usd=0 — fallback to tokens × rates
# ---------------------------------------------------------------------------


def test_subscription_zero_cost_falls_back_to_token_rates(tmp_path: Path):
    """When subscription billing returns total_cost_usd=0, the ledger must
    estimate cost via tokens × claude_rates(model) so ceiling math still works."""
    ledger, sf = _make_ledger(tmp_path)
    # 1M input + 1M output Opus tokens; total_cost_usd=0 (subscription).
    ledger.record(
        "s1",
        _result(cost=0.0, input_tokens=1_000_000, output_tokens=1_000_000),
        model="claude-opus-4-7",
    )
    state = sf.load()
    # Inferred cost should be > 0 (Opus pricing: ~$15 input + ~$75 output per M).
    assert state.total_cost_usd > 0


def test_claude_rates_returns_three_tuple_for_opus():
    inp, cached, out = claude_rates("claude-opus-4-7")
    assert inp > 0
    assert cached >= 0
    assert out > inp  # output is always pricier than input for Anthropic models


def test_claude_rates_unknown_model_returns_safe_defaults():
    inp, cached, out = claude_rates("unknown-model-x")
    assert inp > 0
    assert out > 0


# ---------------------------------------------------------------------------
# Malformed log + crash recovery
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
