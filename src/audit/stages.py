"""Audit pipeline stage entry points.

L1 (Foundation) ships **stub-shaped stages** wired enough for the
preflight runner to be reachable from a production code path. Full
stage logic lands in L3 (Phase 2 — Stage pipeline + agents) per
master plan §7.2 + §7.4.

F8 self-review (master plan §7.2) acknowledges that
``stage_1_warmup`` is half-wired in L1 — the preflight runner is
invoked, but the full Stage 1a behavior (asyncio.Semaphore(12) over
~17 Tier-1 providers, cache_or_call wrapping, RenderedFetcher
homepage seed) is L3 work that depends on the Phase 1.5 provider
build.

This module is the architectural anchor: stages.py exists, exposes
``stage_1_warmup``, and the preflight runner is callable through it.
That's all L1 needs to satisfy work-item #4 in §7.2.
"""
from __future__ import annotations

from pathlib import Path

from src.audit.preflight import runner as preflight_runner
from src.audit.preflight.runner import PreflightConfig, PreflightResult
from src.audit.state import AuditStateFile


async def stage_1_warmup(
    state_file: AuditStateFile,
    *,
    preflight_config: PreflightConfig | None = None,
) -> PreflightResult:
    """Stage 1a — cache warmup + preflight signal capture.

    L1 implementation: invokes the preflight runner against
    ``state.prospect_domain`` and returns the aggregated
    ``PreflightResult``. Tier-1 provider fan-out (DataForSEO + Cloro
    + 12 monitoring adapters + Wappalyzer + Playwright homepage
    fetch) lands in L3 once the cache layer + Wappalyzer-next port
    + RenderedFetcher exist (master plan §3.4 + §4.4 + §4.5).

    The L3 implementation will:
    1. Run the preflight runner concurrently with provider fan-out
       under a single ``asyncio.gather`` + ``Semaphore(12)`` per
       master plan §3.4
    2. Wrap each provider call through ``tools/cache.cache_or_call``
       so re-runs are bit-identical to first-runs
    3. Persist per-tool cache files under
       ``clients/<slug>/audit/cache/<tool>_<sha256>.json``

    Until then, callers receive a ``PreflightResult`` covering the
    8 preflight checks only.
    """
    state = state_file.load()
    return await preflight_runner.run(state.prospect_domain, config=preflight_config)


__all__ = [
    "stage_1_warmup",
]
