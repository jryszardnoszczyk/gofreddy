"""Single-semaphore concurrency controller.

Per Plan B U9 + audit §14 (docs/research/2026-05-11-001): collapsed from
5 per-resource semaphores (claude / codex / opencode / judge_http /
cloro_search) to a single MAX_PARALLEL_AGENTS sem. The per-resource
shape was over-engineered — the only catch in production was Claude
Max throttling at high concurrency, which a single global cap of 4
prevents just as well.

Env vars:
    AUTORESEARCH_CONCURRENCY=serial         — degrade every parallel_for to a for loop
    MAX_PARALLEL_AGENTS=4                   — global concurrency cap (default 4)
    AUTORESEARCH_CONCURRENCY_TRACE=1        — log per-worker timing to stderr

Public API (signature-stable for callers — ``resource=`` arg is accepted
but ignored):
    controller()                  — singleton accessor
    parallel_for(items, fn, res)  — concurrent iteration
    _reset_for_test()             — drop singleton (test hook)
"""

from __future__ import annotations

import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Callable, Iterable, TypeVar

T = TypeVar("T")
R = TypeVar("R")

_DEFAULT_MAX = 4


@dataclass
class ConcurrencyController:
    sem: threading.Semaphore
    serial_mode: bool
    trace: bool


_BUILD_LOCK = threading.Lock()
_INSTANCE: ConcurrencyController | None = None
_TRACE_LOCK = threading.Lock()


def controller() -> ConcurrencyController:
    global _INSTANCE
    if _INSTANCE is not None:
        return _INSTANCE
    with _BUILD_LOCK:
        if _INSTANCE is None:
            _INSTANCE = _build_from_env()
    return _INSTANCE


def _build_from_env() -> ConcurrencyController:
    cap_env = os.environ.get("MAX_PARALLEL_AGENTS")
    if cap_env:
        try:
            cap = int(cap_env)
        except ValueError as exc:
            raise ValueError(
                f"MAX_PARALLEL_AGENTS must be a positive integer, got {cap_env!r}"
            ) from exc
    else:
        cap = _DEFAULT_MAX
    if cap < 1:
        raise ValueError(f"MAX_PARALLEL_AGENTS must be >= 1, got {cap}")
    return ConcurrencyController(
        sem=threading.Semaphore(cap),
        serial_mode=(os.environ.get("AUTORESEARCH_CONCURRENCY") == "serial"),
        trace=(os.environ.get("AUTORESEARCH_CONCURRENCY_TRACE") == "1"),
    )


def _reset_for_test() -> None:
    """Test-only: drop singleton so subsequent tests rebuild from env."""
    global _INSTANCE
    with _BUILD_LOCK:
        _INSTANCE = None


def parallel_for(
    items: Iterable[T],
    work_fn: Callable[[T], R],
    resource: str | None = None,
    *,
    max_workers: int | None = None,
) -> list[R]:
    """Run ``work_fn(item)`` for each item concurrently, gated by the global sem.

    The ``resource`` arg is accepted for backward compatibility with the
    per-resource sem era but ignored — every call shares MAX_PARALLEL_AGENTS.
    """
    ctl = controller()
    items_list = list(items)
    if not items_list:
        return []

    if ctl.serial_mode:
        return [work_fn(item) for item in items_list]

    workers = max_workers if max_workers is not None else max(len(items_list), 1)

    def _gated(item: T) -> R:
        with ctl.sem:
            t0 = time.monotonic()
            try:
                return work_fn(item)
            finally:
                if ctl.trace:
                    line = (
                        f"  parallel_for item={item!r} "
                        f"dt={time.monotonic() - t0:.2f}s\n"
                    )
                    with _TRACE_LOCK:
                        sys.stderr.write(line)
                        sys.stderr.flush()

    results: list[R | None] = [None] * len(items_list)
    first_exc: BaseException | None = None
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_idx = {
            executor.submit(_gated, item): idx
            for idx, item in enumerate(items_list)
        }
        for fut in as_completed(future_to_idx):
            idx = future_to_idx[fut]
            try:
                results[idx] = fut.result()
            except BaseException as exc:  # noqa: BLE001
                if first_exc is None:
                    first_exc = exc
                    for other in future_to_idx:
                        if other is not fut:
                            other.cancel()
    if first_exc is not None:
        raise first_exc
    return results  # type: ignore[return-value]
