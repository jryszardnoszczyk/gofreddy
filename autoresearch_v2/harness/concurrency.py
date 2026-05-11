"""Concurrency — one global semaphore via MAX_PARALLEL_AGENTS.

Replaces v1's 5-per-resource ConcurrencyController (182 LOC). Per Plan B,
the per-resource semaphores were YAGNI; one mutex is enough for the
sequential-by-default v2 loop. JR dials up via env var if needed.

Usage:
    from autoresearch_v2.harness.concurrency import semaphore, parallel_for

    with semaphore():
        run_one_thing()

    parallel_for(items, fn)   # respects MAX_PARALLEL_AGENTS
"""

from __future__ import annotations

import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Iterable, TypeVar

T = TypeVar("T")
R = TypeVar("R")


def max_parallel() -> int:
    """Read MAX_PARALLEL_AGENTS env var. Default 1 (sequential)."""
    raw = os.environ.get("MAX_PARALLEL_AGENTS", "1").strip()
    try:
        value = int(raw)
    except ValueError:
        return 1
    return max(1, value)


_LOCK = threading.Lock()
_SEMAPHORE: threading.BoundedSemaphore | None = None
_SEM_CAP: int | None = None


def semaphore() -> threading.BoundedSemaphore:
    """Return the global semaphore (rebuilds if MAX_PARALLEL_AGENTS changed)."""
    global _SEMAPHORE, _SEM_CAP
    current = max_parallel()
    with _LOCK:
        if _SEMAPHORE is None or _SEM_CAP != current:
            _SEMAPHORE = threading.BoundedSemaphore(current)
            _SEM_CAP = current
    return _SEMAPHORE


def parallel_for(items: Iterable[T], fn: Callable[[T], R]) -> list[R]:
    """Run fn(item) for each item, with concurrency capped by MAX_PARALLEL_AGENTS."""
    item_list = list(items)
    cap = max_parallel()
    if cap == 1 or len(item_list) <= 1:
        return [fn(item) for item in item_list]

    sem = semaphore()

    def _worker(item: T) -> R:
        with sem:
            return fn(item)

    results: list[R] = [None] * len(item_list)  # type: ignore
    with ThreadPoolExecutor(max_workers=cap) as ex:
        future_to_idx = {ex.submit(_worker, item): i for i, item in enumerate(item_list)}
        for future in as_completed(future_to_idx):
            results[future_to_idx[future]] = future.result()
    return results


def reset_for_test() -> None:
    """Drop the cached semaphore (lets tests vary MAX_PARALLEL_AGENTS)."""
    global _SEMAPHORE, _SEM_CAP
    with _LOCK:
        _SEMAPHORE = None
        _SEM_CAP = None
