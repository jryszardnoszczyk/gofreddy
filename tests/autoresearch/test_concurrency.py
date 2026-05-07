"""Tests for autoresearch/concurrency.py — central provider semaphores + parallel_for."""

from __future__ import annotations

import threading
import time
from typing import Any

import pytest

import concurrency


@pytest.fixture(autouse=True)
def _reset_controller(monkeypatch):
    """Clear concurrency env vars + singleton between tests so each test reads fresh env."""
    for name in (
        "AUTORESEARCH_CONCURRENCY",
        "AUTORESEARCH_CONCURRENCY_CLAUDE",
        "AUTORESEARCH_CONCURRENCY_CODEX",
        "AUTORESEARCH_CONCURRENCY_OPENCODE",
        "AUTORESEARCH_CONCURRENCY_JUDGE_HTTP",
        "AUTORESEARCH_CONCURRENCY_CLORO_SEARCH",
        "AUTORESEARCH_CONCURRENCY_TRACE",
    ):
        monkeypatch.delenv(name, raising=False)
    concurrency.reset_for_test()
    yield
    concurrency.reset_for_test()


def test_parallel_for_runs_concurrently(monkeypatch):
    """4 items × 0.20s sleep should finish well under serial 0.80s when claude cap >= 4."""
    monkeypatch.setenv("AUTORESEARCH_CONCURRENCY_CLAUDE", "4")

    def work(item: int) -> int:
        time.sleep(0.20)
        return item * 2

    t0 = time.monotonic()
    results = concurrency.parallel_for([1, 2, 3, 4], work, resource="claude")
    elapsed = time.monotonic() - t0

    assert results == [2, 4, 6, 8]
    assert elapsed < 0.50, f"expected concurrent run < 0.50s, got {elapsed:.2f}s"


def test_parallel_for_serial_mode_runs_sequentially(monkeypatch):
    """AUTORESEARCH_CONCURRENCY=serial degrades to a plain for loop on calling thread."""
    monkeypatch.setenv("AUTORESEARCH_CONCURRENCY", "serial")

    main_tid = threading.get_ident()
    seen_threads: list[int] = []

    def work(item: int) -> int:
        seen_threads.append(threading.get_ident())
        return item

    results = concurrency.parallel_for([1, 2, 3], work, resource="claude")

    assert results == [1, 2, 3]
    assert all(tid == main_tid for tid in seen_threads), (
        f"serial mode should run on calling thread, saw {seen_threads}"
    )


def test_parallel_for_propagates_first_exception():
    """First raised exception is re-raised; later workers are cancelled where possible."""
    started = threading.Event()
    completed: list[int] = []

    def work(item: int) -> int:
        started.set()
        if item == 2:
            raise RuntimeError(f"boom-{item}")
        time.sleep(0.05)
        completed.append(item)
        return item

    with pytest.raises(RuntimeError, match="boom-2"):
        concurrency.parallel_for([1, 2, 3, 4], work, resource="claude")


def test_semaphore_caps_from_env(monkeypatch):
    """Per-resource caps come from AUTORESEARCH_CONCURRENCY_<RESOURCE> env vars."""
    monkeypatch.setenv("AUTORESEARCH_CONCURRENCY_CLAUDE", "1")
    monkeypatch.setenv("AUTORESEARCH_CONCURRENCY_CODEX", "7")

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

    results = concurrency.parallel_for([1, 2, 3, 4], work, resource="claude")

    assert results == [1, 2, 3, 4]
    assert max_in_flight == 1, (
        f"claude cap=1 should serialise; observed max_in_flight={max_in_flight}"
    )

    ctl = concurrency.controller()
    assert ctl.acquire("claude") is ctl.acquire("claude"), "same resource → same semaphore"
    assert ctl.acquire("claude") is not ctl.acquire("codex"), "different resources → different sems"


def test_invalid_cap_raises(monkeypatch):
    """Caps < 1 are rejected at controller construction."""
    monkeypatch.setenv("AUTORESEARCH_CONCURRENCY_CLAUDE", "0")
    with pytest.raises(ValueError, match="AUTORESEARCH_CONCURRENCY_CLAUDE"):
        concurrency.controller()


def test_unknown_resource_raises_value_error():
    """Unknown resource name is a ValueError, not a silent fallback."""
    with pytest.raises(ValueError, match="Unknown resource"):
        concurrency.parallel_for([1, 2], lambda x: x, resource="not_a_provider")


def test_empty_items_returns_empty_list_without_executor():
    """Empty input is a fast-path: no executor, no semaphore acquisition."""

    def work(item: Any) -> Any:
        raise AssertionError("work_fn should not be invoked for empty items")

    assert concurrency.parallel_for([], work, resource="claude") == []


def test_results_in_input_order():
    """Even when workers complete out of order, results match input order."""

    def work(item: tuple[int, float]) -> int:
        idx, delay = item
        time.sleep(delay)
        return idx

    items = [(0, 0.20), (1, 0.05), (2, 0.10), (3, 0.01)]
    results = concurrency.parallel_for(items, work, resource="claude")
    assert results == [0, 1, 2, 3]
