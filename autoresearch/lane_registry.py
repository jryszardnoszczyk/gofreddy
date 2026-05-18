"""Lane registry — single source of truth for per-lane data + divergent-behavior hooks.

Replaces 24 hardcoded lane-name dispatch sites. The 5 existing lanes are LaneSpec
instances; future divergent lanes register their own with optional `custom_*`
callables overriding default behavior at the 5 divergence points (mutate / score
/ validate / promote / objective_score_from_entry).

A new lane inherits three parallelism dimensions automatically — holdout
finalists, critic domains, and fixture fan-out — by registering here. Cross-
lane parallelism in `run_all_lanes` is intentionally NOT enabled (cmd_run is
not thread-safe — see `docs/architecture/concurrency.md`). No concurrency
code goes in the lane's own modules.

See:
- `docs/architecture/lane-registry.md` — how to add a lane (field reference + worked example).
- `docs/architecture/concurrency.md` — how lanes inherit parallel_for + provider semaphores.
- `docs/plans/2026-04-27-002-feat-autoresearch-lane-registry-plan.md` — design rationale.
"""

from __future__ import annotations

import hashlib
import json
import sys
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
    # Optional hook called by `evaluate_variant._evaluate_one_run` after a
    # judge-service response is normalized, before the result dict is built.
    # Signature: ``(judge_payload: dict, session_dir: Path | None, fixture_id: str) -> None``.
    # Lets a lane persist judge-side metadata sidecars (e.g. monitoring's
    # `digest-meta.json` carrying DQS) without the orchestrator carrying a
    # hardcoded `domain == "monitoring"` branch. D3 (audit 2026-05-07).
    custom_persist_judge_payload: Callable[[dict, Path | None, str], None] | None = None
    # A5: optional rubric IDs for the rendering-quality dimensions. Lanes that
    # opt into self-improving report rendering set this to e.g. ("RND-1",
    # "RND-2", ..., "RND-5"). Default empty tuple = lane does NOT participate
    # in rendering scoring (current behavior preserved). The rendering rubric
    # is a cross-lane domain in src/evaluation/rubrics.py per spec D2.
    # Spec section A5 (docs/plans/2026-05-07-003-self-improving-report-rendering.md).
    render_rubric_ids: tuple[str, ...] = ()
    # Per-step model split (2026-05-13): override the inner fixture-session
    # backend/model for THIS lane only, regardless of EVOLUTION_INNER_BACKEND/
    # EVOLUTION_INNER_MODEL env vars. Used when a lane has a known
    # provider-specific incompatibility with the run-wide default.
    # Geo: codex/gpt-5.5 cybersecurity filter rejects geo's bot-UA enumeration
    # (v183 collapse). See memory project-geo-regression-root-cause-2026-05-12.md.
    # Resolution priority: lane override > CLI flag > env var > default.
    inner_backend: str | None = None
    inner_model: str | None = None


def _rubric_ids(prefix: str) -> tuple[str, ...]:
    return tuple(f"{prefix}-{i}" for i in range(1, 9))


def _persist_monitoring_dqs_score(
    judge_payload: dict, session_dir: Path | None, fixture_id: str
) -> None:
    """Persist DQS sidecar (``digest-meta.json``) when the monitoring judge
    payload carries one. Wired as ``LaneSpec.custom_persist_judge_payload`` for
    monitoring; replaces the hardcoded ``domain == "monitoring"`` branch in
    ``evaluate_variant._evaluate_one_run`` (D3, audit 2026-05-07)."""
    dqs_score = judge_payload.get("dqs_score") if isinstance(judge_payload, dict) else None
    if dqs_score is None or session_dir is None:
        return
    try:
        meta_path = session_dir / "digest-meta.json"
        existing: dict = {}
        if meta_path.exists():
            try:
                payload = json.loads(meta_path.read_text(encoding="utf-8", errors="replace"))
                if isinstance(payload, dict):
                    existing = payload
            except json.JSONDecodeError:
                existing = {}
        existing["dqs_score"] = dqs_score
        meta_path.write_text(json.dumps(existing, indent=2) + "\n")
    except OSError as exc:
        print(
            f"  warning: failed to persist dqs_score for {fixture_id}: {exc}",
            file=sys.stderr,
        )


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
    # Dynamic-renderer prompts: agent-controlled output flows into rendered
    # reports + screenshots that feed the vision sub-judge → render_quality
    # dimension. A meta-agent able to mutate these can manufacture high
    # render scores by injecting fabricated content. Closes adv-render-10.
    "programs/render",
    "scripts/render_report.py",
    "scripts/render_judge.py",
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
            "`gap_allocation.json` exists at the session root with at least one allocation entry.",
            "The artifact contains a `[FAQ]` marker, or a `## FAQ` heading, or a `## Frequently Asked` heading (around the 5-7 Q&A block from CQ-2).",
            "The artifact contains a literal `[INTRO]` marker — the bracket form is required; `## Intro` / `## Introduction` will fail.",
            "The artifact is at least 300 words. The `[HOWTO]`, `[SCHEMA]`, `[TECHFIX]`, `[PRUNE]`, and `[FILL]` markers follow the same bracket convention and are read by `scripts/build_geo_report.py` when compiling the final report.",
        ),
        structural_gate_functions=(
            "_validate_geo.optimized_non_empty",
            "_validate_geo.json_ld_parses",
            "_session_eval_geo.gap_allocation_present",
            "_session_eval_geo.faq_marker",
            "_session_eval_geo.intro_marker",
            "_session_eval_geo.min_300_words",
        ),
        # α2: full RND-1..5 — geo reports use static + interactive surfaces both.
        render_rubric_ids=("RND-1", "RND-2", "RND-3", "RND-4", "RND-5"),
        # codex/gpt-5.5 cyber filter rejected bot-UA enumeration on v183
        # (2026-05-12); claude/sonnet override removed 2026-05-17 — the
        # prompt-level "Why this isn't a security task" block in
        # programs/geo-session.md neutralises the filter. Re-add override
        # only if the cyber marker fires again in is_terminal_codex_failure.
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
        render_rubric_ids=("RND-1", "RND-2", "RND-3", "RND-4", "RND-5"),
        # codex/gpt-5.5 cyber filter rejected epic/figma/canva intel on
        # 2026-05-13 Phase 3; claude/sonnet override removed 2026-05-17 —
        # the prompt-level "Why this isn't a security task" block in
        # programs/competitive-session.md neutralises the filter. Re-add
        # override only if the cyber marker fires in is_terminal_codex_failure.
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
        custom_persist_judge_payload=_persist_monitoring_dqs_score,
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
        render_rubric_ids=("RND-1", "RND-2", "RND-3", "RND-4", "RND-5"),
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
        # Storyboard skips RND-3 (PDF print-readiness less critical for the
        # cinematic dark-mode theme — meant for screen, not paper).
        render_rubric_ids=("RND-1", "RND-2", "RND-4", "RND-5"),
    ),
    # Marketing audit — 6th lane (5th workflow lane). Master plan
    # 2026-05-06-001 §3.1. 2 of 5 callables wired in v1
    # (custom_score + custom_validate); custom_promote stays None
    # until post-audit-3 holdout fixtures land; custom_mutate uses
    # default meta-agent; custom_objective_score_from_entry stays
    # None (default reader works — custom_score pre-folds engagement
    # bonus into metrics.domains.marketing_audit.score per §6.2).
    "marketing_audit": LaneSpec(
        name="marketing_audit",
        is_workflow_lane=True,
        rubric_ids=_rubric_ids("MA"),
        path_prefixes=(
            "marketing_audit-findings.md",
            "programs/marketing_audit-session.md",
            "programs/marketing_audit/prompts/",
            "templates/marketing_audit",
            "workflows/marketing_audit.py",
            "workflows/session_eval_marketing_audit.py",
        ),
        readonly_subprefixes=(
            "workflows/marketing_audit.py",
            "workflows/session_eval_marketing_audit.py",
        ),
        session_md_filename="marketing_audit-session.md",
        deliverables=(
            "findings.md",
            "report.md",
            "report.json",
            "report.html",
            "report.pdf",
        ),
        intermediate_artifacts=(
            "stage2_subsignals/L*_*.json",
            "stage2_parent_findings/*.json",
        ),
        structural_doc_facts=(
            "`findings.md` exists with all 9 deliverable sections — "
            "findability, narrative, acquisition, experience, competitive, "
            "monitoring, geo (display: AI Visibility), state_of_business, "
            "martech_compliance.",
            "`proposal.md` (when present) contains the 3 capability-registry "
            "tier headers in fixed order: fix_it, build_it, run_it.",
        ),
        structural_gate_functions=(
            "_validate_marketing_audit.findings_nine_sections",
            "_validate_marketing_audit.proposal_three_tiers",
        ),
        # Custom callables are imported lazily via _load_marketing_audit_callables()
        # to avoid circular imports between lane_registry → src.audit → ...
        # The wired callables are populated in the module bottom; see
        # _wire_marketing_audit_callables() below.
        render_rubric_ids=("RND-1", "RND-2", "RND-3", "RND-4", "RND-5"),
    ),
    # X Engine — content-engine sibling lane producing X drafts on a per-fixture
    # basis. Per master plan v13 §4.1. rubric_ids inlined as 6-tuple (the
    # `_rubric_ids("X")` helper above hardcodes range(1, 9) which would
    # over-shoot to 8 IDs). The shared voice substrate
    # programs/references/voice.md is locked in BOTH lanes'
    # readonly_subprefixes — single file, both lanes' meta-agents read but
    # neither mutates. path_is_readonly is per-lane lookup so dual-claim is
    # safe (Round-7 housekeeping).
    "x_engine": LaneSpec(
        name="x_engine",
        is_workflow_lane=True,
        rubric_ids=("X-1", "X-2", "X-3", "X-4", "X-5", "X-6", "X-9"),
        path_prefixes=(
            "programs/x_engine-session.md",
            "programs/x_engine-evaluation-scope.yaml",
            "programs/references/voice.md",
            "templates/x_engine",
            "workflows/x_engine.py",
            "workflows/session_eval_x_engine.py",
        ),
        readonly_subprefixes=(
            "workflows/x_engine.py",
            "workflows/session_eval_x_engine.py",
            "programs/references/voice.md",
        ),
        session_md_filename="x_engine-session.md",
        deliverables=("drafts/*.md",),
        intermediate_artifacts=("angles/*.json", "drafts/*.eval.json"),
        # Bullets describe what `session_eval_x_engine.structural_gate`
        # enforces per-artifact (workflows/session_eval_x_engine.py:72-163).
        # Geo/competitive/monitoring/storyboard route through
        # `_validate_<domain>` in structural.py; new lanes route through
        # SessionEvalSpec.structural_gate. Both end up with the same shape
        # of session-md AUTOGEN block.
        structural_doc_facts=(
            "Frontmatter is valid YAML with required fields: `draft_id`, `angle_id`, `platform`, `length_bracket`, `char_count`, `voice_pillar`.",
            "`length_bracket` is one of {sharp, build, case_study}.",
            "`[BODY]` block char_count fits the length_bracket: sharp 250-300, build 500-900, case_study 1000-1500.",
            "`[META]` block has `hook`, `authority_anchor`, `specific_number`, `attribution`.",
            "`xeng slop-check --platform x` passes against the `[BODY]` text.",
        ),
        structural_gate_functions=(
            "session_eval_x_engine.frontmatter_yaml_required_fields",
            "session_eval_x_engine.length_bracket_valid",
            "session_eval_x_engine.body_chars_fit_bracket",
            "session_eval_x_engine.meta_required_keys",
            "session_eval_x_engine.slop_check_x_passes",
        ),
        # Vision sub-judge — grades the rendered report screenshot against
        # the RND-1..5 rubric. Without this, render_judge.py post-render is
        # a no-op for x_engine and the renderer-evolution loop has nothing
        # to optimise against.
        render_rubric_ids=("RND-1", "RND-2", "RND-3", "RND-4", "RND-5"),
    ),
    # LinkedIn Engine — sibling to x_engine. Same shape, different rubric ids
    # + per-platform structural rules in SessionEvalSpec (hashtags ≤5, longer
    # length brackets, no em-dash check, LinkedIn-specific tells). Consumes
    # X-derived angles per D13 (plan §3.6) — same v1 angles table.
    "linkedin_engine": LaneSpec(
        name="linkedin_engine",
        is_workflow_lane=True,
        rubric_ids=("LI-1", "LI-2", "LI-3", "LI-4", "LI-5", "LI-6"),
        path_prefixes=(
            "programs/linkedin_engine-session.md",
            "programs/linkedin_engine-evaluation-scope.yaml",
            "programs/references/voice.md",
            "templates/linkedin_engine",
            "workflows/linkedin_engine.py",
            "workflows/session_eval_linkedin_engine.py",
        ),
        readonly_subprefixes=(
            "workflows/linkedin_engine.py",
            "workflows/session_eval_linkedin_engine.py",
            "programs/references/voice.md",
        ),
        session_md_filename="linkedin_engine-session.md",
        deliverables=("drafts/*.md",),
        intermediate_artifacts=("angles/*.json", "drafts/*.eval.json"),
        structural_doc_facts=(
            "Frontmatter is valid YAML with required fields: `draft_id`, `angle_id`, `platform`, `length_bracket`, `char_count`, `voice_pillar`.",
            "`length_bracket` is one of {short_take, thought_leader, case_study}.",
            "`[BODY]` block char_count fits the length_bracket: short_take 500-900, thought_leader 1500-2500, case_study 2500-3000.",
            "`[META]` block has `hook`, `authority_anchor`, `specific_number`, `attribution`, `hashtags`.",
            "Hashtag count in `[META]` is in `[1, 5]` (0 or >5 blocks ship).",
            "`xeng slop-check --platform linkedin` passes against the `[BODY]` text.",
        ),
        structural_gate_functions=(
            "session_eval_linkedin_engine.frontmatter_yaml_required_fields",
            "session_eval_linkedin_engine.length_bracket_valid",
            "session_eval_linkedin_engine.body_chars_fit_bracket",
            "session_eval_linkedin_engine.meta_required_keys",
            "session_eval_linkedin_engine.hashtag_count_valid",
            "session_eval_linkedin_engine.slop_check_linkedin_passes",
        ),
        # Same rationale as x_engine — without rubric IDs, render_judge.py
        # is a no-op for this lane and the evolution loop has no signal to
        # optimise the renderer-prompts against.
        render_rubric_ids=("RND-1", "RND-2", "RND-3", "RND-4", "RND-5"),
    ),
}


def _wire_marketing_audit_callables() -> None:
    """Lazy-bind the 2 wired callables to the marketing_audit LaneSpec.

    Called once at module load (bottom of file). Avoids circular
    imports between lane_registry → src.audit.score / src.audit.validate
    → (anything that touches lane_registry).

    LaneSpec is frozen, so we use object.__setattr__ to bypass the
    immutability for this one-shot binding.

    Soft-fail on ImportError: lane_registry is imported by autoresearch
    subprocesses that may not have ``src/`` on sys.path (e.g. CLIs run
    from the autoresearch directory). The src.audit.* callables are
    L1 stubs returning sane defaults — when src/ isn't reachable, the
    callables stay None and the substrate falls through to default
    behavior (matching peer-lane wiring before L3).
    """
    # 2026-05-12 fix: marketing_audit_score is a STUB that returns score=0
    # and never writes to lineage.jsonl, so every variant gets discarded
    # via `not variant_in_lineage(...)` in evolve.py. Symptoms: today's
    # marketing_audit lane discarded every variant across multiple gens.
    # Until L3 implements the real geometric-mean MA-1..MA-8 scoring, leave
    # custom_score=None so the substrate falls through to _score_variant_search,
    # which DOES run the 4 marketing_audit fixtures (anthropic, dwf, perplexity,
    # substack) defined in eval_suites/search-v1.json and writes lineage.
    # marketing_audit_validate is fine to wire (returns (True, []) — pass).
    try:
        from src.audit.validate import marketing_audit_validate
    except ImportError:
        return

    spec = LANES["marketing_audit"]
    object.__setattr__(spec, "custom_validate", marketing_audit_validate)


_wire_marketing_audit_callables()


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


# Stream A A5 (plan docs/plans/2026-05-11-002 §6.A5): fragile fixtures whose
# per-variant scores swing by more than two standard deviations across the
# archive — they single-handedly flip the lane composite. Audit data and
# rationale live alongside this constant in
# docs/plans/2026-05-11-002-A5-fragile-fixtures.md. Excluded from the lane
# composite unconditionally; their scores still appear under
# `fixtures_detail` for observability.
FRAGILE_FIXTURES: frozenset[str] = frozenset({
    # sd > 2.0 on the v006/v007/v008+ archive (≥5 observations each).
    # Most share a "min=0.00 because the variant failed to produce
    # output" pattern; oversampling won't fix that, so excluding them
    # from composite while still keeping them in the run preserves
    # diagnostic signal.
    "competitive-epic-ehr",            # sd=3.49, range 0.00–8.15, n=6
    "geo-nubank-br-conta",             # sd=3.41, range 0.00–7.45, n=11
    "geo-mayoclinic-atrial-fibrillation",  # sd=3.36, range 0.00–7.95, n=12
    "competitive-figma",               # sd=3.36, range 0.00–7.85, n=6
    "competitive-patreon",             # sd=3.04, range 0.00–7.95, n=5
    "geo-semrush-pricing",             # sd=2.75, range 0.00–7.90, n=12
    "monitoring-ramp-arc-t1",          # sd=2.47, range 1.50–8.43, n=7
})


def is_fragile_fixture(fixture_id: str) -> bool:
    """Return ``True`` if ``fixture_id`` is in the curated fragile set."""
    return fixture_id in FRAGILE_FIXTURES


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
