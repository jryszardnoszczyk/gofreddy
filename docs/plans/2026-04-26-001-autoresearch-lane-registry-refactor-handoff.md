# Autoresearch lane-registry refactor — agent prompt

**Created:** 2026-04-26
**Target:** implementation agent (autonomous, ~5-7 days wall-clock)
**Branch policy:** spawn on a fresh branch off `main` (e.g., `refactor/autoresearch-lane-registry`); land via PR

Paste everything below this line as the agent's input.

---

## ROLE

You are an implementation agent. Refactor only. You are NOT adding new lanes. You are NOT changing behavior. You are extracting a single source of truth for autoresearch's lane definitions so that adding a new lane becomes a registry entry, not a 14-site edit.

## GOAL

Replace 23 independent lane-name enumerations across `autoresearch/` and `src/evaluation/` with one `LaneRegistry` that aligns with the existing partial registry (`workflows/specs.py:WorkflowSpec` + `workflows/session_eval_registry.py:SESSION_EVAL_SPECS`). Behavior must remain bit-identical for the 4 existing workflow lanes (geo, competitive, monitoring, storyboard) plus the non-workflow `core` lane. The existing test suite is the contract.

## CONTEXT

The autoresearch platform has 4 workflow lanes (geo, competitive, monitoring, storyboard) + 1 non-workflow `core` lane. The framework was extended lane-by-lane via copy-paste. Today, lane-name data lives in **23 independent sites**; per-lane workflow + evaluator runtime files share structural skeletons but live as 4 forks each.

A partial registry pattern already exists for the workflow + evaluator runtime layer:

- `autoresearch/archive/current_runtime/workflows/specs.py` defines `WorkflowSpec` (frozen dataclass per workflow lane, holding runtime hooks like `configure_env`, `pre_summary_hooks`, `snapshot_evaluations`, `completion_guard`, `count_findings`, etc.)
- `autoresearch/archive/current_runtime/workflows/session_eval_registry.py` defines `SESSION_EVAL_SPECS: dict[str, SessionEvalSpec]` aggregating the four `session_eval_<lane>.py` SPEC objects.

What's missing is the **lane-name + criteria + paths + structural-doc** dimension — that data is forked across 23 sites with no single source of truth. Your job is to add that dimension as a new `LaneSpec` registry that complements (not replaces) the existing two registries.

Two new lanes are being designed elsewhere: `marketing_audit` (full plan committed at `origin/plan/audit-engine-fusion-v1`) and `harness_fixer` (brainstorm in flight). **Neither is in scope for this refactor.** They are downstream consumers of your work and must NOT be added by you.

Python version: `>=3.13,<3.14` per `pyproject.toml`. `Literal[*expr]` unpacking is supported.

## REQUIRED READING (before any code edit)

Read each, take notes on what data the surrounding code consumes from the enumeration:

1. `autoresearch/lane_paths.py` (full file — `LANES` at `:36`, `WORKFLOW_PREFIXES` at `:44-77`)
2. `autoresearch/lane_runtime.py` (full file — `LANES` at `:12`, `_sync_filtered` at `:84-114`, `resolve_runtime_dir` at `:66`)
3. `autoresearch/evolve.py` (full file — `ALL_LANES` at `:44`, `run_all_lanes` at `:453`)
4. `autoresearch/frontier.py` (full file — `DOMAINS` at `:15`, `LANES` at `:16`, `objective_score` at `:76-86`, `domain_score` at `:62-68`)
5. `autoresearch/program_prescription_critic.py` (full file — `DOMAINS` at `:41`, consumer at `:301-306`)
6. `autoresearch/evaluate_variant.py` — focus on `DELIVERABLES` at `:44-49`, `_INTERMEDIATE_ARTIFACTS` at `:53-56`, `_INNER_PHASE_TAGS` at `:744`, L1 marker check at `:588`, consumer at `:432-436`, the `for domain in DOMAINS` iterations across the file (`:144`, `:151`, `:155`, `:167`, `:170`, `:253`, `:351`, `:1086`, `:1118-20`, `:1133`, `:1648-51`, `:2160`, `:2177`, `:2182`, `:2188`, `:2226-50` — all auto-propagate from frontier.DOMAINS)
7. `autoresearch/regen_program_docs.py` (full file — `DOMAIN_FILENAMES` at `:40-45`, paired sanity check at `:166-172`)
8. `autoresearch/archive/current_runtime/scripts/evaluate_session.py` — argparse `choices` at `:402` (note: also exists at `archive/v001/...:375` and `archive/v006/...:402` as historical snapshots; do NOT edit those)
9. `autoresearch/archive/current_runtime/workflows/specs.py` — full file
10. `autoresearch/archive/current_runtime/workflows/session_eval_registry.py` — full file
11. `autoresearch/archive/current_runtime/workflows/{geo,competitive,monitoring,storyboard}.py` — read at least one in detail (e.g., geo.py)
12. `autoresearch/archive/current_runtime/workflows/session_eval_{geo,competitive,monitoring,storyboard}.py` — read at least one
13. `autoresearch/archive/current_runtime/workflows/session_eval_common.py`
14. `autoresearch/test_lane_ownership.py` — full file (existing test that exercises lane-ownership invariants)
15. `tests/autoresearch/conftest.py` — full file (`frontier.DOMAINS` stub at `:43`, `WORKFLOW_LANES=()` at `:50`)
16. `src/evaluation/structural.py` — full file (dispatch at `:38-46`, `STRUCTURAL_DOC_FACTS` at `:405`, `STRUCTURAL_GATE_FUNCTIONS` at `:444`)
17. `src/evaluation/service.py` — full file (`_DOMAIN_PREFIXES` at `:30-33`, `_DOMAIN_CRITERIA` at `:36-41`, `_JUDGE_PRIMARY_DELIVERABLE` at `:49-56`, consumers at `:61` + `:251`)
18. `src/evaluation/models.py` — focus on `EvaluateRequest.domain` Literal at `:160`
19. `src/evaluation/rubrics.py` — focus on `RUBRICS` dict at `:949-986` and `assert len(RUBRICS) == 32` at `:1001`
20. `pyproject.toml` — confirm `requires-python` (should be 3.13)

If anything in `## VERIFIED ENUMERATION SITES` below points to a path that doesn't match what you find on disk, **stop and escalate** — the audit may be stale.

## VERIFIED ENUMERATION SITES (23 confirmed as of 2026-04-26)

Migrate every site to the new registry. The list below is exhaustive. If you discover a 24th site that holds lane-name data, **stop and escalate**.

### A. Lane-name tuples (5 lanes including `core`)

1. `autoresearch/lane_paths.py:36` — `LANES = ("core", "geo", "competitive", "monitoring", "storyboard")`
2. `autoresearch/lane_runtime.py:12` — `LANES = (same)`
3. `autoresearch/evolve.py:44` — `ALL_LANES = (same)`

### B. Workflow-lane tuples (4 lanes excluding `core`)

4. `autoresearch/frontier.py:15` — `DOMAINS = ("geo", "competitive", "monitoring", "storyboard")`; line 16 derives `LANES = ("core", *DOMAINS)`
5. `autoresearch/program_prescription_critic.py:41` — `DOMAINS = (same)`
6. `autoresearch/archive/current_runtime/scripts/evaluate_session.py:402` — argparse `choices=["geo", "competitive", "monitoring", "storyboard"]`
7. `tests/autoresearch/conftest.py:43` — pytest stub of `frontier.DOMAINS` for test isolation

### C. Lane-keyed dicts (per-lane data)

8. `autoresearch/lane_paths.py:44-77` — `WORKFLOW_PREFIXES: dict[str, tuple[str, ...]]` (per-lane owned-path prefixes; 5-7 prefix strings per lane; consumed by `lane_runtime._sync_filtered`)
9. `autoresearch/evaluate_variant.py:44-49` — `DELIVERABLES: dict[str, str]` (single glob per lane today; consumer at `:432-436`). **Migrate to `tuple[str, ...]` simultaneously per the marketing_audit plan's Unit 17 documented coupling — the consumer becomes `any(list(session_dir.glob(g)) for g in DELIVERABLES[domain])`.**
10. `autoresearch/evaluate_variant.py:53-56` — `_INTERMEDIATE_ARTIFACTS: dict[str, str]` (only `monitoring` + `storyboard` populated; consumer at `:435`; same migration to tuple).
11. `autoresearch/evaluate_variant.py:744` — `_INNER_PHASE_TAGS = frozenset({...})` (closed allowlist of phase-event row types; consumer at `:814` filters `results.jsonl` rows).
12. `autoresearch/evaluate_variant.py:588` — L1 marker file path: `for domain in DOMAINS: program_path = variant_dir / "programs" / f"{domain}-session.md"`. The DOMAINS reference auto-propagates; the path-format string is implicit.
13. `autoresearch/regen_program_docs.py:40-45` — `DOMAIN_FILENAMES: dict[str, str]` (per-lane session.md filename; paired sanity check at `:166-172` requires every `STRUCTURAL_DOC_FACTS` key to be a `DOMAIN_FILENAMES` key — adding to one without the other emits a warning).
14. `src/evaluation/structural.py:38-46` — `structural_gate` dispatch (if/if/if chain routing each domain to its `_validate_<domain>` function; the validators themselves are domain-specific and stay).
15. `src/evaluation/structural.py:405` — `STRUCTURAL_DOC_FACTS: dict[str, list[str]]` (per-lane structural-gate descriptions consumed by the AUTOGEN block in session.md).
16. `src/evaluation/structural.py:444` — `STRUCTURAL_GATE_FUNCTIONS: dict[str, tuple[str, ...]]` (per-lane named gate functions; paired test in `tests/evaluation/test_structural.py` enforces this matches `STRUCTURAL_DOC_FACTS`).
17. `src/evaluation/service.py:30-33` — `_DOMAIN_PREFIXES: dict[str, str]` (sparse — only `geo` + `storyboard` populated; consumer at `:251`).
18. `src/evaluation/service.py:36-41` — `_DOMAIN_CRITERIA: dict[str, list[str]]` (per-lane rubric criterion IDs).
19. `src/evaluation/service.py:49-56` — `_JUDGE_PRIMARY_DELIVERABLE: dict[str, tuple[str, ...]]` (per-lane judge-input file selection; sparse — only `monitoring` + `competitive` populated; consumer at `:61` does `\n\n`.join concat).

### D. Type-level / module-load constants

20. `src/evaluation/models.py:160` — `domain: Literal["geo", "competitive", "monitoring", "storyboard"]` on `EvaluateRequest`. Use `Literal[*lane_registry.workflow_lanes()]` (Python 3.13 supports it).
21. `src/evaluation/rubrics.py:1001` — `assert len(RUBRICS) == 32` (8 per workflow lane × 4 lanes; magic number).

### E. Existing partial registry (extend or compose; do NOT duplicate)

22. `autoresearch/archive/current_runtime/workflows/specs.py` — `WorkflowSpec` dataclass (already structured per-lane, holds workflow runtime hooks).
23. `autoresearch/archive/current_runtime/workflows/session_eval_registry.py` — `SESSION_EVAL_SPECS: dict[str, SessionEvalSpec]`.

The new `LaneSpec` complements these by holding lane-name + criteria + paths + structural-doc data. Add a runtime cross-check at module load asserting that every workflow lane in `LANE_REGISTRY` has matching entries in `WorkflowSpec` registry and `SESSION_EVAL_SPECS`.

## DELIVERABLE — code changes

### Step 1: Create `autoresearch/lane_registry.py` (new file)

```python
# autoresearch/lane_registry.py
"""
Single source of truth for autoresearch lane definitions.

Adding a lane:
  (1) Add a LaneSpec entry to LANE_REGISTRY below.
  (2) Create the workflow + evaluator files following the geo.py /
      session_eval_geo.py templates; register the SPEC objects in
      workflows/specs.py + workflows/session_eval_registry.py.
  (3) Add the lane's rubric prompts to src/evaluation/rubrics.py.
  (4) Done. No other files need editing.
"""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class LaneSpec:
    name: str                                     # "geo", "core", etc.
    display_name: str                             # human-readable
    is_workflow_lane: bool                        # True for 4 workflow lanes; False for "core"
    rubric_ids: tuple[str, ...]                   # () for core; ("GEO-1", ..., "GEO-8") for geo
    path_prefixes: tuple[str, ...]                # values today in WORKFLOW_PREFIXES[lane]
    session_md_filename: str                      # "geo-session.md"; "" for core
    judge_primary_deliverable: tuple[str, ...]    # values today in _JUDGE_PRIMARY_DELIVERABLE; () if not registered
    judge_prefix: str                             # value today in _DOMAIN_PREFIXES; "" if not registered
    deliverables: tuple[str, ...]                 # values today in DELIVERABLES (post tuple-migration)
    intermediate_artifacts: tuple[str, ...]       # values today in _INTERMEDIATE_ARTIFACTS; () if absent
    inner_phase_tags: frozenset[str]              # phase tags this lane emits in results.jsonl
    structural_doc_facts: tuple[str, ...]         # values today in STRUCTURAL_DOC_FACTS[lane]; () if no gates
    structural_gate_functions: tuple[str, ...]    # values today in STRUCTURAL_GATE_FUNCTIONS[lane]; () if no gates


LANE_REGISTRY: dict[str, LaneSpec] = {
    "core": LaneSpec(
        name="core",
        display_name="Core (autoresearch internal evolve target)",
        is_workflow_lane=False,
        rubric_ids=(),
        path_prefixes=...,  # transcribe from current code
        session_md_filename="",
        judge_primary_deliverable=(),
        judge_prefix="",
        deliverables=(),
        intermediate_artifacts=(),
        inner_phase_tags=frozenset(),
        structural_doc_facts=(),
        structural_gate_functions=(),
    ),
    "geo": LaneSpec(
        name="geo",
        display_name="GEO (Generative Engine Optimization)",
        is_workflow_lane=True,
        rubric_ids=("GEO-1", "GEO-2", "GEO-3", "GEO-4", "GEO-5", "GEO-6", "GEO-7", "GEO-8"),
        path_prefixes=...,                  # transcribe from WORKFLOW_PREFIXES["geo"]
        session_md_filename="geo-session.md",
        judge_primary_deliverable=...,      # transcribe (sparse — () if not in _JUDGE_PRIMARY_DELIVERABLE)
        judge_prefix=...,                    # transcribe from _DOMAIN_PREFIXES["geo"] (GEO_PREFIX constant)
        deliverables=...,                    # transcribe DELIVERABLES["geo"] glob, wrapped in tuple
        intermediate_artifacts=(),
        inner_phase_tags=...,                # transcribe subset of _INNER_PHASE_TAGS that geo emits
        structural_doc_facts=...,            # transcribe from STRUCTURAL_DOC_FACTS["geo"]
        structural_gate_functions=...,       # transcribe from STRUCTURAL_GATE_FUNCTIONS["geo"]
    ),
    "competitive": LaneSpec(...),  # similar
    "monitoring":  LaneSpec(...),  # similar
    "storyboard":  LaneSpec(...),  # similar
}


# Accessors:
def all_lanes() -> tuple[str, ...]:
    """All 5 lanes including 'core'."""
    return tuple(LANE_REGISTRY.keys())

def workflow_lanes() -> tuple[str, ...]:
    """4 workflow lanes (excludes 'core')."""
    return tuple(name for name, spec in LANE_REGISTRY.items() if spec.is_workflow_lane)

def get_spec(name: str) -> LaneSpec:
    """Raises KeyError on miss."""
    return LANE_REGISTRY[name]

def workflow_prefixes() -> dict[str, tuple[str, ...]]:
    return {name: spec.path_prefixes for name, spec in LANE_REGISTRY.items() if spec.is_workflow_lane}

def domain_criteria() -> dict[str, list[str]]:
    return {name: list(spec.rubric_ids) for name, spec in LANE_REGISTRY.items() if spec.is_workflow_lane}

def domain_prefixes() -> dict[str, str]:
    """Sparse — only lanes with non-empty judge_prefix."""
    return {name: spec.judge_prefix for name, spec in LANE_REGISTRY.items() if spec.judge_prefix}

def judge_primary_deliverable() -> dict[str, tuple[str, ...]]:
    """Sparse — only lanes with non-empty judge_primary_deliverable."""
    return {name: spec.judge_primary_deliverable for name, spec in LANE_REGISTRY.items() if spec.judge_primary_deliverable}

def deliverables() -> dict[str, tuple[str, ...]]:
    return {name: spec.deliverables for name, spec in LANE_REGISTRY.items() if spec.is_workflow_lane}

def intermediate_artifacts() -> dict[str, tuple[str, ...]]:
    """Sparse — only lanes that emit intermediate artifacts."""
    return {name: spec.intermediate_artifacts for name, spec in LANE_REGISTRY.items() if spec.intermediate_artifacts}

def inner_phase_tags() -> frozenset[str]:
    """Union of all lanes' phase tags (replaces the closed allowlist at evaluate_variant.py:744)."""
    union: set[str] = set()
    for spec in LANE_REGISTRY.values():
        union.update(spec.inner_phase_tags)
    return frozenset(union)

def domain_filenames() -> dict[str, str]:
    return {name: spec.session_md_filename for name, spec in LANE_REGISTRY.items() if spec.session_md_filename}

def structural_doc_facts() -> dict[str, list[str]]:
    return {name: list(spec.structural_doc_facts) for name, spec in LANE_REGISTRY.items() if spec.structural_doc_facts}

def structural_gate_functions() -> dict[str, tuple[str, ...]]:
    return {name: spec.structural_gate_functions for name, spec in LANE_REGISTRY.items() if spec.structural_gate_functions}

def total_rubric_count() -> int:
    """Sum of len(spec.rubric_ids) — replaces magic 32."""
    return sum(len(spec.rubric_ids) for spec in LANE_REGISTRY.values())


# Module-load cross-check: every workflow lane has matching WorkflowSpec + SessionEvalSpec
def _validate_partial_registry_alignment() -> None:
    from autoresearch.archive.current_runtime.workflows.session_eval_registry import SESSION_EVAL_SPECS
    # ...similarly import the workflow SPEC registry...
    for lane in workflow_lanes():
        if lane not in SESSION_EVAL_SPECS:
            raise RuntimeError(f"LANE_REGISTRY workflow lane {lane!r} missing from SESSION_EVAL_SPECS")
        # ...similar for WorkflowSpec registry...

_validate_partial_registry_alignment()
```

If you find `LaneSpec` needs a 16th or 17th field to capture an existing-lane property, **stop and escalate** — the field set should be small; large = wrong abstraction.

### Step 2: Migrate each enumeration site to call the registry

Migrate **one site at a time**. After each migration: run tests, cascade-grep, commit. One commit per site.

| Site | Migration |
|---|---|
| `lane_paths.py:LANES` | `from autoresearch.lane_registry import all_lanes; LANES = all_lanes()` (re-export for backward compat if external imports) |
| `lane_paths.py:WORKFLOW_PREFIXES` | `WORKFLOW_PREFIXES = lane_registry.workflow_prefixes()` |
| `lane_runtime.py:LANES` | `lane_registry.all_lanes()` |
| `evolve.py:ALL_LANES` | `lane_registry.all_lanes()` |
| `frontier.py:DOMAINS` | `lane_registry.workflow_lanes()` |
| `frontier.py:LANES` | `lane_registry.all_lanes()` |
| `program_prescription_critic.py:DOMAINS` | `lane_registry.workflow_lanes()` |
| `evaluate_session.py:402 argparse` | `choices=list(lane_registry.workflow_lanes())` |
| `tests/autoresearch/conftest.py:43` | `lane_registry.workflow_lanes()` |
| `evaluate_variant.py:DELIVERABLES` | `DELIVERABLES = lane_registry.deliverables()`. Also migrate consumer at `:432-436` to iterate the tuple: `any(list(session_dir.glob(g)) for g in DELIVERABLES[domain])` |
| `evaluate_variant.py:_INTERMEDIATE_ARTIFACTS` | `_INTERMEDIATE_ARTIFACTS = lane_registry.intermediate_artifacts()`. Consumer at `:435` migrates similarly |
| `evaluate_variant.py:_INNER_PHASE_TAGS` | `_INNER_PHASE_TAGS = lane_registry.inner_phase_tags()`. Consumer at `:814` unchanged |
| `regen_program_docs.py:DOMAIN_FILENAMES` | `DOMAIN_FILENAMES = lane_registry.domain_filenames()` |
| `structural.py:STRUCTURAL_DOC_FACTS` | `STRUCTURAL_DOC_FACTS = lane_registry.structural_doc_facts()` |
| `structural.py:STRUCTURAL_GATE_FUNCTIONS` | `STRUCTURAL_GATE_FUNCTIONS = lane_registry.structural_gate_functions()` |
| `structural.py:38-46 dispatch` | Keep the if/if/if chain (validators are domain-specific functions; can't be data-driven without losing type narrowing). Optional: generate the dispatch from `lane_registry.workflow_lanes()` if cleaner. |
| `service.py:_DOMAIN_PREFIXES` | `_DOMAIN_PREFIXES = lane_registry.domain_prefixes()` |
| `service.py:_DOMAIN_CRITERIA` | `_DOMAIN_CRITERIA = lane_registry.domain_criteria()` |
| `service.py:_JUDGE_PRIMARY_DELIVERABLE` | `_JUDGE_PRIMARY_DELIVERABLE = lane_registry.judge_primary_deliverable()` |
| `models.py:160 EvaluateRequest.domain` | `Literal[*lane_registry.workflow_lanes()]` (Python 3.13 unpacking). If Pydantic doesn't accept it, fall back to manual Literal + module-load assertion that `set(get_args(...)) == set(lane_registry.workflow_lanes())` — and document the choice in lane_registry.py module docstring. |
| `rubrics.py:1001` | `assert len(RUBRICS) == lane_registry.total_rubric_count()` |

### Step 3: Delete duplicated constants once their callers are migrated

For each old constant name, grep the entire repo (including `src/`, `tests/`, `cli/`, `harness/`) for residual imports:

```
grep -rn "ALL_LANES\|WORKFLOW_PREFIXES\|_DOMAIN_CRITERIA\|_JUDGE_PRIMARY_DELIVERABLE\|^DELIVERABLES = \|_INTERMEDIATE_ARTIFACTS\|_INNER_PHASE_TAGS\|DOMAIN_FILENAMES\|STRUCTURAL_DOC_FACTS\|STRUCTURAL_GATE_FUNCTIONS\|_DOMAIN_PREFIXES" --include="*.py"
```

If anything outside the migrated sites imports the old name, either migrate that consumer too or keep a deprecation re-export at the original location.

## CONSTRAINTS — DO

- **Behavior bit-identical** for the 4 existing lanes. The full test suite must pass:
  ```
  pytest autoresearch/test_lane_ownership.py
  pytest tests/autoresearch/
  pytest tests/evaluation/
  pytest -k lane
  ```
- **Take a baseline test snapshot BEFORE any code edit**:
  ```
  pytest --tb=no -q > /tmp/baseline_tests.txt 2>&1
  ```
  If baseline has any failures, **stop and escalate** — don't paper over preexisting breakage. After each migration, re-run and diff against baseline.

- **Cascade-grep after every rename.** For each old constant migrated, grep the entire repo for the old name. Confirm zero stale references before claiming the migration complete.

- **Sanity import check** at end of each commit:
  ```
  python -c "from autoresearch import lane_registry; print(lane_registry.all_lanes()); print(lane_registry.workflow_lanes()); print(lane_registry.total_rubric_count())"
  ```
  Should print `('core', 'geo', 'competitive', 'monitoring', 'storyboard')`, `('geo', 'competitive', 'monitoring', 'storyboard')`, `32` respectively.

- **Document the "add a lane" path** in `lane_registry.py`'s module docstring (~20 lines, included in the Step 1 template above).

- **One commit per migrated site** so any regression can be bisected to a single migration.

- **"Add a hypothetical lane" diff-size validation** at the end: locally branch, add a fake LaneSpec entry (`"foo": LaneSpec(name="foo", ...)`) plus the unavoidable rubric prompts. Count `git diff --stat` lines changed in existing files. **Should be ≤5 lines outside the new fake lane's own files.** If higher, the registry isn't single-source-of-truth and needs another iteration. Discard the test branch.

## CONSTRAINTS — DO NOT

- **Do NOT add `marketing_audit` or `harness_fixer` lanes.** They are separate plans downstream.
- **Do NOT refactor** the bodies of `workflows/<lane>.py` or `workflows/session_eval_<lane>.py`. Those are lane-specific implementations, not framework duplication.
- **Do NOT** change `WorkflowSpec` / `SessionEvalSpec` data shapes (extend or compose; don't replace).
- **Do NOT** move rubric prompt text out of `src/evaluation/rubrics.py`. RUBRICS dict stays where it is.
- **Do NOT** add caching, dependency injection, plugin auto-discovery, class hierarchies, base classes, or any abstraction beyond `dataclass + dict + accessor functions`. If you find yourself writing a class hierarchy, stop.
- **Do NOT** rename directories or move files beyond what's structurally required.
- **Do NOT** edit `archive/v001/...` or `archive/v006/...` snapshots — only `archive/current_runtime/` is invoked at runtime.
- **Do NOT** skip git hooks (`--no-verify`). If a hook fails, fix the underlying issue.

## HARD-STOP CONDITIONS

Stop and write a structured report (per `## REPORT BACK FORMAT`) without continuing if:

1. **A test that wasn't already broken breaks** during any single migration. Don't paper over.
2. **A 24th independent enumeration site exists** that's not in the verified list above.
3. **`LaneSpec` needs a 16th or 17th field** to capture an existing-lane property.
4. **`Literal[*expr]` doesn't work** despite Python 3.13 (e.g., Pydantic version doesn't accept it). Pick fallback option (manual Literal + module-load assertion), document the choice, AND escalate so JR is aware.
5. **A conflict arises with the existing partial registry** (`WorkflowSpec` or `SESSION_EVAL_SPECS`) where the new `LaneSpec` and the existing spec need contradictory changes. Don't pick one over the other unilaterally.
6. **Existing test suite was already broken** before your first edit (per baseline snapshot).

## WORKING APPROACH

1. **Baseline test snapshot**: `pytest --tb=no -q > /tmp/baseline_tests.txt 2>&1`. If failures, escalate.
2. **Read all 23 enumeration sites** end-to-end before writing anything. Take notes on what data each site holds and what consumes it.
3. **Implement `lane_registry.py` first.** Verify via the sanity import check.
4. **Migrate one site at a time.** Tests + cascade-grep + commit per migration.
5. **After all migrations**: run the full test suite. Run a smoke autoresearch evolve dry-run if possible (or the closest equivalent the repo provides) to catch any runtime-only consumers.
6. **"Add a hypothetical lane" diff-size validation** as final test.
7. **Update `CLAUDE.md` / `AGENTS.md`** if either documents the lane structure.
8. **Report back** per the structured format below.

## EFFORT ESTIMATE

5-7 days wall-clock for an autonomous agent. Breakdown:

- Day 1: Read all sites, design `LaneSpec`, implement `lane_registry.py`, verify accessors.
- Days 2-4: Migrate the 23 sites with tests + cascade-grep + commits.
- Day 5: Full test suite + smoke dry-run + "add a hypothetical lane" diff-size validation.
- Days 6-7: Buffer for cross-cutting issues (existing-partial-registry alignment, Pydantic Literal compatibility, deprecation re-exports).

## REPORT BACK FORMAT

Write a structured summary as your final message. JR reads this; do not continue past it.

```markdown
## Refactor outcome

### Status
[completed | hard-stopped at step N]

### Created
- `autoresearch/lane_registry.py` (line count: <N>; field count: <M>)

### Migrated sites (commit SHA per site)
- lane_paths.LANES: <sha>
- lane_paths.WORKFLOW_PREFIXES: <sha>
- ... (one bullet per site, all 23)

### Test results
[pasted output of final `pytest` run + diff vs baseline; NOT summarized]

### Cascade-grep verification
[pasted output of final grep across the repo for each migrated constant; should be empty or limited to deprecation re-exports]

### "Add a hypothetical lane" diff size
[lines changed in existing files when adding a fake LaneSpec entry — should be ≤5]

### Deviations from this prompt + reasoning
[list each, with rationale]

### Hard stops encountered (if any)
[for each: site, what blocked, what you tried, what JR needs to decide]

### Plan-update follow-up needed
- `docs/plans/2026-04-24-005-feat-audit-engine-fusion-plan.md` Unit 17 is now obsolete; needs rewrite. Marketing_audit lane registration becomes: (1) LaneSpec entry; (2) workflow file at `workflows/marketing_audit.py`; (3) evaluator file at `workflows/session_eval_marketing_audit.py`; (4) MA-1..MA-8 rubric prompts in `src/evaluation/rubrics.py`. Total Unit 17 sites drops from ~17 to ~5.
- The audit-engine plan branch (`origin/plan/audit-engine-fusion-v1`) is awaiting this refactor before merge.
```

End of prompt.
