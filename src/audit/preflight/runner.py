"""Stage-1a orchestrator.

Dispatches the 8 check modules in parallel against a single prospect domain,
collects their structured results, and returns a `PreflightResult` that
downstream agents read as context.

Runtime expectations:

- Wall-clock budget: 10-30s total (dominated by HTTP fetches; DNS is fast).
- Cost: effectively $0 (no LLM calls; DNS + ~15 HTTP requests).
- Failure mode: skip-not-raise. Individual check failures are recorded in
  `result.failures` and do not block the aggregate result from returning.
  Downstream agents treat missing signal as "unknown", not "absent".
- Idempotency: safe to re-run on the same domain (no side effects beyond
  network I/O). Caller handles caching at `clients/<slug>/audit/cache/` level.

Not in this scaffold:

- No actual DNS / HTTP requests. Each check module is a stub that returns
  `{"implemented": False}`.
- No retries, no per-check timeouts, no circuit breakers. Those land when
  real I/O does.
- No Slack telemetry / events.jsonl. Those live in `src/audit/telemetry.py`
  (also unbuilt).

The shape here is the architectural proposal — review before filling in the
check bodies.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Awaitable, Callable, Protocol

from . import checks


# ── Types ─────────────────────────────────────────────────────────────────
class CheckFunction(Protocol):
    """Signature every preflight check module must implement."""

    async def __call__(self, domain: str, /) -> dict: ...


@dataclass(frozen=True, slots=True)
class PreflightConfig:
    """Input to `run()`. All fields have defaults appropriate for v1 dogfood."""

    # Per-check wall-clock ceiling. Individual checks exceeding this are
    # recorded as failures rather than hanging the run.
    per_check_timeout_s: float = 15.0

    # Total wall-clock ceiling. Exceeding this cancels remaining checks.
    total_timeout_s: float = 60.0

    # Which checks to run. Default is all 8. Pass a subset for debugging.
    enabled: frozenset[str] = frozenset({
        "dns", "wellknown", "schema", "badges",
        "headers", "social", "assets", "tooling",
    })


@dataclass(slots=True)
class PreflightResult:
    """Aggregate output. `signals` maps check_name → structured signal dict.
    `failures` maps check_name → error string for checks that raised."""

    domain: str
    started_at: float
    elapsed_s: float
    signals: dict[str, dict] = field(default_factory=dict)
    failures: dict[str, str] = field(default_factory=dict)

    @property
    def ok_count(self) -> int:
        return len(self.signals)

    @property
    def failure_count(self) -> int:
        return len(self.failures)


# ── Dispatch table ────────────────────────────────────────────────────────
# Each entry: (name, module.check). Adding a 9th check = append one line.
_CHECKS: dict[str, CheckFunction] = {
    "dns":       checks.dns.check,
    "wellknown": checks.wellknown.check,
    "schema":    checks.schema.check,
    "badges":    checks.badges.check,
    "headers":   checks.headers.check,
    "social":    checks.social.check,
    "assets":    checks.assets.check,
    "tooling":   checks.tooling.check,
}


# ── Runner ────────────────────────────────────────────────────────────────
async def _invoke(name: str, fn: CheckFunction, domain: str, timeout_s: float) -> tuple[str, dict | Exception]:
    """Run one check with an individual timeout. Returns (name, result_or_error)."""
    try:
        async with asyncio.timeout(timeout_s):
            result = await fn(domain)
            return name, result
    except asyncio.TimeoutError:
        return name, TimeoutError(f"{name} exceeded {timeout_s}s")
    except Exception as exc:
        return name, exc


async def run(domain: str, *, config: PreflightConfig | None = None) -> PreflightResult:
    """Fan out enabled checks in parallel, aggregate signals, return result.

    Raises only on the total_timeout_s cancel — individual check failures
    populate `result.failures` and never propagate.
    """
    cfg = config or PreflightConfig()
    started = time.monotonic()

    tasks = [
        _invoke(name, fn, domain, cfg.per_check_timeout_s)
        for name, fn in _CHECKS.items()
        if name in cfg.enabled
    ]

    async with asyncio.timeout(cfg.total_timeout_s):
        outcomes = await asyncio.gather(*tasks)

    result = PreflightResult(domain=domain, started_at=started, elapsed_s=0.0)
    for name, outcome in outcomes:
        if isinstance(outcome, Exception):
            result.failures[name] = f"{type(outcome).__name__}: {outcome}"
        else:
            result.signals[name] = outcome
    result.elapsed_s = time.monotonic() - started
    return result
