"""AuditState + AuditStateFile tests — round-trip, concurrency, corrupt-load."""
from __future__ import annotations

import json
import threading
from dataclasses import replace
from pathlib import Path

import pytest

from src.audit.state import AuditState, AuditStateFile


def _new_state(audit_id: str = "a-0001") -> AuditState:
    return AuditState(
        audit_id=audit_id,
        client_slug="acme",
        prospect_domain="acme.test",
    )


def test_audit_state_is_frozen():
    s = _new_state()
    with pytest.raises(Exception):
        s.audit_id = "hacked"  # type: ignore[misc]


def test_save_and_load_roundtrip(tmp_path: Path):
    f = AuditStateFile(tmp_path / "state.json")
    state = _new_state()
    state = replace(state, status="running", total_cost_usd=12.34)
    f.save(state)
    reloaded = f.load()
    assert reloaded == state
    assert reloaded.status == "running"
    assert reloaded.total_cost_usd == 12.34


def test_save_preserves_tuple_fields_after_json_roundtrip(tmp_path: Path):
    f = AuditStateFile(tmp_path / "state.json")
    state = replace(
        _new_state(),
        completed_lenses=("L-A-01", "L-A-02"),
        failed_lenses=("L-B-99",),
        bundles_activated=("v-b2b-saas",),
        stage2_pids=(123, 456),
    )
    f.save(state)
    reloaded = f.load()
    # Tuples must round-trip (JSON stores as list; load must coerce back).
    assert reloaded.completed_lenses == ("L-A-01", "L-A-02")
    assert isinstance(reloaded.completed_lenses, tuple)
    assert reloaded.stage2_pids == (123, 456)


def test_load_missing_file_raises_file_not_found(tmp_path: Path):
    f = AuditStateFile(tmp_path / "no-such-state.json")
    with pytest.raises(FileNotFoundError):
        f.load()


def test_load_corrupt_json_raises_json_decode_error(tmp_path: Path):
    """Corrupt JSON deliberately surfaces — checkpointing convention is to raise,
    not paper over."""
    path = tmp_path / "state.json"
    path.write_text("{not json", encoding="utf-8")
    f = AuditStateFile(path)
    with pytest.raises(json.JSONDecodeError):
        f.load()


def test_corrupt_load_preserves_original_file(tmp_path: Path):
    path = tmp_path / "state.json"
    raw = "{not json"
    path.write_text(raw, encoding="utf-8")
    f = AuditStateFile(path)
    with pytest.raises(json.JSONDecodeError):
        f.load()
    # File must still hold the original bytes — failed load doesn't truncate.
    assert path.read_text(encoding="utf-8") == raw


def test_mutate_round_trip_via_replace(tmp_path: Path):
    f = AuditStateFile(tmp_path / "state.json")
    f.save(_new_state())
    out = f.mutate(lambda s: replace(s, status="completed", total_cost_usd=100.0))
    assert out.status == "completed"
    assert out.total_cost_usd == 100.0
    reloaded = f.load()
    assert reloaded == out


def test_concurrent_mutate_no_lost_writes(tmp_path: Path):
    """Two threads each appending 200 lens IDs — final list length must be 400."""
    f = AuditStateFile(tmp_path / "state.json")
    f.save(_new_state())

    n_per_thread = 200

    def worker(prefix: str) -> None:
        for i in range(n_per_thread):
            lens_id = f"{prefix}-{i:04d}"
            f.mutate(
                lambda s, lid=lens_id: replace(
                    s, completed_lenses=s.completed_lenses + (lid,)
                )
            )

    t1 = threading.Thread(target=worker, args=("T1",))
    t2 = threading.Thread(target=worker, args=("T2",))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    final = f.load()
    assert len(final.completed_lenses) == 2 * n_per_thread
    # No duplicates: every lens id is unique, so set size == list size.
    assert len(set(final.completed_lenses)) == 2 * n_per_thread
