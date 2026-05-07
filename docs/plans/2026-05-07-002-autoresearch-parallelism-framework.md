---
title: "feat: Autoresearch parallelism framework (Phase 1 — central ConcurrencyController + 3 loop conversions + provider semaphores)"
type: feat
status: ready
date: 2026-05-07
supersedes: []
related:
  - docs/plans/2026-04-27-002-feat-autoresearch-lane-registry-plan.md  # extends LaneSpec ergonomics
  - docs/plans/2026-05-07-001-x-engine-autoresearch-port-master-plan.md  # lane onboarding inherits this
---

# feat: Autoresearch parallelism framework (Phase 1)

> **Why this plan exists:** Today autoresearch has exactly two `ThreadPoolExecutor` call sites (both inside `evaluate_variant.py`, both fan out fixtures within one variant) and three hand-rolled `for` loops doing the rest of the orchestration serially: lanes, holdout finalists, critic domains. Every new lane (X-engine, marketing-audit) inherits the serial loops by default. Provider quotas (Codex CLI ~5–10 RPM in particular) are a global resource that today's parallelism can already trample if anyone wires a third `ThreadPoolExecutor` without coordination. This plan adds **one** module — `autoresearch/concurrency.py` — that owns provider semaphores and a `parallel_for` helper, then converts the three serial loops to use it. New lanes inherit cross-lane + finalist + critic-domain parallelism by registering a `LaneSpec`; nothing else.

## Overview

Add a central `ConcurrencyController` (module-level singleton in `autoresearch/concurrency.py`) that exposes:
- **Per-resource semaphores** keyed by provider/service: `claude`, `codex`, `opencode`, `judge_http`, `cloro_search`. Caps come from env vars with conservative defaults.
- **A `parallel_for(items, work_fn, resource)` helper** that wraps `ThreadPoolExecutor` and acquires the named semaphore inside `work_fn` so global quota is honored across lanes and variants.
- **A global kill switch** `AUTORESEARCH_CONCURRENCY=serial` that forces every `parallel_for` to degrade to a plain `for` loop (debugging escape hatch).

Then convert the three serial loops:
1. `evolve.py:run_all_lanes` — `for lane in all_lane_names()` → `parallel_for(lanes, ...)` with `claude` semaphore.
2. `evolve.py:1755` finalists loop — `for finalist_id in finalists:` → `parallel_for(finalists, ...)` with `judge_http` semaphore.
3. `program_prescription_critic.py:571` — `for domain in domains:` → `parallel_for(domains, ...)` with `claude` semaphore.

Add a **lineage append lock** (`threading.Lock` in `evolve_ops.py`) wrapping `mark_promoted()` + `set_current_head()`; required before parallel finalists are safe.

Replace the two raw `ThreadPoolExecutor` blocks in `evaluate_variant.py` with `parallel_for` calls so fixture fan-out also acquires provider semaphores.

**No `ParallelismProfile` field on `LaneSpec`.** Phase 2 adds that if and only if a real lane needs lane-specific concurrency tuning. Phase 1 ships a single global default that covers all 4 lanes today.

**No variant-pipelining inside a lane.** That's medium-risk (baseline-freshness gate) and ships in a separate plan.

## Problem Frame

The orchestration layer (`autoresearch/`) has two `ThreadPoolExecutor` call sites in production code:

- `evaluate_variant.py:2004` — holdout fixture fan-out (per-variant, internal)
- `evaluate_variant.py:2612` — search fixture fan-out (per-variant, internal)

Both are bare `ThreadPoolExecutor(max_workers=len(all_fixtures))` with no awareness of provider quotas. Outside of these, every other orchestration loop is serial:

- `evolve.py:990` — lanes one-at-a-time inside `run_all_lanes()`
- `evolve.py:1755` — holdout finalists one-at-a-time
- `program_prescription_critic.py:571` — critic domains one-at-a-time
- `evolve.py:2170` — variants one-at-a-time inside the generation loop (out of scope here; see "What This Plan Does NOT Build")

Adding parallelism per-site means each new contributor:
1. Re-implements `ThreadPoolExecutor` boilerplate
2. Picks a `max_workers` value with no knowledge of what other parts of the system are doing concurrently
3. Has no tool for honoring provider quotas (Codex CLI ceiling is the binding constraint)

This plan collapses all three concerns into one module: `parallel_for(items, work_fn, resource="claude")` is the entire surface a future lane author needs.

## Requirements Trace

- **R1.** Adding a new lane (X-engine, marketing-audit, future) inherits cross-lane + critic-domain + finalist parallelism by registering a `LaneSpec`. No concurrency code in the lane's own modules.
- **R2.** Provider quotas honored globally — at most N concurrent Codex CLI calls across all lanes and variants, regardless of how many `parallel_for` calls are in flight.
- **R3.** Existing fixture fan-out (`evaluate_variant.py:2004,2612`) routed through the same controller so its workers also count against the provider semaphore.
- **R4.** Lineage append (`evolve_ops.mark_promoted`) is concurrency-safe.
- **R5.** Single env var (`AUTORESEARCH_CONCURRENCY=serial`) reverts the entire system to today's serial behavior for debugging.
- **R6.** Per-resource caps tunable via env vars without code changes (`AUTORESEARCH_CONCURRENCY_CODEX=2` etc.).
- **R7.** No new abstractions beyond `threading.Semaphore` + `ThreadPoolExecutor` + module-level state. No asyncio migration. No plugin/protocol classes.

## Scope Boundaries

**In scope:**
- `autoresearch/concurrency.py` (new): `ConcurrencyController` singleton + `parallel_for` helper.
- Three loop conversions: `evolve.py:run_all_lanes`, `evolve.py:1755`, `program_prescription_critic.py:571`.
- Lineage append lock in `evolve_ops.py`.
- Convert two existing `ThreadPoolExecutor` call sites in `evaluate_variant.py` to `parallel_for`.
- New tests under `tests/autoresearch/test_concurrency.py`.

**Out of scope:**
- Phase 2: `ParallelismProfile` field on `LaneSpec` (lane-specific tuning). Defer until a lane needs different caps.
- Variant pipelining within a lane (`evolve.py:2170`) — needs a baseline-freshness gate; separate plan.
- Draft-level parallelism inside a fixture session (`harness/agent.py`) — agent-internal, ordering-sensitive.
- Search-provider quota wrappers beyond `cloro_search` semaphore (freddy-search rate-limiting separate work).
- Async migration. The codebase uses threading; nothing here changes that.
- Auto-tuning caps from observed throughput. Caps are env vars; operator dials them.
- Backpressure / queueing on top of semaphores. Bare `acquire()` blocks; that's the whole policy.

## Context & Research

### Relevant Code and Patterns

**Existing concurrency primitives in production code (full list):**
- `autoresearch/evaluate_variant.py:23` — import.
- `autoresearch/evaluate_variant.py:2004` — `with ThreadPoolExecutor(max_workers=len(all_fixtures)) as executor:` (holdout).
- `autoresearch/evaluate_variant.py:2612` — same pattern (search).
- `autoresearch/sessions.py:11` — comment noting `ThreadPoolExecutor` writers; uses `threading.Lock` around `.session_ids.json`.

That is the entire concurrency surface in `autoresearch/` today. (Snapshots under `autoresearch/archive/v00X/run.py` are per-variant frozen copies; not orchestration code.)

**Three serial loops to convert:**
- `autoresearch/evolve.py:990` (`run_all_lanes`) — `for lane in all_lane_names(): ... command_func(lane_config)`.
- `autoresearch/evolve.py:1755` — `for finalist_id in finalists: _run_holdout(config, ...)`.
- `autoresearch/program_prescription_critic.py:571` — `for domain in domains: critique_program(domain, ...)`.

**Lineage hot path (lock target):**
- `autoresearch/evolve_ops.py:720-731` — `current_lineage()` reads + `mark_promoted()` appends. Read-modify-write; clobbers under concurrent writers.
- `autoresearch/evolve_ops.py:188-192` — `set_current_head()` writes `archive/current.json`. Same race profile.

**Existing retry plumbing (do not touch):**
- `autoresearch/agent_retry.py` — 3 attempts, 2/8/30s backoff for Claude/Codex/OpenCode subprocess failures.
- `autoresearch/evaluate_variant.py:_invoke_judge_with_retry` — 3 attempts, 600s shared budget for judge HTTP.

Semaphores compose with retries: a worker holds the semaphore across retry attempts. Acceptable because retry latency is bounded (max 30s + judge timeout). If this becomes a problem in practice, Phase 2 adds release-on-retry; not Phase 1.

**Observed quota signals (from memory + recent runs):**
- Codex CLI: tightest constraint, ~5–10 RPM observed during evaluation. Saturates first.
- Claude (Anthropic Pro/Max): ~100 RPM soft, well under for a few concurrent meta-agent calls.
- OpenCode → DeepSeek via OpenRouter: 100–500 RPM aggregate, ample headroom; transient retry already wired in `harness/opencode_jsonl.py`.
- Judge HTTP service: deployment-dependent; conservative cap until measured.
- Cloro search: ~100 calls/week per API key — strict; semaphore = 2 prevents stampede.

### Institutional Learnings

- **2026-05-07 audit (memory `project-autoresearch-evolution-fixes-pending.md`):** Three production bugs surfaced under increased load: (a) `7788ce3` 0444 perm leak in `sync_variant_workspace`; (b) `d175aed` `MAX_GENERATION_SECONDS` 7200→21600 default; (c) `a96eff2` inner-critique subprocess `AUTORESEARCH_REPO_ROOT` env var. All three would have been worse with concurrent variant runs sharing workspace state — reinforces the rule that workspace-permission and subprocess-env races must be sealed before parallelism is enabled.
- **Lane registry precedent (`docs/plans/2026-04-27-002`):** "Simplest thing that works" beat the substrate-plugin variant. Same heuristic applies here: one module, one helper, one lock — not a plugin architecture for parallelism profiles.
- **Pressure-test memory (`feedback-pressure-test-overconfidence.md`):** caps must be empirical. Defaults are conservative; operator dials up after measuring.

## Key Technical Decisions

- **D1. Threading, not asyncio.** Existing codebase uses `ThreadPoolExecutor`. Migrating to asyncio is a separate, larger project. Threads + semaphores compose with the existing subprocess-based retry helpers without changing call signatures.
- **D2. Module-level singleton semaphores.** A `ConcurrencyController` instance is constructed once at import and exposed via `controller()`. Required so semaphores are shared across `parallel_for` calls in different modules. Tests reset it via `reset_for_test()`.
- **D3. `parallel_for` acquires inside the worker, not outside.** Submitting N futures and acquiring per-worker means the executor's `max_workers` can be set higher than the semaphore cap; the semaphore enforces actual concurrency. This avoids the "semaphore = max_workers" anti-pattern where blocked workers occupy executor slots.
- **D4. Default caps (subject to empirical tuning):** `claude=4`, `codex=2`, `opencode=8`, `judge_http=10`, `cloro_search=2`. All overridable via `AUTORESEARCH_CONCURRENCY_<RESOURCE>` env vars. Document defaults in `concurrency.py` docstring.
- **D5. `AUTORESEARCH_CONCURRENCY=serial` short-circuits.** When set, `parallel_for` runs items in a plain `for` loop on the calling thread. Required for debugging non-deterministic failures.
- **D6. Lineage lock is module-level in `evolve_ops.py`.** Wraps `mark_promoted` + `set_current_head` as a single critical section (the two writes are logically one promotion event). Test asserts no clobbering under concurrent writers.
- **D7. Resource key for `run_all_lanes` is `claude`.** Lanes overlap mostly in proposer + critic stages (Claude). Search/judge stages have their own semaphores (`opencode`/`codex` for sessions, `judge_http` for scoring), acquired deeper in the call stack. Cross-lane parallelism is bounded by the union.
- **D8. Resource key for finalists loop is `judge_http`.** Holdout finalize is dominated by judge service calls; finalists run concurrently up to judge cap.
- **D9. Resource key for critic domains is `claude`.** Each `critique_program` call is a Claude subprocess.
- **D10. `parallel_for` propagates the first exception** (matches today's `for`-loop semantics: first failure stops processing). Other in-flight workers are cancelled if possible. Logs all exceptions before raising.
- **D11. No release-on-retry in Phase 1.** Worker holds semaphore across retry attempts. Retry latency is bounded; over-conservative but simple. Revisit if measurements show wasted slots.

## Open Questions

### Resolved During Planning

- **Q. Should we measure quotas before setting defaults?**
  Resolved: ship conservative defaults, document operator workflow for dial-up. Empirical measurement script can be a follow-up — blocking on it is YAGNI.

- **Q. Asyncio vs threading?**
  Resolved (D1): threading. The retry helpers and subprocess plumbing assume blocking calls; asyncio migration is its own project.

- **Q. Should every Anthropic call go through one semaphore or split (proposer vs critic)?**
  Resolved: one `claude` semaphore. Proposer + critic share quota in reality; splitting them creates false isolation. If contention becomes visible, Phase 2 splits via `ParallelismProfile`.

### Deferred to Implementation

- **Q1. Should `EVOLUTION_PARENT_ID` be lane-scoped to avoid cross-lane parallelism races during peak overlap?**
  Currently lane-global. Cross-lane `run_all_lanes` parallelism reads it inside per-lane `command_func(lane_config)` after `dataclasses.replace(config, lane=lane)`, so lanes get their own config copies. Verify during Unit 2 that no shared mutable state escapes the `lane_config` copy. If it does, scope `EVOLUTION_PARENT_ID` per-lane via `os.environ` or a thread-local.

- **Q2. Default for `judge_http` cap.**
  Stub at `10`. Real cap depends on judge service deployment topology. Surface as the first env var to dial in operations.

- **Q3. Should `parallel_for` log per-worker timing?**
  Useful for empirical cap tuning. Default off; flip on via `AUTORESEARCH_CONCURRENCY_TRACE=1`. Cheap to add.

## High-Level Technical Design

### `autoresearch/concurrency.py` API

```python
"""Central concurrency controller — provider semaphores + parallel_for helper.

One singleton owns per-resource semaphores (claude, codex, opencode, judge_http,
cloro_search). `parallel_for` runs N independent items concurrently, acquiring
the named semaphore inside each worker so global quotas are honored.

Env vars:
- AUTORESEARCH_CONCURRENCY=serial       → degrade every parallel_for to a for loop
- AUTORESEARCH_CONCURRENCY_CLAUDE=4     → cap concurrent Claude calls (default 4)
- AUTORESEARCH_CONCURRENCY_CODEX=2      → cap concurrent Codex calls   (default 2)
- AUTORESEARCH_CONCURRENCY_OPENCODE=8   → cap concurrent OpenCode      (default 8)
- AUTORESEARCH_CONCURRENCY_JUDGE_HTTP=10
- AUTORESEARCH_CONCURRENCY_CLORO_SEARCH=2
- AUTORESEARCH_CONCURRENCY_TRACE=1      → log per-worker timing
"""

from __future__ import annotations
import os, sys, threading, time
from concurrent.futures import ThreadPoolExecutor, as_completed, FIRST_EXCEPTION, wait
from dataclasses import dataclass
from typing import Callable, Iterable, TypeVar

T = TypeVar("T")
R = TypeVar("R")

_DEFAULTS = {
    "claude":        4,
    "codex":         2,
    "opencode":      8,
    "judge_http":   10,
    "cloro_search":  2,
}

@dataclass
class ConcurrencyController:
    semaphores: dict[str, threading.Semaphore]
    serial_mode: bool
    trace: bool

    def acquire(self, resource: str) -> threading.Semaphore:
        if resource not in self.semaphores:
            raise ValueError(f"Unknown resource: {resource!r}. Known: {sorted(self.semaphores)}")
        return self.semaphores[resource]


_LOCK = threading.Lock()
_INSTANCE: ConcurrencyController | None = None

def controller() -> ConcurrencyController:
    global _INSTANCE
    if _INSTANCE is not None:
        return _INSTANCE
    with _LOCK:
        if _INSTANCE is None:
            _INSTANCE = _build_from_env()
    return _INSTANCE

def _build_from_env() -> ConcurrencyController:
    sems = {}
    for name, default in _DEFAULTS.items():
        cap_env = os.environ.get(f"AUTORESEARCH_CONCURRENCY_{name.upper()}")
        cap = int(cap_env) if cap_env else default
        if cap < 1:
            raise ValueError(f"AUTORESEARCH_CONCURRENCY_{name.upper()} must be >= 1, got {cap}")
        sems[name] = threading.Semaphore(cap)
    return ConcurrencyController(
        semaphores=sems,
        serial_mode=(os.environ.get("AUTORESEARCH_CONCURRENCY") == "serial"),
        trace=(os.environ.get("AUTORESEARCH_CONCURRENCY_TRACE") == "1"),
    )

def reset_for_test() -> None:
    """Clear singleton so tests can rebuild from env."""
    global _INSTANCE
    with _LOCK:
        _INSTANCE = None


def parallel_for(
    items: Iterable[T],
    work_fn: Callable[[T], R],
    resource: str,
    *,
    max_workers: int | None = None,
) -> list[R]:
    """Run work_fn(item) for each item concurrently, gated by `resource` semaphore.

    Returns results in input order. Propagates the first exception (matches
    today's serial-loop semantics) after cancelling siblings where possible.

    If AUTORESEARCH_CONCURRENCY=serial, runs items in a plain for loop on the
    calling thread (no executor, no semaphore overhead). Required for debugging.
    """
    items = list(items)
    if not items:
        return []

    ctl = controller()
    if ctl.serial_mode:
        return [work_fn(item) for item in items]

    sem = ctl.acquire(resource)
    workers = max_workers or max(len(items), 1)

    def _gated(item: T) -> R:
        with sem:
            t0 = time.monotonic()
            try:
                return work_fn(item)
            finally:
                if ctl.trace:
                    print(f"  parallel_for[{resource}] item={item!r} dt={time.monotonic()-t0:.2f}s",
                          file=sys.stderr)

    results: list[R | None] = [None] * len(items)
    exc: BaseException | None = None
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_idx = {executor.submit(_gated, item): i for i, item in enumerate(items)}
        for fut in as_completed(future_to_idx):
            i = future_to_idx[fut]
            try:
                results[i] = fut.result()
            except BaseException as e:  # noqa: BLE001
                if exc is None:
                    exc = e
                    for other in future_to_idx:
                        if other is not fut:
                            other.cancel()
    if exc is not None:
        raise exc
    return results  # type: ignore[return-value]
```

### Three loop conversions

**`evolve.py:run_all_lanes` (lines 990–1006):**

```python
# BEFORE
def run_all_lanes(config: EvolutionConfig, command_func) -> None:
    for lane in all_lane_names():
        print(f"=== Running lane={lane} ===")
        try:
            lane_config = dataclasses.replace(config, lane=lane)
            _init_lane_config(lane_config)
            preflight_checks(lane_config)
            command_func(lane_config)
        except Exception as exc:
            print(f"ERROR: lane={lane} failed: {exc}", file=sys.stderr)
            continue

# AFTER
from autoresearch.concurrency import parallel_for

def run_all_lanes(config: EvolutionConfig, command_func) -> None:
    def _run_one(lane: str) -> None:
        print(f"=== Running lane={lane} ===")
        try:
            lane_config = dataclasses.replace(config, lane=lane)
            _init_lane_config(lane_config)
            preflight_checks(lane_config)
            command_func(lane_config)
        except Exception as exc:
            print(f"ERROR: lane={lane} failed: {exc}", file=sys.stderr)
    parallel_for(all_lane_names(), _run_one, resource="claude")
```

Note: the original swallows lane errors via `continue`. Preserved by catching inside `_run_one`. `parallel_for` does not see exceptions; lanes fail independently exactly as today.

**`evolve.py:1755` finalists loop:**

```python
# BEFORE
for finalist_id in finalists:
    print(f"Finalizing {finalist_id}...")
    _run_holdout(config, str(config.archive_dir / finalist_id))

# AFTER
def _finalize_one(finalist_id: str) -> None:
    print(f"Finalizing {finalist_id}...")
    _run_holdout(config, str(config.archive_dir / finalist_id))
parallel_for(finalists, _finalize_one, resource="judge_http")
```

**`program_prescription_critic.py:571`:**

```python
# BEFORE
for domain in domains:
    old = _read_program(parent_programs, domain)
    new = _read_program(variant_programs, domain)
    ...
    result = critique_program(domain, old, new, model=model, ...)
    results[domain] = result
    _append_review(Path(variant_dir), domain, result)

# AFTER
results: dict[str, CriticResult] = {}
results_lock = threading.Lock()  # results dict + _append_review serialization

def _critique_one(domain: str) -> None:
    old = _read_program(parent_programs, domain)
    new = _read_program(variant_programs, domain)
    if new is None:
        return
    if old is None:
        result = {"verdict": "advise", "reasoning": f"New program file introduced for {domain} (no parent version)."}
    else:
        agent_key = f"critic-{Path(variant_dir).name}-{domain}" if sessions_file is not None else None
        result = critique_program(domain, old, new, model=model, sessions_file=sessions_file, agent_key=agent_key)
    with results_lock:
        results[domain] = result
        _append_review(Path(variant_dir), domain, result)

parallel_for(list(domains), _critique_one, resource="claude")
return results
```

### Lineage append lock

```python
# autoresearch/evolve_ops.py — add at module top
import threading
_LINEAGE_LOCK = threading.Lock()

# Wrap mark_promoted + set_current_head together at every call site, OR
# (preferred) introduce promote_atomic() that holds the lock for both writes:
def promote_atomic(archive_dir: str, lane: str, variant_id: str, timestamp: str) -> None:
    """Single critical section for promotion: lineage append + head pointer write."""
    with _LINEAGE_LOCK:
        mark_promoted(archive_dir, variant_id, timestamp)
        set_current_head(archive_dir, lane, variant_id)
```

Update the two existing `mark_promoted` + `set_current_head` call sites in `evolve.py` to use `promote_atomic`. Test exercises 5 concurrent writers and asserts lineage line count + head pointer match.

### `evaluate_variant.py` ThreadPoolExecutor → parallel_for

Both `:2004` and `:2612` use `ThreadPoolExecutor(max_workers=len(all_fixtures))` with no provider awareness. Convert to:

```python
from autoresearch.concurrency import parallel_for

# Picks resource based on fixture's session backend env (codex / opencode / claude).
# Default is opencode per provider routing recommendation; respects override.
session_backend = os.environ.get("AUTORESEARCH_SESSION_BACKEND", "opencode")
resource = {"claude": "claude", "codex": "codex", "opencode": "opencode"}.get(session_backend, "opencode")
results = parallel_for(all_fixtures, _run_and_score_fixture, resource=resource)
```

This is the only change to fixture fan-out — same parallelism shape, but now bounded by the global `opencode`/`codex`/`claude` semaphore.

## Implementation Units

### Unit 1: ship `autoresearch/concurrency.py` (new module + tests)
- Create `autoresearch/concurrency.py` with the API above.
- Create `tests/autoresearch/test_concurrency.py` with:
  - `test_parallel_for_runs_concurrently` (timing-based: N items × per-item sleep ≈ wallclock / cap)
  - `test_parallel_for_serial_mode` (env var degrades)
  - `test_parallel_for_propagates_first_exception` (other workers cancel)
  - `test_semaphore_caps_from_env` (override + minimum)
  - `test_unknown_resource_raises_value_error`
- Verify: `pytest tests/autoresearch/test_concurrency.py -v` all pass.
- Commit: `feat(autoresearch): central ConcurrencyController + parallel_for helper`.

### Unit 2: lineage append lock + `promote_atomic`
- Add `_LINEAGE_LOCK` + `promote_atomic` to `evolve_ops.py`.
- Update both `mark_promoted` + `set_current_head` call sites in `evolve.py` to call `promote_atomic`.
- Test: `tests/autoresearch/test_evolve_ops_lineage_lock.py` — spawn 5 threads each calling `promote_atomic`, assert lineage line count = 5 and head pointer is one of the 5 ids.
- Verify: existing `tests/autoresearch/` suite green.
- Commit: `fix(autoresearch): lock lineage append + head pointer for concurrent promotion`.

### Unit 3: convert `evolve.py:run_all_lanes` (cross-lane parallelism)
- Apply the diff above. Preserve per-lane error isolation.
- Add `tests/autoresearch/test_run_all_lanes_parallel.py` — stub `command_func` that records lane + thread id; assert all 4 lanes invoked, distinct threads when cap > 1.
- Manual smoke: `python -m autoresearch.evolve cmd_run --lane all --candidates-per-iteration=1 --iterations=1` on a sandbox archive; verify wallclock < serial baseline.
- Commit: `feat(autoresearch): run_all_lanes runs lanes concurrently (claude semaphore)`.

### Unit 4: convert `evolve.py:1755` finalists loop
- Apply the diff above.
- Test: `tests/autoresearch/test_finalists_parallel.py` — stub `_run_holdout` to sleep 1s × 3 finalists; assert wallclock < 3s when judge_http cap >= 3.
- Commit: `feat(autoresearch): finalists evaluated concurrently (judge_http semaphore)`.

### Unit 5: convert `program_prescription_critic.py:571`
- Apply the diff above.
- Test: extend `tests/autoresearch/test_program_prescription_critic.py` — assert per-domain results dict integrity under mocked concurrent execution.
- Commit: `feat(autoresearch): critic domains run concurrently (claude semaphore)`.

### Unit 6: route `evaluate_variant.py` ThreadPoolExecutors through `parallel_for`
- Replace both `with ThreadPoolExecutor(...)` blocks at `:2004` and `:2612`.
- Pick resource from `AUTORESEARCH_SESSION_BACKEND` env (default `opencode`).
- Verify: existing fixture tests pass; sessions still complete.
- Commit: `refactor(autoresearch): fixture fan-out routes through ConcurrencyController`.

### Unit 7: documentation + operator runbook
- Add `docs/architecture/concurrency.md` (small, ~50 lines): when to use `parallel_for`, env vars, default caps, kill switch, how lanes inherit parallelism via `LaneSpec`.
- Update `autoresearch/lane_registry.py` header comment: note that lanes inherit cross-lane / critic-domain / finalist parallelism automatically.
- Commit: `docs(autoresearch): concurrency framework operator notes`.

## System-Wide Impact

| Area | Change |
|---|---|
| `evolve.py:run_all_lanes` | 4 lanes run concurrently (cap = `claude` semaphore = 4) instead of strictly serial. Wall-time: ~4× → ~1× of slowest lane on a full sweep. |
| `evolve.py:1755` finalists | 2–4 finalists evaluated concurrently (cap = `judge_http`). Finalize phase: ~Nx → ~1x slowest finalist. |
| `program_prescription_critic.py:571` | 5 domains in parallel (cap = `claude`). Critic phase: ~5× faster. |
| `evaluate_variant.py:2004,2612` | No change in fan-out shape; now bounded by `opencode`/`codex`/`claude` semaphore. Cross-variant fixture floods to Codex impossible. |
| `evolve_ops.py:mark_promoted/set_current_head` | Atomic via `_LINEAGE_LOCK`. No observable behavior change in serial usage. |
| New lanes (X-engine, marketing-audit) | Inherit all four parallelism dimensions by registering a `LaneSpec`. Zero concurrency code in their modules. |
| Provider quota safety | At most N concurrent calls per provider globally, regardless of how many `parallel_for` invocations are nested or in flight. |

## Risks & Dependencies

- **Provider quota caps are guesses.** Defaults are conservative; first real run on `--lane all` will surface contention. Operator dials caps via env vars; no code change. Risk: if Codex cap = 2 is too tight, search-phase wallclock regresses vs today's per-variant fan-out. Mitigation: env var; revert to `serial` if needed.
- **Workspace 0444 sealing race (`7788ce3`)** — variant clones must let `sync_meta_workspace` complete before holdout reads. Cross-lane parallelism (Unit 3) does not introduce new sharing because lanes have disjoint `path_prefixes`. Variant pipelining (out of scope) would; that's why it's deferred.
- **`EVOLUTION_PARENT_ID` cross-lane contamination (Q1).** Verify in Unit 3 that `dataclasses.replace(config, lane=lane)` plus `_init_lane_config` produces a fully isolated config per thread. If env vars leak across threads, scope per-lane.
- **Retry-while-holding-semaphore.** A worker that hits a transient rate-limit retries with the semaphore held. For Codex (cap=2, retry up to 30+8+2s), this means a lane could occupy a Codex slot for 60s+ while others wait. Acceptable for Phase 1; revisit if tracing shows wasted slots.
- **Lineage clobber pre-Unit-2.** If Unit 4 (finalist parallelism) ships before Unit 2 (lineage lock), parallel finalists racing into `mark_promoted` clobber lineage. **Hard ordering: Unit 2 ships before Unit 4.**
- **Test flake from timing assertions.** Unit 1's `test_parallel_for_runs_concurrently` uses sleep-based timing. Use generous tolerances (e.g. wallclock < 1.5 × theoretical) and run thrice in CI to detect flakiness.

## Documentation / Operational Notes

**Pre-flight (operator):**
- Set conservative caps for first run: `AUTORESEARCH_CONCURRENCY_CODEX=1` (most defensive), `AUTORESEARCH_CONCURRENCY_CLAUDE=2`.
- Run `python -m autoresearch.evolve cmd_run --lane all --candidates-per-iteration=1 --iterations=1` and capture wallclock + per-stage timing (use `AUTORESEARCH_CONCURRENCY_TRACE=1`).
- Compare to last `--lane all` baseline run on origin/main.

**Dial-up workflow:**
- If wallclock improves but no provider rate-limit errors: bump caps one at a time (Codex first since it's tightest).
- If `agent_retry.py` logs show transient errors clustered when concurrency is high: that cap is too high; revert.
- Target steady-state: Codex 2–3, Claude 4–6, OpenCode 8–12, judge_http 10–20.

**Kill switch:**
- `AUTORESEARCH_CONCURRENCY=serial` reverts to today's behavior. No code change. Use when debugging non-deterministic failures or measuring serial baseline.

**Merge gate:**
- All units' tests green: `pytest tests/autoresearch/ -v`.
- Live `--lane all` smoke run completes one full generation across all 4 lanes without provider rate-limit errors.
- Lineage and head-pointer integrity verified: `git show <archive>/lineage.jsonl` matches expected promotion count.

## Effort Estimate

- Unit 1 (concurrency module + tests): **~3h**
- Unit 2 (lineage lock + tests): **~1h**
- Unit 3 (run_all_lanes parallel): **~1.5h**
- Unit 4 (finalists parallel): **~1h**
- Unit 5 (critic domains parallel): **~1.5h**
- Unit 6 (evaluate_variant routing): **~1h**
- Unit 7 (docs): **~1h**
- Live smoke run (operator-coordinated): **~1h** (1 generation × 4 lanes)
- **Total: ~10h engineer + 1h operator coordination** = ~1.5 working days.

## What This Plan Does NOT Build

- **Phase 2: declarative `ParallelismProfile` field on `LaneSpec`** for lane-specific tuning. Defer until a real lane needs different caps. Today's defaults cover all 4 lanes.
- **Variant pipelining inside a lane** (`evolve.py:2170`). Medium-risk; needs baseline-freshness gate before holdout judge sees candidate. Separate plan.
- **Draft-level parallelism inside a fixture session** (`harness/agent.py`). High-risk; ordering-sensitive; agent-internal. Separate work, possibly never.
- **Search provider rate-limit wrappers beyond `cloro_search`**. freddy-search and other providers are not currently rate-limited at the autoresearch boundary; out of scope.
- **Asyncio migration.** Threads + semaphores match the existing codebase. Not changing that surface.
- **Auto-tuning caps from observed throughput.** Caps are env vars; operator dials. A measure-quotas script could be a follow-up, but blocking on it is YAGNI.
- **Backpressure / queueing on top of semaphores.** `acquire()` blocks; that's the policy.
- **Per-lane dashboards / observability.** Use `AUTORESEARCH_CONCURRENCY_TRACE=1` for now.

## Sources & References

- `autoresearch/lane_registry.py` — `LaneSpec` + `LANES` dict (5 entries: 1 core + 4 workflow lanes verified 2026-05-07).
- `autoresearch/evolve.py:990` — `run_all_lanes` serial loop.
- `autoresearch/evolve.py:1755` — finalists serial loop.
- `autoresearch/program_prescription_critic.py:571` — critic domains serial loop.
- `autoresearch/evolve_ops.py:720-731` — `current_lineage` + `mark_promoted` (lock target).
- `autoresearch/evolve_ops.py:188-192` — `set_current_head` (lock target).
- `autoresearch/evaluate_variant.py:2004,2612` — existing `ThreadPoolExecutor` call sites to route through `parallel_for`.
- `autoresearch/agent_retry.py` — Claude/Codex/OpenCode retry policy (composes with semaphores).
- `docs/plans/2026-04-27-002-feat-autoresearch-lane-registry-plan.md` — precedent plan structure + "simplest thing that works" heuristic.
- Memory: `project-autoresearch-evolution-fixes-pending.md` (recent prod bugs surfacing under load), `feedback-pressure-test-overconfidence.md` (caps must be empirical).
