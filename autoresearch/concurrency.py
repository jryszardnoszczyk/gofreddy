"""Central concurrency controller — provider semaphores + parallel_for helper.

One singleton owns per-resource semaphores (claude, codex, opencode, judge_http,
cloro_search). ``parallel_for`` runs N independent items concurrently, acquiring
the named semaphore inside each worker so global quotas are honored across
lanes, finalists, critic domains, and fixture fan-out.

Env vars:
    AUTORESEARCH_CONCURRENCY=serial         — degrade every parallel_for to a for loop
    AUTORESEARCH_CONCURRENCY_CLAUDE=4       — cap concurrent Claude calls   (default 4)
    AUTORESEARCH_CONCURRENCY_CODEX=2        — cap concurrent Codex calls    (default 2)
    AUTORESEARCH_CONCURRENCY_OPENCODE=8     — cap concurrent OpenCode calls (default 8)
    AUTORESEARCH_CONCURRENCY_JUDGE_HTTP=10  — cap concurrent judge HTTP     (default 10)
    AUTORESEARCH_CONCURRENCY_CLORO_SEARCH=2 — cap concurrent cloro search   (default 2)
    AUTORESEARCH_CONCURRENCY_TRACE=1        — log per-worker timing to stderr

Public API:
    controller()                  — singleton accessor
    parallel_for(items, fn, res)  — concurrent iteration
    reset_for_test()              — drop singleton (test hook)
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

_DEFAULTS: dict[str, int] = {
    "claude": 4,
    "codex": 2,
    "opencode": 8,
    "judge_http": 10,
    "cloro_search": 2,
}


@dataclass
class ConcurrencyController:
    semaphores: dict[str, threading.Semaphore]
    serial_mode: bool
    trace: bool

    def acquire(self, resource: str) -> threading.Semaphore:
        if resource not in self.semaphores:
            raise ValueError(
                f"Unknown resource: {resource!r}. Known: {sorted(self.semaphores)}"
            )
        return self.semaphores[resource]


_BUILD_LOCK = threading.Lock()
_INSTANCE: ConcurrencyController | None = None


def controller() -> ConcurrencyController:
    global _INSTANCE
    if _INSTANCE is not None:
        return _INSTANCE
    with _BUILD_LOCK:
        if _INSTANCE is None:
            _INSTANCE = _build_from_env()
    return _INSTANCE


def _build_from_env() -> ConcurrencyController:
    sems: dict[str, threading.Semaphore] = {}
    for name, default in _DEFAULTS.items():
        cap_env = os.environ.get(f"AUTORESEARCH_CONCURRENCY_{name.upper()}")
        cap = int(cap_env) if cap_env else default
        if cap < 1:
            raise ValueError(
                f"AUTORESEARCH_CONCURRENCY_{name.upper()} must be >= 1, got {cap}"
            )
        sems[name] = threading.Semaphore(cap)
    return ConcurrencyController(
        semaphores=sems,
        serial_mode=(os.environ.get("AUTORESEARCH_CONCURRENCY") == "serial"),
        trace=(os.environ.get("AUTORESEARCH_CONCURRENCY_TRACE") == "1"),
    )


def reset_for_test() -> None:
    """Clear the singleton so subsequent tests rebuild from env."""
    global _INSTANCE
    with _BUILD_LOCK:
        _INSTANCE = None


def parallel_for(
    items: Iterable[T],
    work_fn: Callable[[T], R],
    resource: str,
    *,
    max_workers: int | None = None,
) -> list[R]:
    """Run ``work_fn(item)`` for each item concurrently, gated by ``resource``.

    Returns results in input order. Propagates the first exception (matches the
    serial-loop semantics it replaces) after cancelling siblings where possible.

    If ``AUTORESEARCH_CONCURRENCY=serial``, runs items in a plain for loop on
    the calling thread — no executor, no semaphore overhead — for debugging.
    """
    items_list = list(items)
    if not items_list:
        return []

    ctl = controller()
    if ctl.serial_mode:
        return [work_fn(item) for item in items_list]

    sem = ctl.acquire(resource)
    workers = max_workers if max_workers is not None else max(len(items_list), 1)

    def _gated(item: T) -> R:
        with sem:
            t0 = time.monotonic()
            try:
                return work_fn(item)
            finally:
                if ctl.trace:
                    print(
                        f"  parallel_for[{resource}] item={item!r} "
                        f"dt={time.monotonic() - t0:.2f}s",
                        file=sys.stderr,
                    )

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
