"""Tests for autoresearch/concurrency.py — single-sem parallel_for.

Per Plan B U9b (2026-05-11): collapsed from 5 per-resource semaphores
(claude / codex / opencode / judge_http / cloro_search) to a single
MAX_PARALLEL_AGENTS sem. The ``resource=`` arg is accepted but ignored.
"""

from __future__ import annotations

import threading
import time
from typing import Any

import pytest

import concurrency


@pytest.fixture(autouse=True)
def _reset_controller(monkeypatch):
    for name in (
        "AUTORESEARCH_CONCURRENCY",
        "MAX_PARALLEL_AGENTS",
        "AUTORESEARCH_CONCURRENCY_TRACE",
    ):
        monkeypatch.delenv(name, raising=False)
    concurrency._reset_for_test()
    yield
    concurrency._reset_for_test()


def test_parallel_for_runs_concurrently(monkeypatch):
    monkeypatch.setenv("MAX_PARALLEL_AGENTS", "4")

    def work(item: int) -> int:
        time.sleep(0.20)
        return item * 2

    t0 = time.monotonic()
    results = concurrency.parallel_for([1, 2, 3, 4], work)
    elapsed = time.monotonic() - t0

    assert results == [2, 4, 6, 8]
    assert elapsed < 0.50, f"expected concurrent run < 0.50s, got {elapsed:.2f}s"


def test_parallel_for_serial_mode_runs_sequentially(monkeypatch):
    monkeypatch.setenv("AUTORESEARCH_CONCURRENCY", "serial")

    main_tid = threading.get_ident()
    seen_threads: list[int] = []

    def work(item: int) -> int:
        seen_threads.append(threading.get_ident())
        return item

    results = concurrency.parallel_for([1, 2, 3], work)

    assert results == [1, 2, 3]
    assert all(tid == main_tid for tid in seen_threads), (
        f"serial mode should run on calling thread, saw {seen_threads}"
    )


def test_parallel_for_propagates_first_exception():
    def work(item: int) -> int:
        if item == 2:
            raise RuntimeError(f"boom-{item}")
        time.sleep(0.05)
        return item

    with pytest.raises(RuntimeError, match="boom-2"):
        concurrency.parallel_for([1, 2, 3, 4], work)


def test_max_parallel_agents_cap_enforced(monkeypatch):
    """MAX_PARALLEL_AGENTS=1 serialises every parallel_for call."""
    monkeypatch.setenv("MAX_PARALLEL_AGENTS", "1")

    in_flight = 0
    max_in_flight = 0
    lock = threading.Lock()

    def work(item: int) -> int:
        nonlocal in_flight, max_in_flight
        with lock:
            in_flight += 1
            max_in_flight = max(max_in_flight, in_flight)
        time.sleep(0.05)
        with lock:
            in_flight -= 1
        return item

    results = concurrency.parallel_for([1, 2, 3, 4], work)

    assert results == [1, 2, 3, 4]
    assert max_in_flight == 1, f"cap=1 should serialise; observed {max_in_flight}"


def test_invalid_cap_raises(monkeypatch):
    monkeypatch.setenv("MAX_PARALLEL_AGENTS", "0")
    with pytest.raises(ValueError, match="MAX_PARALLEL_AGENTS"):
        concurrency.controller()


def test_non_numeric_cap_raises_with_helpful_message(monkeypatch):
    monkeypatch.setenv("MAX_PARALLEL_AGENTS", "four")
    with pytest.raises(ValueError, match="must be a positive integer"):
        concurrency.controller()


def test_resource_kwarg_ignored():
    """The ``resource=`` arg survives for back-compat but has no effect."""
    results = concurrency.parallel_for([1, 2, 3], lambda x: x * 2, resource="claude")
    assert results == [2, 4, 6]


def test_empty_items_returns_empty_list_without_executor():
    def work(item: Any) -> Any:
        raise AssertionError("work_fn should not be invoked for empty items")

    assert concurrency.parallel_for([], work) == []


def test_results_in_input_order():
    def work(item: tuple[int, float]) -> int:
        idx, delay = item
        time.sleep(delay)
        return idx

    items = [(0, 0.20), (1, 0.05), (2, 0.10), (3, 0.01)]
    results = concurrency.parallel_for(items, work)
    assert results == [0, 1, 2, 3]


def test_singleton_coherent_across_known_production_call_sites():
    """The 3 modules that import concurrency must share parallel_for."""
    import evaluate_variant
    import evolve
    import program_prescription_critic

    assert evolve.parallel_for is evaluate_variant.parallel_for
    assert evolve.parallel_for is program_prescription_critic.parallel_for
    assert evolve.parallel_for is concurrency.parallel_for
