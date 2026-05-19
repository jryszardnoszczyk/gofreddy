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
    FAL_IMAGE_MAX_CONCURRENCY=2             — per-account fal.ai cap (D23, U14)

Public API (signature-stable for callers — ``resource=`` arg is accepted
but ignored):
    controller()                  — singleton accessor
    parallel_for(items, fn, res)  — concurrent iteration
    fal_image_semaphore()         — fal.ai per-account semaphore (D23, U14)
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
    global _INSTANCE, _FAL_IMAGE_SEM
    with _BUILD_LOCK:
        _INSTANCE = None
    with _FAL_IMAGE_LOCK:
        _FAL_IMAGE_SEM = None


# fal.ai per-account concurrency semaphore (D23, U14). Separate from the
# global MAX_PARALLEL_AGENTS sem because fal.ai's account-level rate
# limits trip well before MAX_PARALLEL_AGENTS=4 — a 5-slide carousel
# fanned out via parallel_for could blast through fal's per-account cap
# even when the global agent count is 1. Default 2 matches fal's typical
# free-tier shape; operators bump via FAL_IMAGE_MAX_CONCURRENCY when on a
# paid plan with higher headroom.
_FAL_IMAGE_LOCK = threading.Lock()
_FAL_IMAGE_SEM: threading.Semaphore | None = None
_FAL_IMAGE_DEFAULT_MAX = 2


def fal_image_semaphore() -> threading.Semaphore:
    """Lazy-init singleton semaphore for fal.ai image generation calls.

    Image_engine workflow wraps each `FalPlatformClient.generate_image`
    call with `with fal_image_semaphore(): ...`. Sized from
    `FAL_IMAGE_MAX_CONCURRENCY` env var; default 2.
    """
    global _FAL_IMAGE_SEM
    if _FAL_IMAGE_SEM is not None:
        return _FAL_IMAGE_SEM
    with _FAL_IMAGE_LOCK:
        if _FAL_IMAGE_SEM is None:
            cap_env = os.environ.get("FAL_IMAGE_MAX_CONCURRENCY")
            if cap_env:
                try:
                    cap = int(cap_env)
                except ValueError as exc:
                    raise ValueError(
                        f"FAL_IMAGE_MAX_CONCURRENCY must be a positive "
                        f"integer, got {cap_env!r}"
                    ) from exc
            else:
                cap = _FAL_IMAGE_DEFAULT_MAX
            if cap < 1:
                raise ValueError(
                    f"FAL_IMAGE_MAX_CONCURRENCY must be >= 1, got {cap}"
                )
            _FAL_IMAGE_SEM = threading.Semaphore(cap)
    return _FAL_IMAGE_SEM


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
