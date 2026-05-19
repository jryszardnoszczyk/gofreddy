"""Lifecycle-wrap integration test (smoke replacement).

The plan called for a live smoke run on each of the 5 lanes
(`autoresearch evolve --lane <name> --iterations 1 --candidates 1`) as the
merge gate. That requires backend services (LLM API, judges, archive infra)
and conflicts with the active harness on this dev machine. This test is the
contained replacement: it exercises every `LaneSpec.custom_*` dispatch point
with synthetic callables and verifies the registry-driven dispatch fires for
divergent lanes while leaving the 5 existing lanes untouched (since they all
have `custom_* = None`).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from autoresearch.lane_registry import (
    LANES,
    LaneSpec,
    default_objective_score_from_entry,
)


# Lanes that U9/U10/U10b wired with `custom_promote = brief_emitter`.
# `_wire_brief_emitting_lanes()` in autoresearch/lane_registry.py binds
# `make_brief_emitting_promote(lane_name)` after the LaneSpec is defined,
# so the `custom_promote` field is non-None at import time for these
# lanes. Tests below acknowledge the post-U9/U10/U10b invariant.
_BRIEF_EMITTING_LANES = frozenset({"geo", "monitoring", "marketing_audit"})

# Lanes that U8 + CE-review fix wired with `custom_score = format-mode
# reweighter`. _wire_storyboard_callables() in autoresearch/lane_registry.py
# now imports from v007-curated (was current_runtime — ephemeral state).
_CUSTOM_SCORE_WIRED_LANES = frozenset({"storyboard"})


@pytest.mark.parametrize("lane_name", ["core", "geo", "competitive", "monitoring", "storyboard"])
def test_existing_lane_specs_have_no_custom_callables_other_than_wired_hooks(lane_name: str):
    """The 5 pre-U13 lanes (core, geo, competitive, monitoring,
    storyboard) all have custom_mutate/custom_validate/
    custom_objective_score_from_entry = None. After U9/U10/U10b
    (1b22277): `geo` + `monitoring` carry brief-emitting custom_promote.
    After U8 (6f931d4): `storyboard` carries a format-mode reweighter
    custom_score. Non-wired lanes keep all hooks None."""
    spec = LANES[lane_name]
    assert spec.custom_mutate is None, f"{lane_name}: custom_mutate must default to None"
    assert spec.custom_validate is None, f"{lane_name}: custom_validate must default to None"
    assert spec.custom_objective_score_from_entry is None, (
        f"{lane_name}: custom_objective_score_from_entry must default to None"
    )

    if lane_name in _CUSTOM_SCORE_WIRED_LANES:
        # U8 wired storyboard's custom_score for format-mode reweighting.
        # Soft-fail keeps None when v007-curated workflow isn't importable.
        if spec.custom_score is not None:
            assert callable(spec.custom_score)
    else:
        assert spec.custom_score is None, (
            f"{lane_name}: not a custom-score lane; custom_score must be None"
        )

    if lane_name in _BRIEF_EMITTING_LANES:
        if spec.custom_promote is not None:
            assert callable(spec.custom_promote)
    else:
        assert spec.custom_promote is None, (
            f"{lane_name}: not a brief-emitting lane; custom_promote must be None"
        )


def test_marketing_audit_lane_has_partial_custom_callables_per_master_plan():
    """Marketing_audit is the first divergent lane in production. Per master
    plan §3.1 line 185-189: custom_score + custom_validate WIRED (engagement
    bonus pre-fold + manifest drift pin); custom_mutate uses default meta-agent.

    2026-05-12 update: custom_score is INTENTIONALLY left as None until L3
    implements the real geometric-mean MA-1..MA-8 scoring. The L1 stub at
    src/audit/score.py returned score=0 + never wrote lineage, causing every
    marketing_audit variant to be discarded (`not variant_in_lineage(...)`
    in evolve.py). Falling through to the default _score_variant_search
    actually runs the 4 marketing_audit fixtures defined in
    eval_suites/search-v1.json. custom_validate stays wired (passes through).

    2026-05-19 update (U10b): custom_promote is now wired with a
    brief-emitting callable per `_wire_brief_emitting_lanes` —
    marketing_audit findings get promoted to cross-lane briefs at finalize
    time (when src.briefs is importable; soft-fail otherwise).
    """
    spec = LANES["marketing_audit"]
    assert spec.custom_score is None, (
        "custom_score deliberately None until L3 lands (the L1 stub broke "
        "evolution by never writing lineage; substrate fall-through works)"
    )
    assert spec.custom_validate is not None, (
        "custom_validate must be wired (manifest drift pin)"
    )
    assert spec.custom_mutate is None, "custom_mutate uses default meta-agent in v1"
    # U10b: brief-emission chained after the prior custom_promote (which is
    # None pre-U10b, so post-U10b is just the brief emitter when src.briefs
    # is importable). Soft-fail when src.briefs isn't on path keeps it None.
    if spec.custom_promote is not None:
        assert callable(spec.custom_promote)
    assert spec.custom_objective_score_from_entry is None, (
        "custom_objective_score_from_entry uses default reader"
    )


def test_divergent_lane_can_register_and_dispatch_all_5_callables():
    """Register a fake divergent lane with all 5 callables, exercise each."""
    calls: dict[str, dict] = {}

    def fake_mutate(*args, **kwargs):
        calls["mutate"] = {"args": args, "kwargs": kwargs}
        return 0

    def fake_score(config, variant_dir, parent_id):
        calls["score"] = {"config": config, "variant_dir": variant_dir, "parent_id": parent_id}

    def fake_validate(variant_dir, parent_dir):
        calls["validate"] = {"variant_dir": variant_dir, "parent_dir": parent_dir}
        return True

    def fake_promote(archive_dir, variant_id, lane):
        calls["promote"] = {"archive_dir": archive_dir, "variant_id": variant_id, "lane": lane}
        return True

    def fake_objective(entry):
        calls["objective"] = {"entry": entry}
        return 99.0

    fake_lane = LaneSpec(
        name="fake_divergent",
        is_workflow_lane=True,
        custom_mutate=fake_mutate,
        custom_score=fake_score,
        custom_validate=fake_validate,
        custom_promote=fake_promote,
        custom_objective_score_from_entry=fake_objective,
    )
    LANES["fake_divergent"] = fake_lane
    try:
        result = default_objective_score_from_entry({"any": "shape"}, "fake_divergent")
        assert result == 99.0
        assert calls["objective"]["entry"] == {"any": "shape"}

        spec = LANES["fake_divergent"]
        assert spec.custom_mutate is not None
        meta_exit = spec.custom_mutate(
            Path("/tmp/rendered.md"),
            Path("/tmp/meta_variant"),
            None,
            log_file=Path("/tmp/meta-session.log"),
        )
        assert meta_exit == 0
        assert "mutate" in calls

        passed = spec.custom_validate(Path("/tmp/variant_dir"), Path("/tmp/parent_dir"))
        assert passed is True
        assert "validate" in calls

        spec.custom_score(None, "/tmp/variant", "v0001")
        assert "score" in calls

        promoted = spec.custom_promote("/tmp/archive", "v0042", "fake_divergent")
        assert promoted is True
        assert "promote" in calls
    finally:
        del LANES["fake_divergent"]


def test_divergent_lane_with_partial_callables_falls_through_to_defaults():
    """Lane with custom_score but no custom_objective_score still gets default
    objective dispatch."""

    def custom_score(*_, **__):
        return None

    fake = LaneSpec(
        name="partial_lane",
        is_workflow_lane=True,
        custom_score=custom_score,
    )
    LANES["partial_lane"] = fake
    try:
        entry = {"search_metrics": {"domains": {"partial_lane": {"score": 0.42}}}}
        result = default_objective_score_from_entry(entry, "partial_lane")
        assert result == 0.42
    finally:
        del LANES["partial_lane"]


def test_existing_lane_objective_score_unchanged_by_refactor():
    """Existing lanes still produce the same objective_score they did pre-refactor."""
    core_entry = {"search_metrics": {"composite": 0.71}}
    assert default_objective_score_from_entry(core_entry, "core") == 0.71
    geo_entry = {"search_metrics": {"domains": {"geo": {"score": 0.55}}}}
    assert default_objective_score_from_entry(geo_entry, "geo") == 0.55


def test_derived_constants_agree_with_registry():
    """Every derived re-export in lane_registry agrees with the underlying LaneSpec data."""
    from autoresearch.lane_registry import (
        DELIVERABLES,
        DOMAIN_FILENAMES,
        STRUCTURAL_DOC_FACTS,
        STRUCTURAL_GATE_FUNCTIONS,
        WORKFLOW_PREFIXES,
        _DOMAIN_CRITERIA,
        _INTERMEDIATE_ARTIFACTS,
    )

    for name, spec in LANES.items():
        if spec.deliverables:
            assert DELIVERABLES[name] == spec.deliverables
        if spec.intermediate_artifacts:
            assert _INTERMEDIATE_ARTIFACTS[name] == spec.intermediate_artifacts
        if spec.session_md_filename:
            assert DOMAIN_FILENAMES[name] == spec.session_md_filename
        if spec.structural_doc_facts:
            assert STRUCTURAL_DOC_FACTS[name] == list(spec.structural_doc_facts)
        if spec.structural_gate_functions:
            assert STRUCTURAL_GATE_FUNCTIONS[name] == spec.structural_gate_functions
        if spec.is_workflow_lane:
            assert WORKFLOW_PREFIXES[name] == spec.path_prefixes
        if spec.rubric_ids:
            assert _DOMAIN_CRITERIA[name] == list(spec.rubric_ids)
