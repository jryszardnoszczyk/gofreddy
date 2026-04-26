# Autoresearch

Production autoresearch now has one architecture:

- `autoresearch/run.sh` is the production entrypoint and fixed bootstrap
- `autoresearch/runtime_bootstrap.py` resolves the active production runtime
- `autoresearch/archive/current.json` stores promoted heads per lane
- `autoresearch/archive/current_runtime/` is a derived materialized runtime cache when lane heads are active
- `autoresearch/evolve.sh` is the production outer evolution loop
- `autoresearch/evaluate_variant.py` is the fixed outer evaluator orchestrator
- `autoresearch/eval_suites/search-v1.json` defines the public search benchmark
- `autoresearch/archive/index.json` + `autoresearch/archive/frontier.json` are the proposer-facing search-only archive views
- `src/evaluation/` is the fixed server-side evolution judge
- the meta agent backend and the evaluator backend are configured independently

The old shell orchestration path (`run-all.sh`, `outer_loop.sh`, `lib.sh`, `*-session.sh`) has been retired.

## Fixture authoring

See `autoresearch/eval_suites/SCHEMA.md` (pointer index) for schema + pool layout.

CLI: `freddy fixture validate | list | envs | staleness | refresh | dry-run | discriminate`. Holdout authoring, pool migration, and rotation-policy proposals are agent-driven tasks (see Plan B Phase 2 Step A, Phase 4 Step 2, and the `rotation-policy.md` task spec) — each composes existing primitives and calls the existing `system_health_agent`. No new CLI commands, no specialized agents beyond the four already specced (promotion / rollback / canary / system_health). `freddy fixture --help` is authoritative.

## Production Runner

Run one or more domains through the promoted production variant:

```bash
./autoresearch/run.sh --domain geo
./autoresearch/run.sh --domain geo,competitive
./autoresearch/run.sh --resume
./autoresearch/run.sh --dry-run
```

For monitoring in production, pass a real monitor UUID or export `AUTORESEARCH_MONITORING_CONTEXT`. The old placeholder UUID is no longer treated as runnable production input.

For evolution scoring, monitoring fixture contexts come from the public search suite manifest via env references. Create each monitor first via `POST /v1/monitors` (name, keywords, sources=[twitter, instagram, reddit]) — the response id is the UUID to export:

```bash
export AUTORESEARCH_SEARCH_MONITORING_SHOPIFY_CONTEXT="<monitor-uuid>"
export AUTORESEARCH_SEARCH_MONITORING_LULULEMON_CONTEXT="<monitor-uuid>"
export AUTORESEARCH_SEARCH_MONITORING_NOTION_CONTEXT="<monitor-uuid>"
export AUTORESEARCH_SEARCH_MONITORING_RIPPLING_CONTEXT="<monitor-uuid>"
export AUTORESEARCH_SEARCH_MONITORING_RAMP_CONTEXT="<monitor-uuid>"   # shared by ramp-arc-t0 + ramp-arc-t1
```

`run.sh` is a thin wrapper around:

```bash
python3 autoresearch/runtime_bootstrap.py
```

## Evolution Loop

Run the production outer loop:

```bash
./autoresearch/evolve.sh score-current
./autoresearch/evolve.sh score-current --lane geo
./autoresearch/evolve.sh seed-baseline
./autoresearch/evolve.sh --iterations 1 --candidates-per-iteration 3
./autoresearch/evolve.sh --lane all --iterations 1 --candidates-per-iteration 1
./autoresearch/evolve.sh finalize
./autoresearch/evolve.sh promote
./autoresearch/evolve.sh rollback
```

The evolution loop:

1. refreshes the public archive index and frontier
2. snapshots the current archive for parent sampling during that cycle
3. selects parents with a fixed handcrafted score-child-prop policy over eligible variants in the active lane
4. creates `N` children per iteration under `autoresearch/archive/` (`--candidates-per-iteration`, default `3`)
5. launches the editable meta layer in a lane-shaped proposer workspace
6. evaluates each child against the lane-projected search suite
7. refreshes lineage, frontier membership, and variant manifests

Lanes:

- `core` evolves shared runtime behavior under all-domain pressure
- `geo`, `competitive`, `monitoring`, and `storyboard` evolve workflow-owned paths only
- `--lane all` runs the selected operator command across all five lanes sequentially

Search-scored variants remain pending final evaluation internally with `promotion_summary.reason = "holdout_required"`, but that state is not exposed in the proposer-facing archive.

`evolve.sh finalize` now runs the hidden holdout privately over the active lane frontier and automatically promotes the best finalized candidate that still beats that lane’s current promoted baseline.

`evolve.sh promote` is now autonomous in holdout mode. It promotes the best already-finalized candidate for the active lane holdout suite; there is no operator-picked finalist path anymore. Final promotion uses the active lane objective only; ties and lower scores do not promote.

The outer evaluator requires explicit settings:

```bash
export EVOLUTION_EVAL_BACKEND=codex
export EVOLUTION_EVAL_MODEL=gpt-5.4
export EVOLUTION_EVAL_REASONING_EFFORT=high
```

### OpenCode (multi-provider via OpenRouter / OSS models)

To run autoresearch with open-source models or OpenRouter-hosted Anthropic/OpenAI models, install OpenCode (`curl -fsSL https://opencode.ai/install | bash`) and configure credentials with `opencode auth login`. Then:

```bash
export META_BACKEND=opencode                                    # evolve meta-agent
export EVOLUTION_EVAL_BACKEND=opencode                          # per-variant eval subprocess
export EVOLUTION_EVAL_MODEL=openrouter/deepseek/deepseek-v3
export AUTORESEARCH_SESSION_BACKEND=opencode                    # harness fixer/verifier
export AUTORESEARCH_SESSION_MODEL=openrouter/deepseek/deepseek-v3
```

OpenCode handles its own authentication via `~/.local/share/opencode/auth.json` — no `OPENROUTER_API_KEY` is needed in `.env` for OpenCode-routed paths. If you also want the parent-selection JSON judge in `agent_calls.py` routed through OpenRouter (rather than OpenAI direct), set:

```bash
export AUTORESEARCH_PARENT_BASE_URL=https://openrouter.ai/api/v1
export AUTORESEARCH_PARENT_API_KEY=sk-or-...
```

Hidden holdouts are loaded only from non-repo env sources:

```bash
export EVOLUTION_HOLDOUT_MANIFEST=/private/path/holdout-v1.json
# or
export EVOLUTION_HOLDOUT_JSON='{"suite_id":"holdout-v1", ...}'
```

Detailed private holdout outputs and finalized shortlists can be written outside the repo:

```bash
export EVOLUTION_PRIVATE_ARCHIVE_DIR=/private/path/autoresearch-holdouts
```

If `EVOLUTION_PRIVATE_ARCHIVE_DIR` is not set, autoresearch falls back to a private cache under the system temp directory (`$(python3 -c 'import tempfile; print(tempfile.gettempdir())')/autoresearch-holdouts`). Hidden-holdout results for promoted baselines are cached there and reused on later finalization attempts. Finalized shortlist files are stored there as operator-private artifacts.

The promoted production configuration is stored in `autoresearch/archive/current.json`. The bootstrap materializes `archive/current_runtime/` from the active lane heads while preserving runtime state directories like `sessions/`, `metrics/`, and `runs/`. Lane heads may point at the same variant id until a lane actually forks.

### Autonomous promotion + rollback (Plan B Phase 6)

After each `evolve.sh run` iteration's finalize step, two agent-driven bookkeeping calls run automatically:

1. **`is_promotable(archive_dir, variant_id, lane)`** — gathers the full scoring context (primary + secondary judge scores across fixtures, holdout composites, per-fixture breakdowns, lane promotion history) and POSTs to the evolution-judge at `${EVOLUTION_JUDGE_URL}/invoke/decide/promotion`. The promotion agent returns `promote` / `reject` / `abstain` with reasoning. No hardcoded thresholds. One programmatic invariant: wrong-lane short-circuit (the judge is never asked to decide about a lane-mismatched variant — that's a data bug, not a judgment call). Abstain verdicts AND any `concerns[*].severity == "blocking"` flag both return False — belt + suspenders.

2. **`check_and_rollback_regressions(archive_dir, lane)`** — emits `kind="head_score"` for the newly-promoted head, then asks the rollback agent whether the post-promotion trajectory warrants reverting. Programmatic invariants (not judgments):
   - Cooldown: ≥3 post-promotion cycles between two consecutive rollbacks on the same lane
   - Needs prior head + ≥2 post-promotion samples on the current head
   - Dry-run window: while `datetime.utcnow() < ROLLBACK_DRY_RUN_UNTIL_ISO` (default `2026-05-15T00:00:00Z`), rollback decisions are LOGGED with `decision="rollback_dry_run"` but the `promote --undo` subprocess is NOT run. Operator audits the agent's judgment before it gets write access.

### Judge calibration drift

Run monthly (operator cron):

```bash
python3 autoresearch/judge_calibration.py --check
```

Delegates bi-directional cross-family drift detection to the evolution-judge (Claude judging Codex's baseline-vs-current traces AND vice versa). Pairs config at `~/.config/gofreddy/calibration-pairs.json` (operator-maintained; PR-gated mirror on judge-service side). Exit 0 = stable; exit 1 = drift detected (`magnitude_drift` / `variance_drift` / `reasoning_drift` / `mixed`); exit 2 = configuration error.

### Unified events log

All agent decisions land in `~/.local/share/gofreddy/events.jsonl`. Kinds:

| kind | emitted when |
|---|---|
| `promotion_decision` | every `is_promotable` call (promote/reject/abstain) |
| `judge_abstain` | low-confidence or blocking-severity concerns |
| `judge_unreachable` | evolution-judge HTTP errors / malformed response |
| `head_score` | after each promotion, feeds rollback agent |
| `regression_check` | every `check_and_rollback_regressions` call |
| `judge_drift` | monthly calibration check verdict |
| `content_drift` | `freddy fixture refresh` detects content-hash drift |
| `saturation_cycle` | per-fixture saturation verdicts (emitted by autoresearch) |

Sample queries:

```bash
jq 'select(.kind == "promotion_decision")' ~/.local/share/gofreddy/events.jsonl | tail -5
jq 'select(.kind == "regression_check" and .decision == "rollback")' ~/.local/share/gofreddy/events.jsonl
jq 'select(.kind == "judge_drift")' ~/.local/share/gofreddy/events.jsonl
```

## Evaluators

Autoresearch intentionally uses two evaluator layers:

1. Session-time evaluator inside the archive
   - `autoresearch/archive/current_runtime/scripts/evaluate_session.py`
   - evolvable session-time critique owned by the variant
   - uses trusted external judge execution via the existing `freddy` / API / service evaluation stack
   - informs rework and completion guards, but is not authoritative for search or promotion
2. Evolution-time evaluator outside the archive
   - `src/evaluation/`
   - `cli/freddy/commands/evaluate.py`
   - `src/api/routers/evaluation.py`
   - used by `autoresearch/evaluate_variant.py`

This split is deliberate: session critique is evolvable, outer-loop reward is fixed.

## Main Files

```text
autoresearch/
  eval_suites/
    search-v1.json
  run.sh
  runtime_bootstrap.py
  lane_runtime.py
  lane_paths.py
  evolve.sh
  select_parent.py
  evaluate_variant.py
  frontier.py
  archive_index.py
  archive/
    current.json
    current -> v001
    current_runtime/
    index.json
    frontier.json
    lineage.jsonl
    v001/
      run.py
      run.sh
      meta.md
      programs/
      templates/
      scripts/
```

## Notes

- the materialized production runtime defaults to `multiturn` for real sessions.
- `evaluate_variant.py` forces `fresh` for benchmark scoring, projects suites by lane, and reads suite definitions from JSON manifests.
- Public archive views are search-only; they intentionally omit hidden-holdout outcomes and current promoted winner identity.
- Lane archive views are logical only; `archive/index.json` and `archive/frontier.json` are the authoritative public archive outputs.
- Monitoring benchmark windows can be pinned with `AUTORESEARCH_WEEK_START` / `AUTORESEARCH_WEEK_END`.
- Files are the source of truth for session state. The runner strategy may change, but the state contract does not.
