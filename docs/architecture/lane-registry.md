---
title: "Lane registry — adding a lane to autoresearch"
date: 2026-04-28
status: active
---

# Lane registry — adding a lane to autoresearch

`autoresearch/lane_registry.py` is the single source of truth for per-lane data and divergent-behavior hooks. The 5 existing lanes (`core`, `geo`, `competitive`, `monitoring`, `storyboard`) are `LaneSpec` instances; new lanes register their own.

## LaneSpec field reference

| Field | Type | Purpose |
|---|---|---|
| `name` | `str` | Lane identifier — must match the key under which the spec is registered in `LANES`. |
| `is_workflow_lane` | `bool` | `True` for research-shaped lanes (geo / competitive / monitoring / storyboard / new lanes that follow the same shape). `False` only for the `core` lane today; non-workflow lanes own everything outside workflow path prefixes. |
| `rubric_ids` | `tuple[str, ...]` | The 8 LLM-judge criterion IDs scored for this lane (e.g. `("GEO-1", …, "GEO-8")`). Cross-checked at module load against `src/evaluation/rubrics.py`. |
| `path_prefixes` | `tuple[str, ...]` | Files this lane owns inside a variant. Used by `lane_paths.path_owned_by_lane`. Empty for `core` (it owns by exclusion). |
| `session_md_filename` | `str` | The lane's session-evaluator program file under `programs/` (e.g. `"geo-session.md"`). |
| `deliverables` | `tuple[str, ...]` | Glob(s) for the lane's primary output file(s) — what `_has_deliverables` checks for and what LLM judges score. |
| `intermediate_artifacts` | `tuple[str, ...]` | Glob(s) for outputs produced mid-session that prove real work happened (used by `_has_deliverables` as a fallback). |
| `structural_doc_facts` | `tuple[str, ...]` | The bullets that get rendered into `programs/<lane>-session.md`'s `## Structural Validator Requirements` block. |
| `structural_gate_functions` | `tuple[str, ...]` | Names of the gate-function checks the structural validator runs for this lane. The bidirectional paired test in `tests/autoresearch/test_structural_doc_facts.py` enforces that bullets and gates stay in sync. |
| `custom_mutate` | `Callable \| None` | Optional override for the meta-agent invocation in `evolve.cmd_run`. `None` → run the default meta-agent. Used by `harness_fixer` to invoke `harness/engine.py`'s fix-verify loop. |
| `custom_score` | `Callable \| None` | Optional override for `_score_variant_search`. `None` → default geometric-mean scoring. Used by `marketing_audit` (weighted-sum + cost penalty) and `harness_fixer` (HM-1..HM-8 weighted). |
| `custom_validate` | `Callable \| None` | Optional pre-scoring gate. `None` → no extra check. Used by `marketing_audit` (stage-prompt manifest) and `harness_fixer` (verifier.md SHA256). Returns `False` to discard the variant without scoring. |
| `custom_promote` | `Callable \| None` | Optional gate during `evolve.cmd_promote`. `None` → no extra check. Used by `marketing_audit` for a pre-promotion smoke test. |
| `custom_objective_score_from_entry` | `Callable \| None` | Optional override for `frontier.objective_score`. `None` → default (composite for non-workflow, `domains[lane].score` for workflow). Used by `marketing_audit` for time-varying engagement-weighted fitness. |

## Adding a research-shaped lane

A research-shaped lane (geomean × geomean scoring, session.md deliverable, structural gates) requires exactly **2 file edits**:

1. **`autoresearch/lane_registry.py`** — add a `LaneSpec` entry to `LANES`.
2. **`src/evaluation/rubrics.py`** — add 8 criterion prompts and bump the `assert len(RUBRICS) == N` line.

Worked example — `code_review` lane:

```python
# autoresearch/lane_registry.py
LANES["code_review"] = LaneSpec(
    name="code_review",
    is_workflow_lane=True,
    rubric_ids=_rubric_ids("CR"),
    path_prefixes=(
        "code_review-findings.md",
        "programs/code_review-session.md",
        "templates/code_review",
        "workflows/code_review.py",
        "workflows/session_eval_code_review.py",
    ),
    session_md_filename="code_review-session.md",
    deliverables=("review.md",),
    structural_doc_facts=(
        "`review.md` exists with non-empty content.",
        "`review.md` contains at least one suggested change with a file:line anchor.",
    ),
    structural_gate_functions=(
        "_validate_code_review.review_exists",
        "_validate_code_review.has_anchored_change",
    ),
)
```

Then add `CR-1`..`CR-8` to `RUBRICS` in `src/evaluation/rubrics.py` and bump the assertion. That's it. Every consumer (`for domain in DOMAINS`, `for lane in LANES`, etc.) starts seeing the new lane automatically because those constants are derived from the registry.

The plan also documents one Known Divergence Point that may also need a touch (`STRUCTURAL_DOC_FACTS` if/if/if validator dispatch in `src/evaluation/structural.py:38-46` — a 1-line addition for a new structural validator). See `docs/plans/2026-04-27-002-feat-autoresearch-lane-registry-plan.md` §"Known Divergence Points" for the seven deferred axes.

## Adding a divergent lane

A divergent lane (different scoring, custom mutate, file-bytes manifest, etc.) registers a `LaneSpec` with one or more `custom_*` callables set:

```python
# Marketing audit (illustrative — actual marketing_audit lives behind its own plan)
from src.audit.score import marketing_audit_score
from src.audit.validate import marketing_audit_validate

LANES["marketing_audit"] = LaneSpec(
    name="marketing_audit",
    is_workflow_lane=True,
    rubric_ids=("MA-1", "MA-2", "MA-3", "MA-4", "MA-5", "MA-6", "MA-7", "MA-8"),
    # … data fields per research-shaped pattern …
    custom_score=marketing_audit_score,           # weighted-sum + cost penalty
    custom_validate=marketing_audit_validate,     # file-bytes manifest
    # custom_mutate=None → uses default meta-agent
)
```

The 5 callables hook into `evolve.cmd_run` / `evolve.cmd_promote` automatically — divergent lanes never edit `evolve.py`.

## Shared file-bytes manifest utilities

For lanes that need to lock specific markdown files at clone time and verify them later:

```python
from autoresearch.lane_registry import file_hash, compute_manifest, verify_manifest

# At clone time:
manifest = compute_manifest(
    [variant_dir / "harness/prompts/fixer.md", variant_dir / "harness/prompts/verifier.md"],
    variant_dir,
)
(variant_dir / "manifest.json").write_text(json.dumps(manifest))

# At validate time (custom_validate):
passed, failures = verify_manifest(variant_dir / "manifest.json", variant_dir)
if not passed:
    print("manifest drift:", failures)
    return False
```

These three primitives are intentionally split (`file_hash` for one file, `compute_manifest` for snapshot, `verify_manifest` for re-check) so divergent lanes share iteration logic, not just the hash primitive.

## When to use `custom_*` callables vs default behavior

- **Default behavior (callable = None)** — when the lane fits the existing research-shaped pattern: geomean × geomean of 8 LLM-judge scores, single session.md deliverable, meta-agent-driven mutation, structural gates declared in `structural_doc_facts`. All 5 existing lanes (`core` + 4 workflow) use defaults.
- **`custom_score`** — when the lane scores by anything other than geomean of LLM judges (e.g., weighted sum, cost penalty, externally-reported metrics).
- **`custom_validate`** — when the lane has invariants that should fail-fast before the (expensive) scoring step (e.g., file-bytes manifest verification).
- **`custom_promote`** — when promotion needs an extra check beyond the standard search-metrics-present + promotability rule (e.g., pre-promotion smoke test).
- **`custom_mutate`** — when the lane's "mutation" mechanism isn't the meta-agent (e.g., a fix-verify engine, an external suggestion source).
- **`custom_objective_score_from_entry`** — when the per-lane scalar selection signal isn't `composite` or `domains[lane].score` (e.g., time-varying engagement-weighted fitness on lineage entries that grow over time).

## See also

- `docs/plans/2026-04-27-002-feat-autoresearch-lane-registry-plan.md` — the full plan, including the 7 Known Divergence Points and rationale for each.
- `autoresearch/lane_registry.py` — module docstring + accessors.
- `tests/autoresearch/test_lane_registry.py` — the 23 tests that exercise the registry, accessors, runtime assertion, and manifest utilities.
