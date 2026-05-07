---
title: "Concurrency — parallel_for and provider semaphores"
date: 2026-05-07
status: active
---

# Concurrency — `parallel_for` and provider semaphores

`autoresearch/concurrency.py` is the single source of truth for concurrent execution in the orchestration layer. One module-level `ConcurrencyController` owns per-resource semaphores; one `parallel_for(items, work_fn, resource)` helper wraps `ThreadPoolExecutor` and acquires the named semaphore inside each worker so global provider quotas are honored across lanes, finalists, critic domains, and fixture fan-out.

## Default semaphore caps

Caps are conservative; tune with env vars after measuring.

| Resource | Default | Override env | What it gates |
|---|---|---|---|
| `claude` | 4 | `AUTORESEARCH_CONCURRENCY_CLAUDE` | `run_all_lanes` cross-lane meta-agent + critic-domain Claude subprocesses |
| `codex` | 2 | `AUTORESEARCH_CONCURRENCY_CODEX` | Codex CLI session backend (tightest provider — saturates first) |
| `opencode` | 8 | `AUTORESEARCH_CONCURRENCY_OPENCODE` | OpenCode → DeepSeek (default fixture-session backend) |
| `judge_http` | 10 | `AUTORESEARCH_CONCURRENCY_JUDGE_HTTP` | Holdout finalists + judge-service calls |
| `cloro_search` | 2 | `AUTORESEARCH_CONCURRENCY_CLORO_SEARCH` | Cloro search API (~100 calls/week per key — strict) |

## Kill switch

```bash
AUTORESEARCH_CONCURRENCY=serial python -m autoresearch.evolve …
```

Degrades every `parallel_for` to a plain `for` loop on the calling thread — no executor, no semaphore acquisition. Use to debug non-deterministic failures or measure a serial baseline.

## Tracing

```bash
AUTORESEARCH_CONCURRENCY_TRACE=1 …
```

Logs `parallel_for[<resource>] item=<repr> dt=<seconds>` per worker to stderr.

## How lanes inherit parallelism

A new lane registered as a `LaneSpec` in `autoresearch/lane_registry.py` automatically inherits four parallelism dimensions with no concurrency code in its own modules:

1. **Cross-lane**: `evolve.run_all_lanes` runs all registered lanes concurrently under the `claude` semaphore.
2. **Holdout finalists**: `cmd_finalize` evaluates frontier finalists concurrently under `judge_http`.
3. **Critic domains**: `program_prescription_critic.critique_all_programs` runs per-domain critics concurrently under `claude`.
4. **Fixture fan-out**: `evaluate_variant.{evaluate_search, _run_holdout_suite}` route through `parallel_for` with the resource derived from `eval_target.backend` (claude / codex / opencode).

## Adding a new `parallel_for` call site

```python
from concurrency import parallel_for

def _do_one(item):
    # ... whatever per-item work, side effects with a lock if needed
    pass

parallel_for(items, _do_one, resource="opencode")
```

Pick the resource that matches the dominant external call inside `work_fn`:
- Claude subprocess → `"claude"`
- Codex CLI → `"codex"`
- OpenCode CLI / OpenRouter → `"opencode"`
- Judge HTTP service → `"judge_http"`
- Cloro search → `"cloro_search"`

If the work_fn dispatches to one of several backends, derive the resource at call time (see `evaluate_variant._BACKEND_TO_RESOURCE`).

`parallel_for` propagates the first exception it sees and cancels siblings where possible — matching the serial-loop semantics it replaces. Per-item side effects (results dict mutation, heartbeat printing) belong inside the `work_fn` under a `threading.Lock` shared via closure.

## Operator dial-up workflow

1. Run a baseline with conservative caps: `AUTORESEARCH_CONCURRENCY_CODEX=1 AUTORESEARCH_CONCURRENCY_CLAUDE=2 python -m autoresearch.evolve cmd_run --lane all --candidates-per-iteration=1 --iterations=1`. Capture wall-clock + per-stage timing with `AUTORESEARCH_CONCURRENCY_TRACE=1`.
2. If the run completes without provider rate-limit errors in `agent_retry.py` logs, bump caps one at a time (Codex first since it is tightest).
3. If transient errors cluster when concurrency is high, that cap is too high — revert.
4. Steady-state target: Codex 2–3, Claude 4–6, OpenCode 8–12, judge_http 10–20.

## Why threading and not asyncio

The codebase uses `subprocess`-based retry helpers (`agent_retry.py`, `_invoke_judge_with_retry`) that assume blocking calls. Threads + semaphores compose with that surface without changing call signatures. Asyncio migration is its own larger project; not in scope here.

## See also

- `docs/plans/2026-05-07-002-autoresearch-parallelism-framework.md` — design rationale, alternatives considered.
- `autoresearch/concurrency.py` — implementation.
- `tests/autoresearch/test_concurrency.py` — contract tests for `parallel_for`.
