"""Tests for evolve.run_all_lanes — concurrent lane execution + per-lane error isolation."""

from __future__ import annotations

import threading
import time
from unittest.mock import patch

import pytest

import concurrency


@pytest.fixture(autouse=True)
def _reset_controller(monkeypatch):
    for name in (
        "AUTORESEARCH_CONCURRENCY",
        "AUTORESEARCH_CONCURRENCY_CLAUDE",
        "AUTORESEARCH_CONCURRENCY_TRACE",
    ):
        monkeypatch.delenv(name, raising=False)
    concurrency.reset_for_test()
    yield
    concurrency.reset_for_test()


def _import_run_all_lanes():
    """Import evolve.run_all_lanes lazily so we can stub heavy bootstrap helpers."""
    import evolve
    return evolve


def test_run_all_lanes_invokes_command_per_lane_concurrently(monkeypatch):
    """4 lanes × ~0.20s sleep should finish well under serial 0.80s under claude cap=4."""
    monkeypatch.setenv("AUTORESEARCH_CONCURRENCY_CLAUDE", "4")
    evolve = _import_run_all_lanes()

    threads_seen: list[int] = []
    lanes_seen: list[str] = []
    lock = threading.Lock()

    def fake_command(lane_config):
        with lock:
            lanes_seen.append(lane_config.lane)
            threads_seen.append(threading.get_ident())
        time.sleep(0.20)

    config = object.__new__(evolve.EvolutionConfig)
    config.lane = "core"

    def fake_replace(orig, *, lane: str):
        clone = object.__new__(evolve.EvolutionConfig)
        clone.lane = lane
        return clone

    monkeypatch.setattr(evolve.dataclasses, "replace", fake_replace)
    monkeypatch.setattr(evolve, "_init_lane_config", lambda cfg: None)
    monkeypatch.setattr(evolve, "preflight_checks", lambda cfg: None)

    expected_lanes = list(evolve.all_lane_names())
    assert len(expected_lanes) >= 2, "test requires registry to expose at least 2 lanes"

    t0 = time.monotonic()
    evolve.run_all_lanes(config, fake_command)
    elapsed = time.monotonic() - t0

    assert sorted(lanes_seen) == sorted(expected_lanes), (
        f"every registered lane must be invoked exactly once, saw {lanes_seen}"
    )
    serial_estimate = 0.20 * len(expected_lanes)
    assert elapsed < serial_estimate * 0.75, (
        f"expected concurrent run < {serial_estimate * 0.75:.2f}s, got {elapsed:.2f}s"
    )
    assert len(set(threads_seen)) >= 2, (
        f"expected lanes to run on distinct threads, saw {threads_seen}"
    )


def test_run_all_lanes_isolates_per_lane_errors(monkeypatch, capsys):
    """One lane raising must not stop other lanes — preserves serial-loop semantics."""
    evolve = _import_run_all_lanes()

    completed: list[str] = []
    lock = threading.Lock()

    def fake_command(lane_config):
        if lane_config.lane == evolve.all_lane_names()[0]:
            raise RuntimeError(f"boom-{lane_config.lane}")
        with lock:
            completed.append(lane_config.lane)

    config = object.__new__(evolve.EvolutionConfig)
    config.lane = "core"

    def fake_replace(orig, *, lane: str):
        clone = object.__new__(evolve.EvolutionConfig)
        clone.lane = lane
        return clone

    monkeypatch.setattr(evolve.dataclasses, "replace", fake_replace)
    monkeypatch.setattr(evolve, "_init_lane_config", lambda cfg: None)
    monkeypatch.setattr(evolve, "preflight_checks", lambda cfg: None)

    evolve.run_all_lanes(config, fake_command)

    expected_lanes = list(evolve.all_lane_names())
    surviving = expected_lanes[1:]
    assert sorted(completed) == sorted(surviving), (
        "all non-failing lanes must complete despite a sibling raise"
    )
    err = capsys.readouterr().err
    assert f"ERROR: lane={expected_lanes[0]}" in err
    assert "boom-" in err


def test_run_all_lanes_serial_mode(monkeypatch):
    """AUTORESEARCH_CONCURRENCY=serial degrades to a plain sequential loop on caller thread."""
    monkeypatch.setenv("AUTORESEARCH_CONCURRENCY", "serial")
    evolve = _import_run_all_lanes()

    main_tid = threading.get_ident()
    threads_seen: list[int] = []

    def fake_command(lane_config):
        threads_seen.append(threading.get_ident())

    config = object.__new__(evolve.EvolutionConfig)
    config.lane = "core"

    def fake_replace(orig, *, lane: str):
        clone = object.__new__(evolve.EvolutionConfig)
        clone.lane = lane
        return clone

    monkeypatch.setattr(evolve.dataclasses, "replace", fake_replace)
    monkeypatch.setattr(evolve, "_init_lane_config", lambda cfg: None)
    monkeypatch.setattr(evolve, "preflight_checks", lambda cfg: None)

    evolve.run_all_lanes(config, fake_command)

    assert all(tid == main_tid for tid in threads_seen), (
        f"serial mode must run on calling thread, saw {threads_seen}"
    )
