---
title: "Autoresearch evolve substrate — bare-bones extensible design"
date: 2026-04-27
status: draft (awaiting JR review)
supersedes: docs/plans/2026-04-26-001-autoresearch-lane-registry-refactor-handoff.md
authors: J Ryszard Noszczyk + Claude Opus 4.7
---

# Autoresearch evolve substrate — bare-bones extensible design

## 1. Problem statement

Autoresearch's evolve framework today has 4 lanes — geo, competitive, monitoring, storyboard — that share structural shape because they were copy-pasted from one template. Two new consumers are pending: `marketing_audit` (full plan at `origin/plan/audit-engine-fusion-v1`) and `harness_fixer` (brainstorm at `git show 7bd6b0b:docs/brainstorms/2026-04-26-harness-fixer-autoresearch-fusion-requirements.md`). Both are structurally different from the existing 4 — different score scales, different aggregation, different deliverable shapes, different gate sequences, different frozen-content mechanisms.

Today's framework has lane-name dispatch baked into ~24 sites (file paths, score branches, status markers, gate sequences). The first refactor attempt aimed to centralize lane-name *data* into a `LaneRegistry` — but that solves the wrong problem at the wrong altitude: marketing_audit and harness_fixer don't share the existing-lane *shape*; they share the variant *lifecycle*. A data-only registry forces them to fit a shape they reject; the result is "adding a lane = 8-9 file edits" even after the registry refactor.

This spec proposes a bare-bones substrate + plugin architecture instead. Substrate owns variant lifecycle (filesystem, CLI, lineage, parent selection). Plugins own behavior (scoring, gates, manifest, deliverable shape). Adding a new lane becomes one registration line + one plugin module.

**Concretely:**
- Marketing_audit's current 19-file footprint drops to: 1 line in `lanes/__init__.py:LANES` + the plugin module + (separately) the customer-facing audit pipeline.
- Harness_fixer's current 16-file footprint drops to: 1 line + the plugin module + 3 harness/ wrappers.
- Existing 4 lanes get 19 sites of duplication collapsed into one registry, plus their behavior consolidates into a `ResearchLaneHelper` utility module.

## 2. Goal

Build a substrate that's bare-bones but genuinely extensible, where:
- The contract a lane plugin must satisfy is small (~6 methods + 2 attributes).
- Adding a new lane that fits the existing template is one registration line.
- Adding a structurally different lane (different score scale, different gates) requires only its own plugin module, never substrate edits.
- Future lanes we haven't anticipated (code review, prompt compression, research synthesis) plug in without changing the substrate.
- Existing 4 lanes' behavior is bit-identical after migration.

## 3. Non-goals

- **Not redesigning evolve's variant lifecycle.** The variant clone → mutate → score → validate → promote phases stay; only their per-lane bindings change.
- **Not changing scoring semantics for existing 4 lanes.** Geomean × geomean stays the default for the research helper; tests must pass before and after.
- **Not building plugin auto-discovery.** Explicit dict registration in `lanes/__init__.py`. Greppable, no import-side-effect surprises.
- **Not touching the marketing_audit customer-facing audit pipeline.** R2, Cloudflare Worker, payment ledger, audit-lineage stay separately. The plugin participates in evolve; the commercial wrapper lives in `src/audit/`.
- **Not touching harness wrappers.** `harness/engine.py`, `harness/run.py`, `harness/prompts.py` stay as harness-side infrastructure; the plugin reads runtime prompts from them.
- **Not redesigning the marketing_audit plan or the harness_fixer brainstorm.** They get rewritten against the new substrate as separate work, after this substrate ships.
- **Not adding a class hierarchy.** `ResearchLaneHelper` is a utility module of free functions, not a base class. Lanes implement the `LanePlugin` Protocol independently and call into the helper.

## 4. Architecture

```
autoresearch/
  evolve_runtime/                            # SUBSTRATE — ~250 LoC
    __init__.py
    lane_plugin.py                           # Protocol + ScoreResult + ValidationResult
    cli.py                                   # `autoresearch evolve` dispatcher
    variant_fs.py                            # clone_variant, current_head, set_head
    lineage.py                               # append_entry with required-fields enforcement
    parent_select.py                         # within-lane parent picking by objective_score
    multi_lane.py                            # --lane all orchestration
  lanes/
    __init__.py                              # LANES = {"geo": GeoLane(), ...} explicit registry
    research/                                # SHARED HELPER — ~600 LoC
      helper.py                              # default_geomean_score, default_l1_validate, etc.
      runner.py                              # run.py logic moves here (pre-session config + session loop)
      geo.py                                 # GeoLane plugin — ~120 LoC
      competitive.py
      monitoring.py
      storyboard.py
    marketing_audit/                         # PLUGIN — ~400 LoC (without commercial wrapper)
      plugin.py
      score.py                               # weighted-sum + penalties
      manifest.py                            # file-bytes hashing
      smoke_test.py                          # pre-promotion gate
    harness_fixer/                           # PLUGIN — ~300 LoC
      plugin.py
      score.py                               # weighted-sum + cost penalty
      manifest.py                            # markdown file hashing
docs/
  superpowers/specs/
    2026-04-27-autoresearch-evolve-substrate-design.md     # this doc
  architecture/
    lane-plugin-authoring-guide.md           # how to add a new lane (created in implementation)
    substrate-vs-plugin-decision-table.md    # what's where and why (created in implementation)
```

## 5. The Protocol

```python
# autoresearch/evolve_runtime/lane_plugin.py
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class ScoreResult:
    """Result of plugin.score(). The substrate uses `objective_score` for
    within-lane parent selection; `details` is opaque plugin-specific data
    that gets written into lineage entry's `lane_data` sub-dict."""

    objective_score: float
    details: dict[str, object]


@dataclass(frozen=True)
class ValidationResult:
    """Result of plugin.validate(). Used to gate variants before scoring."""

    passed: bool
    failures: list[str]


class LanePlugin(Protocol):
    """A lane plugin participates in the evolve lifecycle.

    Required: name, path_prefixes, mutate, score.
    Optional (substrate provides defaults): clone, validate, promote, lineage_entry_extension.
    """

    # Required attributes
    name: str
    """Lane identifier — used in CLI, lineage entries, file paths. Lowercase, snake_case."""

    path_prefixes: tuple[str, ...]
    """Paths within a variant directory this lane owns. Used for clone-and-filter
    operations. Existing lanes own things like `programs/geo-session.md`,
    `templates/geo/`, etc."""

    # Required methods
    def mutate(self, variant_dir: Path) -> None:
        """Produce a new variant by mutating files in variant_dir. Typically
        invokes a meta-agent. Returns when complete."""
        ...

    def score(self, variant_dir: Path, fixtures: list[dict]) -> ScoreResult:
        """Evaluate this variant against the provided fixtures. Returns a single
        comparable scalar (`objective_score`) used for parent selection, plus
        opaque `details` that get written to the lineage entry's lane_data."""
        ...

    # Optional methods (substrate provides defaults; plugins override only if needed)
    def clone(self, parent_dir: Path, child_dir: Path) -> None:
        """Default: copy parent_dir to child_dir, filtered by path_prefixes.
        Plugins override to do special things at clone time (e.g. snapshot
        critique manifests, inject runtime config files)."""
        ...

    def validate(self, variant_dir: Path) -> ValidationResult:
        """Default: check that every path in path_prefixes exists. Plugins
        override to do deeper validation (file-bytes hash verification,
        compile checks, structural gates)."""
        ...

    def promote(self, variant_dir: Path) -> None:
        """Default: set_head(name, variant_dir.name). Plugins override to
        add pre-promotion gates (smoke tests, regression checks, customer-
        facing safety rails)."""
        ...

    def lineage_entry_extension(self, variant_dir: Path, score: ScoreResult) -> dict:
        """Default: returns score.details. Plugins can override to inject
        additional fields. The result becomes the `lane_data` sub-dict in
        the lineage entry."""
        ...
```

**4 required + 4 with defaults = 8 surface elements.** The required four are the minimum viable: every plugin must say what produces a variant (`mutate`) and what evaluates one (`score`). Everything else has a sensible default.

## 6. Substrate services

### 6.1 Variant filesystem (`evolve_runtime/variant_fs.py`)

Owns `archive/<variant_id>/` convention. Provides:
- `clone_variant(parent_dir, child_dir, included_paths) -> None` — copy with path filter.
- `current_head(lane: str) -> str | None` — read from `archive/current.json`.
- `set_head(lane: str, variant_id: str) -> None` — write to `archive/current.json`.
- `next_variant_id(archive_dir: Path) -> str` — `v002`, `v003`, ... sequence.

Knows nothing about scoring, behavior, or lane-specific paths.

### 6.2 CLI dispatcher (`evolve_runtime/cli.py`)

`autoresearch evolve --lane <name> [--candidates N] [--iterations M]` looks up the plugin in `lanes.LANES` and drives the lifecycle:

```python
def evolve(lane_name: str, ...) -> None:
    plugin = lanes.LANES[lane_name]
    parent_id = current_head(plugin.name)
    parent_dir = archive_dir / parent_id
    for i in range(iterations):
        for c in range(candidates):
            child_id = next_variant_id(archive_dir)
            child_dir = archive_dir / child_id
            plugin.clone(parent_dir, child_dir)
            plugin.mutate(child_dir)
            validation = plugin.validate(child_dir)
            if not validation.passed:
                lineage.append_discarded(child_id, parent_id, plugin.name, validation.failures)
                continue
            score = plugin.score(child_dir, fixtures)
            lineage.append_entry(child_id, parent_id, plugin.name, score, plugin.lineage_entry_extension(child_dir, score))
        parent_id = parent_select.best_in_lane(archive_dir, plugin.name)
        parent_dir = archive_dir / parent_id
    if config.require_holdout:
        finalist = best_finalist_in_lane(plugin.name)
        plugin.promote(archive_dir / finalist)
```

`--lane all` iterates `lanes.LANES.items()` sequentially.

### 6.3 Lineage (`evolve_runtime/lineage.py`)

Appends to `archive/lineage.jsonl`. Enforces 5 required root fields:

```python
{
    "id": "v012",                        # required
    "lane": "geo",                       # required
    "parent": "v011",                    # required (or null for v002)
    "children": 0,                       # required (auto-incremented on next clone)
    "timestamp": "2026-04-27T10:00:00Z", # required
    "objective_score": 0.847,            # required for non-discarded entries
    "lane_data": {...}                   # plugin's extension dict
}
```

Plugin's `lineage_entry_extension(variant_dir, score)` returns the `lane_data` sub-dict. The substrate adds the 5 required root fields + `objective_score = score.objective_score`.

The existing 4 lanes' lineage entries — `scores`, `search_metrics`, `domains`, `inner_metrics`, `secondary_scores`, `promotion_summary`, `selection_rationale`, `backend`, `model`, `eval_target`, `promoted_at`, `holdout_metrics` — all move into `lane_data`. Per-lane scripts that read these continue to work via `entry["lane_data"]["..."]`.

### 6.4 Within-lane parent selection (`evolve_runtime/parent_select.py`)

Filters lineage by lane, picks variant with highest `objective_score` (excluding discarded). Replaces today's scattered logic in `select_parent.py:_objective_score()` and `frontier.py:objective_score()` — no more `if lane == "core"` dispatch.

```python
def best_in_lane(archive_dir: Path, lane: str) -> str:
    entries = [e for e in read_lineage(archive_dir) if e["lane"] == lane and e.get("status") != "discarded"]
    return max(entries, key=lambda e: e["objective_score"])["id"]
```

### 6.5 Multi-lane orchestration (`evolve_runtime/multi_lane.py`)

`--lane all` iterates registered plugins. Per-lane independent state; no cross-lane coupling.

## 7. Lineage schema split (the key call)

Per Agent 5's analysis (read all consumers of `archive/lineage.jsonl`), only **5 fields are substrate-required at root**:
- `id`, `lane`, `parent`, `children`, `timestamp`

Plus one substrate-required field for selection:
- `objective_score` — produced by `plugin.score()`, used for parent picking

Everything else moves to `lane_data` sub-dict, owned per-plugin:
- Existing 4 lanes' `lane_data`: `scores`, `search_metrics`, `secondary_scores`, `inner_metrics`, `promotion_summary`, `selection_rationale`, `backend`, `model`, `eval_target`, `promoted_at`, `holdout_metrics`.
- Marketing_audit's `lane_data`: weighted-sum component breakdown, engagement signal pointer (`audits/lineage.jsonl` row id), per-stage cost.
- Harness_fixer's `lane_data`: HM-1..HM-8 axis scores, cost penalty applied, `verifier_report.json` pointer, `changes.txt` summary.

## 8. ResearchLaneHelper

The existing 4 lanes share enough that consolidating their helper logic is worth it. `autoresearch/lanes/research/helper.py` provides free functions:

- `default_geomean_score(variant_dir, fixtures, lane_name) -> ScoreResult` — invokes `evaluate_variant.py` as subprocess (preserving today's isolation), parses output, returns geomean × geomean composite.
- `default_l1_validate(variant_dir, lane_name) -> ValidationResult` — checks critique manifest (Python symbol hashing), `run.py` exists, `*.py` compile, `programs/<lane>-session.md` exists.
- `default_clone_with_manifest_snapshot(parent_dir, child_dir, path_prefixes) -> None` — clone-and-filter + snapshot critique manifest at clone time.
- `default_lineage_extension(variant_dir, score) -> dict` — current-shape lineage extras (search_metrics, domains, etc.).

Plus `runner.py` containing the pre-session config + session loop logic from today's `run.py`. Non-research plugins (marketing_audit, harness_fixer) don't import this — they have their own runners.

Each existing-lane plugin (`research/geo.py`, etc.) is ~120 LoC — declares `name`, `path_prefixes`, `rubric_ids`, `structural_doc_facts`, `session_md_filename`; delegates `score`, `validate`, `clone`, `lineage_entry_extension` to the helper; trivial-overrides where needed (geo's `pre_summary_hooks` runs `build_geo_report.py` — that becomes part of the geo plugin's `mutate()`).

## 9. Plugin registration

Explicit dict in `autoresearch/lanes/__init__.py`:

```python
from autoresearch.lanes.research.geo import GeoLane
from autoresearch.lanes.research.competitive import CompetitiveLane
from autoresearch.lanes.research.monitoring import MonitoringLane
from autoresearch.lanes.research.storyboard import StoryboardLane
from autoresearch.lanes.marketing_audit.plugin import MarketingAuditLane
from autoresearch.lanes.harness_fixer.plugin import HarnessFixerLane

LANES: dict[str, LanePlugin] = {
    "geo": GeoLane(),
    "competitive": CompetitiveLane(),
    "monitoring": MonitoringLane(),
    "storyboard": StoryboardLane(),
    "marketing_audit": MarketingAuditLane(),
    "harness_fixer": HarnessFixerLane(),
}
```

Adding a 7th lane: import + one dict entry. Greppable. No import side effects beyond the plugin's class definition.

## 10. What this unblocks

**Marketing_audit Unit 17** drops from 18 file ops to ~3:
1. Add to `lanes/__init__.py:LANES`.
2. The plugin module itself.
3. `autoresearch/archive/current_runtime/programs/marketing_audit/...` — runtime files (stage prompts, eval scope yaml). These are runtime artifacts the plugin owns.

The customer-facing wrapper (R2, Worker, payment, audit-lineage, evolve_lock) is separately tracked and unaffected by this design — it's `src/audit/` which already exists in the marketing_audit plan.

**Harness_fixer §7** drops from ~16 sites to ~5:
1. Add to `lanes/__init__.py:LANES`.
2. The plugin module itself.
3. `autoresearch/archive/current_runtime/programs/harness_fixer-session.md` — runtime file.
4-6. `harness/engine.py`, `harness/run.py`, `harness/prompts.py` — harness-side wrappers (stay no matter what).

The new `_file_hash(path)` extension to `critique_manifest.py` (~30-50 LoC) becomes a substrate utility used by harness_fixer's plugin's manifest module.

## 11. Migration plan (big-bang)

One PR series, ~10 days. Rough sequencing:

1. **Day 1-2:** Substrate skeleton — `evolve_runtime/` directory, Protocol, variant_fs, lineage append, parent_select. Tests for each component in isolation.
2. **Day 3:** CLI dispatcher + multi-lane orchestration. Tests against a stub plugin.
3. **Day 4-5:** ResearchLaneHelper — extract today's run.py, evaluate_variant.py subprocess pattern, default_geomean_score, default_l1_validate. Tests passing on existing fixtures.
4. **Day 6-7:** Migrate geo + competitive plugins. Tests passing for both.
5. **Day 8:** Migrate monitoring + storyboard plugins. Full existing test suite passes.
6. **Day 9:** Cascade-grep + delete the 24 duplicated lane-name sites. Update consumers (frontier, select_parent, evaluate_variant) to use the new substrate.
7. **Day 10:** Smoke run of `autoresearch evolve --lane all` with 1 iteration. Land PR.

Marketing_audit and harness_fixer migrations happen *after* this lands, as separate PRs against the existing marketing_audit plan + new harness_fixer plan.

The old handoff doc (`docs/plans/2026-04-26-001-autoresearch-lane-registry-refactor-handoff.md`) gets a small commit on the refactor branch marking it superseded by this design.

## 12. Risks + mitigations

**R1. Existing 4 lanes don't fit ResearchLaneHelper as cleanly as I expect.** Mitigation: the helper is utility functions, not a base class — if 1-2 functions don't fit a particular lane, that lane just doesn't import them. Plugins always have escape hatches.

**R2. Substrate API turns out to be wrong mid-implementation.** Mitigation: substrate gets built first, tested in isolation, then existing 4 lanes migrate. If migration reveals an API gap, we fix it before marketing_audit/harness_fixer touch it.

**R3. Subprocess isolation breaks under the new architecture.** Mitigation: ResearchLaneHelper preserves the subprocess pattern (`evaluate_variant.py` invocation) inside `default_geomean_score`. Existing 4 lanes don't notice the difference.

**R4. Lineage schema migration breaks downstream consumers I haven't checked.** Mitigation: Agent 5 surveyed all *code* consumers, all use accessor functions or dict lookups that work post-migration. *Non-code* consumers (dashboards, alerting, manual scripts) are an unknown — to be validated during implementation by grepping for `lineage.jsonl` outside the autoresearch tree. If a consumer breaks, fields can be added back to root.

**R5. Marketing_audit's commercial-wrapper / plugin separation isn't as clean as sketched.** The engagement-judge feedback loop crosses both layers. Mitigation: this design doesn't redesign the commercial wrapper — it stays in `src/audit/` per the marketing_audit plan. The bridge (commercial path writes `audits/lineage.jsonl` → engagement judge reads → updates autoresearch lineage `lane_data.engagement` lazily) is specified as a sketch in the marketing_audit plan rewrite, not in this substrate design.

**R6. Pre-promotion smoke-test ends up duplicated between marketing_audit and harness_fixer.** Mitigation: per-plugin for now. If a 3rd consumer wants the same shape, extract a substrate utility. ~50-100 LoC of acceptable duplication.

## 13. Decision table

| Concern | Substrate or plugin? | Why |
|---|---|---|
| Variant directory layout | Substrate | Universal — every lane uses `archive/<id>/` |
| Variant cloning (filtered copy) | Substrate (default) | Plugin can override for clone-time work |
| `autoresearch evolve` CLI | Substrate | One entry point, dispatches to plugins |
| Multi-lane orchestration | Substrate | Cross-cuts plugins by definition |
| Lineage append (5 root fields) | Substrate | Required for cross-lane visibility + parent selection |
| Lineage extension (lane_data) | Plugin | Lane-specific by definition |
| Within-lane parent selection | Substrate | Generic numeric comparison; same algorithm for all lanes |
| Cross-lane comparison | Not needed | Parent selection is always within-lane |
| Score scale ([0,1] vs [-2,10] vs cost-weighted) | Plugin | Plugin produces `objective_score` scalar; substrate doesn't care about range |
| Score aggregation (geomean, weighted-sum, etc.) | Plugin | Each lane's policy |
| Gate sequence (L1 marker, manifest, structural, smoke-test) | Plugin (`validate`, `promote`) | Each lane decides what to gate |
| Frozen-content mechanism (Python symbol vs file-bytes) | Plugin | Each lane manages its own freeze policy |
| Pre-promotion smoke-test | Plugin's `promote()` | YAGNI on substrate-level utility |
| Engagement signal (delayed scoring) | Out-of-band module | Marketing_audit's bridge between commercial path + plugin |
| Pre-session config (stall_limit, max_turns, max_wall_time) | Plugin's `mutate()` (research helper for the 4) | Existing lanes share via helper; new lanes manage their own |
| Subprocess isolation for scoring | Plugin's choice | ResearchLaneHelper preserves it; new lanes decide |
| Customer-facing audit pipeline (R2, Worker, payment) | Out of scope | Lives in `src/audit/`, not the plugin |
| Harness wrappers (engine.py, run.py, prompts.py) | Out of scope | Lives in `harness/`, not the plugin |
| Rubric prompt text | `src/evaluation/rubrics.py` (existing) | Plugin references rubric IDs; prompt text stays in shared registry |

## 14. Open items I'm uncertain about (for implementation to validate)

These are flagged for explicit checking during implementation, not redesign:

1. **ResearchLaneHelper fit:** assumed clean for all 4 existing lanes; verify per-lane during migration.
2. **`objective_score` as single scalar:** assumed sufficient for all near-term lanes; revisit if a future lane wants Pareto-frontier multi-axis selection.
3. **Substrate LoC budget:** estimated ~250 LoC; could land at 300-400 once written. Not a design problem.
4. **Lineage non-code consumers:** Agent 5 surveyed code consumers; non-code (dashboards, scripts, alerts) is to be greplisted at implementation time.
5. **Commercial-wrapper bridge for marketing_audit:** specified in this doc as a sketch; concrete bridge design lives in the marketing_audit plan rewrite.
6. **Smoke-test duplication between marketing_audit and harness_fixer:** keep per-plugin; extract if a 3rd consumer wants the same shape.

## 15. After this spec ships

1. **Spec self-review** — fix placeholders, contradictions, scope creep inline.
2. **JR review gate** — JR reads the spec, requests changes or approves.
3. **Writing-plans skill invocation** — produces the implementation plan with concrete work units, dependencies, test strategy.
4. **Mark old handoff superseded** — small commit on `refactor/autoresearch-lane-registry` pointing at this spec.
5. **Implementation per the plan** — substrate first, then 4 lane migrations, then marketing_audit + harness_fixer plan rewrites against the new substrate.

End of spec.
