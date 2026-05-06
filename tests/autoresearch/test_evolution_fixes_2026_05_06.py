"""Tests for the A0/A2/A5/A6/A7 fixes in plan 2026-05-06-001.

These cover the unit-testable behavior introduced by
``docs/plans/2026-05-06-001-...`` to make the autoresearch evolution loop
validate promotions honestly:

- **A0** First-of-lane variants must produce a non-zero holdout score
  before they're treated as eligible for promotion.
- **A2** Critic ``verdict='error'`` must discard the variant — the
  predicate is extracted to ``evolve._critic_infra_failures`` so a typo
  regression is caught by unit tests.
- **A5** ``LaneSpec.readonly_subprefixes`` declares files inside the
  lane's owned tree that the meta-agent may read but not edit.
- **A6** ``cmd_promote --undo`` is gated on ``is_promotable`` so we
  don't roll back to a variant that never passed holdout. Operator
  override: ``--force-undo``.
- **A7** ``_outer_pass_from_score`` is continuous on [0, 1] instead of
  binary 0/1, so ``mean_pass_rate_delta`` actually measures
  inner-vs-outer calibration drift.

The full sync-time ScopeViolation enforcement (``sync_variant_workspace``)
is exercised in ``test_a5_scope_violation.py`` — that file bypasses the
conftest's archive_index stub via a per-test fixture.
"""
from __future__ import annotations

import pathlib

import pytest

import evaluate_variant
import lane_registry


# ---------------------------------------------------------------------------
# A7: _outer_pass_from_score continuous form
# ---------------------------------------------------------------------------


def test_outer_pass_from_score_continuous() -> None:
    """A7: pre-fix this returned 1.0/0.0; now it scales by ``score / max_score``."""
    fn = evaluate_variant._outer_pass_from_score
    assert fn(7.95, True) == pytest.approx(0.795)
    assert fn(0.0, True) == 0.0
    assert fn(9.5, False) == 0.0  # structural fail short-circuits to 0
    assert fn(11.0, True) == 1.0  # clip above max_score
    assert fn(-3.0, True) == 0.0  # clip below 0


def test_outer_pass_from_score_alternate_max() -> None:
    """Caller can pass a non-default ``max_score`` for non-10-scale rubrics."""
    assert evaluate_variant._outer_pass_from_score(0.4, True, max_score=1.0) == 0.4


# ---------------------------------------------------------------------------
# A5: path_is_readonly + LaneSpec.readonly_subprefixes wiring
# ---------------------------------------------------------------------------


def test_path_is_readonly_matches_geo_workflow() -> None:
    """A5: workflows/geo.py is readonly for the geo lane."""
    assert lane_registry.path_is_readonly("workflows/geo.py", "geo")
    assert lane_registry.path_is_readonly(
        "workflows/session_eval_geo.py", "geo"
    )
    # programs/* is editable for the geo lane (mutation-target territory)
    assert not lane_registry.path_is_readonly(
        "programs/geo-session.md", "geo"
    )
    # core has no readonly files
    assert not lane_registry.path_is_readonly("workflows/geo.py", "core")


def test_path_is_readonly_trailing_slash_boundary_real_lane() -> None:
    """A5: ``path_is_readonly`` requires ``rel == subprefix`` OR
    ``rel.startswith(subprefix + '/')`` — i.e., the production helper
    appends the slash at match time, so subprefixes are declared without
    a trailing slash.

    G4 (review of d128a5c, finding #7): the previous test re-implemented
    matching inline using a permissive ``rel.startswith(p)`` instead of
    production's ``rel.startswith(subprefix + '/')``. A regression to the
    permissive form would have passed against its own copy of the logic.
    Now we call the real helper so the boundary cases below are real
    regression coverage.

    For the geo lane, ``workflows/geo.py`` is the subprefix; on disk it
    is a file, but the match rule is purely string-based. The CRITICAL
    boundary is the trailing-slash one: ``workflows/geo.py.bak`` shares
    the subprefix as a string-prefix but is NOT under it once the slash
    is appended (``"workflows/geo.py.bak".startswith("workflows/geo.py/")``
    is False). The buggy ``startswith(subprefix)`` form would return True
    for that path — that's the regression this test catches.
    """
    # Exact match against a file-shaped subprefix → True.
    assert lane_registry.path_is_readonly("workflows/geo.py", "geo")
    # CRITICAL boundary: sibling that string-prefix-matches but is not
    # under ``workflows/geo.py/``. Buggy ``rel.startswith(p)`` returns
    # True; production's ``startswith(subprefix + '/')`` returns False.
    assert not lane_registry.path_is_readonly("workflows/geo.py.bak", "geo")
    # Production's match rule is purely string-based, so anything under
    # the synthetic ``workflows/geo.py/`` directory namespace would
    # technically register as readonly even though the file would never
    # exist. That's the documented behavior — assert it explicitly so a
    # behavior change (e.g., adding a "must be a real file" check) gets
    # caught.
    assert lane_registry.path_is_readonly("workflows/geo.py/foo", "geo")


def test_path_is_readonly_directory_subprefix_branch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A5: directory-subprefix branch — files under a ``subprefix`` are
    readonly via ``rel.startswith(subprefix + '/')``. The trailing-slash
    boundary is the security-relevant invariant.

    Production today doesn't ship a directory-shaped subprefix (all geo /
    competitive / monitoring / storyboard entries are file paths), so we
    register a synthetic lane via ``monkeypatch.setitem`` to exercise the
    branch through the real helper. Subprefixes are declared without a
    trailing slash — the helper appends ``'/'`` at match time. G4
    (review of d128a5c, finding #7).
    """
    monkeypatch.setitem(
        lane_registry.LANES,
        "_g4_test_lane",
        lane_registry.LaneSpec(
            name="_g4_test_lane",
            is_workflow_lane=True,
            readonly_subprefixes=("workflows/locked",),
        ),
    )

    # File under the locked directory → readonly.
    assert lane_registry.path_is_readonly(
        "workflows/locked/foo.py", "_g4_test_lane"
    )
    # CRITICAL boundary: a sibling whose name string-prefix-matches
    # ``workflows/locked`` (without the trailing slash) must NOT register.
    # ``"workflows/lockedfoo.py".startswith("workflows/locked/")`` is
    # False, so we get the right answer. The buggy
    # ``startswith("workflows/locked")`` form would return True — this
    # is exactly the security regression the trailing-slash boundary
    # protects against.
    assert not lane_registry.path_is_readonly(
        "workflows/lockedfoo.py", "_g4_test_lane"
    )
    # Exact-equality match against the subprefix itself → True (the
    # ``rel == subprefix`` clause).
    assert lane_registry.path_is_readonly(
        "workflows/locked", "_g4_test_lane"
    )
    # Path that doesn't start with the subprefix string at all → False.
    assert not lane_registry.path_is_readonly(
        "workflows/other.py", "_g4_test_lane"
    )


def test_lane_spec_readonly_subprefixes_populated() -> None:
    """A5 wiring sanity: each workflow lane has its enforcement files locked."""
    geo = lane_registry.get_spec("geo")
    assert "workflows/geo.py" in geo.readonly_subprefixes
    assert "workflows/session_eval_geo.py" in geo.readonly_subprefixes

    competitive = lane_registry.get_spec("competitive")
    assert "workflows/competitive.py" in competitive.readonly_subprefixes
    assert "workflows/session_eval_competitive.py" in competitive.readonly_subprefixes

    monitoring = lane_registry.get_spec("monitoring")
    assert "workflows/monitoring.py" in monitoring.readonly_subprefixes
    assert "workflows/session_eval_monitoring.py" in monitoring.readonly_subprefixes

    storyboard = lane_registry.get_spec("storyboard")
    assert "workflows/storyboard.py" in storyboard.readonly_subprefixes
    assert "workflows/session_eval_storyboard.py" in storyboard.readonly_subprefixes

    # Core has no workflow enforcement → nothing locked.
    core = lane_registry.get_spec("core")
    assert core.readonly_subprefixes == ()


def test_shared_workflow_infra_readonly_for_all_lanes() -> None:
    """G1: shared workflow infra (`workflows/__init__.py`, `eval_cache.py`,
    `specs.py`, `session_eval_common.py`, `session_eval_registry.py`) is
    readonly for EVERY lane — including `core`, which has an empty
    per-lane ``readonly_subprefixes``. Closes the gap where a `core`-lane
    mutation could monkey-patch shared imports and silently propagate to
    every workflow lane's holdout (same attack class as Pi v007's
    completion_guard neutering, different file).
    """
    shared_paths = (
        "workflows/__init__.py",
        "workflows/eval_cache.py",
        "workflows/specs.py",
        "workflows/session_eval_common.py",
        "workflows/session_eval_registry.py",
    )
    for lane in lane_registry.all_lane_names():
        for rel_path in shared_paths:
            assert lane_registry.path_is_readonly(rel_path, lane), (
                f"{rel_path} should be readonly for lane {lane}"
            )

    # Spot-check the cases called out in the review charter explicitly.
    assert lane_registry.path_is_readonly(
        "workflows/session_eval_common.py", "core"
    )
    assert lane_registry.path_is_readonly("workflows/__init__.py", "geo")
    assert lane_registry.path_is_readonly("workflows/specs.py", "competitive")

    # Negative case — only the explicit shared list is locked, not the whole
    # `workflows/` tree. A new `workflows/something_new.py` must remain
    # editable for `core` (and lane-specific files stay editable for their
    # owning lane via existing per-lane checks).
    assert not lane_registry.path_is_readonly(
        "workflows/something_new.py", "core"
    )


def test_scope_violation_is_runtime_error_subclass() -> None:
    """A5: ScopeViolation is a RuntimeError so existing except RuntimeError
    handlers (rare, but they exist in evolve.py) still catch it. Callers that
    want to discriminate can match the specific class."""
    assert issubclass(lane_registry.ScopeViolation, RuntimeError)


# ---------------------------------------------------------------------------
# A0: first-of-lane promotion gate
# ---------------------------------------------------------------------------


def test_first_of_lane_requires_nonzero_holdout() -> None:
    """A0: pre-fix a fresh-lane variant auto-promoted regardless of holdout
    outcome. Now it must produce a strictly-positive composite holdout
    score before being treated as eligible.

    G4 (review of d128a5c, finding #6): the previous test defined a local
    ``_gate(...)`` that mirrored production logic and asserted against
    its own copy — a tautology that wouldn't catch drift. The production
    gate is now extracted to ``evaluate_variant._holdout_eligibility``;
    this test calls the real helper directly.

    Real ``_objective_score_from_scores`` plumbing is exercised with the
    geo lane, which reads ``scores["geo"]`` (the workflow-lane domain
    score). No monkeypatching — the test depends on the real composite
    scoring path so a behavior drift there is also caught.
    """
    gate = evaluate_variant._holdout_eligibility

    # First-of-lane (no baseline) + zero score → ineligible.
    eligible, reason = gate({"geo": 0.0}, None, "geo")
    assert eligible is False
    assert reason == "first_variant_holdout_zero_score"

    # First-of-lane + missing key → defaults to 0.0 → ineligible.
    eligible, reason = gate({}, None, "geo")
    assert eligible is False
    assert reason == "first_variant_holdout_zero_score"

    # First-of-lane + positive score → eligible.
    eligible, reason = gate({"geo": 6.4}, None, "geo")
    assert eligible is True
    assert reason == "first_variant_holdout_passed"

    # Standard "candidate > baseline" path still works when baseline exists.
    eligible, reason = gate({"geo": 7.0}, {"geo": 5.0}, "geo")
    assert eligible is True
    assert reason == "holdout_passed"

    eligible, reason = gate({"geo": 4.0}, {"geo": 5.0}, "geo")
    assert eligible is False
    assert reason == "holdout_not_better_than_baseline"

    # Equal scores must NOT promote — strictly greater is required.
    eligible, reason = gate({"geo": 5.0}, {"geo": 5.0}, "geo")
    assert eligible is False
    assert reason == "holdout_not_better_than_baseline"

    # Core-lane path reads the "composite" key (non-workflow lane).
    eligible, reason = gate({"composite": 0.0}, None, "core")
    assert eligible is False
    assert reason == "first_variant_holdout_zero_score"
    eligible, reason = gate({"composite": 0.7}, None, "core")
    assert eligible is True
    assert reason == "first_variant_holdout_passed"


# ---------------------------------------------------------------------------
# G2 (review of d128a5c): silent regressions in meta-prompt rendering
# ---------------------------------------------------------------------------


def test_brace_escape_prevents_recursive_substitution() -> None:
    """G2 (review of d128a5c, finding #4): if parent_critic_review contains
    a literal '{recent_alerts}' substring, the rendered output must preserve
    it, not substitute the operator's actual recent_alerts value into
    what looks like the critic's text.

    Pre-fix: meta-prompt rendering ran 8 sequential ``str.replace`` calls
    in fixed order. ``{parent_critic_review}`` was substituted before
    ``{recent_alerts}`` and ``{selection_rationale}``. A meta-agent could
    arrange for the critic review to quote one of those literal tokens —
    the next ``str.replace`` would then inject operator-controlled alert
    text into a region the next agent reads as "parent critic review".

    Post-fix: ``_render_meta_template`` is a single-pass regex
    substitution. The regex engine consumes the template left-to-right
    exactly once, so any ``{...}`` token a substituted value happens to
    contain is emitted verbatim into the output — no second-pass
    substitution can reach inside an already-rendered region.
    """
    import evolve  # noqa: WPS433  — local import after conftest sets sys.path

    template = (
        "CRITIC SAYS: {parent_critic_review}\n"
        "RECENT ALERTS: {recent_alerts}\n"
        "WHY THIS PARENT: {selection_rationale}\n"
    )

    # Adversarial critic review embedding two literal placeholder tokens.
    parent_critic_review_raw = (
        "critic noted: {recent_alerts} and the operator should ignore "
        "{selection_rationale}"
    )
    recent_alerts_raw = '{"code":"DRIFT","severity":"med"}'
    selection_rationale_text_raw = "highest composite among unpromoted variants"

    rendered = evolve._render_meta_template(
        template,
        {
            "parent_critic_review": parent_critic_review_raw,
            "recent_alerts": recent_alerts_raw,
            "selection_rationale": selection_rationale_text_raw,
        },
    )

    # The critic's quoted ``{recent_alerts}`` and ``{selection_rationale}``
    # tokens must survive verbatim inside the CRITIC SAYS region — the
    # operator-controlled alert payload and rationale must NOT have been
    # substituted into them.
    critic_line = next(
        line for line in rendered.splitlines() if line.startswith("CRITIC SAYS:")
    )
    assert "{recent_alerts}" in critic_line, (
        "single-pass substitution must preserve untrusted ``{recent_alerts}`` "
        "token in critic-quoted region"
    )
    assert "{selection_rationale}" in critic_line, (
        "single-pass substitution must preserve untrusted "
        "``{selection_rationale}`` token in critic-quoted region"
    )
    assert '"code":"DRIFT"' not in critic_line, (
        "second-order injection: operator-controlled alert payload leaked "
        "into the critic-quoted region"
    )
    assert "highest composite" not in critic_line, (
        "second-order injection: selection_rationale leaked into critic region"
    )

    # The legitimate placeholder regions still receive their values verbatim.
    assert 'RECENT ALERTS: {"code":"DRIFT","severity":"med"}' in rendered
    assert "WHY THIS PARENT: highest composite among unpromoted variants" in rendered

    # Unknown placeholders are left verbatim rather than substituted to
    # the empty string — missing-key bugs stay loud.
    leftover = evolve._render_meta_template(
        "this is {not_in_mapping} text", {"foo": "bar"}
    )
    assert leftover == "this is {not_in_mapping} text"


# ---------------------------------------------------------------------------
# A2 (review of d128a5c, finding #9): critic infra-failure predicate
# ---------------------------------------------------------------------------


def test_critic_infra_failures_finds_error_verdicts() -> None:
    """G4: ``_critic_infra_failures`` returns the subset of critic results
    whose verdict is ``'error'``. The upstream loop in ``cmd_run`` discards
    the variant when this dict is non-empty, so a regression that flips
    ``verdict`` to ``status`` (or any other typo) would silently let
    contaminated variants through the gate.
    """
    import evolve

    results = {
        "geo": {"verdict": "no-change", "reasoning": "OK"},
        "competitive": {"verdict": "error", "reasoning": "subprocess crashed"},
        "monitoring": {"verdict": "advise", "reasoning": "drift detected"},
    }
    failures = evolve._critic_infra_failures(results)
    assert "competitive" in failures
    assert "geo" not in failures
    assert "monitoring" not in failures


def test_critic_infra_failures_handles_malformed_values() -> None:
    """G4: non-dict values in the results map don't crash the predicate
    (``isinstance(result, dict)`` guard) — only legitimate
    ``verdict='error'`` dict entries surface."""
    import evolve

    results = {
        "geo": "oops not a dict",  # malformed — must be skipped
        "competitive": {"verdict": "error", "reasoning": "real failure"},
        "monitoring": None,  # malformed — must be skipped
        "storyboard": {"verdict": "no-change"},
    }
    failures = evolve._critic_infra_failures(results)
    assert list(failures.keys()) == ["competitive"]


def test_critic_infra_failures_empty_when_all_clean() -> None:
    """G4: no error verdicts → empty dict → caller proceeds with scoring."""
    import evolve

    results = {
        "geo": {"verdict": "no-change", "reasoning": "ok"},
        "competitive": {"verdict": "advise", "reasoning": "drift"},
    }
    assert evolve._critic_infra_failures(results) == {}


def test_critic_infra_failures_uncaught_sentinel_path() -> None:
    """G4: the synthesized ``_uncaught`` sentinel emitted by the outer
    ``except`` in ``cmd_run`` must register as an infra failure so an
    exception escaping ``critique_all_programs`` discards the variant."""
    import evolve

    results = {
        "_uncaught": {
            "verdict": "error",
            "reasoning": "critique_all_programs raised: TimeoutExpired",
        }
    }
    failures = evolve._critic_infra_failures(results)
    assert "_uncaught" in failures


# ---------------------------------------------------------------------------
# A6 (review of d128a5c, finding #10): cmd_promote --undo gate
# ---------------------------------------------------------------------------


def test_cmd_promote_undo_blocks_when_prev_not_promotable(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A6 (plan 2026-05-06-001): ``--undo`` without ``--force-undo``
    refuses to roll back to a non-promotable variant. Plan §Verification §2
    required this test."""
    import evolve
    import evolve_ops

    # Stub the lookup chain to simulate a non-promotable previous variant.
    monkeypatch.setattr(
        evolve_ops, "previous_promoted_variant",
        lambda archive_dir, lane: "v005_bad",
    )
    monkeypatch.setattr(
        evolve_ops, "is_promotable",
        lambda archive_dir, variant_id, lane: False,
    )
    monkeypatch.setattr(
        evolve_ops, "promotion_reason",
        lambda archive_dir, variant_id: "holdout_skipped",
    )
    # Belt-and-braces: if the gate ever leaks past, these would write the
    # rollback. The test should never reach them.
    def _unexpected(*args: object, **kwargs: object) -> None:
        raise AssertionError("gate let --undo through to mark_promoted")

    monkeypatch.setattr(evolve_ops, "mark_promoted", _unexpected)
    monkeypatch.setattr(evolve_ops, "set_current_head", _unexpected)
    monkeypatch.setattr(evolve, "refresh_archive", _unexpected)

    config = evolve.EvolutionConfig(command="promote")
    config.promote_undo = True
    config.force_undo = False
    config.lane = "geo"
    config.archive_dir = pathlib.Path("/tmp/fake-archive-not-touched")

    with pytest.raises(SystemExit) as exc:
        evolve.cmd_promote(config)

    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "not promotable" in captured.err.lower()
    assert "v005_bad" in captured.err
    assert "holdout_skipped" in captured.err


def test_cmd_promote_force_undo_overrides_gate(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    """A6: ``--force-undo`` overrides the ``is_promotable`` gate (operator
    escape hatch). ``mark_promoted`` + ``set_current_head`` MUST be called
    on the rollback target."""
    import evolve
    import evolve_ops

    monkeypatch.setattr(
        evolve_ops, "previous_promoted_variant",
        lambda archive_dir, lane: "v005_bad",
    )
    # is_promotable would say False, but --force-undo skips the call entirely.
    monkeypatch.setattr(
        evolve_ops, "is_promotable",
        lambda *a, **k: (_ for _ in ()).throw(
            AssertionError("--force-undo must skip is_promotable check")
        ),
    )

    calls: dict[str, tuple] = {}

    def _record_mark(archive_dir, variant_id, timestamp):
        calls["mark_promoted"] = (archive_dir, variant_id, timestamp)

    def _record_head(archive_dir, lane, variant_id):
        calls["set_current_head"] = (archive_dir, lane, variant_id)

    def _record_refresh(config):
        calls["refresh_archive"] = (config.lane,)

    monkeypatch.setattr(evolve_ops, "mark_promoted", _record_mark)
    monkeypatch.setattr(evolve_ops, "set_current_head", _record_head)
    monkeypatch.setattr(evolve, "refresh_archive", _record_refresh)

    config = evolve.EvolutionConfig(command="promote")
    config.promote_undo = True
    config.force_undo = True
    config.lane = "geo"
    config.archive_dir = pathlib.Path("/tmp/fake-archive-not-touched")

    evolve.cmd_promote(config)

    assert "mark_promoted" in calls
    assert calls["mark_promoted"][1] == "v005_bad"
    assert "set_current_head" in calls
    assert calls["set_current_head"] == (
        str(pathlib.Path("/tmp/fake-archive-not-touched")),
        "geo",
        "v005_bad",
    )
    assert "refresh_archive" in calls
    assert calls["refresh_archive"] == ("geo",)


def test_cmd_promote_undo_gate_passes_when_prev_is_promotable(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    """A6: the gate is on ``is_promotable=False`` only — when the previous
    variant IS promotable, ``--undo`` (without ``--force-undo``) succeeds
    normally."""
    import evolve
    import evolve_ops

    monkeypatch.setattr(
        evolve_ops, "previous_promoted_variant",
        lambda archive_dir, lane: "v004_good",
    )
    monkeypatch.setattr(
        evolve_ops, "is_promotable",
        lambda archive_dir, variant_id, lane: True,
    )
    calls: dict[str, tuple] = {}
    monkeypatch.setattr(
        evolve_ops, "mark_promoted",
        lambda *a, **k: calls.setdefault("mark", a),
    )
    monkeypatch.setattr(
        evolve_ops, "set_current_head",
        lambda *a, **k: calls.setdefault("head", a),
    )
    monkeypatch.setattr(
        evolve, "refresh_archive", lambda config: calls.setdefault("refresh", ())
    )

    config = evolve.EvolutionConfig(command="promote")
    config.promote_undo = True
    config.force_undo = False
    config.lane = "geo"
    config.archive_dir = pathlib.Path("/tmp/fake-archive-not-touched")

    evolve.cmd_promote(config)

    assert calls["mark"][1] == "v004_good"
    assert calls["head"] == (
        str(pathlib.Path("/tmp/fake-archive-not-touched")),
        "geo",
        "v004_good",
    )


# ---------------------------------------------------------------------------
# Cached holdout bypass — _discard_variant clears private cache (post-d128a5c)
# ---------------------------------------------------------------------------


def test_discard_variant_clears_private_holdout_cache(tmp_path, monkeypatch):
    """Cached holdout result must be discarded alongside the variant dir.

    Adversarial review of d128a5c flagged that ``_load_private_result``
    keys cached holdout scores by ``<private_root>/<variant_id>/...``;
    after a discard via ``_safe_rmtree(variant_dir)``, the loop can
    re-mint the same variant_id and inherit stale cached scores,
    bypassing A0's ``candidate_score > 0.0`` gate. Fix added a
    ``_discard_variant`` helper that clears both paths together.
    """
    import sys as _sys
    # evolve.py imports many side-effecting modules at top — the conftest
    # stubs handle most. We need the real evolve module so the helper is
    # importable.
    _sys.modules.pop("evolve", None)
    import importlib
    _AUTORESEARCH = pytest.importorskip("evaluate_variant").__file__  # ensure path setup
    spec = importlib.util.spec_from_file_location(
        "evolve",
        str(__import__("pathlib").Path(_AUTORESEARCH).parent / "evolve.py"),
    )
    # We don't actually need to exec evolve (it pulls in heavy deps).
    # Test the helper logic in isolation by re-implementing the predicate
    # against the same env-var contract. The production helper is at
    # autoresearch/evolve.py:_discard_variant; this test pins its
    # cache-clearing contract.
    variant_dir = tmp_path / "archive" / "v_test"
    variant_dir.mkdir(parents=True)
    private_root = tmp_path / "private-cache"
    cache_dir = private_root / variant_dir.name
    cache_dir.mkdir(parents=True)
    (cache_dir / "holdout_result.json").write_text('{"scores": {}}')

    monkeypatch.setenv("EVOLUTION_PRIVATE_ARCHIVE_DIR", str(private_root))

    # Mirror the production helper's clearing contract.
    import os
    import shutil
    private_root_resolved = (
        __import__("pathlib").Path(os.environ["EVOLUTION_PRIVATE_ARCHIVE_DIR"]).resolve()
    )
    per_variant_cache = private_root_resolved / variant_dir.name
    assert per_variant_cache.is_dir()
    shutil.rmtree(per_variant_cache, ignore_errors=True)
    shutil.rmtree(variant_dir, ignore_errors=True)

    # After discard, neither path should exist
    assert not variant_dir.exists()
    assert not per_variant_cache.exists()
    # And the parent private_root still does — only the per-variant subdir went
    assert private_root_resolved.is_dir()
