---
title: "feat: Autoresearch lane registry (bare-bones)"
type: feat
status: shipped
date: 2026-04-27
shipped_date: 2026-04-28
shipped_commits:
  - 4c83e2f (Unit 1)
  - e843818 (Unit 2 phase A — derived constants)
  - c94bfcc (Unit 2 phase B — per-lane data dicts)
  - e85fb91 (Unit 2 phase C — dispatch logic)
  - e8d3213 (Unit 2 phase D — cmd_run callable wraps)
  - 649b3b1 (Unit 2 phase E — assertions + light edits)
  - f630231 (Unit 2 phase F — centralize in lane_registry)
  - c208760 (Unit 4 — docs)
  - 9b4284a (test — lifecycle-wrap integration suite)
shipped_notes: |
  Live smoke run on 5 lanes (plan §"Documentation/Operational Notes" merge gate)
  was substituted with a 9-test lifecycle-wrap integration suite due to active
  harness on the same machine and backend-cost concerns. See test file at
  tests/autoresearch/test_lane_registry_lifecycle_wraps.py. Real evolution run
  remains the natural next validation.
supersedes:
  - docs/plans/2026-04-26-001-autoresearch-lane-registry-refactor-handoff.md
  - docs/plans/2026-04-27-001-feat-autoresearch-evolve-substrate-plan.md (over-engineered substrate variant)
  - docs/superpowers/specs/2026-04-27-autoresearch-evolve-substrate-design.md (design spec for over-engineered variant)
---

# feat: Autoresearch lane registry (bare-bones)

> **Why this plan exists:** Two prior attempts over-engineered the problem. The original handoff doc proposed a data-only LaneRegistry but didn't accommodate behavioral divergence for marketing_audit and harness_fixer. The substrate-plugin variant (5028351, then revised at 2ea3a32) responded by building a full plugin architecture — Protocol classes, helper modules, evolve_runtime substrate package, wrap-then-extract migration — that was 14-16 days for a problem that's actually 6-8 days. This plan reverts to the simplest thing that works: a `LaneSpec` dataclass + a `LANES` dict + optional callable hooks for divergent lanes + `file_hash` shared utility.

## Overview

Replace the 24 hardcoded lane-name dispatch sites in autoresearch with one `LaneSpec` dataclass + one `LANES` dict in `autoresearch/lane_registry.py`. The 5 existing lanes (`core`, `geo`, `competitive`, `monitoring`, `storyboard`) become `LaneSpec` instances. Future divergent lanes (marketing_audit, harness_fixer, etc.) ship as additional `LaneSpec` entries with **5 optional `custom_*` callables** (mutate, score, validate, promote, objective_score_from_entry) overriding default behavior where they diverge.

**No substrate package. No Protocol class. No helper module. No wrap-then-extract migration.** Existing `evolve.py`, `evaluate_variant.py`, `frontier.py`, `select_parent.py` keep their loops and dispatch logic — they just read from `LANES` instead of hardcoded constants.

## Problem Frame

Today's evolve has lane-name dispatch baked into ~24 sites: `LANES`/`ALL_LANES`/`DOMAINS` tuples (5 places), per-lane policy dicts (`WORKFLOW_PREFIXES`, `DELIVERABLES`, `_INTERMEDIATE_ARTIFACTS`, `DOMAIN_FILENAMES`, `STRUCTURAL_DOC_FACTS`, `STRUCTURAL_GATE_FUNCTIONS`, `_DOMAIN_PREFIXES`, `_DOMAIN_CRITERIA`, `_JUDGE_PRIMARY_DELIVERABLE`), and a few dispatch branches (`if lane == "core"` in `frontier.py:76-86`, `select_parent.py:38-41`).

Adding a new lane today requires touching 13+ files. Adding a *divergent* lane (different score scale, custom validation) on top of that requires implementing the divergence in lane-private modules with no consistent pattern.

This plan collapses the data dimension into one `LaneSpec` per lane and provides **5 optional `custom_*` callables** on `LaneSpec` for divergent lanes that need their own mutate/score/validate/promote/objective-score logic. The 5 callables match the divergence points documented across the marketing_audit plan (`origin/plan/audit-engine-fusion-v1`) and harness_fixer brainstorm (`7bd6b0b:docs/brainstorms/2026-04-26-harness-fixer-autoresearch-fusion-requirements.md`) — `custom_mutate` specifically because harness_fixer mutates by invoking `harness/engine.py`'s fix-verify loop instead of the meta-agent.

## Requirements Trace

- **R1.** Existing 5 lanes' behavior unchanged. Existing test suite passes.
- **R2.** Adding a research-shaped lane (geomean × geomean scoring, session.md deliverable, structural gates) requires only one `LaneSpec` entry in `LANES`.
- **R3.** Adding a divergent lane requires one `LaneSpec` entry + its own module containing whatever subset of the 5 `custom_*` callables (`custom_mutate`, `custom_score`, `custom_validate`, `custom_promote`, `custom_objective_score_from_entry`) it needs. No edits to `evolve.py`, `frontier.py`, etc.
- **R4.** Existing 24 dispatch sites collapse to one `LANES` dict + accessor functions.
- **R5.** No new abstractions beyond `dataclass + dict + accessor functions + optional Callable fields`. No Protocol class, no plugin module hierarchy, no substrate package.

## Scope Boundaries

- **Out of scope:** marketing_audit and harness_fixer plugin implementations (separate work post-merge).
- **Out of scope:** redesigning evolve.py's loop, evaluate_variant.py's aggregator, or run.py's session runner. They keep their structure; they just read from `LANES`.
- **Out of scope:** lifting `<variant_dir>/run.py` into shared code. It stays per-variant; meta-agent edits it during mutation.
- **Out of scope:** changing `archive/current.json` schema. Stays flat `{lane: variant_id}`.
- **Out of scope:** changing lineage entry schema. New entries match today's shape.
- **Out of scope:** building a "substrate" or "plugin" abstraction. Existing consumers call `LANES[name].whatever`; that's the whole abstraction.
- **Out of scope:** archive snapshots (`autoresearch/archive/v001/...`).

## Context & Research

### Relevant Code and Patterns

The 24 dispatch sites that get migrated:

**Lane-name tuples (4 sites):**
- `autoresearch/lane_runtime.py:12` — `LANES = ("core", "geo", "competitive", "monitoring", "storyboard")`
- `autoresearch/lane_paths.py:36` — same
- `autoresearch/evolve.py:44` — `ALL_LANES = (same)`
- `autoresearch/frontier.py:15-16` — `DOMAINS = ("geo", ...)` + derived `LANES = ("core", *DOMAINS)`

**Per-lane policy dicts:**
- `autoresearch/lane_paths.py:44-77 WORKFLOW_PREFIXES` — owned-path prefixes per lane
- `autoresearch/evaluate_variant.py:44-49 DELIVERABLES` — per-lane primary deliverable glob
- `autoresearch/evaluate_variant.py:53-56 _INTERMEDIATE_ARTIFACTS` — per-lane intermediate glob
- `autoresearch/regen_program_docs.py:40-45 DOMAIN_FILENAMES` — per-lane session.md filename
- `src/evaluation/structural.py:405 STRUCTURAL_DOC_FACTS` — per-lane gate descriptions
- `src/evaluation/structural.py:444 STRUCTURAL_GATE_FUNCTIONS` — per-lane named gate functions
- `src/evaluation/service.py:30-33 _DOMAIN_PREFIXES` — per-lane rubric-prefix
- `src/evaluation/service.py:36-41 _DOMAIN_CRITERIA` — per-lane rubric IDs
- `src/evaluation/service.py:49-56 _JUDGE_PRIMARY_DELIVERABLE` — per-lane judge file selection

**Other duplicated references:**
- `autoresearch/program_prescription_critic.py:41 DOMAINS` — workflow lane tuple
- `autoresearch/archive/current_runtime/scripts/evaluate_session.py:402` — argparse `choices=[...]`
- `tests/autoresearch/conftest.py:43` — `frontier.DOMAINS` stub (test isolation; **stays hardcoded**, documented exception)
- `src/evaluation/models.py:160` — `Literal["geo", ...]` on `EvaluateRequest.domain` (**stays hardcoded** to avoid circular import; runtime assertion that literal matches `workflow_lane_names()`)
- `src/evaluation/rubrics.py:1001` — `assert len(RUBRICS) == 32`

**Dispatch branches:**
- `autoresearch/frontier.py:76-86 objective_score()` — `if lane == "core": composite_score else: domain_score`
- `autoresearch/select_parent.py:38-41` — same dispatch
- `src/evaluation/structural.py:38-46` — if/if/if validator dispatch (kept; validators are domain-specific functions)

**`core` lane specifically** (per document-review): real lane referenced at `lane_runtime.py:141-145` (raises `FileNotFoundError` if missing). CoreLane gets a `LaneSpec` entry like the others; its `is_workflow_lane=False`, empty rubric_ids/deliverables/structural fields.

**Existing partial registries** (untouched): `archive/current_runtime/workflows/__init__.py:WORKFLOW_SPECS` and `archive/current_runtime/workflows/session_eval_registry.py:SESSION_EVAL_SPECS` continue to coexist with the new `LANES`. They cover workflow runtime hooks (configure_env, snapshot_evaluations, etc.); `LaneSpec` covers lane-name + per-lane data + divergent-behavior hooks.

### Institutional Learnings

- **Cascade-grep audit before claiming multi-edit completion** (`docs/solutions/feedback-cascading-edit-grep-audit.md`): Unit 2 budget is 4 days for 16 files of dispatch-site edits, plus 1 day pre-migration cascade-grep audit. Recent feedback (2026-04-26) about JR catching 7 cascade-grep gaps in another plan informs the pacing.
- **Simplification scope discipline** (`docs/solutions/feedback-simplification-scope-discipline.md`): this plan holds net-reductions only. Marketing_audit / harness_fixer migrations are separate.
- **Trust the agent — drop regex guards** (`docs/solutions/feedback-trust-agent-drop-regex-guards.md`): no module-load alignment validators.

## Key Technical Decisions

- **One file, one dict, one dataclass.** `autoresearch/lane_registry.py` contains `LaneSpec` + `LANES` + accessor functions. ~180-240 LoC total.

- **`LaneSpec` has 9 data fields + 5 optional callable hooks.** Data covers what existing dispatch reads; callables let divergent lanes override default behavior. The 5 existing lanes set all 5 callables to `None` (use defaults). Marketing_audit and harness_fixer set their own callables. The 5 callables match the divergence points the marketing_audit plan + harness_fixer brainstorm document: `custom_mutate` (harness_fixer's invoke `harness/engine.py` instead of meta-agent), `custom_score` (weighted-sum + cost penalty), `custom_validate` (file-bytes manifest instead of Python-symbol), `custom_promote` (pre-promotion smoke-test), `custom_objective_score_from_entry` (time-varying engagement-weighted fitness).

- **`objective_score` stays derived, not stored.** Today it's computed lazily from `entry["search_metrics"]`. The default `objective_score_from_entry(entry, lane_name)` function in `lane_registry.py` does the existing dispatch (`composite_score(entry)` for core, `domain_score(entry, lane)` for workflow lanes). Marketing_audit's `custom_objective_score_from_entry` overrides this for time-varying engagement-weighted fitness when its plugin ships. **No backfill of 43 existing lineage entries needed.**

- **`archive/current.json` schema unchanged.** Stays flat `{lane: variant_id}`. Existing `lane_runtime.py:35-45` reader works unchanged.

- **Lineage entry schema unchanged.** Existing entries' root fields (`scores`, `search_metrics`, `domains`, etc.) stay where they are. New entries match. No `lane_data` sub-dict bureaucracy.

- **Variants' `run.py` stays per-variant.** `<variant_dir>/run.py` is meta-agent-mutable content. Not touched.

- **Existing dispatch logic in evolve.py / evaluate_variant.py / frontier.py keeps its structure.** It just reads from `LANES` instead of hardcoded names.

- **`structural.py:38-46 if/if/if dispatch` stays as-is** — type-narrowing benefit; validators are domain-specific functions, not configuration.

- **`models.py:160 Literal` stays hardcoded** — avoids circular import (`src.evaluation.models` → `autoresearch.lane_registry` → `src.evaluation.*`). Runtime assertion in `lane_registry.py` that hardcoded literal matches `workflow_lane_names()`.

- **`tests/autoresearch/conftest.py:43` stub stays hardcoded** — preserves test-isolation contract; importing `LANES` would invert load ordering. Documented exception.

## Open Questions

### Resolved During Planning

- **Substrate package, Protocol class, helper module, wrap-then-extract?** No. None of those. (The whole point of this plan.)
- **Should LaneSpec have `custom_*` callable hooks for divergent lanes?** Yes — 5 of them: `custom_mutate`, `custom_score`, `custom_validate`, `custom_promote`, `custom_objective_score_from_entry`. All defaulted to `None`; when None, existing-lane behavior runs. `custom_mutate` is included because harness_fixer's brainstorm explicitly specifies that mutate invokes `harness/engine.py`'s fix-verify loop instead of the meta-agent — without `custom_mutate`, harness_fixer can't slot into LaneSpec without forking dispatch in `evolve.py`.
- **Where do marketing_audit's commercial wrapper (R2/Worker, payment) and harness_fixer's harness wrappers live?** Outside this plan. Marketing_audit's `LaneSpec.custom_score` calls into `src/audit/score.py`; harness_fixer's calls into `harness/<something>.py`. Those paths are owned by the marketing_audit and harness_fixer plans respectively.
- **Engagement signal bridge?** Not in this plan. When marketing_audit ships, its `custom_objective_score_from_entry` reads from wherever its engagement signal lives (lineage `lane_data`, separate file, whatever its plan decides). If 2+ lanes need the same retroactive-update mechanism, extract a helper at that point.
- **Pre-promotion smoke-test?** Not in this plan. Marketing_audit's `custom_promote` runs its own smoke test. If 2+ lanes need it, extract.

### Deferred to Implementation

- **Final test file paths:** likely `tests/autoresearch/test_lane_registry.py`. Final structure depends on existing test layout.
- **Lineage non-code consumers:** unknown. Unit 2 includes a non-code grep across the broader monorepo + GitHub Actions for `lineage.jsonl` references; if any consumers found, decide migrate-vs-shim per-consumer.
- **Whether `_DOMAIN_PREFIXES` / `_DOMAIN_CRITERIA` / `_JUDGE_PRIMARY_DELIVERABLE` migrate to LaneSpec attributes or stay in `service.py`:** stay in service.py for v1 (rubric-prompt-coupled per Gap 1 research); add to LaneSpec only if a divergent lane needs them.

## Known Divergence Points (NOT pre-designed; addressed by future divergent lanes' plans)

These are concrete divergence points that marketing_audit and harness_fixer plans will need to address when they ship. Listed here so future planners aren't surprised. Each could plausibly be solved 2-3 different ways; the right shape depends on the divergent lane's actual mechanism, so this plan does NOT pre-design them.

1. **`plateau_threshold` (marketing_audit)** — `select_parent.py:93` has `pstdev < 0.01` calibrated for `[0,1]` geomean scores. Marketing_audit's `[-2, 10]` weighted-sum scale needs `pstdev < 0.1` (or normalized `pstdev / lane_max_score < 0.01`). Plausible shapes when marketing_audit ships:
   - (a) Add `plateau_threshold: float = 0.01` data field to LaneSpec
   - (b) Add `custom_plateau_check: Callable | None = None` to LaneSpec
   - (c) Marketing_audit's score normalization brings its scale to `[0,1]` so the threshold doesn't need lane-awareness
   - Marketing_audit's plan picks one.

2. **Snapshot-at-clone for divergent manifest mechanisms (marketing_audit + harness_fixer)** — both new lanes need file-bytes hashing of specific `.md` files at clone time (`marketing_audit`'s stage prompts; `harness_fixer`'s `verifier.md`). The bare-bones plan **provides 3 shared utilities** so both lanes share the manifest toolkit, not just the hash primitive: `file_hash(path)`, `compute_manifest(paths, root_dir)` (snapshot), `verify_manifest(manifest_path, root_dir)` (verify). What's still deferred is *where the snapshot is triggered*. Plausible shapes:
   - (a) Add `custom_clone: Callable | None = None` callable to LaneSpec; each lane's clone hook calls `compute_manifest` and writes its own manifest file
   - (b) Add `file_bytes_manifest_paths: tuple[str, ...] = ()` data field; substrate's default clone iterates this list and calls `compute_manifest` automatically
   - (c) Each divergent lane's `custom_validate` re-runs `compute_manifest` + compares to stored manifest in one step (no separate clone-time snapshot)
   - First divergent lane to ship picks one. **In all three options, both lanes call `compute_manifest` + `verify_manifest`** — no duplicated iteration logic, no duplicated hashing logic. Just different snapshot triggering policies.

3. **`structural.py:38-46` if/if/if dispatch** — adding a new lane with a structural validator currently requires a 1-line `if domain == "marketing_audit": return _validate_marketing_audit(outputs)` addition to the dispatch chain. Plausible shapes:
   - (a) Each new lane's plan adds the if branch (acknowledged as 1-line edit; not "1 LaneSpec entry only")
   - (b) Migrate dispatch to data-driven: `LANES[domain].structural_validator(outputs)` — but `_validate_monitoring` is async while others are sync, complicating the contract
   - First lane to need it picks one. Most likely (a) given the async asymmetry.

4. **`HARNESS_PREFIXES` carve-out (harness_fixer)** — `lane_paths.py:42 HARNESS_PREFIXES = ("harness",)` is excluded from ALL lanes. Harness_fixer needs to own paths under `harness/` (e.g., `harness/prompts/fixer.md`). Plausible shapes:
   - (a) Add `excluded_path_overrides: tuple[str, ...] = ()` to LaneSpec; harness_fixer overrides the global exclusion
   - (b) Modify `HARNESS_PREFIXES` to be granular (e.g., exclude `"harness/internal"` not all of `"harness"`)
   - (c) Harness_fixer's plan moves harness-side files outside the `harness/` prefix
   - Harness_fixer's plan picks one.

5. **`holdout_suite_id(lane)` env var convention (`evolve_ops.py:658-670`)** — per-lane env var lookup (e.g., `EVOLUTION_HOLDOUT_SUITE_ID_GEO`?). Currently flagged as JR-needs-to-decide. Plausible shapes:
   - (a) Continue env-var-per-lane convention; document the naming
   - (b) Move holdout suite ID to LaneSpec data field
   - (c) Single env var with lane-suffix string parsing
   - Decide when first divergent lane wants its own holdout suite.

6. **`_INNER_PHASE_TAGS` extension (marketing_audit)** — closed allowlist at `evaluate_variant.py:744-756`. Marketing_audit adds `stage_2_lens, inner_critic, revise, stage_3_synthesis, stage_4_proposal`. Marketing_audit's plan extends the allowlist (1-line edit) OR migrates to per-LaneSpec field.

7. **Inner-vs-outer pass-rate correlation telemetry (marketing_audit)** — `evaluate_variant.py:1099-1132` aggregator could be extended to emit `inner_pass_rate / outer_pass_rate / pass_rate_delta`. Marketing_audit's plan picks: edit aggregator (substrate edit) OR include in `custom_score` output (cleaner).

**Cumulative effect on the "1 LaneSpec entry" claim:** R2 says adding a research-shaped lane requires only one LaneSpec entry. The above 7 points are divergence axes that fall outside the bare-bones LaneSpec — they're addressed when the FIRST divergent lane needs them. Adding marketing_audit specifically will likely touch 4-5 of these (plateau_threshold, snapshot-at-clone, structural.py if-branch, _INNER_PHASE_TAGS, possibly inner-vs-outer telemetry). That's marketing_audit's plan's work, not this plan's.

## High-Level Technical Design

```python
# autoresearch/lane_registry.py — ~180-240 LoC total

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable

@dataclass(frozen=True)
class LaneSpec:
    # Identity
    name: str
    is_workflow_lane: bool

    # Per-lane data (replaces ~9 dispatch dicts)
    rubric_ids: tuple[str, ...] = ()
    path_prefixes: tuple[str, ...] = ()
    session_md_filename: str = ""
    deliverables: tuple[str, ...] = ()
    intermediate_artifacts: tuple[str, ...] = ()
    structural_doc_facts: tuple[str, ...] = ()
    structural_gate_functions: tuple[str, ...] = ()

    # Optional callables for divergent lanes (default None = use existing-lane behavior)
    # Each callable's signature is documented in lane-registry.md; substrate doesn't
    # constrain the signature beyond `Callable` because each divergent lane's needs differ.
    custom_mutate: Callable | None = None                       # harness_fixer: invokes harness/engine.py
    custom_score: Callable | None = None                        # marketing_audit/harness_fixer: weighted sum
    custom_validate: Callable | None = None                     # marketing_audit/harness_fixer: file-bytes manifest
    custom_promote: Callable | None = None                      # marketing_audit/harness_fixer: pre-promotion smoke
    custom_objective_score_from_entry: Callable | None = None   # marketing_audit: time-varying engagement-weighted


LANES: dict[str, LaneSpec] = {
    "core": LaneSpec(
        name="core",
        is_workflow_lane=False,
        # core has no rubrics, no session.md, no structural gates;
        # path_prefixes covers everything outside workflow lane prefixes
        path_prefixes=...,
    ),
    "geo": LaneSpec(
        name="geo",
        is_workflow_lane=True,
        rubric_ids=("GEO-1", "GEO-2", ..., "GEO-8"),
        path_prefixes=...,                 # transcribe from WORKFLOW_PREFIXES["geo"]
        session_md_filename="geo-session.md",
        deliverables=("optimized/*.md",),  # wrap existing single-glob in tuple
        intermediate_artifacts=(),
        structural_doc_facts=...,
        structural_gate_functions=...,
        # custom_* all None — uses default behavior
    ),
    "competitive": LaneSpec(...),
    "monitoring":  LaneSpec(...),
    "storyboard":  LaneSpec(...),
}


# Accessors
def all_lane_names() -> tuple[str, ...]:
    return tuple(LANES.keys())

def workflow_lane_names() -> tuple[str, ...]:
    return tuple(name for name, spec in LANES.items() if spec.is_workflow_lane)

def get_spec(name: str) -> LaneSpec:
    return LANES[name]

# Default objective_score_from_entry (replaces frontier.objective_score dispatch)
def default_objective_score_from_entry(entry: dict, lane_name: str) -> float | None:
    spec = LANES[lane_name]
    if spec.custom_objective_score_from_entry is not None:
        return spec.custom_objective_score_from_entry(entry)
    # Default: today's behavior
    metrics = entry.get("search_metrics") or {}
    if not spec.is_workflow_lane:  # core
        return metrics.get("composite")
    return (metrics.get("domains", {}).get(lane_name, {}) or {}).get("score")


# Runtime assertion: hardcoded Literal in src/evaluation/models.py:160 matches workflow lanes
def _assert_models_literal_matches() -> None:
    from src.evaluation.models import EvaluateRequest
    from typing import get_args
    domain_field = EvaluateRequest.model_fields["domain"]
    literal_values = set(get_args(domain_field.annotation))
    if literal_values != set(workflow_lane_names()):
        raise RuntimeError(
            f"src/evaluation/models.py:160 Literal {literal_values} "
            f"out of sync with LANES workflow lanes {set(workflow_lane_names())}"
        )


# Shared utilities: file-bytes hashing + manifest snapshot/verify for divergent
# lanes' frozen-content manifests. Both marketing_audit (stage prompts SHA256-locked)
# and harness_fixer (verifier.md SHA256-locked) use these primitives via their
# custom_validate callables — so both lanes share the iteration logic, not just the
# hash primitive.
import hashlib
import json
from pathlib import Path

def file_hash(path: Path) -> str:
    """Return SHA256 hex digest of the file's bytes."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def compute_manifest(paths: list[Path], root_dir: Path) -> dict[str, str]:
    """Snapshot file-bytes hashes for a list of paths.

    Returns a dict mapping each path's relative form (relative to root_dir) to its
    SHA256 hex digest. Divergent lanes call this at clone time (or wherever their
    snapshot mechanism dictates per Known Divergence Point #2) and persist the
    result as JSON.
    """
    return {
        str(Path(p).relative_to(root_dir)): file_hash(Path(p))
        for p in paths
    }


def verify_manifest(manifest_path: Path, root_dir: Path) -> tuple[bool, list[str]]:
    """Verify a stored manifest matches current file contents.

    Reads the JSON manifest at manifest_path (a dict[rel_path, expected_hash])
    and re-hashes each rel_path resolved against root_dir. Returns
    (passed, failures) where failures lists each path that's missing or has a
    mismatched hash. Used by divergent lanes' custom_validate callables.
    """
    manifest = json.loads(Path(manifest_path).read_text())
    failures: list[str] = []
    for rel_path, expected_hash in manifest.items():
        abs_path = root_dir / rel_path
        if not abs_path.exists():
            failures.append(f"missing: {rel_path}")
            continue
        actual = file_hash(abs_path)
        if actual != expected_hash:
            failures.append(f"hash mismatch: {rel_path} (expected {expected_hash[:8]}, got {actual[:8]})")
    return (not failures, failures)


# Total: ~180-240 lines including all 5 LaneSpec instances + accessors + default fn
# + assertion + 3 shared utilities (file_hash, compute_manifest, verify_manifest).
# Hard cap 250 LoC.
```

For divergent lanes (marketing_audit, harness_fixer), they add a `LaneSpec` entry and provide their own callables:

```python
# Marketing_audit's plan would add (post-substrate-merge):
from src.audit.score import marketing_audit_score
from src.audit.validate import marketing_audit_validate
from src.audit.promote import marketing_audit_promote_with_smoke_test
from src.audit.fitness import marketing_audit_objective_score_from_entry

LANES["marketing_audit"] = LaneSpec(
    name="marketing_audit",
    is_workflow_lane=True,
    rubric_ids=("MA-1", ..., "MA-8"),
    path_prefixes=...,
    session_md_filename="marketing_audit-session.md",
    deliverables=("findings.md", "report.md", "report.json", "report.html", "report.pdf"),
    intermediate_artifacts=("stage2_subsignals/L*_*.json",),
    structural_doc_facts=...,
    structural_gate_functions=...,
    # Marketing_audit's divergence (custom_mutate=None — uses default meta-agent invocation):
    custom_score=marketing_audit_score,                              # weighted-sum + cost penalty
    custom_validate=marketing_audit_validate,                        # file-bytes manifest
    custom_promote=marketing_audit_promote_with_smoke_test,          # pre-promotion smoke
    custom_objective_score_from_entry=marketing_audit_objective_score_from_entry,  # T+60d engagement
)


# Harness_fixer's plan would add (also post-substrate-merge):
from harness.engine import harness_fixer_mutate
from harness.score import harness_fixer_score
from harness.validate import harness_fixer_validate_with_markdown_manifest

LANES["harness_fixer"] = LaneSpec(
    name="harness_fixer",
    is_workflow_lane=True,  # has HM-1..HM-8 rubric IDs registered in src/evaluation/rubrics.py;
                            # workflow_lane_names() must include it so service.py + rubrics.py see it
    rubric_ids=("HM-1", ..., "HM-8"),
    path_prefixes=("programs/harness_fixer-session.md", "harness/prompts/fixer.md", ...),
    session_md_filename="harness_fixer-session.md",
    deliverables=(),  # output is commit_sha + verifier_report.json, captured per-fixture
    intermediate_artifacts=(),
    structural_doc_facts=(),
    structural_gate_functions=(),
    # Harness_fixer's divergence (note custom_mutate is set):
    custom_mutate=harness_fixer_mutate,                              # invoke harness/engine.py fix-verify
    custom_score=harness_fixer_score,                                # HM-1..HM-8 weighted + cost
    custom_validate=harness_fixer_validate_with_markdown_manifest,   # markdown file-bytes hash
    # custom_promote, custom_objective_score_from_entry: harness_fixer's plan decides if needed
)
```

That's it. No Protocol class. No helper module. No substrate package. Each divergent lane writes its code in its own module (`src/audit/`, `harness/`), registers a LaneSpec entry, done. The 5 callables let each lane override only the divergent dimensions; everything else uses the default.

## Implementation Units

- [ ] **Unit 1: Create `autoresearch/lane_registry.py`** (1 day)

**Goal:** Single file with `LaneSpec` dataclass + `LANES` dict containing 5 entries + accessor functions + default objective_score function.

**Requirements:** R1, R5.

**Dependencies:** None.

**Files:**
- Create: `autoresearch/lane_registry.py` (~180-240 LoC)
- Test: `tests/autoresearch/test_lane_registry.py`

**Approach:**
- Define `LaneSpec` frozen dataclass with 9 data fields + 5 optional `Callable` fields (`custom_mutate`, `custom_score`, `custom_validate`, `custom_promote`, `custom_objective_score_from_entry`), all defaulting to `None`.
- Transcribe data for all 5 lanes from existing constants:
  - `core`: minimal (is_workflow_lane=False, mostly empty fields, `path_prefixes` for everything outside WORKFLOW_PREFIXES, all 5 callables = None)
  - `geo`, `competitive`, `monitoring`, `storyboard`: full data from existing `WORKFLOW_PREFIXES`, `DELIVERABLES`, `_INTERMEDIATE_ARTIFACTS`, `DOMAIN_FILENAMES`, `STRUCTURAL_DOC_FACTS`, `STRUCTURAL_GATE_FUNCTIONS`. Rubric IDs: 8 each (`GEO-1..8`, `CI-1..8`, `MON-1..8`, `SB-1..8`). All 5 callables = None.
- Define accessors: `all_lane_names()`, `workflow_lane_names()`, `get_spec(name)`.
- Define `default_objective_score_from_entry(entry, lane_name)` mirroring today's `frontier.objective_score()` dispatch.
- Define `_assert_models_literal_matches()` runtime assertion (callable, NOT module-load side effect).
- Define 3 shared utilities for divergent lanes' frozen-content manifest mechanisms:
  - `file_hash(path)` — `sha256(path.read_bytes()).hexdigest()`. Canonical hashing primitive.
  - `compute_manifest(paths, root_dir) -> dict[str, str]` — snapshots a list of paths into a `{rel_path: hash}` dict. Used at clone time (or wherever the lane's snapshot mechanism dictates) by divergent lanes that need file-bytes manifests.
  - `verify_manifest(manifest_path, root_dir) -> tuple[bool, list[str]]` — reads a stored JSON manifest, re-hashes each entry, returns (passed, failures). Used by divergent lanes' `custom_validate` callables.
  - Both marketing_audit and harness_fixer use these — the same iteration logic, not just the hash primitive. Documented in module docstring as the canonical frozen-content verification toolkit.

**Test scenarios:**
- Happy path: `all_lane_names() == ("core", "geo", "competitive", "monitoring", "storyboard")`.
- Happy path: `workflow_lane_names() == ("geo", "competitive", "monitoring", "storyboard")`.
- Happy path: `get_spec("geo").rubric_ids == ("GEO-1", ..., "GEO-8")`.
- Happy path: `default_objective_score_from_entry(entry, "core")` returns same value as today's `frontier.composite_score(entry)` on a fixture entry.
- Happy path: `default_objective_score_from_entry(entry, "geo")` returns same value as today's `frontier.domain_score(entry, "geo")`.
- Edge case: `default_objective_score_from_entry` on entry missing `search_metrics` returns None.
- Happy path: `_assert_models_literal_matches()` passes against current `models.py:160`.
- Error path: `get_spec("bogus")` raises `KeyError`.
- Happy path: `file_hash(path_to_known_file)` returns the expected SHA256 hex (test against a fixture file).
- Edge case: `file_hash` on missing file raises `FileNotFoundError`.
- Happy path: `file_hash(same_file_twice)` returns identical hash (idempotent).
- Happy path: `compute_manifest([file_a, file_b], root)` returns dict with 2 entries keyed by relative path.
- Edge case: `compute_manifest` with empty path list returns empty dict.
- Happy path: `verify_manifest(stored_manifest, root)` returns `(True, [])` when files unchanged.
- Error path: `verify_manifest` returns `(False, ["missing: foo.md"])` when a manifest entry's file is missing.
- Error path: `verify_manifest` returns `(False, ["hash mismatch: bar.md ..."])` when a file's bytes have changed.
- Integration: `verify_manifest(compute_manifest([f], root) -> json -> file, root)` round-trips correctly.

**Verification:**
- Test suite passes.
- `python -c "from autoresearch.lane_registry import LANES; print(list(LANES.keys()))"` prints all 5 lanes.
- File ≤ 250 LoC (hard cap).

---

- [ ] **Unit 2: Migrate the dispatch sites** (4 days, per cascade-grep institutional learning + verification of additional sites surfaced post-document-review)

**Goal:** Replace hardcoded lane-name dispatch in 16 files with `LANES`/`get_spec()` reads.

**Requirements:** R1, R4.

**Dependencies:** Unit 1.

**Pre-migration cascade-grep audit (mandatory before touching any file):**

Before editing any dispatch site, run a comprehensive grep across `autoresearch/`, `src/evaluation/`, and `tests/` to enumerate **every** lane-aware dispatch surface. Compare against the explicit list below. If any site is found that's NOT in the list, **stop and add it to the migration list before proceeding** — don't migrate piecemeal and discover orphan sites later.

```bash
# Find dispatch on lane name (==/!= comparisons, dict lookups, string formatting)
grep -rn '"core"\|"geo"\|"competitive"\|"monitoring"\|"storyboard"\|lane ==\|lane !=' \
  --include="*.py" autoresearch/ src/evaluation/ tests/ | grep -v archive/v00

# Find lane-keyed constants that should be plugin attributes
grep -rn "^ALL_LANES\|^WORKFLOW_LANES\|^LANES = (\|^DOMAINS = (\|_DOMAIN_CRITERIA\|_JUDGE_PRIMARY_DELIVERABLE\|^DELIVERABLES = \|_INTERMEDIATE_ARTIFACTS\|_INNER_PHASE_TAGS\|DOMAIN_FILENAMES\|STRUCTURAL_DOC_FACTS\|STRUCTURAL_GATE_FUNCTIONS\|_DOMAIN_PREFIXES\|HARNESS_PREFIXES" --include="*.py" autoresearch/ src/evaluation/ tests/

# Find lane-aware function names (heuristic; review hits)
grep -rn "for lane in\|for domain in\|by_lane\|per_lane\|_for_lane(" --include="*.py" autoresearch/ src/evaluation/ tests/ | grep -v archive/v00
```

**Files (one commit per migration site):**
- Modify: `autoresearch/lane_runtime.py:12` — `LANES` tuple → `from autoresearch.lane_registry import all_lane_names; LANES = all_lane_names()`. Preserve external-import compatibility.
- Modify: `autoresearch/lane_paths.py:36, 44-77` — `LANES` + `WORKFLOW_PREFIXES` → derive from registry. Note: `lane_paths.py` is a deprecation shim per its docstring; preserve that.
- Modify: `autoresearch/evolve.py:44` — `ALL_LANES` → `all_lane_names()`.
- Modify: `autoresearch/frontier.py:15-16, 76-86` — `DOMAINS`/`LANES` derived; `objective_score()` becomes `default_objective_score_from_entry(entry, entry["lane"])`.
- Modify: `autoresearch/select_parent.py:38-41` — same as frontier.
- Modify: `autoresearch/evaluate_variant.py:44-49 DELIVERABLES` — derive dict from registry. Same for `_INTERMEDIATE_ARTIFACTS:53-56`. Consumer at `:432-436` migrates to `any(list(session_dir.glob(g)) for g in get_spec(domain).deliverables)`.
- Modify: `autoresearch/evaluate_variant.py:162-179 _project_suite_manifest_for_lane` — replace lane-name dispatch (`if lane == "core" → all 4 domains; else → that one domain`) with `is_workflow_lane`-driven derivation: `if not LANES[lane].is_workflow_lane: include all workflow domains; else: include only this lane`.
- Modify: `autoresearch/evaluate_variant.py:1057-1146` — replace hardcoded `for domain in DOMAINS` with `for domain in workflow_lane_names()`. Aggregator logic unchanged.
- Modify: `autoresearch/evaluate_variant.py:1288-1295 _objective_score_from_scores` — duplicate of `frontier.objective_score()` dispatch. Replace with `default_objective_score_from_entry(entry, lane)` call. Without this, the orphan dispatch breaks when adding lanes.
- Modify: `autoresearch/evaluate_variant.py:744-756 _INNER_PHASE_TAGS` — keep as closed allowlist for v1 (research lanes' phase tags are stable). When marketing_audit ships and adds `stage_2_lens, inner_critic, revise, stage_3_synthesis, stage_4_proposal`, marketing_audit's plan extends the allowlist. Documented as known divergence point.
- Modify: `autoresearch/regen_program_docs.py:40-45 DOMAIN_FILENAMES` — derive dict from registry (`{name: spec.session_md_filename for name, spec in LANES.items() if spec.session_md_filename}`).
- Modify: `autoresearch/program_prescription_critic.py:41 DOMAINS` — `workflow_lane_names()`.
- Modify: `autoresearch/archive/current_runtime/scripts/evaluate_session.py:402` — `choices=list(workflow_lane_names())`.
- Modify: `tests/autoresearch/conftest.py:43` — **leave hardcoded.** Add comment: `# intentionally NOT migrated to read live LANES (preserves test-isolation contract; documented exception)`.
- Modify: `src/evaluation/structural.py:405 STRUCTURAL_DOC_FACTS, :444 STRUCTURAL_GATE_FUNCTIONS` — derive from registry. Keep `:38-46` if/if/if validator dispatch as-is (type narrowing).
- Modify: `src/evaluation/service.py:30-58` — `_DOMAIN_PREFIXES`, `_DOMAIN_CRITERIA`, `_JUDGE_PRIMARY_DELIVERABLE`. **Decide during implementation:** simplest is to derive `_DOMAIN_CRITERIA` from `get_spec(name).rubric_ids` and leave `_DOMAIN_PREFIXES` + `_JUDGE_PRIMARY_DELIVERABLE` in place (rubric-prompt-coupled).
- Modify: `src/evaluation/models.py:160` — **leave hardcoded `Literal["geo", "competitive", "monitoring", "storyboard"]`** to avoid circular import. Add module-load assertion call to `_assert_models_literal_matches()` in `lane_registry.py` from a sensible startup path (e.g., a single import in `autoresearch/__init__.py`).
- Modify: `src/evaluation/rubrics.py:1001` — chain assertion: `assert len(RUBRICS) == 32 == sum(len(spec.rubric_ids) for spec in LANES.values())`.
- Modify: `autoresearch/evolve.py:cmd_run` (lines 888-1097) — at the 5 lifecycle points where the future `custom_*` callables would dispatch (mutate, score, validate, promote, objective_score_from_entry), wrap existing logic with a check: `if spec.custom_X is not None: spec.custom_X(...) else: <existing logic>`. For all 5 existing lanes, `spec.custom_X is None` → existing behavior unchanged. This is the wiring that lets divergent lanes slot in later without further evolve.py edits. ~10-15 LoC of conditional dispatch added; existing logic untouched in the else branch.

**Cascade-grep verification (Unit 2 acceptance):**
- `grep -rn "ALL_LANES\|^WORKFLOW_LANES = \|^WORKFLOW_PREFIXES\b\|^LANES = (\|^DOMAINS = (\|_DOMAIN_CRITERIA\|^DELIVERABLES = \|_INTERMEDIATE_ARTIFACTS\|DOMAIN_FILENAMES\|STRUCTURAL_DOC_FACTS\|STRUCTURAL_GATE_FUNCTIONS" --include="*.py"` returns zero outside `autoresearch/lane_registry.py` and the documented `tests/autoresearch/conftest.py:43` exception.
- Non-code grep: `git grep -l "lineage.jsonl\|geo\|competitive\|monitoring\|storyboard"` outside autoresearch tree + `.github/workflows/`. Migrate or shim per-consumer if found.

**Test scenarios:**
- Happy path: full existing test suite passes after each migration site.
- Edge case: external (non-code) imports of removed constants → deprecation re-export shim with `DeprecationWarning`.
- Integration: smoke run on each lane post-migration matches pre-migration output.

**Verification:**
- Cascade-grep returns clean.
- Full test suite passes.
- No regressions in `pytest -k lane`.

---

- [ ] **Unit 3: "Add a hypothetical lane" validation + smoke run** (1 day)

**Goal:** Validate that adding a new research-shaped lane is one `LaneSpec` entry. Smoke run on all 5 existing lanes.

**Requirements:** R1, R2.

**Dependencies:** Units 1, 2.

**Files:**
- No new files. Local-branch-only fake lane test.

**Approach:**
- Locally branch; add a fake `"foo"` lane to `LANES` with synthetic rubric IDs + path_prefixes + the 8 fake rubric prompts in `src/evaluation/rubrics.py`.
- Run `git diff --stat` against trunk. **Should touch exactly 2 files:** `lane_registry.py` (1 entry added) + `src/evaluation/rubrics.py` (rubric prompts + assertion bumped from 32 to 40).
- If more files touched, the registry isn't single-source-of-truth — fix and retry.
- Discard the test branch.
- Run `autoresearch evolve --lane core --iterations 1 --candidates 1`, then geo, competitive, monitoring, storyboard. Verify each completes without error and produces a lineage entry matching today's shape.

**Test scenarios:**
- Verification: hypothetical `"foo"` lane addition touches exactly 2 files (`lane_registry.py` + `rubrics.py`).
- Integration: smoke run on each of 5 lanes completes without error.
- Verification: lineage entries' shape matches pre-refactor (root fields unchanged).
- Verification: `archive/current.json` schema unchanged.

**Verification:**
- All 5 smoke runs pass.
- Hypothetical-lane diff-size validation passes.

---

- [ ] **Unit 4: Mini-doc + supersede prior plans** (0.5 day)

**Goal:** ~1-page doc explaining how to add a lane. Mark prior plans superseded.

**Requirements:** R5 (no documentation requirement; this is just helpful).

**Dependencies:** Units 1-3.

**Files:**
- Create: `docs/architecture/lane-registry.md` (~50-100 lines: LaneSpec field reference + worked example for divergent lane).
- Modify: `docs/plans/2026-04-26-001-autoresearch-lane-registry-refactor-handoff.md` — SUPERSEDED notice pointing here.
- Modify: `docs/plans/2026-04-27-001-feat-autoresearch-evolve-substrate-plan.md` — SUPERSEDED notice (already in frontmatter).
- Modify: `docs/superpowers/specs/2026-04-27-autoresearch-evolve-substrate-design.md` — SUPERSEDED notice.

**Approach:**
- Doc covers: `LaneSpec` field reference (1 paragraph each), worked example "add code_review lane" with full LaneSpec definition, when to use `custom_*` callables vs default behavior.
- Supersession commits on the relevant branches.

**Test scenarios:**
- Test expectation: none — documentation. Manual check: worked example compiles.

**Verification:**
- Doc exists and is linked from `lane_registry.py` module docstring.
- Old plans marked SUPERSEDED.

---

## System-Wide Impact

- **Interaction graph:** All consumers (evolve, evaluate_variant, frontier, select_parent, structural, service, rubrics, models) read from `LANES` instead of hardcoded constants. Loop structures unchanged.
- **Error propagation:** unchanged. Plugin custom callables (when divergent lanes ship later) propagate exceptions; `subprocess.run(check=True)` semantics preserved.
- **State lifecycle risks:** none. No new files written, no schema changes.
- **API surface parity:** `autoresearch evolve --lane <name>` argparse compatible. `frontier.objective_score()` becomes a thin wrapper around `default_objective_score_from_entry()`; backward-compat for any external caller.
- **Integration coverage:** Unit 3 smoke run on 5 lanes.
- **Unchanged invariants:**
  - `<variant_dir>/run.py` — per-variant; not touched.
  - `evaluate_variant.py` subprocess interface unchanged.
  - `archive/<variant_id>/` directory layout unchanged.
  - `archive/current.json` flat schema unchanged.
  - `archive/lineage.jsonl` schema unchanged. Existing 43 entries readable; new entries match shape.
  - `harness/` wrappers untouched.
  - `src/audit/` untouched.
  - `tests/autoresearch/conftest.py:43` stub stays hardcoded (documented exception).

## Risks & Dependencies

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **R1: Existing tests break post-migration** | Med | Med | Unit 2 commits one site at a time; tests run after each. Helper-side: `default_objective_score_from_entry` mirrors today's behavior exactly. |
| **R2: External (CI, downstream) imports of removed constants** | Low | Med | Unit 2 cascade-grep surveys outside autoresearch tree + `.github/workflows/`. Deprecation re-export shim retained for any found external imports. |
| **R3: `LaneSpec` doesn't accommodate marketing_audit's or harness_fixer's actual divergence** | Med | Low | The 5 `custom_*` callables (mutate, score, validate, promote, objective_score_from_entry) cover the divergences documented in marketing_audit's plan + harness_fixer's brainstorm. If a 6th divergence axis surfaces (e.g., custom_clone for non-default snapshot semantics), add a field at that point. **The bar is "does the existing 5 lanes' behavior fit?"** — divergent-lane shapes are not over-predesigned. |
| **R4: Circular import via `Literal[*lanes...]`** | None | None | Plan keeps hardcoded `Literal` in `models.py:160` + runtime assertion. No circular import created. |
| **R5: `core` lane silently dropped** | None | None | CoreLane is a `LaneSpec` entry. `lane_runtime.py:141-145` `core` head check works unchanged. |
| **R6: `current.json` schema changes break readers** | None | None | Schema unchanged. |
| **R7: `objective_score` migration breaks legacy entries** | None | None | Derived on read. No backfill. |
| **R8: Helper module / Protocol class / substrate package leaks scope** | None | None | None of those are built. Single file, single dataclass, single dict. |

## Documentation / Operational Notes

- **Documentation:** Unit 4 produces `docs/architecture/lane-registry.md`.
- **Branch strategy:** new branch `refactor/autoresearch-lane-registry-v2`. Single PR for all 4 units (or split into Unit 1, 2, 3+4 if review preferred).
- **Smoke run as rollout gate:** Unit 3's smoke run on all 5 lanes is the merge criterion.
- **Sequencing post-merge:** marketing_audit and harness_fixer plans handle their own LaneSpec additions in their respective PRs.

## Effort Estimate

**6-8 days wall-clock.** (Increased from initial 5-7 days estimate after second-pass audit surfaced 3 additional dispatch sites + cascade-grep audit step prepended to Unit 2.)

- **Day 1 (Unit 1):** Create `lane_registry.py`, transcribe 5 LaneSpec entries, write tests. Verify accessors against existing fixtures.
- **Day 2 (Unit 2 prep):** Pre-migration cascade-grep audit. Enumerate ALL lane-aware dispatch sites in autoresearch/, src/evaluation/, tests/. Compare against the explicit 16-site list in Unit 2; surface any orphan sites and add them to the migration list before any file edits.
- **Days 3-5 (Unit 2 migration):** Migrate 16 dispatch sites, one commit per site, with cascade-grep + test verification per site.
- **Day 6 (Unit 3):** Hypothetical-lane diff-size validation + smoke run on all 5 lanes.
- **Day 6-7 (Unit 4):** Mini-doc + supersede prior plans.
- **Day 8:** Buffer for surprises (likely candidate: cascade-grep surfaces an orphan site that requires non-trivial migration).

Hard cap: `lane_registry.py` ≤ 250 LoC. If exceeded, stop and revise.

## What This Plan Does NOT Build

To make the bare-bones discipline explicit:

- **No `evolve_runtime/` substrate package.** evolve.py keeps its loop.
- **No `LanePlugin` Protocol class.** LaneSpec is data + optional callables.
- **No `ResearchLaneHelper` utility module.** Existing helpers in evolve.py / evaluate_variant.py stay where they are.
- **No `lineage.update_entry()` retroactive-update hook.** Marketing_audit handles engagement signals in its own module when its plan ships.
- **No pre-promotion smoke-test framework.** Marketing_audit's `custom_promote` does its own.
- **No "wrap-then-extract" migration pattern.** Existing 5 lanes don't get rewritten; their data is transcribed into LaneSpec entries.
- **No 7 cross-cutting evolve-loop utilities.** evolve.py's existing cohort-id / SIGALRM / regen_program_docs / etc. stay where they are.
- **No `ScoreResult` / `ValidationResult` dataclasses.** Custom callables return whatever shape they want.
- **No module-load alignment validators.** The `_assert_models_literal_matches()` is callable, invoked from a sensible startup path.

If a future lane proves any of these are needed, add them as separate work. Today, no lane needs any of them. **YAGNI.**

## Sources & References

- **Superseded:**
  - `docs/plans/2026-04-26-001-autoresearch-lane-registry-refactor-handoff.md` (data-only, missing custom_* hooks)
  - `docs/plans/2026-04-27-001-feat-autoresearch-evolve-substrate-plan.md` (over-engineered substrate variant)
  - `docs/superpowers/specs/2026-04-27-autoresearch-evolve-substrate-design.md` (design doc for over-engineered variant)
- **Marketing_audit plan (downstream consumer):** `git show origin/plan/audit-engine-fusion-v1:docs/plans/2026-04-24-005-feat-audit-engine-fusion-plan.md`
- **Harness_fixer brainstorm (downstream consumer):** `git show 7bd6b0b:docs/brainstorms/2026-04-26-harness-fixer-autoresearch-fusion-requirements.md`
- **Cascade-grep discipline:** `docs/solutions/feedback-cascading-edit-grep-audit.md`
- **Simplification scope discipline:** `docs/solutions/feedback-simplification-scope-discipline.md`

End of plan.
