"""Tests for src/audit/graceful_stop — flag set/clear/check on AuditState."""
from __future__ import annotations

from pathlib import Path

from src.audit.graceful_stop import (
    clear_stop,
    is_stop_requested,
    request_stop,
)
from src.audit.state import AuditState, AuditStateFile


def _new(tmp_path: Path) -> AuditStateFile:
    sf = AuditStateFile(tmp_path / "state.json")
    sf.save(AuditState(audit_id="a", client_slug="c", prospect_domain="d"))
    return sf


def test_initial_state_no_stop_requested(tmp_path: Path):
    sf = _new(tmp_path)
    assert is_stop_requested(sf) is False


def test_request_stop_sets_flag_and_reason(tmp_path: Path):
    sf = _new(tmp_path)
    request_stop(sf, reason="cost_ceiling")
    assert is_stop_requested(sf) is True
    state = sf.load()
    assert state.graceful_stop_requested is True
    assert state.graceful_stop_reason == "cost_ceiling"


def test_clear_stop_resets_flag_and_reason(tmp_path: Path):
    sf = _new(tmp_path)
    request_stop(sf, reason="external")
    clear_stop(sf)
    state = sf.load()
    assert state.graceful_stop_requested is False
    assert state.graceful_stop_reason == ""


def test_request_stop_overwrites_reason(tmp_path: Path):
    sf = _new(tmp_path)
    request_stop(sf, reason="first")
    request_stop(sf, reason="second")
    state = sf.load()
    assert state.graceful_stop_reason == "second"
