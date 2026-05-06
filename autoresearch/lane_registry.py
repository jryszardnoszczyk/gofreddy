"""Lane registry — single source of truth for per-lane data + divergent-behavior hooks.

Replaces 24 hardcoded lane-name dispatch sites. The 5 existing lanes are LaneSpec
instances; future divergent lanes register their own with optional `custom_*`
callables overriding default behavior at the 5 divergence points (mutate / score
/ validate / promote / objective_score_from_entry).

See:
- `docs/architecture/lane-registry.md` — how to add a lane (field reference + worked example).
- `docs/plans/2026-04-27-002-feat-autoresearch-lane-registry-plan.md` — design rationale.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class LaneSpec:
    """Per-lane configuration + optional divergent-behavior callables."""
    name: str
    is_workflow_lane: bool
    rubric_ids: tuple[str, ...] = ()
    path_prefixes: tuple[str, ...] = ()
    # Subprefixes within the lane's owned tree that the meta-agent may
    # READ but not EDIT. Workflow enforcement code (completion_guard,
    # stall_limit, count_findings, etc.) goes here so the meta-agent
    # cannot lower its own evaluation bar — Pi v007 mutated workflows/geo.py
    # to neuter completion_guard + raise stall_limit 5→15 and the loop
    # silently accepted the gradient. Match is by exact rel_path equality
    # OR rel_path startswith(subprefix + "/"). A5 (plan 2026-05-06-001).
    readonly_subprefixes: tuple[str, ...] = ()
    session_md_filename: str = ""
    deliverables: tuple[str, ...] = ()
    intermediate_artifacts: tuple[str, ...] = ()
    structural_doc_facts: tuple[str, ...] = ()
    structural_gate_functions: tuple[str, ...] = ()
    custom_mutate: Callable[..., Any] | None = None
    custom_score: Callable[..., Any] | None = None
    custom_validate: Callable[..., Any] | None = None
    custom_promote: Callable[..., Any] | None = None
    custom_objective_score_from_entry: Callable[..., Any] | None = None


def _rubric_ids(prefix: str) -> tuple[str, ...]:
    return tuple(f"{prefix}-{i}" for i in range(1, 9))


# Files inside `workflows/` that are *shared* infra used by every workflow lane
# (re-exported from `__init__`, eval-cache, the spec types, and the
# session_eval_common / session_eval_registry plumbing that every lane's
# enforcement code imports). These are off-limits to ALL lanes — not just
# core — because a `core`-lane mutation that monkey-patches
# `workflows/__init__.py` (e.g. `import workflows.geo as g; g.completion_guard
# = lambda *a, **k: (None, None)`) propagates via Python imports to every
# workflow lane's holdout. Same class as Pi v007's completion_guard neutering,
# different file. Kept separate from `LaneSpec.readonly_subprefixes` so future
# readers see "shared = always readonly" instead of being confused about why
# `core` would carry workflow-related entries. G1 (review of d128a5c).
SHARED_WORKFLOW_READONLY: tuple[str, ...] = (
    "workflows/__init__.py",
    "workflows/eval_cache.py",
    "workflows/specs.py",
    "workflows/session_eval_common.py",
    "workflows/session_eval_registry.py",
)


LANES: dict[str, LaneSpec] = {
    "core": LaneSpec(name="core", is_workflow_lane=False),
    "geo": LaneSpec(
        name="geo",
        is_workflow_lane=True,
        rubric_ids=_rubric_ids("GEO"),
        path_prefixes=(
            "geo-findings.md", "programs/geo-session.md", "templates/geo",
            "scripts/allocate_gaps.py", "scripts/build_geo_report.py",
            "workflows/geo.py", "workflows/session_eval_geo.py",
        ),
        readonly_subprefixes=("workflows/geo.py", "workflows/session_eval_geo.py"),
        session_md_filename="geo-session.md",
        deliverables=("optimized/*.md",),
        structural_doc_facts=(
            "At least one `optimized/<file>` is present with non-empty content.",
            "Every `<script type=\"application/ld+json\">` block inside an optimized file parses as valid JSON.",
        ),
        structural_gate_functions=(
            "_validate_geo.optimized_non_empty",
            "_validate_geo.json_ld_parses",
        ),
    ),
    "competitive": LaneSpec(
        name="competitive",
        is_workflow_lane=True,
        rubric_ids=_rubric_ids("CI"),
        path_prefixes=(
            "competitive-findings.md", "programs/competitive-session.md",
            "templates/competitive", "scripts/extract_prior_summary.py",
            "scripts/format_report.py", "workflows/competitive.py",
            "workflows/session_eval_competitive.py",
        ),
        readonly_subprefixes=(
            "workflows/competitive.py", "workflows/session_eval_competitive.py",
        ),
        session_md_filename="competitive-session.md",
        deliverables=("brief.md",),
        structural_doc_facts=(
            "A file with `brief` in its name ending in `.md` exists (e.g. `brief.md`).",
            "At least one `competitors/<name>.json` (excluding `_`-prefixed helpers) is present and parses as valid JSON — shape only; judges evaluate sufficiency.",
        ),
        structural_gate_functions=(
            "_validate_competitive.brief_exists",
            "_validate_competitive.competitor_json_parses",
        ),
    ),
    "monitoring": LaneSpec(
        name="monitoring",
        is_workflow_lane=True,
        rubric_ids=_rubric_ids("MON"),
        path_prefixes=(
            "monitoring-findings.md", "programs/monitoring-session.md",
            "templates/monitoring", "workflows/monitoring.py",
            "workflows/session_eval_monitoring.py",
        ),
        readonly_subprefixes=(
            "workflows/monitoring.py", "workflows/session_eval_monitoring.py",
        ),
        session_md_filename="monitoring-session.md",
        deliverables=("digest.md",),
        intermediate_artifacts=("mentions/*.json",),
        structural_doc_facts=(
            "`session.md` exists.",
            "`results.jsonl` is non-empty and parseable.",
            "At least one `results.jsonl` entry has `type: select_mentions`.",
            "Clustering evidence is present — either `stories/*.json` files or a `digest.md` (low-volume weeks may skip clustering).",
            "Synthesis evidence is present — `digest.md` is the synthesized deliverable.",
            "Recommendation evidence is present — `recommendations/` files, a `results.jsonl` entry with `type: recommend`, or `digest.md`.",
            "`digest.md` exists.",
            "`findings.md` exists.",
            "Session status is terminal — `## Status: COMPLETE` in `session.md` or `digest.md` present.",
            "If any `recommendations/` files exist, `executive_summary.md` and `action_items.md` are both present.",
            "Source coverage — the latest `select_mentions` entry reports ≥2 sources, or `digest.md` is present (low-volume fallback).",
        ),
        structural_gate_functions=(
            "session_md_exists", "results_non_empty", "has_select_mentions",
            "has_cluster_stories", "has_synthesize", "has_recommend",
            "digest_exists", "findings_exists", "status_complete",
            "rec_exec_summary_and_action_items", "source_coverage",
        ),
    ),
    "storyboard": LaneSpec(
        name="storyboard",
        is_workflow_lane=True,
        rubric_ids=_rubric_ids("SB"),
        path_prefixes=(
            "storyboard-findings.md", "programs/storyboard-session.md",
            "templates/storyboard", "workflows/storyboard.py",
            "workflows/session_eval_storyboard.py",
        ),
        readonly_subprefixes=(
            "workflows/storyboard.py", "workflows/session_eval_storyboard.py",
        ),
        session_md_filename="storyboard-session.md",
        deliverables=("stories/*.json",),
        intermediate_artifacts=("patterns/*.json",),
        structural_doc_facts=(
            "At least one `stories/*.json` (PLAN_STORY phase) or `storyboards/*.json` (IDEATE phase) file is present.",
            "Each story/storyboard file parses as valid JSON and the top level is an object.",
            "Each file has a non-empty `scenes` / `scene_plan` array (storyboards may fall back to `source_story_plan.scenes`).",
            "When a story declares `scene_count`, it matches the length of the scenes array.",
            "Every scene has a non-empty `prompt`.",
            "Every scene (PLAN_STORY) has a non-empty camera field — `camera`, `camera_motion`, or `camera_movement`.",
        ),
        structural_gate_functions=(
            "_validate_storyboard.files_present", "_validate_storyboard.json_parses",
            "_validate_storyboard.scenes_non_empty", "_validate_storyboard.scene_count_matches",
            "_validate_storyboard.scene_has_prompt", "_validate_storyboard.scene_has_camera",
        ),
    ),
}


class ScopeViolation(RuntimeError):
    """Meta-agent edited a path declared readonly for the active lane.

    Raised by ``archive_index.sync_variant_workspace`` when the post-mutation
    file hash differs from pre-mutation for any path covered by
    ``LaneSpec.readonly_subprefixes``. Defense-in-depth: the workspace is
    chmod 0444 before the meta-agent runs (``prepare_meta_workspace``),
    but a determined agent can ``chmod +w`` first — this hash check
    catches that path. A5 (plan 2026-05-06-001).
    """


def path_is_readonly(rel_path: str, lane_name: str) -> bool:
    """Check whether ``rel_path`` (relative to the variant root) is declared
    readonly for ``lane_name``. Match is exact equality OR
    ``startswith(subprefix + '/')`` so a directory subprefix shields its
    contents. Unknown lane names raise KeyError to surface registry drift.

    Two lists are consulted: the lane's own ``LaneSpec.readonly_subprefixes``
    (lane-specific enforcement files) AND ``SHARED_WORKFLOW_READONLY``
    (shared workflow infra that propagates across lanes via Python imports).
    A path that matches either list is readonly. G1 (review of d128a5c)."""
    spec = LANES[lane_name]
    for subprefix in spec.readonly_subprefixes:
        if rel_path == subprefix or rel_path.startswith(subprefix + "/"):
            return True
    for subprefix in SHARED_WORKFLOW_READONLY:
        if rel_path == subprefix or rel_path.startswith(subprefix + "/"):
            return True
    return False


def all_lane_names() -> tuple[str, ...]:
    """All registered lane names (insertion order: core first, then workflow lanes)."""
    return tuple(LANES.keys())


def workflow_lane_names() -> tuple[str, ...]:
    """Workflow lane names — every lane with `is_workflow_lane=True`."""
    return tuple(name for name, spec in LANES.items() if spec.is_workflow_lane)


def get_spec(name: str) -> LaneSpec:
    """Look up a LaneSpec by name. Raises KeyError if not registered."""
    return LANES[name]


# Derived re-exports — single source of truth for consumers (evolve, evaluate_variant,
# regen_program_docs, structural, service, lane_paths). Consumers `from lane_registry
# import X` instead of declaring their own copy.
WORKFLOW_PREFIXES: dict[str, tuple[str, ...]] = {n: s.path_prefixes for n, s in LANES.items() if s.is_workflow_lane}
DELIVERABLES: dict[str, tuple[str, ...]] = {n: s.deliverables for n, s in LANES.items() if s.deliverables}
_INTERMEDIATE_ARTIFACTS: dict[str, tuple[str, ...]] = {n: s.intermediate_artifacts for n, s in LANES.items() if s.intermediate_artifacts}
DOMAIN_FILENAMES: dict[str, str] = {n: s.session_md_filename for n, s in LANES.items() if s.session_md_filename}
STRUCTURAL_DOC_FACTS: dict[str, list[str]] = {n: list(s.structural_doc_facts) for n, s in LANES.items() if s.structural_doc_facts}
STRUCTURAL_GATE_FUNCTIONS: dict[str, tuple[str, ...]] = {n: s.structural_gate_functions for n, s in LANES.items() if s.structural_gate_functions}
_DOMAIN_CRITERIA: dict[str, list[str]] = {n: list(s.rubric_ids) for n, s in LANES.items() if s.rubric_ids}


def default_objective_score_from_entry(entry: dict[str, Any], lane_name: str) -> float | None:
    """Per-lane single-scalar selection signal. Mirrors today's `frontier.objective_score()`:
    core ranks by composite; workflow lanes rank by their domain score."""
    spec = LANES[lane_name]
    if spec.custom_objective_score_from_entry is not None:
        return spec.custom_objective_score_from_entry(entry)
    metrics = entry.get("search_metrics")
    if not isinstance(metrics, dict):
        return None
    if not spec.is_workflow_lane:
        value = metrics.get("composite")
    else:
        domains = metrics.get("domains")
        if not isinstance(domains, dict):
            return None
        payload = domains.get(lane_name)
        if not isinstance(payload, dict):
            return None
        value = payload.get("score")
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _assert_models_literal_matches() -> None:
    """Verify `src/evaluation/models.py:160 EvaluateRequest.domain` Literal matches
    `workflow_lane_names()`. Callable, NOT module-load — avoids circular import."""
    from typing import get_args
    from src.evaluation.models import EvaluateRequest
    domain_field = EvaluateRequest.model_fields["domain"]
    literal_values = set(get_args(domain_field.annotation))
    expected = set(workflow_lane_names())
    if literal_values != expected:
        raise RuntimeError(
            f"src/evaluation/models.py:160 Literal {literal_values} "
            f"out of sync with LANES workflow lanes {expected}"
        )


def file_hash(path: Path) -> str:
    """SHA256 hex digest of the file's bytes. Raises FileNotFoundError if missing."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def compute_manifest(paths: list[Path], root_dir: Path) -> dict[str, str]:
    """Snapshot file-bytes hashes for `paths` keyed by path-relative-to-root_dir."""
    return {str(Path(p).relative_to(root_dir)): file_hash(Path(p)) for p in paths}


def verify_manifest(manifest_path: Path, root_dir: Path) -> tuple[bool, list[str]]:
    """Re-hash each entry in the JSON manifest at `manifest_path` against `root_dir`.
    Returns `(passed, failures)` listing missing/changed paths."""
    manifest = json.loads(Path(manifest_path).read_text())
    failures: list[str] = []
    for rel_path, expected_hash in manifest.items():
        abs_path = root_dir / rel_path
        if not abs_path.exists():
            failures.append(f"missing: {rel_path}")
            continue
        actual = file_hash(abs_path)
        if actual != expected_hash:
            failures.append(
                f"hash mismatch: {rel_path} (expected {expected_hash[:8]}, got {actual[:8]})"
            )
    return (not failures, failures)
