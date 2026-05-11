# autoresearch_v2 — AI-first substrate

This is the v2 evolution substrate. It replaces `autoresearch/` (14,374 LOC) with
a leaner, prose-driven wrapper around the existing session runtime and judge HTTP
services.

The v2 thesis (ratified in
`docs/research/2026-05-11-001-substrate-feature-audit-evidence-based.md`): ~11k
LOC of the v1 substrate was defending against problems that don't occur when you
trust the agent. v2 keeps the load-bearing pieces (holdout isolation, judge
separation, critique-manifest hash, alert agent, backend abstraction) and
collapses the rest into prose the agent reads.

## Reading order

1. `docs/research/2026-05-09-001-autoresearch-overengineering-audit.md` — architectural framing
2. `docs/research/2026-05-09-003-autoresearch-bare-bones-rewrite-handoff.md` — target shape
3. `docs/research/2026-05-11-001-substrate-feature-audit-evidence-based.md` — per-feature verdicts
4. `docs/plans/2026-05-11-001-refactor-autoresearch-substrate-simplification-plan.md` — execution plan
5. `autoresearch.md` — the driver prompt the agent runs (loop forever)
6. `lanes/<lane>.md` — per-lane prose the agent edits

## Layout

```
autoresearch_v2/
├── README.md
├── autoresearch.md          # driver prompt (U9)
├── tools/                   # callable tools the agent invokes (U2-U7)
│   ├── run_experiment.py        # wraps archive/v006/run.py subprocess
│   ├── score_holdout.py         # calls evolution-judge :7200 over 6 holdout fixtures
│   ├── log_experiment.py        # git commit / reset + results.tsv append
│   ├── verify_critique_integrity.py  # critique-manifest SHA256 check
│   ├── alert_check.py           # LLM alert agent on results.tsv trajectory
│   ├── inspect.py               # freddy autoresearch frontier/topk/show/...
│   └── render_report.py         # (U10+) wraps archive/v006/scripts/render_report.py
├── harness/                 # slim wrapper layer (U8)
│   ├── backend.py               # multi-provider router (~80 LOC)
│   ├── opencode_jsonl.py        # transient-error detection (~50 LOC)
│   ├── telemetry.py             # freddy session start/end/iteration push (~80 LOC)
│   ├── sessions.py              # viable_resume_id + ensure_materialized_runtime shim (~50 LOC)
│   ├── events.py                # audit log (kept verbatim from v1)
│   ├── concurrency.py           # 1 semaphore via MAX_PARALLEL_AGENTS (~20 LOC)
│   └── judge_calibration.py     # judge drift detection (kept verbatim)
├── lanes/                   # per-lane prose + per-lane state
│   ├── geo.md
│   ├── geo/results.tsv          # untracked ledger; one row per attempted experiment
│   └── geo/attempts/<sha>/      # untracked per-attempt session deliverables
└── judges -> ../autoresearch/judges/   # symlink (vestigial; see "Judges" below)
```

## Judges

The 4 judge HTTP services are NOT physically inside `autoresearch_v2/`. They
live at the repo's top-level `judges/` directory and are reached over HTTP:

- `judges/session/` — session-judge service (:7100)
- `judges/evolution/` — evolution-judge service (:7200)
- `judges/inner_critique/` — inner-critique subprocess (no HTTP)
- `judges/promotion_judge.py` and `autoresearch/judges/promotion_judge.py` — promotion-judge

The symlink `autoresearch_v2/judges -> ../autoresearch/judges/` is preserved as
a pointer for compatibility with any tool that uses the v1 module path. v2's
own tools speak HTTP to the running services, not Python imports.

## Operator model

The agent's loop, in pseudo-prose (the actual prose is in `autoresearch.md`):

```
read lanes/<lane>/results.tsv (the ledger)
pick a parent commit (anti-drift floor: composite >= top-1 * 0.7)
edit lanes/<lane>.md in place
tools/run_experiment.py --domain <lane> --fixture <fid>  # 1-fixture sniff
if sniff looks good:
    tools/score_holdout.py --lane <lane>                 # 6-fixture holdout
    tools/log_experiment.py keep|discard|crash|checks_failed
        keep    -> git commit, append results.tsv
        discard -> git reset --hard, append results.tsv with pre-reset sha
tools/alert_check.py --lane <lane>                       # only after a keep
LOOP FOREVER
```

## State on disk

- `lanes/<lane>/results.tsv` — single source of truth per lane. UNTRACKED by
  git (`.gitignore`). Survives `git reset --hard discard` because it's not in
  the working tree's git index. Mirrors karpathy/autoresearch.
- `lanes/<lane>/attempts/<short-sha>/sessions/...` — per-attempt deliverables.
  UNTRACKED. Agent decides retention; JR can purge.
- `alerts.jsonl` — append-only log of alert-check findings. UNTRACKED.

## Concurrency

One env var: `MAX_PARALLEL_AGENTS` (default 1 = sequential). The 5 per-resource
semaphores from v1 are collapsed to one mutex; opencode parallelism was never
proven necessary at the per-resource level.

## Stream A flags (REQUIRED during measurement)

Any v2 measurement that compares against v006 baselines MUST export Stream A's
3 env flags:

```
export AUTORESEARCH_EVAL_FIX_AXIS_COLLAPSE=on
export AUTORESEARCH_EVAL_FIX_HOLDOUT=on
export AUTORESEARCH_EVAL_FIX_FRAGILE_FIXTURES=on
```

Without these, the holdout-v1 ≥ 4.5 gate is uninterpretable (Bug 2 fix). See
`docs/plans/2026-05-11-002-eval-pipeline-bug-fixes-plan.md` for context.
