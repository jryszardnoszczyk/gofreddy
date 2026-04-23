---
title: "design: Unified RAL (running-agent-loop) runtime — fusing autoresearch + harness"
type: design
status: active
date: 2026-04-23
scope: Generic runtime design. Workload-agnostic. No marketing-audit content here.
related:
  - autoresearch/  (existing self-improving research engine)
  - harness/       (existing self-driving bug-fix engine)
---

# Unified RAL runtime — fusing autoresearch + harness

## Premise

`gofreddy` already runs two production long-horizon-running agent systems on entirely separate infrastructure:

- **`autoresearch/`** — self-improving research engine. Lanes, variants, evolution, lineage, judges, holdout. Research workload (geo / competitive / monitoring / storyboard).
- **`harness/`** — self-driving bug-fix engine. Sessions, parallel tracks, graceful-stop+resume, scope guard, cost circuit-breaker, skip-not-raise. Code-modification workload.

Both are LHR ("hot code agents running long-horizon"). They solve overlapping infrastructure problems with non-overlapping primitives. Each has invented or inherited patterns the other doesn't have. **Neither alone is a complete RAL runtime.**

This doc inventories what each contributes, specifies the unified runtime, and identifies what's missing from both.

**Not in scope:** any specific workload. Marketing audits, fixture refresh, video studio — these are workloads that *run on* the RAL runtime, not part of the runtime itself.

## What "RAL runtime" means here

A runtime that supervises agent processes which:
- Run **long-horizon** (minutes to days) without human babysitting
- **Multi-turn** (hundreds of turns per session) using `ClaudeSDKClient` or `claude` CLI subprocess
- **Unconstrained** (full toolbelt — Bash, WebFetch, Edit, Task — under explicit safety boundaries, not artificial restriction)
- **Resumable** across crashes, rate limits, restarts, machine reboots
- **Parallelizable** at multiple layers (process, lane, track, in-session subagent)
- **Self-improving** via evolution loops fed by judges + signal capture
- **Persistent** with cross-session memory (variant archive, lineage, learnings library)

The runtime is workload-agnostic. Plug in a workload (research, bug-fix, audit, content-gen, monitoring) by writing a session program + a fitness function + a fixture suite. The runtime handles everything else.

## What each existing system contributes

### From `autoresearch/` (the evolution + multi-tenant lanes engine)

| Primitive | File | What it does | Reusable as-is? |
|---|---|---|---|
| **Variant archive** | `archive/vNNN/` shape, `archive_index.py`, `lane_paths.py` | Each agent variant materialized as immutable directory with run.py + programs/ + scripts/ + scores.json | Yes |
| **Lane separation** | `lane_runtime.py`, `lane_paths.py` | Multi-tenant workloads run in same runtime; per-lane prompts + fixtures + scoring | Yes (extend `LANES` tuple to add new lane) |
| **Lineage tracking** | `archive/lineage.jsonl` | Append-only parent/child + scores + promotion + selection_rationale | Yes |
| **Materialized active runtime** | `runtime_bootstrap.py`, `archive/current_runtime/` | Resolves promoted variant per lane, materializes editable runtime from immutable archive | Yes |
| **Per-lane promotion manifest** | `archive/current.json` | One promoted variant per lane; atomic update | Yes |
| **Meta-agent variant mutation** | `evolve.py:855-898` | Subprocess (Claude CLI) mutates parent variant into candidate | Yes |
| **Parent selection policy** | `select_parent.py` | Top-K candidates from frontier; trajectory-window across recent generations | Yes |
| **Layer1 validation gating** | `evaluate_variant.py:544-594` | Hash check + py_compile + bash -n + import check before expensive scoring | Yes |
| **Outer-loop fitness scoring** | `evaluate_variant.py`, `src/evaluation/` | Multi-judge ensemble (Gemini + GPT-5.4), paraphrase + calibration judges, geometric-mean per domain | Yes |
| **Telemetry blindness** | Metrics outside variant workspace | Meta-agent can't see metrics it might game; operator-only view | Yes (architectural pattern, not code) |
| **Cohort-boundary metric flush** | `evolve.py:988-1000` | Emit telemetry per cohort even if final variant fails | Yes |
| **Wall-clock cohort termination** | `evolve.py:825` SIGALRM | Hard deadline per generation; clean shutdown on timeout | Yes |
| **Holdout suite isolation** | env-var pointer to non-repo manifest | Hidden eval set never visible to meta-agent or proposer | Yes |
| **Session-time inner-loop critique** | `archive/vNNN/scripts/evaluate_session.py` | Evolvable per-variant critique driving rework decisions | Yes (architectural pattern) |
| **Append-only events log** | `events.py` → `~/.local/share/gofreddy/events.jsonl` | Unified audit trail across CLI invocations; flock for concurrent writers | Yes |
| **Critique manifest hashing** | `critique_manifest.py` | SHA256 over frozen evaluator boundaries to prevent silent drift | Yes |
| **Automatic promotion on Pareto-dominance** | `evolve.py:1014` | No operator finalist pick; lane objective decides | Yes |
| **`evolve.sh` operator commands** | `score-current`, `seed-baseline`, `--lane`, `--iterations`, `--candidates-per-iteration`, `finalize`, `promote`, `rollback` | Full CRUD over evolution state | Yes |

### From `harness/` (the autonomy + multi-track session engine)

| Primitive | File | What it does | Reusable as-is? |
|---|---|---|---|
| **Sessions checkpoint** | `sessions.py:56-102` SessionsFile | Atomic-write JSON tracking session_id + status per agent role; threading.Lock + temp+rename | Yes |
| **Resume from session_id** | `engine.py` `_run_agent` resume path + `run.py:78-101` `_viable_resume_id` | Verifies SDK conversation jsonl exists at `~/.claude/projects/<encoded-cwd>/<sid>.jsonl` before resume | Yes |
| **Rate-limit detection** | `engine.py` `parse_rate_limit(log_path)` | Parses Claude CLI stream-json tail to detect rate-limit termination | Yes (Claude-specific; pattern generalizable) |
| **Silent-hang detection** | `engine.py:444-460` | Timeout + tiny output → infer hang, retry | Yes |
| **Graceful-stop atomic flag** | `run.py:344-350` `state.graceful_stop_requested` | Lock-protected flag; in-flight tracks observe and clean-exit | Yes |
| **EngineExhausted transient-budget** | `engine.py:52,484-486` | Bounded retry budget; raise to orchestrator when exhausted | Yes |
| **Cost circuit-breaker via wall-time deadline** | `config.py:74-75` `max_walltime` + `engine.py:55-68` deadline propagation | Hard wall budget; retries check deadline before sleeping | Yes (extend with token-budget for cost cap) |
| **Per-track parallel queue draining** | `run.py:377-502` ThreadPoolExecutor + per-track Finding queue | Tracks evaluate in parallel; per-track fixer drain serial; cross-track parallelism via threads | Yes |
| **Skip-not-raise on malformed YAML** | `findings.py:68-90` | Bad block logs warning + continues; one malformed item never kills file | Yes |
| **Verdict parsing with mid-write retry** | `engine.py:105-136` | YAML parse failure → 200ms sleep + retry once → unverified verdict, never crash | Yes |
| **Per-cycle directory layout** | `run_dir/track-{a\|b\|c}/cycle-{n}/` | Structured per-task output: findings.md + agent.log + sentinel.txt + verdicts/ + fix-diffs/ | Yes (rename "track" → "lane" or "agent_role") |
| **Sentinel files** | `run.py:505-510` `read_sentinel` | Agent writes `done reason=<reason>` to signal completion; orchestrator reads | Yes |
| **Patch capture before rollback** | `run.py:641-664` | `git add -N` + diff capture + reset intent-to-add → patch lives outside worktree | Yes (only when worktrees in use) |
| **Git worktree per run + scoped rollback** | `worktree.py` | Per-run worktree, scope allowlist enforces who-touches-what, leak detection separates actionable vs advisory | Yes (opt-in per workload) |
| **Pre-flight checks** | `preflight.py` | Env vars + tool presence + auth + JWT + stack health + resume branch validation | Yes (workload extends with own checks) |
| **Backend lifecycle tied to run** | `worktree.py:120-142` `restart_backend` | Service restarted between fixer/verifier; terminated on cleanup | Yes (opt-in for workloads needing live service) |
| **Atexit + SIGTERM handlers** | `worktree.py:236-254` | Cleanup on any exit path (normal, signal, exception) | Yes |
| **Engine choice abstraction** | `engine.py` claude vs codex command construction | Pluggable LLM backend per role | Yes |
| **Per-role model + auth config** | `config.py` Config dataclass | eval_model / fixer_model / verifier_model + claude_mode (oauth/bare) | Yes (rename roles per workload) |
| **CLI scaffolding** | `cli.py:11-31` argparse → `Config.from_cli_and_env` | Standard CLI shape: --engine, --resume-branch, --max-walltime, --staging-root, --keep-worktree | Yes |

## What's missing from BOTH (the gap to close)

| Missing primitive | Why it matters | Where it would live in unified runtime |
|---|---|---|
| **Cross-session memory library** (per-agent learnings, vertical patterns, failure modes) — beyond variant archive | Variant archive captures *what changed*; doesn't capture *what was learned*. Operator-curated lessons aren't structured anywhere | `runtime/memory/{global,by_lane,by_agent_role,failure_modes}/*.md` with frontmatter + index |
| **Per-call cost cap via SDK `max_budget_usd`** | harness only has wall-time; autoresearch has no per-call cost cap | `runtime/cost_ledger.py` reads ResultMessage.total_cost_usd; per-stage soft cap + total hard breaker |
| **Judge-driven inner loop** (vs fixed-N critique) | autoresearch's session-time critique fires unconditionally; harness has no inner loop. Right pattern: judge gates, agent revises only on fail | `runtime/inner_loop.py`: judge → on-fail revise once → skip-not-raise |
| **Engagement-conversion / business-outcome judge** (long-loop, async) | Both systems score on synchronous quality only. Some workloads have business signal that lags weeks/months | `runtime/judges/long_loop.py` reads `lineage.jsonl` row at T+N days, writes back fitness signal |
| **Multi-session orchestration** (8 Claude sessions on one Mac, today) | Neither system coordinates parallel sessions. Each invocation is independent. Result: rate-limit thrash + duplicated work | `runtime/lock.py` global mutex + per-lane locks; `runtime/scheduler.py` policy on what runs when |
| **Hooks ecosystem** (PreToolUse, PostToolUse, PreCompact, Stop) | SDK supports hooks; neither system uses them systematically | `runtime/hooks/`: standard hooks for cost capture, telemetry flush, transcript archive, safety enforcement |
| **Variant materialization for non-research workloads** | autoresearch's `lane_runtime.py` materializes per-lane based on hardcoded `WORKFLOW_PREFIXES` for 5 known lanes | `runtime/materialization.py` data-driven from lane manifest, not hardcoded |
| **`fork_session` for what-if exploration** | SDK supports forking a session; neither system uses it. Useful for: judge re-evaluates by forking, multi-candidate inner loop | `runtime/fork.py` thin wrapper |
| **`fallback_model` graceful degrade** | SDK supports primary→fallback model on failure; not exploited | `runtime/agent_runner.py` always passes `fallback_model` |
| **MCP tool registry per lane** | autoresearch uses MCP for some lanes; harness doesn't use MCP. Need uniform per-lane tool surface | `runtime/mcp_registry.py` per-lane tool allowlist + custom MCP servers |

## Proposed unified runtime architecture

### Module layout

```
runtime/                              # NEW package — neither autoresearch nor harness
  __init__.py
  cli.py                              # `freddy ral run --lane <name> ...` `freddy ral evolve --lane <name> ...`
  config.py                           # Config dataclass merging harness/config.py + autoresearch env vars
  bootstrap.py                        # Resolve active variant per lane → materialize active_runtime/
  agent_runner.py                     # ClaudeSDKClient wrapper; cost capture; session_id persist;
                                      #   tenacity retries with jitter; fallback_model; timeout
  sessions.py                         # PORTED FROM harness/sessions.py with per-lane namespacing
  cost_ledger.py                      # Per-call max_budget_usd + per-stage soft cap + total hard breaker
  graceful_stop.py                    # PORTED FROM harness/run.py atomic flag + SIGTERM handler
  inner_loop.py                       # Judge-driven correction (Judge → revise once → skip-not-raise)
  hooks/
    cost_capture.py                   # PostToolUse hook → cost_ledger.append
    transcript_archive.py             # PreCompact hook → archive full conversation
    telemetry_flush.py                # Stop hook → flush events.jsonl
    safety_enforce.py                 # PreToolUse hook → scope_allowlist + leak_detection
  memory/
    library.py                        # Frontmatter-indexed cross-session learnings
    lessons_capture.py                # Post-run hook proposes 0-3 lessons to lessons_<lane>.md
  scheduler.py                        # Multi-session orchestration; global lock; per-lane locks
  judges/
    sync.py                           # Judge runner; structural + LLM ensemble; reuses src/evaluation/
    long_loop.py                      # T+N day async judge writing back to lineage
  evolution/                          # WIRES TO autoresearch/evolve.py — does not reinvent
    lane.py                           # Add a workload as an autoresearch lane (data-driven)
    fitness.py                        # Per-lane fitness function spec
  parallelism/
    tracks.py                         # PORTED FROM harness/run.py per-track parallel queue draining
    sessions_concurrency.py           # asyncio.TaskGroup + Semaphore for in-process parallel agents
  worktree.py                         # PORTED FROM harness/worktree.py; opt-in per lane via config
  preflight.py                        # PORTED FROM harness/preflight.py; per-lane extension hooks
  lineage.py                          # READS+WRITES autoresearch/archive/lineage.jsonl in shared format
  events.py                           # READS+WRITES autoresearch/events.py shared events.jsonl
```

### Lane = workload contract

A lane is a workload definition. To add a lane to the runtime, supply:

```yaml
# runtime/lanes/<lane_name>.yaml
name: <lane_name>
description: <one line>
session_program: programs/<lane_name>-session.md
inner_loop:
  enabled: true|false
  judge: <judge_name>
  threshold: 0.6
  max_corrections: 1
fitness:
  fitness_fn: judges.<lane_name>_fitness  # 0.0-1.0 weighted combination
  weights:
    sync_quality: 0.6
    long_loop: 0.4
parallelism:
  tracks: 1   # or N for parallel sub-tasks within one session
  sessions_concurrency: 1
cost:
  per_call_max_usd: 12.0
  per_stage_soft_usd: {discovery: 30, work: 60, synthesis: 10}
  total_hard_breaker_usd: 150.0
runtime_shape:
  worktree: false  # true for code-modification workloads
  backend_required: false
  evaluator_backend: codex|claude
  fallback_model: claude-sonnet-4-5
fixtures:
  manifest: eval_suites/<lane_name>-v1.json
  holdout_env: EVOLUTION_HOLDOUT_MANIFEST_<LANE_NAME>
```

That's the entire workload contract. Everything else (sessions, resume, cost, hooks, telemetry, evolution) is provided by the runtime.

### How it runs (one invocation, end to end)

```
$ freddy ral run --lane <X>
   │
   ├─► cli.py parses → Config
   ├─► bootstrap.py: read autoresearch/archive/audit_agents/current.json → materialize active_runtime/
   ├─► preflight.py: env vars + tools + cost cap sane + lane fixtures present + acquire lane_lock
   ├─► scheduler.py: check global_lock (no evolve generation in flight); acquire active_run lock
   ├─► agent_runner.py: ClaudeSDKClient(options=lane.options + cost_ledger hooks + safety hooks)
   │      ├─► run for N turns (per session_program logic)
   │      ├─► after each turn: cost_ledger.record(ResultMessage.total_cost_usd)
   │      ├─► sessions.py: persist session_id immediately on first ResultMessage
   │      └─► on inner_loop trigger: judges.sync → if fail → revise once → skip-not-raise
   ├─► judges.sync: end-of-run quality scoring (structural + LLM ensemble via src/evaluation/)
   ├─► lineage.py: append row to audits/lineage.jsonl with audit_id + variant_id + scores
   ├─► hooks/telemetry_flush.py: events.jsonl flushed
   └─► release lane_lock + active_run

$ freddy ral resume --lane <X> --run-id <ts>
   │
   ├─► Same as above but bootstrap reads sessions.json
   ├─► Skip stages whose checkpoint files exist
   └─► Resume in-flight session via SDK resume="<session_id>"

$ freddy ral evolve --lane <X> --iterations 1 --candidates-per-iteration 3
   │
   ├─► Acquire global_lock (no live runs allowed during evolve)
   ├─► Wire to autoresearch/evolve.py --lane <X> directly
   │      ├─► select_parent → meta-agent mutate → layer1 validate → holdout replay
   │      ├─► fitness scoring per lane.fitness.fitness_fn
   │      └─► Pareto-dominance promotion → update current.json
   └─► Release global_lock
```

### Self-improvement loop (the closed circuit)

```
[run] freddy ral run --lane X
  ↓ produces per-run output + scores
[lineage] runtime/lineage.py appends row to archive/lineage.jsonl
  ↓ accumulates across many runs
[long-loop judge] runtime/judges/long_loop.py at T+N days writes business outcome back
  ↓ accumulates fitness signal
[evolve] freddy ral evolve --lane X (weekly/monthly)
  ↓ mutates parent variants, scores against holdout, promotes winners
[bootstrap] next run reads new active variant from current.json
  ↓ uses promoted (better) variant
[run] freddy ral run --lane X (next)
  ↓ produces better output
```

This is exactly autoresearch's loop. The runtime adds harness's autonomy primitives so each *run* in this loop is hot-code-agent-grade resilient.

## Cross-session memory layer

Neither autoresearch nor harness has structured cross-session memory beyond variant archives + git history. The unified runtime adds:

```
runtime/memory/
  global/
    failure_modes.md             # cross-lane patterns: "rate limits at X, retry with Y"
    cost_baselines.json          # rolling p50/p95 per stage per lane
  by_lane/
    <lane_name>/
      lessons.md                 # operator-curated learnings; frontmatter-indexed
      base_rates.json            # which sub-tasks fire %, which produce keepers %
  by_agent_role/                 # for multi-agent lanes (each role gets its own memory)
    <role>/lessons.md
  index.md                       # MEMORY.md-style pointers
```

Loaded at agent startup as a deterministic prompt prefix:
> "In prior runs of this lane on similar fixtures: pattern A holds 89% but fails ship-gate 34% (consider skeptically). Rolling p95 cost: $7.20 — flag if trending higher."

Lessons capture: post-run hook (`runtime/memory/lessons_capture.py`) proposes 0-3 lessons via single Opus call. Operator reviews monthly, accepts to lessons.md. Same pattern as Claude Code auto-memory.

## Multi-session coordination

Today: 8 parallel Claude sessions on one Mac, no coordination, sometimes fighting for rate limits.

Runtime adds two locks via filesystem:

```
~/.local/share/gofreddy/locks/
  global.lock                    # held by evolve generation; live runs check
  lane_<lane_name>.lock          # held by run on that lane; siblings wait or fail
  active_runs.json               # registry: {pid, lane, started_at, host}
```

`runtime/scheduler.py` enforces:
- Live run acquires `lane_<X>.lock` before running on lane X
- Evolve acquires `global.lock`; refuses to start if any `lane_*.lock` is held
- Live run refuses to start if `global.lock` is held
- `active_runs.json` updated atomically; stale entries (PID dead) cleaned on next acquire

Same pattern as harness `state.active_run.pid` check, generalized.

## Migration path (if we ever build this)

This doc is design only. If we did build it, the migration would be:

| Phase | Scope | Risk |
|---|---|---|
| **Phase 1** | Stand up `runtime/` package with stubs that delegate to existing autoresearch/harness functions. No behavior change. | Low |
| **Phase 2** | Port `runtime/sessions.py` from harness; autoresearch starts using it for its session_id tracking | Low |
| **Phase 3** | Add `runtime/cost_ledger.py` + cost-cap hooks; both systems opt-in | Low |
| **Phase 4** | Add `runtime/judges/long_loop.py` + lineage extensions; both systems write to shared lineage | Medium |
| **Phase 5** | Add `runtime/scheduler.py` global+lane locks; both systems acquire | Medium |
| **Phase 6** | Add `runtime/memory/` cross-session library; both systems load at startup | Low |
| **Phase 7** | Migrate harness to use autoresearch's lane structure (harness becomes `bug_fix` lane). One unified runtime, two existing workloads. | High — but only at the end |

**No rewrite required.** Each phase is additive. Existing autoresearch + harness keep running unchanged until Phase 7 explicitly merges them.

## What this design is NOT

- Not a workload spec. Marketing audit, fixture refresh, video studio — those are workloads that *run on* this runtime, designed elsewhere.
- Not a replacement for autoresearch or harness. Autoresearch's evolution machinery is reused as-is; harness's autonomy primitives are reused as-is. Runtime is the thin layer that fuses them.
- Not a commitment to build now. This is the *target architecture*. Phasing above shows it can land incrementally.
- Not opinionated on engine. Claude SDK and Codex CLI subprocess both supported via existing `engine` abstraction in harness.
- Not opinionated on workload type. Bug-fix, research, audit, content-gen, monitoring all fit if they can express themselves as a lane.

## Open questions

1. **Naming.** `RAL` (running-agent-loop), `LHR` (long-horizon-running), `runtime`, `harness2`, something else? Affects package name and CLI.
2. **Backwards compatibility.** Phase 7 merges harness into runtime as `bug_fix` lane. That's a real migration of harness/runs/, harness/cli.py, harness CI. Worth it or live with two systems forever?
3. **Engine vs SDK.** harness wraps `claude` CLI subprocess (uses stream-json). autoresearch can use either Claude or Codex. SDK ClaudeSDKClient is more ergonomic. Mix-and-match per lane, or pick one?
4. **Hooks vs in-process.** SDK hooks fire in the agent process; some logic (cost ledger, telemetry) might be cleaner there. Other logic (scheduler, lineage) must be in the orchestrator. Where's the line?
5. **MCP server registry.** Per-lane MCP tool allowlist is clean, but autoresearch currently uses prompt-named URL patterns + Bash. Do we standardize on MCP, or accept the heterogeneity?
6. **Worktree default.** harness's worktree+scope+leak-detection is excellent for code modification but pure overhead for read-only research. Default off, opt-in per lane?

## Sources

- `autoresearch/` — full module surface enumerated above
- `harness/` — full module surface enumerated above
- `src/evaluation/` — fixed outer-loop evaluator (reused for judges)
- Claude Agent SDK — `ClaudeSDKClient`, `ClaudeAgentOptions`, `ResultMessage`, hooks
- prior subagent reports in this session (autoresearch deep-dive, harness primitive extraction, src/evaluation contract, lane addition mechanics)
