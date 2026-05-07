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
    concurrency._reset_for_test()
    yield
    concurrency._reset_for_test()


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


def test_empty_input_still_validates_env_caps(monkeypatch):
    """An empty parallel_for must surface AUTORESEARCH_CONCURRENCY_<R>=0 as ValueError.

    Otherwise misconfiguration silently goes undetected on lanes that happen
    to have no items, only biting later when a populated call site fires.
    """
    monkeypatch.setenv("AUTORESEARCH_CONCURRENCY_CLAUDE", "0")
    with pytest.raises(ValueError, match="AUTORESEARCH_CONCURRENCY_CLAUDE"):
        concurrency.parallel_for([], lambda x: x, resource="claude")


def test_singleton_coherent_across_production_call_sites():
    """All production importers must observe the same `parallel_for` and the
    same controller singleton — regression guard for the bare-vs-dotted import
    bug discovered during impl. If a future contributor flips one site to
    `from autoresearch.concurrency import …`, this test fails immediately.
    """
    import evaluate_variant
    import evolve
    import program_prescription_critic

    # All three production modules must reference the same parallel_for object.
    assert evolve.parallel_for is evaluate_variant.parallel_for
    assert evolve.parallel_for is program_prescription_critic.parallel_for
    assert evolve.parallel_for is concurrency.parallel_for

    # And the singleton instance returned by controller() must be shared.
    ctl_via_test = concurrency.controller()
    # The production modules access controller() lazily inside parallel_for;
    # exercise it by calling parallel_for and observing it didn't rebuild.
    concurrency.parallel_for([1], lambda x: x, resource="claude")
    assert concurrency.controller() is ctl_via_test


def test_parallel_for_propagates_first_exception_limits_sibling_work():
    """Sibling cancellation actually limits work — not just the docstring claim.

    With a slow work_fn (1.0s sleep) and item=2 raising immediately, after the
    raise reaches the caller, fewer than (N-1) siblings should have completed.
    Note: ThreadPoolExecutor.Future.cancel() only succeeds for not-yet-running
    futures, so when len(items) <= max_workers all futures start immediately
    and cancellation is best-effort. This test asserts the WEAKER claim that
    the exception eventually propagates without hanging — strengthening it
    further would require restricting max_workers.
    """
    started = []
    completed = []
    lock = threading.Lock()

    def work(item: int) -> int:
        with lock:
            started.append(item)
        if item == 2:
            raise RuntimeError(f"boom-{item}")
        time.sleep(1.0)
        with lock:
            completed.append(item)
        return item

    t0 = time.monotonic()
    with pytest.raises(RuntimeError, match="boom-2"):
        concurrency.parallel_for([1, 2, 3, 4], work, resource="claude")
    elapsed = time.monotonic() - t0

    # Exception must propagate; in-flight workers run to completion (best-effort
    # cancel). Wall must be bounded by 1 sleep interval, not summed.
    assert elapsed < 1.5, f"parallel_for hung past first exception: {elapsed:.2f}s"
    # All non-failing items started concurrently (max_workers >= len(items)).
    assert sorted(started) == [1, 2, 3, 4]


# NOTE: max_workers-below-cap cancellation is intentionally NOT tested here.
# The cancel branch in parallel_for is genuinely best-effort and racy: by the
# time `as_completed` yields a failed future, the executor's worker may have
# already pulled the next queued item off the queue. The
# `test_parallel_for_propagates_first_exception_limits_sibling_work` test
# above proves the meaningful contract (wall-time bounded by one sleep
# interval, not the sum); a stricter cancellation assertion would be flaky.


# NOTE: a runtime test for the nested-parallel_for-at-cap-1 deadlock footgun
# is intentionally NOT included here. ThreadPoolExecutor's worker threads are
# non-daemon, so a wedged executor blocks pytest from exiting even when the
# orchestrating test thread is daemonised. The constraint is documented in
# `docs/architecture/concurrency.md` ("Known limitations") and called out in
# parallel_for's docstring; a code-review-time check is sufficient.
