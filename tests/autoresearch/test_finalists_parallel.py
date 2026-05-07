"""Tests for the finalize-finalists loop in evolve.py — concurrent holdout evaluation."""

from __future__ import annotations

import threading
import time
from pathlib import Path
from unittest.mock import patch

import pytest

import concurrency


@pytest.fixture(autouse=True)
def _reset_controller(monkeypatch):
    for name in (
        "AUTORESEARCH_CONCURRENCY",
        "AUTORESEARCH_CONCURRENCY_JUDGE_HTTP",
        "AUTORESEARCH_CONCURRENCY_TRACE",
    ):
        monkeypatch.delenv(name, raising=False)
    concurrency.reset_for_test()
    yield
    concurrency.reset_for_test()


def test_finalists_run_concurrently_under_judge_http_cap(monkeypatch, tmp_path):
    """3 finalists × ~0.20s holdout should finish well under serial 0.60s with judge_http cap >= 3."""
    monkeypatch.setenv("AUTORESEARCH_CONCURRENCY_JUDGE_HTTP", "3")
    import evolve

    config = object.__new__(evolve.EvolutionConfig)
    config.archive_dir = tmp_path
    config.lane = "core"
    config.search_suite_path = ""
    config.require_holdout = True

    finalists = ["v007", "v008", "v009"]
    threads_seen: list[int] = []
    completed: list[str] = []
    lock = threading.Lock()

    def fake_run_holdout(cfg, variant_dir: str) -> None:
        with lock:
            threads_seen.append(threading.get_ident())
            completed.append(Path(variant_dir).name)
        time.sleep(0.20)

    monkeypatch.setattr(evolve, "_run_holdout", fake_run_holdout)
    monkeypatch.setattr(evolve, "refresh_archive", lambda cfg: None)
    monkeypatch.setattr(evolve, "_record_head_and_check_rollback", lambda *a, **k: None)
    monkeypatch.setattr(
        evolve.evolve_ops, "holdout_configured", lambda: True
    )
    monkeypatch.setattr(
        evolve.evolve_ops, "finalize_candidate_ids",
        lambda *a, **k: list(finalists),
    )
    monkeypatch.setattr(
        evolve.evolve_ops, "holdout_suite_id", lambda lane: "stub-holdout-v1",
    )
    monkeypatch.setattr(
        evolve.evolve_ops, "write_finalized_shortlist",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        evolve.evolve_ops, "best_finalized_variant",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        evolve.evolve_ops, "current_head_variant_id",
        lambda *a, **k: None,
    )

    t0 = time.monotonic()
    evolve._do_finalize_step(config)
    elapsed = time.monotonic() - t0

    assert sorted(completed) == sorted(finalists), (
        f"every finalist must be evaluated, saw {completed}"
    )
    assert elapsed < 0.50, (
        f"expected concurrent finalists < 0.50s, got {elapsed:.2f}s"
    )
    assert len(set(threads_seen)) >= 2, (
        f"expected finalists on distinct threads, saw {threads_seen}"
    )


def test_finalists_serial_mode_runs_on_caller_thread(monkeypatch, tmp_path):
    """AUTORESEARCH_CONCURRENCY=serial degrades finalists loop to a sequential pass."""
    monkeypatch.setenv("AUTORESEARCH_CONCURRENCY", "serial")
    import evolve

    config = object.__new__(evolve.EvolutionConfig)
    config.archive_dir = tmp_path
    config.lane = "core"
    config.search_suite_path = ""
    config.require_holdout = True

    finalists = ["v007", "v008", "v009"]
    main_tid = threading.get_ident()
    threads_seen: list[int] = []

    def fake_run_holdout(cfg, variant_dir: str) -> None:
        threads_seen.append(threading.get_ident())

    monkeypatch.setattr(evolve, "_run_holdout", fake_run_holdout)
    monkeypatch.setattr(evolve, "refresh_archive", lambda cfg: None)
    monkeypatch.setattr(evolve, "_record_head_and_check_rollback", lambda *a, **k: None)
    monkeypatch.setattr(evolve.evolve_ops, "holdout_configured", lambda: True)
    monkeypatch.setattr(
        evolve.evolve_ops, "finalize_candidate_ids", lambda *a, **k: list(finalists)
    )
    monkeypatch.setattr(evolve.evolve_ops, "holdout_suite_id", lambda lane: "stub")
    monkeypatch.setattr(evolve.evolve_ops, "write_finalized_shortlist", lambda *a, **k: None)
    monkeypatch.setattr(evolve.evolve_ops, "best_finalized_variant", lambda *a, **k: None)
    monkeypatch.setattr(evolve.evolve_ops, "current_head_variant_id", lambda *a, **k: None)

    evolve._do_finalize_step(config)

    assert all(tid == main_tid for tid in threads_seen), (
        f"serial mode must run on calling thread, saw {threads_seen}"
    )
