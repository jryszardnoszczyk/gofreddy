---
title: "research record: Audit pipeline — borrowable patterns from harness + autoresearch"
type: research-record
status: active
date: 2026-04-24
purpose: |
  Hand-off research record for the agent building the audit engine (src/audit/)
  and the marketing_audit autoresearch lane (LHR agent). Captures every relevant
  primitive from the two existing LHR systems in this repo (harness/, autoresearch/),
  with concrete file:line refs, contract shapes, gotchas, and application mapping
  to audit use cases.
consumers:
  - The agent implementing the 5-bundle audit product
related:
  - docs/plans/2026-04-20-002-feat-automated-audit-pipeline-plan.md
  - docs/plans/2026-04-22-005-marketing-audit-lens-catalog.md
  - docs/plans/2026-04-22-006-marketing-audit-lens-ranking.md
  - docs/plans/2026-04-23-003-agency-integration-plan.md
  - docs/plans/2026-04-23-004-ral-runtime-design.md (related workload-agnostic design)
---

# Audit pipeline — borrowable patterns from harness + autoresearch

## 0. Purpose + framing

The audit product is two pieces:

1. **Audit engine** (`src/audit/`) — greenfield Python module. 6-stage prospect audit pipeline (Stages 0-5), 149-lens catalog, HTML+PDF deliverable. Per `docs/plans/2026-04-20-002-feat-automated-audit-pipeline-plan.md`.
2. **`marketing_audit` autoresearch lane** — greenfield autoresearch lane that wraps the audit engine. Makes audits self-improving across prospects via existing autoresearch machinery (variants, evolution, judges).

This repo already has two production long-horizon-running agent systems:
- `harness/` — autonomous bug-fixing engine (sessions, resume, parallel tracks, cost circuit-breaker, skip-not-raise)
- `autoresearch/` — self-improving marketing research engine (lanes, variants, evolution, lineage, judges, holdout)

Neither directly solves the audit problem, but collectively they contain ~90% of the infrastructure primitives the audit pipeline needs. This doc enumerates every borrowable primitive with: source file:line, what it does, how it applies to the audit work, and the gotchas the implementing agent should know before adopting it.

**Principle:** don't reinvent what's already running in production. Borrow aggressively.

## 1. Audit engine needs (from plan 002 + catalog 005) — what the implementing agent will build

Before mapping primitives, here's what the audit engine actually needs from infrastructure:

| Need | Where spec'd |
|---|---|
| 6-stage pipeline with per-stage checkpointing | Plan 002 §Architecture |
| `state.json` per audit with atomic writes | Plan 002 U1 |
| 7 (→ may become 4-9) Stage-2 agents running in parallel | Plan 002 U4, updated in catalog 005 |
| Sessions persist across resume via SDK `session_id` | Plan 002 U1 |
| Cost cap: $100 soft warn / $150 hard breaker per audit | Catalog 005 §Architectural Patterns |
| Skip-not-raise on malformed SubSignals | Catalog 005 §Architectural Patterns (SubSignal → ParentFinding) |
| Three gates: intake review, payment, ship | Plan 002 R8 |
| Concurrent-run lock (no double-fire on same slug) | Plan 002 U1 |
| Pre-flight adversarial check | Plan 002 §Architecture |
| `cost_log.jsonl` per-call telemetry | Plan 002 R7 |
| Slack notifications on key events | Plan 002 U1 |
| Atomic writes via temp+rename | Plan 002 U1 |
| Per-lens SubSignal → ParentFinding aggregation | Catalog 005 §Architectural Patterns |
| Stage-1a deterministic pre-pass (~25 cheap lenses in Python) | Catalog 005 §Architectural Patterns |
| Conditional bundle activation (vertical/geo/segment) | Catalog 005 §Conditional Bundles |
| HTML → PDF rendering via Jinja2 + WeasyPrint | Plan 002 U5 |
| R2 upload + Cloudflare Worker relay | Plan 002 U5 |
| Stripe Checkout payment gate | Plan 002 U3 |
| Fireflies webhook ingest (sales + walkthrough) | Plan 002 R15 |

## 2. Patterns from `harness/` (the autonomous-run engine)

Harness ships a hardened LHR runtime for one workload (bug fixing). The audit engine is also an LHR runtime for one workload (audits), with similar shape: parallel agents, long-running sessions, resume, cost budget, graceful stop. **~95% of harness's autonomy primitives transfer directly.**

### 2.1 Sessions checkpoint (ATOMIC, LOCK-PROTECTED, PORTABLE)

**Source:** `harness/sessions.py:56-102` `SessionsFile` class

**What it does:** tracks `session_id` per agent role in a single JSON file with `threading.Lock` + atomic temp-write-and-rename. Every `ClaudeSDKClient` begin/end calls `record_session(role, result_message)` → writes `session_id`, `status`, `last_turn`, `last_cost_usd`, `last_duration_ms` atomically.

```python
# harness/sessions.py pattern (abbreviated)
class SessionsFile:
    def __init__(self, path: Path):
        self._path = path
        self._lock = threading.Lock()
    def record_session(self, role: str, result: ResultMessage):
        with self._lock:
            current = self._read()
            current[role] = {
                "session_id": result.session_id,
                "last_turn": result.num_turns,
                "last_cost_usd": result.total_cost_usd,
                "status": "complete",
            }
            self._atomic_write(current)
```

**Audit application:** ONE-TO-ONE port to `src/audit/state.py` for the `sessions` field of audit `state.json`. Each agent role (pre_discovery, findability, narrative, etc.) gets an entry keyed by role name. Plan 002 U1 line 307-369 specifies this pattern; use harness's implementation.

**Gotcha:** harness uses `ClaudeSDKClient`'s `ResultMessage` streaming. The audit pipeline must capture the FIRST `ResultMessage` (when `session_id` becomes available) and persist immediately — before any second turn. If the process crashes before first ResultMessage lands, that session cannot be resumed and must restart from scratch. Cost: ~$0.50 of agent startup. Plan 002 line 285 already captures this.

### 2.2 Resume logic with session_id verification

**Source:** `harness/run.py:78-101` `_viable_resume_id()`

**What it does:** before telling the SDK to resume a session, verifies the conversation JSONL exists at `~/.claude/projects/<encoded-cwd>/<session_id>.jsonl`. The SDK needs this file to restore the conversation. If it's gone (e.g., after a machine reboot that cleared temp state), `session_id` is unusable → restart from scratch.

```python
def _viable_resume_id(session_id: str, worktree_path: Path) -> bool:
    """True if session_id's JSONL still exists for the SDK to resume from."""
    encoded_cwd = str(worktree_path).replace("/", "-")
    sdk_jsonl = Path.home() / ".claude" / "projects" / encoded_cwd / f"{session_id}.jsonl"
    return sdk_jsonl.exists()
```

**Audit application:** `src/audit/resume.py` or inside `state.py`. Before `freddy audit run --resume`, verify each persisted session is still resumable. Mark un-resumable sessions for restart in resume plan.

**Gotcha:** path encoding is SDK version-specific. Harness uses the encoding scheme in its Claude CLI version. If SDK encoding changes, this check silently returns False for everything. Consider adding a fallback: attempt SDK resume and handle failure, don't rely solely on pre-check.

### 2.3 Rate-limit detection from stream-json tail

**Source:** `harness/engine.py` `parse_rate_limit(log_path)` (lines 239-290)

**What it does:** reads the tail of a Claude CLI stream-json log, detects rate-limit termination events by matching specific error patterns, raises `RateLimitHit` with structured info (reset time, model, account).

```python
class RateLimitHit(Exception):
    def __init__(self, reset_at: datetime | None, model: str, account: str | None):
        ...

def parse_rate_limit(log_path: Path) -> RateLimitHit | None:
    """Tail the stream-json log looking for rate-limit indicators."""
    # reads last ~100 lines, greps for patterns:
    #   "rate_limit_error"
    #   "You have exceeded your"
    #   "anthropic-ratelimit-..." headers
```

**Audit application:** if using `ClaudeSDKClient`, rate-limit events surface as exceptions directly — this parser is Claude-CLI-specific. Two audit paths:

1. If audit uses SDK (recommended per plan 002): catch `RateLimitError` from SDK, persist state, exit gracefully with code 0 (same pattern as harness).
2. If audit uses CLI subprocess for any agent: port this parser.

**Gotcha:** silent-hang detection (harness `engine.py:444-460`) also matters. If an agent session goes quiet (no output for N seconds + tiny byte count), infer hang and retry. SDK has its own timeouts but hung HTTP calls can exceed them.

### 2.4 Graceful-stop atomic flag

**Source:** `harness/run.py:344-350` + `state.graceful_stop_requested`

**What it does:** atomic bool flag + `threading.Lock`. On `RateLimitHit` or SIGTERM, sets flag → in-flight tracks observe and stop cleanly at next checkpoint. Exits with code 0 (not crash). State is preserved; resume works.

```python
# harness pattern (abbreviated)
class OrchestratorState:
    def __init__(self):
        self.graceful_stop_requested = False
        self._lock = threading.Lock()

    def request_graceful_stop(self, reason: str):
        with self._lock:
            self.graceful_stop_requested = True
            self._stop_reason = reason
```

Then tracks check `if state.graceful_stop_requested: break` before each expensive operation.

**Audit application:** ONE-TO-ONE port. Audit Stage-2 fan-out over N parallel agents should check this flag between agents. If the flag is set mid-stage, the audit exits cleanly and `freddy audit run --resume` picks up the remaining agents.

**Gotcha:** must be thread-safe if using threading (harness uses ThreadPoolExecutor) or asyncio-safe if using asyncio.TaskGroup (plan 002 U4 leans this direction). Either works but pick one model.

### 2.5 Transient-budget + wall-time deadline propagation

**Source:** `harness/engine.py:52,484-486` + `harness/config.py:74-75` + `harness/engine.py:55-68`

**What it does:** two bounds on how long an agent can work:
- `EngineExhausted`: per-agent retry budget for transient failures (default 3 retries with exponential backoff). Exceeds → exit.
- `max_walltime`: total wall-clock budget across entire run (default 4h). Propagated as a module-level `_deadline` that `_run_agent` checks before sleeping on any retry.

```python
# engine.py
_deadline: datetime | None = None

def set_deadline(dt: datetime):
    global _deadline
    _deadline = dt

def _sleep_with_deadline(seconds: float):
    if _deadline and (datetime.now(UTC) + timedelta(seconds=seconds)) > _deadline:
        raise WalltimeExceeded()
    time.sleep(seconds)
```

**Audit application:** ports directly with TWO extensions:
1. Add per-agent token-budget via SDK `max_budget_usd=<X>` in `ClaudeAgentOptions` (harness doesn't have this because CLI subprocess doesn't support it — SDK does).
2. Add per-audit total cost breaker at $150 (catalog 005 requirement). Accumulates `ResultMessage.total_cost_usd` across all agents; raises `CostBreakerExceeded` when total exceeds breaker.

**Gotcha:** harness's deadline is module-level global. For async audit code running multiple audits concurrently on the same machine (future scenario), needs to be per-audit-state instance-scoped, not module-level.

### 2.6 Skip-not-raise on malformed YAML/JSON

**Source:** `harness/findings.py:68-90`

**What it does:** when parsing findings.md YAML blocks, one malformed block logs a warning and the loop continues. Other blocks parse normally. Result: one bad block never kills the file.

```python
def parse(findings_md_path: Path) -> list[Finding]:
    findings = []
    for idx, block in enumerate(_iter_yaml_blocks(findings_md_path)):
        try:
            data = yaml.safe_load(block)
            findings.append(Finding(**data))
        except (yaml.YAMLError, ValidationError) as e:
            logger.warning(f"malformed block {idx} in {findings_md_path}: {e}")
            continue
    return findings
```

**Audit application:** port to `src/audit/subsignals.py` for SubSignal parsing. A malformed SubSignal from one Stage-2 agent should not kill the audit. Log, flag in `gap_report.md`, continue. Per catalog 005 this is explicit.

**Gotcha:** also applies to verdict parsing (harness `engine.py:105-136`) — mid-write YAML parse failures get a 200ms retry before returning "unverified". Borrow both patterns.

### 2.7 Per-track parallel queue draining

**Source:** `harness/run.py:377-502` `_evaluate_tracks` + `_process_track_queue:416-453`

**What it does:** harness runs three tracks in parallel. Evaluator phase uses `ThreadPoolExecutor(max_workers=len(tracks))`. Per-track fixer phase drains serially via its own worker thread. Cross-track parallelism emerges from concurrent threads, not asyncio.

```python
# abbreviated
def _evaluate_tracks(self):
    with ThreadPoolExecutor(max_workers=len(self.tracks)) as pool:
        futures = {pool.submit(self._evaluate_track, t): t for t in self.tracks}
        for fut in as_completed(futures):
            track = futures[fut]
            findings = fut.result()
            self._route_findings(track, findings)
```

**Audit application:** plan 002 U4 specifies asyncio.gather + Semaphore(7) for Stage-2. Either model works; asyncio is more idiomatic for SDK-async code, threading is what harness uses. Pick asyncio for audit. Borrow the *pattern* (parallel evaluate, serial per-agent drain, graceful-stop check between items) but use asyncio primitives.

**Gotcha:** per-agent exception handlers matter. If one Stage-2 agent crashes, the other N-1 must keep running. asyncio.gather(return_exceptions=True) does this; TaskGroup does NOT (fail-fast by default). Plan 002 leans TaskGroup; wrap each agent call in its own try/except to get partial-completion semantics.

### 2.8 Per-cycle directory layout + sentinel files

**Source:** `harness/run.py:143-147` cycle_dir setup + `run.py:505-510` `read_sentinel`

**What it does:** every run gets a structured output dir:
```
harness/runs/run-<ts>/
  harness.log
  sessions.json
  track-{a,b,c}/
    cycle-{n}/
      findings.md              # evaluator output
      agent.log                # stream-json
      sentinel.txt             # "done reason=<reason>"
  fixes/{track}/{finding-id}/agent.log
  verifies/{track}/{finding-id}/agent.log
  verdicts/{track}/{finding-id}.yaml
  fix-diffs/{track}/{finding-id}.patch
  review.md
  pr-body.md
```

Agent writes `done reason=rate_limit_hit` to `sentinel.txt` on exit. Orchestrator reads sentinel to determine why agent ended.

**Audit application:** port to `clients/<slug>/audit/`:
```
clients/<slug>/audit/
  state.json                    # orchestrator state
  cost_log.jsonl                # harness-style append-only
  events.jsonl                  # telemetry
  sessions/                     # harness-style session checkpoints
    pre_discovery.json
    agent_<role>.json
  stage1a_preflight/            # deterministic pre-pass results
  stage2_subsignals/            # per-lens SubSignal files
    L<id>_<slug>.json
  stage3_sections/              # per-section intermediate (crash-safe)
  stage3_synthesis/             # final synthesis
    findings.md
    report.md
    report.json
  proposal/
  deliverable/
    report.html
    report.pdf
```

**Gotcha:** per-lens SubSignal files are important — they enable resume by skipping completed lenses. This is more granular than harness's per-cycle checkpointing. Plan 002 U1 implies per-stage; upgrade to per-lens for Stage 2.

### 2.9 Pre-flight checks pattern

**Source:** `harness/preflight.py:40-59` `check_all` + 62-280

**What it does:** runs a battery of pre-run validations before launching any agent:
- Required env vars present (config.py:11-16 REQUIRED_ENV_VARS)
- Production guards (reject ENVIRONMENT=production, non-local DATABASE_URL)
- CLI tools present (claude, gh, freddy)
- Auth credentials (Claude OAuth or bare, Codex profiles)
- Schema applied to DB
- JWT minting works + TTL envelope sanity
- Stack health (backend + frontend health endpoints with 30s timeout)
- Resume branch validation (regex `harness/run-YYYYMMDD-HHMMSS`, ref exists)

**Audit application:** `src/audit/preflight.py`. Audit-specific checks:
- Target URL reachable (HEAD request)
- Cloudflare Worker for scan upload reachable
- R2 bucket credentials present
- Stripe webhook endpoint reachable (if payment gate will fire)
- Fireflies webhook endpoint reachable
- DataForSEO + Cloro credits sufficient (check balance API)
- `state.active_run` lock free (no other audit in flight for this slug)
- Cost ceiling sanely configured ($100 soft < $150 hard)
- Sitemap size < 500 URLs (if > → require `--override-preflight`)
- crt.sh subdomain count < 500
- Domain age > 30 days (adversarial gate, plan 002)

**Gotcha:** harness's pre-flight includes production-safety guards. Audit's pre-flight should too — refuse to run if `ENVIRONMENT=production` or if DATABASE_URL points to production Supabase.

### 2.10 Safety scope allowlist + leak detection

**Source:** `harness/config.py:24-50` SCOPE_ALLOWLIST + `harness/safety.py` (deprecated shim) + `src/shared/safety/tier_c.py`

**What it does:** per-track regex allowlist of file paths. After each agent's work, checks:
- `check_scope(wt, pre_sha, track)` — any files modified outside allowlist = violations
- `check_no_leak(pre_dirty_set)` — files dirty pre-run that got modified = actionable leak (fixer touched out-of-scope) or advisory leak (concurrent dev outside scope)

**Audit application:** weaker need — audit doesn't mutate the repo, only writes to `clients/<slug>/audit/`. BUT:
- Per-stage output validation: after Stage 2, verify all writes are within `stage2_subsignals/` or `sessions/`. Prevents agents from writing to weird places.
- State directory isolation: audit should NEVER write outside `clients/<slug>/audit/`. Enforce as a pre-exit check.

**Gotcha:** harness's scope-guard is designed for code-modification isolation. Audit's is data-write isolation — different threat model (agent going rogue with Bash), same primitive.

### 2.11 Atexit + SIGTERM cleanup

**Source:** `harness/worktree.py:236-254`

**What it does:** registers `atexit` + signal handlers for cleanup on any exit path (normal, SIGTERM, SIGINT, exception). Ensures:
- Worktree state preserved or cleanly removed per config
- Backend processes terminated
- Sessions.json flushed
- Final telemetry event logged

**Audit application:** port. On audit exit (any cause), ensure:
- state.json flushed atomically
- events.jsonl flushed
- state.active_run.pid cleared (so next audit can start)
- Slack notification sent (success or failure mode)
- Temp files cleaned

**Gotcha:** signal handlers must not block. If Slack notification hangs on network, SIGTERM cleanup will fail. Use `signal.alarm(5)` to cap handler duration or fire Slack async with short timeout.

### 2.12 Engine abstraction (Claude vs Codex)

**Source:** `harness/engine.py` `build_claude_cmd` vs `build_codex_cmd`

**What it does:** per-role model + backend configurable. Harness supports both Claude CLI and Codex CLI subprocesses; same orchestrator code picks the right command builder based on config.

**Audit application:** less critical — audit spec (plan 002) commits to SDK, not subprocess. But the pattern of per-role config is relevant. Each Stage-2 agent role should have its own `ClaudeAgentOptions` with model, budget, max_turns, fallback_model. Don't hardcode.

**Gotcha:** if audit needs one Codex-driven step (e.g., a specific judge that works better on GPT-5.4), harness's pattern shows how to mix backends cleanly.

### 2.13 Pre-existing harness patterns we DON'T need

For completeness, pattern from harness that doesn't apply to audit:
- **Worktree isolation** (harness/worktree.py) — audit doesn't mutate the repo; no need for per-audit worktree
- **Backend restart between stages** — audit doesn't depend on a live backend service
- **PR generation (git commit + gh pr create)** — audit produces customer deliverable, not a PR
- **Per-track scope allowlist of src/** — audit has single write scope (clients/<slug>/audit/)
- **Fixer/verifier pattern** — audit has synthesis/proposal pattern instead (similar shape, different domain semantics)

## 3. Patterns from `autoresearch/` (the self-improving research engine)

Autoresearch ships the full variant-evolution + lane + lineage + promotion machinery. The `marketing_audit` autoresearch lane wrapping the audit engine **reuses 100% of this infrastructure**. This section inventories every piece so the implementing agent doesn't reinvent.

### 3.1 Variant archive (the evolved-artifact store)

**Source:** `autoresearch/archive/vNNN/` shape, enforced by `archive_index.py` + `lane_paths.py`

**What it does:** each variant is an immutable directory snapshot:
```
autoresearch/archive/v006/
  run.py                      # session runner (may be lane-owned or core)
  run.sh                      # thin wrapper
  meta.md                     # meta-agent instructions for mutation
  programs/                   # per-lane session programs
    geo-session.md
    competitive-session.md
    monitoring-session.md
    storyboard-session.md
    <lane>-evaluation-scope.yaml
    references/
  scripts/
    evaluate_session.py        # session-time critique (evolvable)
  templates/
  scores.json                 # this variant's search-suite scores
```

Variant id like `v006` increments on each mutation. Archive is append-only — variants are never modified after creation.

**Audit application:** `marketing_audit` lane adds to existing archive:
```
autoresearch/archive/current_runtime/
  programs/
    marketing_audit-session.md         # NEW — audit session program
    marketing_audit-evaluation-scope.yaml  # NEW
```

Per agency-integration plan Bundle 10 (docs/plans/2026-04-23-003 §7.1), the session program is already spec'd. Use that shape; the meta-agent mutates prompts + stage-1a thresholds + lens dispatch logic (NOT lens definitions).

**Gotcha:** variant archive is shared across all lanes. Adding `marketing_audit` content doesn't fork the archive; it just adds files. All 5 existing lanes + marketing_audit share `v006` → `v007` etc.

### 3.2 Lane structure (multi-tenant workload container)

**Source:** `autoresearch/lane_runtime.py` + `lane_paths.py`

**What it does:** workload isolation within shared archive. Each lane has:
- Its own session program (`programs/<lane>-session.md`)
- Its own evaluation scope (`programs/<lane>-evaluation-scope.yaml`)
- Its own promoted head in `archive/current.json`
- Its own per-lane path ownership (`lane_paths.py:WORKFLOW_PREFIXES`)

Current lanes (`lane_runtime.py:12`):
```python
LANES = ("core", "geo", "competitive", "monitoring", "storyboard")
```

**Audit application:** adding `marketing_audit` requires editing 5 files:
- `lane_runtime.py:12` — add to `LANES` tuple
- `lane_paths.py:36-37,44-77` — add to `LANES` tuple + `WORKFLOW_PREFIXES` dict
- `evolve.py:44` — add to `ALL_LANES`
- `frontier.py:15-16` — add to `LANES` and `DOMAINS` tuples (or reframe as non-domain)
- `archive_index.py:381-389` — no change needed, iterates `LANES` dynamically

**Gotcha:** `frontier.py:82-86` `objective_score()` hardcodes logic for `core` (composite score) vs workflow lanes (domain score). `marketing_audit` would need its own scoring branch or map to existing pattern. Per Bundle 10 spec, reuse domain_score shape.

**Effort estimate** (from subagent lane-addition investigation): 3-4 weeks for clean integration including session program authoring, evaluation scope, fixture suite, MA-1..MA-8 rubric in src/evaluation/.

### 3.3 Lineage tracking (append-only history)

**Source:** `autoresearch/archive/lineage.jsonl`

**What it does:** one JSON row per variant with:
```json
{
  "variant_id": "v006",
  "parent_variant_id": "v005",
  "created_at": "2026-04-23T12:00:00Z",
  "lane": "geo",
  "selection_rationale": "explored seo-schema-focused branch",
  "scores": {"geo": 0.72, "competitive": 0.81},
  "promotion": {"promoted": true, "promoted_at": "2026-04-23T14:00:00Z"},
  "meta_session_log": "meta-session.log"
}
```

Writers use flock for concurrent safety.

**Audit application:**
1. Per-audit row in `audits/lineage.jsonl` (NEW file, separate from variant lineage): one row per completed audit with audit_id, prospect_slug, shipped_at, total_cost_usd, ship_gate_edit_count, vertical, segment, geo, finding_count, severity_distribution. Used as fitness signal for marketing_audit variant evolution.
2. When marketing_audit lane evolves, standard lineage row gets written to autoresearch/archive/lineage.jsonl with `lane: "marketing_audit"`.

**Gotcha:** two lineages, both append-only, different schemas. `audits/lineage.jsonl` is per-audit (operations); `autoresearch/archive/lineage.jsonl` is per-variant (evolution). Don't conflate. Both use the same atomic-write + flock pattern.

### 3.4 Materialized active runtime

**Source:** `autoresearch/runtime_bootstrap.py` + `autoresearch/archive/current_runtime/`

**What it does:** resolves the active variant per lane from `current.json`, materializes editable runtime by symlinking / copying from the immutable variant archive. Lets the session runner execute against `current_runtime/` while keeping `archive/vNNN/` pristine.

```bash
./autoresearch/run.sh --domain geo
# → runtime_bootstrap.py reads archive/current.json
# → resolves geo → v006
# → materializes archive/current_runtime/ from v006
# → execs current_runtime/run.py
```

**Audit application:** `freddy audit run --client <slug>` reads `autoresearch/archive/current.json` for `marketing_audit` lane → materializes that variant's prompts/rubric weights/inner-loop config into the audit runner's config → runs the audit engine. Same pattern as autoresearch production runner.

**Gotcha:** materialization preserves runtime state dirs (`sessions/`, `metrics/`, `runs/`). Audit's per-prospect state lives outside the autoresearch runtime at `clients/<slug>/audit/` — don't co-locate.

### 3.5 Meta-agent mutation (Claude CLI subprocess)

**Source:** `autoresearch/evolve.py:855-898`

**What it does:** parent variant is cloned → meta-agent subprocess (Claude CLI with 1800s timeout) receives `meta.md` prompt + variant workspace → mutates programs/, scripts/, prompts based on lane context → writes new variant directory → exit.

**Audit application:** mutations for `marketing_audit` lane evolve:
- `programs/marketing_audit-session.md` (stage prompts)
- Stage-1a applicability thresholds
- Lens dispatch logic (which bundles fire for which detection signals)
- Inner-loop judge thresholds
- `evaluate_session.py` (session-time critique)

Per Bundle 10 spec, lens definitions in `configs/audit/lenses.yaml` are **out of mutation scope** (locked v2). Meta-agent must respect this boundary — enforce via lane-context.md + autoresearch's existing `critique_manifest` SHA256 drift-prevention.

**Gotcha:** 1800s timeout may be tight when mutating prompts that reference 149 lenses. If meta-agent runs long, bump timeout or narrow mutation surface (mutate one agent role per generation, not all at once).

### 3.6 Parent selection policy

**Source:** `autoresearch/select_parent.py:181-189`

**What it does:** TOP_K_CANDIDATES=8 from frontier, TRAJECTORY_WINDOW=3 recent generations, exploration-vs-exploitation balance via handcrafted score-child-prop policy. Parent selection agent (AsyncOpenAI gpt-5.4) picks the parent; rationale stored in lineage.

**Audit application:** use as-is. `marketing_audit` variants get selected same way as research variants. No code change needed — add lane to `ALL_LANES` and the existing selector handles it.

**Gotcha:** first few generations of `marketing_audit` lane have no frontier yet. Falls back to seed baseline (`evolve.sh seed-baseline`). Plan accordingly — the first 3-5 generations produce low-signal variants until frontier has depth.

### 3.7 Layer1 validation gating

**Source:** `autoresearch/evaluate_variant.py:544-594`

**What it does:** cheap deterministic checks BEFORE expensive scoring:
1. Critique-manifest SHA256 hash check (prevents evolution-loop escape from frozen boundaries — R-#13)
2. `py_compile` on all Python files (syntax valid)
3. `bash -n` on all shell scripts (syntax valid)
4. Import check (all imports resolve)
5. Missing required files = hard fail

Any failure → variant marked invalid, archived for audit, skip expensive scoring entirely.

**Audit application:** EXTREMELY relevant. For `marketing_audit` lane, add variant-specific layer1 checks:
- Variant's session program references valid lens IDs (all in catalog 005)
- Stage-1a threshold schema valid
- Lens dispatch logic doesn't reference dropped lens IDs
- MA-1..MA-8 rubric hash matches frozen manifest

**Also applicable to per-audit run:** Stage-1a deterministic pre-pass IS layer1 validation for the audit itself. 8 cheap Python checks (DNS/SPF/DKIM/DMARC, well-known files, JSON-LD parse, badge regex, tooling fingerprint, URL probes) before expensive LLM stages. Same pattern, different scope.

**Gotcha:** `critique_manifest.py:compute_expected_hashes` is the machinery. Reuse it to prevent audit variants from silently drifting off locked MA-1..MA-8 criteria.

### 3.8 Outer-loop fitness scoring

**Source:** `autoresearch/evaluate_variant.py` → calls `src/evaluation/` (authoritative external judge)

**What it does:** multi-judge ensemble (Gemini 2.0 Flash + GPT-5.4 reasoning=high, `judge_replicates_per_model=2` = 4 samples per criterion). Per-criterion pipeline:
1. Structural gate (free, deterministic, per-domain)
2. LLM judges (8 criteria × N judges × replicates, all concurrent)
3. Paraphrase judge (R-#32) verifies evidence quotes exist in output
4. Calibration judge (R-#33) adjusts gradient scores to evidence band
5. Aggregate: `geometric_mean([d.normalized_score for d in dimensions])` with floor 0.01

**Audit application:** extend `src/evaluation/` with `marketing_audit` domain. Per Bundle 10 §7.2, MA-1..MA-8 rubric:

| Criterion | Type | Focus |
|---|---|---|
| MA-1 | Gradient | Observational grounding — every finding cites specific observation |
| MA-2 | Checklist | Recommendation actionability — action + target + effort + timeframe |
| MA-3 | Gradient | Competitive honesty — prospect's losses named |
| MA-4 | Checklist | Cost discipline — under ceiling, per-stage within estimate |
| MA-5 | Gradient | Bundle applicability — dispatched bundles match detection |
| MA-6 | Gradient | Deliverable polish — HTML/PDF renders clean |
| MA-7 | Gradient | Prioritization — top-3 actions unmistakably separated |
| MA-8 | Checklist | Data gap recalibration — failed enrichments named, confidence lowered |

**Implementation effort** (from subagent src/evaluation investigation): ~30 LOC across 5 files to add marketing_audit as a new domain. Changes:
1. `src/evaluation/models.py:160` — add `"marketing_audit"` to domain Literal
2. `src/evaluation/rubrics.py` — add MA-1..MA-8 `RubricTemplate` dataclass instances
3. `src/evaluation/service.py` — add to `_DOMAIN_CRITERIA` dict, `_JUDGE_PRIMARY_DELIVERABLE`
4. `src/evaluation/structural.py` — add audit-specific structural validator
5. `autoresearch/evaluate_variant.py:44-49` — add to `DELIVERABLES` dict

**Gotcha:** `src/evaluation/` is NOT dynamically pluggable (no factory/registry). The Literal type must be edited. This is a one-time PR, ~30 LOC, trivial — but needs a coordinated code change, not a config file.

### 3.9 Telemetry blindness

**Source:** `autoresearch/compute_metrics.py` writes to `autoresearch/metrics/generations.jsonl` OUTSIDE variant workspace; GAPS.md Gap 2 line 62 "Outputs live under autoresearch/metrics ... NOT copied into proposer workspace"

**What it does:** the meta-agent cannot see its own fitness scores. Prevents variants from gaming the fitness function (a variant that sees "judges love long prompts" would make longer prompts next iteration; hiding scores forces it to improve output quality instead).

**Audit application:** STRONG APPLICABILITY. For `marketing_audit` variants:
- MA-1..MA-8 judge scores NEVER in meta-agent workspace
- JR ship-gate edits (Judge-3 signal) NEVER in meta-agent workspace
- Engagement-conversion (Judge-4 signal) NEVER in meta-agent workspace

All judge signals live under `autoresearch/metrics/marketing_audit/` or `audits/lineage.jsonl`, outside the variant workspace. Meta-agent sees only: operator feedback in findings.md, raw session traces (visible now per GAPS Gap 2 fix in progress), structural pass/fail.

**Gotcha:** autoresearch's current Gap 2 implementation is adding some trace visibility to meta-agent. Watch that: if it exposes judge scores, it breaks telemetry blindness for marketing_audit too.

### 3.10 Cohort-boundary metric flush

**Source:** `autoresearch/evolve.py:988-1000` (Fix 9)

**What it does:** per-generation metrics are flushed on generation boundary even if the last variant in the cohort fails. Before Fix 9, if the final variant's scoring crashed, metrics for all earlier variants in the cohort were lost.

**Audit application:** when running an evolve cycle on marketing_audit lane with 3 candidate variants, if candidate #3 crashes, ensure candidates #1 and #2's scores still land in `lineage.jsonl` + `metrics/generations.jsonl`.

**Gotcha:** fix is already in autoresearch. Don't reintroduce the bug when extending for marketing_audit.

### 3.11 Wall-clock cohort termination

**Source:** `autoresearch/evolve.py:825` signal.alarm(MAX_GENERATION_SECONDS) + `_sigalrm_handler:630-644`

**What it does:** hard wall-clock deadline per generation (default 7200s = 2h). SIGALRM fires → clean termination, triggers finalization, promotes best completed variant, exits gracefully.

**Audit application:** marketing_audit generations will be longer (each candidate replays 3-5 past audits × $30-60/replay = $90-300 per candidate, takes 30-60min of wall time). Bump `MAX_GENERATION_SECONDS` for this lane or per-lane config.

**Gotcha:** SIGALRM is POSIX-only. If autoresearch ever runs on Windows, needs different mechanism. Not an issue today (production is Linux).

### 3.12 Holdout suite isolation

**Source:** `autoresearch/evaluate_variant.py:300-315` `_load_holdout_manifest` + env vars

**What it does:** holdout suite (hidden evaluation set) is loaded from non-repo env:
```bash
export EVOLUTION_HOLDOUT_MANIFEST=/private/path/holdout-v1.json
# or
export EVOLUTION_HOLDOUT_JSON='{"suite_id":"holdout-v1", ...}'
```

Meta-agent + proposer workspace NEVER see holdout fixtures. Only the outer-loop evaluator. Prevents overfitting.

**Audit application:** per Bundle 10 §7.6, defer holdout suite until 5 real audits exist, then collect 5 hand-curated audit artifacts as `holdout-marketing-audit-v1.json`. Same env-var isolation pattern; keeps ground-truth audits out of variant workspace.

**Gotcha:** holdout replay cost is expensive ($30-60/audit). Cap holdout size at 5 initially; grow only as signal justifies the compute.

### 3.13 Pareto-dominance promotion

**Source:** `autoresearch/evolve.py:1014` `_do_finalize_step`

**What it does:** `evolve.sh finalize` runs hidden holdout over lane frontier, automatically promotes best candidate that Pareto-dominates current promoted baseline. No operator finalist pick. Promotion uses lane objective only.

**Audit application:** marketing_audit fitness function per Bundle 10:
```python
fitness = (
    0.4 * judge_MA_1_8_composite         # synchronous quality (MA-1..MA-8 geometric mean)
    + 0.2 * (1.0 - normalize(ship_gate_edits))  # fewer edits = better
    + 0.2 * engagement_conversion_60d    # business signal
    + 0.2 * cost_discipline_score        # stayed under ceiling, per-stage within estimate
)
```

Pareto: promote if no-worse on synchronous quality AND ship-gate AND engagement AND cost; strictly better on at least one.

**Gotcha:** engagement_conversion has 60-day lag. Early generations only have 3 signals; weight engagement 0 for those, rebalance once signal accumulates.

### 3.14 `evolve.sh` operator commands (full CLI)

**Source:** `autoresearch/evolve.sh`

**What it does:** operator-facing CRUD over evolution state:
```bash
./autoresearch/evolve.sh score-current
./autoresearch/evolve.sh score-current --lane marketing_audit
./autoresearch/evolve.sh seed-baseline
./autoresearch/evolve.sh --iterations 1 --candidates-per-iteration 3
./autoresearch/evolve.sh --lane marketing_audit --iterations 1 --candidates-per-iteration 3
./autoresearch/evolve.sh finalize
./autoresearch/evolve.sh promote
./autoresearch/evolve.sh rollback
```

**Audit application:** Bundle 10 inherits this interface FOR FREE. Once `marketing_audit` is registered as a lane, operator can run:
```bash
./autoresearch/evolve.sh --lane marketing_audit --iterations 1 --candidates-per-iteration 3
./autoresearch/evolve.sh promote --lane marketing_audit
```

No new CLI needed. ~$300-900 per generation (3 candidates × 3-5 holdout replays × $30-60 each).

**Gotcha:** don't let evolve runs fire during live customer audits. Acquire `state.evolve_lock` before generation; live audits check lock before starting. Same pattern as harness graceful-stop.

### 3.15 Append-only events log (`events.jsonl`)

**Source:** `autoresearch/events.py` → `~/.local/share/gofreddy/events.jsonl`

**What it does:** unified audit trail across all CLI invocations. Rotates at 100 MB, POSIX flock for concurrent writers. Every event: `{kind, timestamp, **data}`.

**Audit application:** per-audit `events.jsonl` at `clients/<slug>/audit/events.jsonl` using same format + rotation. Optionally also append to global events log with `kind: "audit_run"` for cross-system observability.

**Gotcha:** 100 MB rotation is large. Audits produce ~10 MB of events each; consider per-audit events files (isolated) + cross-reference in global log (1-line summary per audit).

### 3.16 Critique manifest hashing (drift prevention)

**Source:** `autoresearch/critique_manifest.py`

**What it does:** SHA256 over frozen evaluator boundaries (MA-1..MA-8 rubric prompts, judge system prompts, structural validator). Layer1 validation checks hash; mismatch → variant rejected with FAST FAIL.

**Audit application:** same primitive, applied to `marketing_audit` rubric + structural validator. Freeze MA-1..MA-8 prompts + hash; prevents silent drift when meta-agent's mutations accidentally touch evaluator code.

**Gotcha:** extending the manifest to cover marketing_audit artifacts needs discipline — every file in the "evaluator boundary" must be listed. Missed files drift silently.

### 3.17 Patterns from autoresearch that DON'T apply to audit

- **Search-suite fixtures** (`eval_suites/search-v1.json`) — audit needs its own fixtures (`marketing-audit-v1.json` per Bundle 10); schema reuses.
- **Storyboard lane's creator-video domain** — completely unrelated to audits.
- **Session-time evaluator script (`evaluate_session.py`)** — audit may or may not want inline critique; decision is workload-specific.
- **Per-lane workflow prefix hardcoding** — annoying but bounded (5 files to edit); worth living with vs refactoring lane_runtime.py now.

## 4. What's missing from BOTH — gaps the audit pipeline will expose

| Gap | Why audit needs it | Where it lives |
|---|---|---|
| **Per-call cost cap via `ClaudeAgentOptions.max_budget_usd`** | Harness has wall-time only; autoresearch has no cost cap at all. Audit needs $100 soft / $150 hard. | `src/audit/agent_runner.py` — thin SDK wrapper that reads per-role budget from config, enforces per-audit total via accumulator |
| **Judge-driven inner loop (vs fixed-N critique)** | Autoresearch's session-time critique fires unconditionally (cost overhead). Harness has no inner loop. Audit should use judge → revise-once-on-fail → skip-not-raise. | `src/audit/inner_loop.py` |
| **Engagement-conversion long-loop judge (T+60d async)** | Both systems score on synchronous quality only. Audit has business signal (did audit lead to $15K engagement) that lags. | `src/audit/judges/engagement.py` writes back to `audits/lineage.jsonl` when JR records `engagement_signed_usd` |
| **SubSignal → ParentFinding aggregation** | Specific to audit's deliverable shape (per catalog 005). Neither system has this aggregation layer. | `src/audit/synthesis.py` |
| **Stage-1a deterministic pre-pass (8 check modules)** | Similar in spirit to autoresearch's layer1 validation but applied to raw prospect data, not variants. | `src/audit/preflight/` with 8 check modules (dns_email_security, well_known, json_ld, trust_badges, security_headers, social_meta, brand_assets, tooling_fingerprint) |
| **Conditional bundle activation** | Vertical (25) + geo (10) + segment (5) bundles fire based on Stage-1b detection signals. Neither system does conditional workload selection. | `src/audit/bundles.py` |
| **Per-lens checkpoint files (skip-completed on resume)** | Harness checkpoints per-cycle; autoresearch per-variant. Audit needs per-lens for Stage-2 resume granularity. | `clients/<slug>/audit/stage2_subsignals/L<id>_*.json` written atomically by each lens agent |
| **Payment gate integration** | Neither system has Stripe Checkout flow. | `src/audit/payment.py` + Stripe webhook endpoint |
| **HTML + PDF rendering from findings** | Neither system produces customer deliverables. | `src/audit/render.py` (Jinja2 → HTML, WeasyPrint → PDF) |
| **R2 upload + Cloudflare Worker relay** | Neither system has customer-facing hosting. | `src/audit/publish.py` |

## 5. Applying patterns: concrete mapping for the implementing agent

### 5.1 Audit engine (Bundle 9) primitive adoption checklist

For `src/audit/` module, port these harness primitives in order of value:

1. **State + sessions** (`harness/sessions.py` → `src/audit/state.py`) — atomic writes, session_id tracking, resume readiness check
2. **Skip-not-raise on malformed outputs** (`harness/findings.py` → `src/audit/subsignals.py`) — one bad SubSignal doesn't kill the audit
3. **Graceful-stop atomic flag** (`harness/run.py` → `src/audit/state.py` state.graceful_stop_requested)
4. **Pre-flight checks pattern** (`harness/preflight.py` → `src/audit/preflight.py`) — audit-specific checks per plan 002
5. **Cost circuit-breaker with deadline propagation** (`harness/engine.py` → `src/audit/agent_runner.py`) — extend with SDK max_budget_usd + total breaker
6. **Per-cycle directory layout** (`harness/run.py` → `src/audit/` client dir structure per plan 002)
7. **Atexit + SIGTERM cleanup** (`harness/worktree.py:236-254` → `src/audit/cleanup.py`)
8. **Parallel queue draining pattern** (`harness/run.py` parallel evaluators → `src/audit/stage2.py` asyncio-based)

Port autoresearch patterns into the audit engine:

9. **Layer1 validation as Stage-1a deterministic pre-pass** (`autoresearch/evaluate_variant.py:544-594` pattern → `src/audit/preflight/` 8 check modules)
10. **Atomic lineage write** (`autoresearch/events.py` flock pattern → `src/audit/lineage.py` writing `audits/lineage.jsonl`)

### 5.2 Marketing_audit lane (Bundle 10) primitive adoption checklist

For the autoresearch `marketing_audit` lane, edit these existing files:

1. `autoresearch/lane_runtime.py:12` — add `"marketing_audit"` to `LANES` tuple
2. `autoresearch/lane_paths.py:36-37,44-77` — add to `LANES` + `WORKFLOW_PREFIXES`
3. `autoresearch/evolve.py:44` — add to `ALL_LANES`
4. `autoresearch/frontier.py:15-16` — add to `LANES` and `DOMAINS`
5. `autoresearch/evaluate_variant.py:44-49` — add to `DELIVERABLES` dict

Create these new files:

6. `autoresearch/archive/current_runtime/programs/marketing_audit-session.md` (per Bundle 10 §7.1)
7. `autoresearch/archive/current_runtime/programs/marketing_audit-evaluation-scope.yaml` (per Bundle 10 §7.1)
8. `autoresearch/eval_suites/marketing-audit-v1.json` (per Bundle 10 §7.3)

Extend `src/evaluation/` with MA-1..MA-8 rubric (~30 LOC across 5 files per §3.8 above):

9. `src/evaluation/models.py:160` — add `"marketing_audit"` to Literal
10. `src/evaluation/rubrics.py` — MA-1..MA-8 `RubricTemplate` dataclass instances
11. `src/evaluation/service.py` — update `_DOMAIN_CRITERIA`, `_JUDGE_PRIMARY_DELIVERABLE`
12. `src/evaluation/structural.py` — audit structural validator (verifies findings.md, deliverable.html, deliverable.pdf, state.json present)

Add cross-cutting infrastructure:

13. `src/audit/judges/engagement.py` — long-loop (T+60d) engagement-conversion judge, writes back to `audits/lineage.jsonl`
14. `runtime/scheduler.py` or similar — `state.evolve_lock` global mutex preventing concurrent evolve + audit runs

## 6. Risks + pre-mortem (audit-specific)

### 6.1 Autoresearch coupling risk (MEDIUM per subagent-6)

**Evidence:** 27 commits touching autoresearch in last 60 days. 3 fixes (11% rate). Recent crash bug (`0392dc2`, load_json AttributeError in evaluate_variant.py). GAPS.md has 4 P0 pre-blockers (Gap 2 trace visibility, Gap 6 regression_floor, Gap 18 eval variance, Gap 30 L1 import check).

**Mitigations:**
1. **Pin autoresearch evaluator to known-good commit at audit ship time.** Freeze a git tag (`autoresearch-audit-stable-YYYYMMDD`). Audit depends on that tag's evaluate_variant.py + src/evaluation/.
2. **Lane isolation already exists.** Marketing_audit variants can't crash geo/competitive/monitoring lanes. Per-lane current.json.
3. **Add safety tests for marketing_audit's specific evaluator interface** (scored_fixtures shape, regression_floor enforcement once Gap 6 lands, DELIVERABLES entry).

### 6.2 Holdout replay cost ($300-900/generation)

**Mitigations:**
1. Cap holdout size at 5 audits initially (Bundle 10 §7.6 already defers this).
2. Cap evolve generation budget at $1000 hard; don't let Claude CLI meta-agent loop infinitely.
3. Rolling "fitness actually improving?" check — pause evolve if fitness flat for 3 generations.

### 6.3 Meta-agent timeout on 149-lens context

**Mitigations:**
1. Per-agent-role mutation (one role per generation). Meta-agent sees only that role's prompt + rubrics + recent fitness, not whole audit system.
2. Bump `MAX_GENERATION_SECONDS` for marketing_audit lane if 1800s proves tight.

### 6.4 Cross-lane resource contention

**Risk:** evolve generation + live audit both running → compete for Claude rate limits → both degrade.

**Mitigation:** `state.evolve_lock` global mutex (new primitive, §5.2 item 14). Live audit refuses to start if evolve active; evolve refuses to start if any audit active.

### 6.5 Goodhart on judges

**Risk:** variants over-fit to MA-1..MA-8 synchronous judges while losing real strategic depth.

**Mitigations:**
1. Judges themselves don't evolve (only agent variants do).
2. JR manually reviews promoted variants before they ship customer audits (ship-gate discipline).
3. Engagement-conversion (Judge-4) is ground-truth check that catches Goodhart on Judges 1-3.

### 6.6 Lineage pollution across lanes

**Risk:** marketing_audit events in shared `autoresearch/archive/lineage.jsonl` make debugging other lanes harder.

**Mitigation:** every lineage row has `lane: "marketing_audit"` field. Existing tooling filters by lane. Per-audit data (operations, not evolution) lives separately in `audits/lineage.jsonl`.

### 6.7 Engagement signal lag (60 days)

**Risk:** Judge-4 fitness is always 2 months stale.

**Mitigation:** fitness function weights synchronous judges 60% (MA-1..MA-8 + ship-gate edits). Engagement is corrective, not primary driver. Early generations weight engagement 0; rebalance as signal accumulates.

## 7. Open architectural questions for the implementing agent

1. **asyncio vs threading for Stage 2 parallelism.** Harness uses threading (ThreadPoolExecutor); plan 002 U4 leans asyncio (TaskGroup + Semaphore). SDK is async-native → asyncio is more idiomatic. Pick one and commit.
2. **Per-lens checkpoint granularity.** Harness checkpoints per cycle. Plan 002 implies per stage. Per-lens is finer (better resume). Cost: more files in `stage2_subsignals/`. Recommended: per-lens.
3. **Worktree per audit — no, right?** Audits produce artifacts, don't mutate repo. Plan 002 doesn't mention worktrees. Confirm: no worktree, audit runs in main working tree; state isolated to `clients/<slug>/audit/`.
4. **Concurrency model for multiple audits on one machine.** Single-worker-per-audit (audit pipeline holds active_run lock for its slug, others wait). Multi-worker horizontal scale = more worker processes. v1 is single-worker; v2 add queue (arq) + multiple workers.
5. **Engine choice: SDK-only or mix with Codex CLI?** Plan 002 commits to SDK. Harness supports both. Some judges might prefer GPT-5.4 (Codex) for certain tasks. Decision: SDK for all agent roles; Codex optional for judges only.
6. **Inner loop on-by-default or opt-in per agent role?** Judge-driven inner loop adds cost when judges fail. Opt-in per agent role via lane variant config. In v3, becomes an evolvable parameter.

## 8. Sources

### Harness files referenced
- `harness/sessions.py` (lines 56-102)
- `harness/engine.py` (lines 52, 55-68, 71-85, 105-136, 239-290, 337-486, 444-460, 484-486)
- `harness/run.py` (lines 78-101, 143-147, 274-277, 287-288, 309, 344-350, 364-414, 416-453, 455-502, 505-510, 513-638, 641-664)
- `harness/worktree.py` (lines 35-100, 120-142, 144-188, 236-254)
- `harness/safety.py` → `src/shared/safety/tier_c.py`
- `harness/preflight.py` (lines 40-59, 62-280)
- `harness/config.py` (lines 11-16, 24-50, 58-143, 74-75)
- `harness/findings.py` (lines 68-90)
- `harness/prompts.py` (lines 18-75)
- `harness/cli.py` (lines 11-31)

### Autoresearch files referenced
- `autoresearch/runtime_bootstrap.py` (line 14)
- `autoresearch/lane_runtime.py` (lines 12, 45, 147-152, 159, 223-228)
- `autoresearch/lane_paths.py` (lines 36-37, 44-77)
- `autoresearch/archive_index.py` (lines 14-23, 220-256, 381-389)
- `autoresearch/frontier.py` (lines 15-16, 36-38, 82-86)
- `autoresearch/select_parent.py` (lines 21-22, 38-41, 181-189)
- `autoresearch/evolve.py` (lines 44, 82-100, 150-161, 453, 616-640, 630-644, 700, 825, 833-1015, 848-850, 855-898, 970-974, 988-1000, 1014)
- `autoresearch/evaluate_variant.py` (lines 40, 44-49, 101-114, 141-155, 162-179, 300-315, 509, 544-594, 667-679, 680-720, 695, 803, 903-964, 998-1040, 1915-1959)
- `autoresearch/critique_manifest.py`
- `autoresearch/compute_metrics.py` (lines 47-55)
- `autoresearch/events.py`
- `autoresearch/evolve_ops.py` (lines 165-180, 616-640)
- `autoresearch/archive/current.json`
- `autoresearch/archive/v006/programs/{geo,competitive,monitoring,storyboard}-session.md`
- `autoresearch/archive/v006/programs/{geo,competitive,monitoring,storyboard}-evaluation-scope.yaml`
- `autoresearch/archive/v006/scripts/evaluate_session.py`
- `autoresearch/archive/lineage.jsonl`
- `autoresearch/eval_suites/search-v1.json`
- `autoresearch/eval_suites/SCHEMA.md`
- `autoresearch/eval_suites/TAXONOMY.md`
- `autoresearch/GAPS.md` (Gaps 2, 3, 6, 17, 18, 26, 28, 30)

### src/evaluation/ files referenced
- `src/evaluation/models.py` (line 160)
- `src/evaluation/service.py` (lines 30-41, 49-56, 119-206, 208-234)
- `src/evaluation/rubrics.py` (lines 29-40)
- `src/evaluation/structural.py`
- `src/api/routers/evaluation.py` (lines 40-108)
- `src/api/main.py` (lines 103-166)

### Plan + catalog files
- `docs/plans/2026-04-20-002-feat-automated-audit-pipeline-plan.md` (R3, R7, R8, R14, R16, R18-R26, U1, U4, U5)
- `docs/plans/2026-04-22-005-marketing-audit-lens-catalog.md` (§Architectural Patterns, §Marketing-Areas View, §Conditional Bundles, §Decision History)
- `docs/plans/2026-04-22-006-marketing-audit-lens-ranking.md` (tier structure + cutoff)
- `docs/plans/2026-04-23-003-agency-integration-plan.md` (Decision 7, Bundle 9, Bundle 10 §7.1-§7.6)
- `docs/plans/2026-04-23-004-ral-runtime-design.md` (parallel design — workload-agnostic runtime)
