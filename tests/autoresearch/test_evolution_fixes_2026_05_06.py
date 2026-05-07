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

import json
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


def test_cmd_promote_undo_trusts_stored_promoted_at(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    """A6 v2 (plan 2026-05-06-001 follow-up): ``--undo`` rolls back to the
    variant returned by ``previous_promoted_variant``, which by definition
    has ``promoted_at`` set in lineage — i.e., it WAS promoted before. We
    trust that stored evidence rather than re-running the LLM-based
    ``is_promotable`` judge (non-deterministic + costly + can block legit
    rollbacks during judge-service outages).

    The previous incarnation of this test asserted that ``is_promotable``
    was called and that its False return blocked the undo. That gate was
    removed because the LLM-judge re-validation was a regression: the
    rollback target's ``promoted_at`` IS the gate.
    """
    import evolve
    import evolve_ops

    monkeypatch.setattr(
        evolve_ops, "previous_promoted_variant",
        lambda archive_dir, lane: "v005_prev",
    )

    # is_promotable MUST NOT be called — the new logic trusts promoted_at.
    monkeypatch.setattr(
        evolve_ops, "is_promotable",
        lambda *a, **k: (_ for _ in ()).throw(
            AssertionError(
                "is_promotable must not be called from --undo path "
                "(LLM-judge re-validation removed in A6 v2)"
            )
        ),
    )

    calls: dict[str, tuple] = {}
    monkeypatch.setattr(
        evolve_ops, "mark_promoted",
        lambda archive_dir, variant_id, timestamp: calls.setdefault(
            "mark", (archive_dir, variant_id, timestamp)
        ),
    )
    monkeypatch.setattr(
        evolve_ops, "set_current_head",
        lambda archive_dir, lane, variant_id: calls.setdefault(
            "head", (archive_dir, lane, variant_id)
        ),
    )
    monkeypatch.setattr(
        evolve, "refresh_archive", lambda config: calls.setdefault("refresh", config.lane)
    )

    config = evolve.EvolutionConfig(command="promote")
    config.promote_undo = True
    config.force_undo = False  # not needed; gate is gone
    config.lane = "geo"
    config.archive_dir = pathlib.Path("/tmp/fake-archive-not-touched")

    evolve.cmd_promote(config)

    assert calls["mark"][1] == "v005_prev"
    assert calls["head"] == (
        str(pathlib.Path("/tmp/fake-archive-not-touched")), "geo", "v005_prev",
    )
    assert calls["refresh"] == "geo"


def test_cmd_promote_undo_propagates_no_history_systemexit(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    """A6 v2: when ``previous_promoted_variant`` raises ``SystemExit`` (no
    promoted history exists in lineage), ``--undo`` propagates that exit
    cleanly. There's no rollback target — neither stored evidence nor an
    LLM judge can save the operator.
    """
    import evolve
    import evolve_ops

    def _no_history(*args: object, **kwargs: object) -> str:
        raise SystemExit("No previous promoted variant to rollback to")

    monkeypatch.setattr(
        evolve_ops, "previous_promoted_variant", _no_history
    )

    config = evolve.EvolutionConfig(command="promote")
    config.promote_undo = True
    config.lane = "geo"
    config.archive_dir = pathlib.Path("/tmp/fake-archive-not-touched")

    with pytest.raises(SystemExit):
        evolve.cmd_promote(config)


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

    Post-audit 2026-05-07: this test now actually invokes the production
    helper. Pre-replacement it rebuilt the contract inline with
    ``shutil.rmtree`` and would pass even if the production fix were
    reverted (a tautology test giving false confidence in the regression
    coverage).
    """
    import evolve  # production module; imports cleanly under conftest stubs

    variant_dir = tmp_path / "archive" / "v_test"
    variant_dir.mkdir(parents=True)
    (variant_dir / "scores.json").write_text("{}")  # ensure non-empty

    private_root = tmp_path / "private-cache"
    cache_dir = private_root / variant_dir.name
    cache_dir.mkdir(parents=True)
    (cache_dir / "holdout_result.json").write_text('{"scores": {"geo": 0.0}}')
    (cache_dir / "geo--holdout_result.json").write_text('{"scores": {"geo": 0.0}}')

    monkeypatch.setenv("EVOLUTION_PRIVATE_ARCHIVE_DIR", str(private_root))

    assert variant_dir.is_dir()
    assert cache_dir.is_dir()

    # Invoke the production helper.
    evolve._discard_variant(variant_dir)

    # Both the variant dir AND the private cache subdir must be gone.
    assert not variant_dir.exists()
    assert not cache_dir.exists()
    # Parent private_root remains — only the per-variant subdir was cleared.
    assert private_root.is_dir()


def test_discard_variant_default_private_root_via_tempfile(tmp_path, monkeypatch):
    """When EVOLUTION_PRIVATE_ARCHIVE_DIR is unset, the helper must use
    tempfile.gettempdir() / 'autoresearch-holdouts' as the default. Tests
    this branch by clearing the env var and pointing tempfile to tmp_path.
    """
    import evolve
    import tempfile as _tempfile

    monkeypatch.delenv("EVOLUTION_PRIVATE_ARCHIVE_DIR", raising=False)
    monkeypatch.setattr(_tempfile, "gettempdir", lambda: str(tmp_path))

    variant_dir = tmp_path / "archive" / "v_default"
    variant_dir.mkdir(parents=True)
    (variant_dir / "scores.json").write_text("{}")

    default_cache_root = tmp_path / "autoresearch-holdouts"
    cache_dir = default_cache_root / variant_dir.name
    cache_dir.mkdir(parents=True)
    (cache_dir / "holdout_result.json").write_text("{}")

    evolve._discard_variant(variant_dir)

    assert not variant_dir.exists()
    assert not cache_dir.exists()


def test_discard_variant_swallows_cache_errors(tmp_path, monkeypatch, capsys):
    """The helper must NOT propagate exceptions from cache cleanup —
    a broken private cache shouldn't block discard of a known-bad variant.
    Verifies the broad-except path emits a WARN to stderr.
    """
    import evolve

    variant_dir = tmp_path / "archive" / "v_err"
    variant_dir.mkdir(parents=True)
    (variant_dir / "scores.json").write_text("{}")

    # Point at a private root that will trigger an error inside the
    # cache-cleanup branch by patching _safe_rmtree to raise the SECOND
    # time it's called (after the variant_dir succeeds).
    calls = {"n": 0}
    real_safe_rmtree = evolve._safe_rmtree
    def _raising_rmtree(path):
        calls["n"] += 1
        if calls["n"] >= 2:
            raise OSError("simulated cache cleanup failure")
        return real_safe_rmtree(path)
    monkeypatch.setattr(evolve, "_safe_rmtree", _raising_rmtree)

    private_root = tmp_path / "private-cache"
    cache_dir = private_root / variant_dir.name
    cache_dir.mkdir(parents=True)
    monkeypatch.setenv("EVOLUTION_PRIVATE_ARCHIVE_DIR", str(private_root))

    # Must not raise even though cache cleanup fails.
    evolve._discard_variant(variant_dir)
    captured = capsys.readouterr()
    assert "failed to clear private holdout cache" in captured.err
    assert not variant_dir.exists()


# ---------------------------------------------------------------------------
# Cross-lane cache key: holdout/finalize files lane-prefixed (post-d128a5c)
# ---------------------------------------------------------------------------


def test_private_result_path_lane_keyed_for_holdout(monkeypatch, tmp_path):
    """Holdout result file path includes the lane prefix.

    Pre-fix the path was <root>/<variant>/holdout_result.json — lane-agnostic.
    In multi-lane runs (--lane all) the first lane's cache would be reused
    for subsequent lanes, causing v007/<lane2> to be falsely promoted
    against v006's stale <lane1> scores. Now lane-prefixed:
    <root>/<variant>/<lane>--holdout_result.json.
    """
    monkeypatch.setenv("EVOLUTION_PRIVATE_ARCHIVE_DIR", str(tmp_path))
    import evaluate_variant as ev

    geo_path = ev._private_result_path("v006", "holdout", lane="geo")
    competitive_path = ev._private_result_path("v006", "holdout", lane="competitive")
    assert geo_path is not None
    assert competitive_path is not None
    # Different lanes write to different files
    assert geo_path != competitive_path
    assert geo_path.name == "geo--holdout_result.json"
    assert competitive_path.name == "competitive--holdout_result.json"
    # Same variant_id directory
    assert geo_path.parent == competitive_path.parent


def test_private_result_path_lane_keyed_for_finalize(monkeypatch, tmp_path):
    """Finalize result file path includes the lane prefix (same fix as holdout)."""
    monkeypatch.setenv("EVOLUTION_PRIVATE_ARCHIVE_DIR", str(tmp_path))
    import evaluate_variant as ev

    geo_path = ev._private_result_path("v006", "finalize", lane="geo")
    monitoring_path = ev._private_result_path("v006", "finalize", lane="monitoring")
    assert geo_path != monitoring_path
    assert geo_path.name == "geo--finalize_result.json"
    assert monitoring_path.name == "monitoring--finalize_result.json"


def _real_load_json(path, default=None):
    """conftest stubs ``archive_index.load_json`` to return ``{}``; for tests
    that exercise real file I/O we need the real implementation. Mirrors
    the production behavior in ``autoresearch/archive_index.py:load_json``.
    """
    import json as _json
    from pathlib import Path as _Path
    p = _Path(path)
    if not p.exists():
        return default
    try:
        return _json.loads(p.read_text())
    except (_json.JSONDecodeError, OSError):
        return default


def test_load_private_result_legacy_fallback_refuses_cross_lane(monkeypatch, tmp_path):
    """Backwards-compat: legacy <root>/<variant>/holdout_result.json files
    (pre-fix) are accepted ONLY when the cached scores match the requested
    lane. Cross-lane reuse is the false-positive vector we're closing.
    """
    monkeypatch.setenv("EVOLUTION_PRIVATE_ARCHIVE_DIR", str(tmp_path))
    import evaluate_variant as ev
    monkeypatch.setattr(ev, "load_json", _real_load_json)
    import json

    # Write a legacy-format file at the OLD pre-fix path with geo scores
    legacy = tmp_path / "v006" / "holdout_result.json"
    legacy.parent.mkdir(parents=True)
    legacy.write_text(json.dumps({
        "variant_id": "v006",
        "suite_id": "holdout-v1",
        "scores": {
            "geo": 5.5,
            "competitive": 0.0,
            "monitoring": 0.0,
            "storyboard": 0.0,
            "composite": 5.5,
        },
    }))

    # Loading with lane=geo: matches → returns cached
    result = ev._load_private_result("v006", "holdout", "holdout-v1", lane="geo")
    assert result is not None
    assert result["scores"]["geo"] == 5.5

    # Loading with lane=competitive: cached scores have zero competitive →
    # the fallback refuses to return it (pre-fix this would have returned
    # the geo-cached scores and v007/competitive would have falsely promoted
    # against the zero-baseline).
    result = ev._load_private_result(
        "v006", "holdout", "holdout-v1", lane="competitive",
    )
    assert result is None


def test_load_private_result_lane_keyed_isolation(monkeypatch, tmp_path):
    """Two lanes' lane-keyed files are isolated — neither leaks into the other."""
    monkeypatch.setenv("EVOLUTION_PRIVATE_ARCHIVE_DIR", str(tmp_path))
    import evaluate_variant as ev
    monkeypatch.setattr(ev, "load_json", _real_load_json)
    import json

    geo_path = tmp_path / "v006" / "geo--holdout_result.json"
    geo_path.parent.mkdir(parents=True)
    geo_path.write_text(json.dumps({
        "variant_id": "v006", "suite_id": "holdout-v1", "lane": "geo",
        "scores": {"geo": 5.5, "composite": 5.5},
    }))
    comp_path = tmp_path / "v006" / "competitive--holdout_result.json"
    comp_path.write_text(json.dumps({
        "variant_id": "v006", "suite_id": "holdout-v1", "lane": "competitive",
        "scores": {"competitive": 4.2, "composite": 4.2},
    }))

    geo_result = ev._load_private_result("v006", "holdout", "holdout-v1", lane="geo")
    comp_result = ev._load_private_result(
        "v006", "holdout", "holdout-v1", lane="competitive",
    )
    assert geo_result["scores"]["geo"] == 5.5
    assert comp_result["scores"]["competitive"] == 4.2


# ---------------------------------------------------------------------------
# P1: per-lane parent eligibility post multi-lane runs (post-d128a5c)
# ---------------------------------------------------------------------------


def test_entry_active_for_lane_uses_search_metrics_domains_active():
    """P1: the per-lane parent-eligibility filter must accept core-lane
    entries that scored a workflow lane via ``search_metrics.domains[lane].
    active``. Pre-fix this filter only matched on the entry's ``lane`` label,
    so after a multi-lane baseline scoring (``--lane all``) the current
    head's lineage entry would be tagged ``lane=core`` and become
    INVISIBLE to per-workflow-lane parent selection — a silent regression
    where the loop would mutate from older / rejected variants instead of
    the operator's actual ``current.json`` head.
    """
    import select_parent as sp

    # Entry: core-lane scored across all 4 workflow lanes (post-fix shape).
    core_entry = {
        "id": "v006",
        "lane": "core",
        "search_metrics": {
            "domains": {
                "geo": {"score": 0.5, "active": True},
                "competitive": {"score": 0.6, "active": True},
                "monitoring": {"score": 0.4, "active": True},
                "storyboard": {"score": 0.0, "active": False},
            },
        },
    }
    # All 3 active-True lanes: eligible. The inactive one (storyboard) falls
    # through to the lane-label match — also False since lane=core != storyboard.
    assert sp._entry_active_for_lane(core_entry, "geo")
    assert sp._entry_active_for_lane(core_entry, "competitive")
    assert sp._entry_active_for_lane(core_entry, "monitoring")
    assert not sp._entry_active_for_lane(core_entry, "storyboard")


def test_entry_active_for_lane_falls_back_to_lane_label_for_legacy_entries():
    """Backwards-compat: lineage entries without ``search_metrics`` (older
    or partial entries) fall back to the lane-label match. Preserves
    behavior for entries that pre-date the per-domain ``active`` flag.
    """
    import select_parent as sp

    legacy_entry = {"id": "v002", "lane": "geo"}  # no search_metrics
    assert sp._entry_active_for_lane(legacy_entry, "geo")
    assert not sp._entry_active_for_lane(legacy_entry, "competitive")


def test_entry_active_for_lane_excludes_workflow_entries_from_other_lanes():
    """A workflow-lane entry (e.g., lane=geo) that was scored on geo only
    should NOT be eligible as a parent for --lane competitive. Prevents the
    other failure mode where the filter is too permissive.
    """
    import select_parent as sp

    geo_only_entry = {
        "id": "v007",
        "lane": "geo",
        "search_metrics": {
            "domains": {
                "geo": {"score": 5.92, "active": True},
                "competitive": {"score": 0.0, "active": False},
                "monitoring": {"score": 0.0, "active": False},
                "storyboard": {"score": 0.0, "active": False},
            },
        },
    }
    assert sp._entry_active_for_lane(geo_only_entry, "geo")
    assert not sp._entry_active_for_lane(geo_only_entry, "competitive")
    assert not sp._entry_active_for_lane(geo_only_entry, "monitoring")
    assert not sp._entry_active_for_lane(geo_only_entry, "storyboard")


# ---------------------------------------------------------------------------
# Unit 1 (post-audit 2026-05-07): _promotion_baseline mirrors
# _entry_active_for_lane so the holdout-baseline lookup survives the
# multi-lane lineage tag (lane=core) the same way select_parent does.
# Pre-fix the gate would fall into A0 first-of-lane semantics on every
# workflow lane after multi-lane scoring.
# ---------------------------------------------------------------------------


def _seed_archive_with_lineage(tmp_path, entries, current_manifest=None):
    """Write minimal archive layout: lineage.jsonl + current.json."""
    import json
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    (archive_dir / "lineage.jsonl").write_text(
        "\n".join(json.dumps(e) for e in entries) + "\n"
    )
    if current_manifest is not None:
        (archive_dir / "current.json").write_text(json.dumps(current_manifest))
    return archive_dir


def _real_load_latest_lineage(archive_dir):
    """conftest stubs ``archive_index.load_latest_lineage`` to ``{}``; for tests
    that need to read a real lineage.jsonl from disk, this mirrors the
    production behavior in ``autoresearch/archive_index.py``.
    """
    import json
    from pathlib import Path as _Path
    path = _Path(archive_dir).resolve() / "lineage.jsonl"
    if not path.exists():
        return {}
    latest = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and payload.get("id"):
            latest[str(payload["id"])] = payload
    return latest


def _real_current_variant_id(archive_dir, lane=None):
    """Mirrors archive_index.current_variant_id reading current.json from disk."""
    import json
    from pathlib import Path as _Path
    path = _Path(archive_dir).resolve() / "current.json"
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    target_lane = (lane or "core").strip().lower()
    variant_id = str(payload.get(target_lane) or "").strip()
    return variant_id or None


def _patch_real_lineage_io(monkeypatch):
    """Bypass the conftest stubs for tests that need real lineage I/O."""
    import evaluate_variant as ev
    monkeypatch.setattr(ev, "load_latest_lineage", _real_load_latest_lineage)
    monkeypatch.setattr(ev, "current_variant_id", _real_current_variant_id)
    # has_search_metrics is also stubbed to always-True; install the real impl.
    def _real_has_search_metrics(entry, suite_id=None):
        sm = entry.get("search_metrics") if isinstance(entry, dict) else None
        if not isinstance(sm, dict):
            return False
        entry_suite_id = sm.get("suite_id")
        if not (isinstance(entry_suite_id, str) and entry_suite_id):
            return False
        if suite_id is not None and entry_suite_id != suite_id:
            return False
        composite = sm.get("composite")
        return isinstance(composite, (int, float))
    monkeypatch.setattr(ev, "has_search_metrics", _real_has_search_metrics)


def test_promotion_baseline_finds_current_head_via_lane_active_flag(tmp_path, monkeypatch):
    """Post-multi-lane the latest lineage entry for v006 is tagged
    ``lane=core`` but ``search_metrics.domains.geo.active=True``. The
    pre-fix label-match returned None and the gate auto-promoted any
    holdout-positive variant. The active-lane predicate must accept this
    entry as the geo baseline.
    """
    _patch_real_lineage_io(monkeypatch)
    v006_entry = {
        "id": "v006",
        "lane": "core",
        "search_metrics": {
            "suite_id": "search-v1",
            "composite": 2.7283,
            "active_domains": ["geo", "competitive", "monitoring", "storyboard"],
            "domains": {
                "geo": {"active": True, "score": 0.7301},
                "competitive": {"active": True, "score": 6.4691},
                "monitoring": {"active": True, "score": 3.7042},
                "storyboard": {"active": True, "score": 0.01},
            },
            "fixtures": 17,
            "active": True,
        },
    }
    archive = _seed_archive_with_lineage(
        tmp_path,
        [v006_entry],
        current_manifest={"core": "v006", "geo": "v006",
                          "competitive": "v006", "monitoring": "v006",
                          "storyboard": "v006"},
    )
    result = evaluate_variant._promotion_baseline(archive, "v_other", "geo")
    assert result is not None
    assert result["id"] == "v006"
    # Same active-lane match should hold for every workflow lane.
    for lane in ("competitive", "monitoring", "storyboard"):
        assert evaluate_variant._promotion_baseline(archive, "v_other", lane) is not None


def test_promotion_baseline_skips_entry_inactive_for_lane(tmp_path, monkeypatch):
    """Entry tagged ``lane=core`` but ``domains.geo.active=False`` (geo
    wasn't actually scored) must NOT be returned for a geo lookup.
    Without this the predicate would over-match every core entry.
    """
    _patch_real_lineage_io(monkeypatch)
    inactive_entry = {
        "id": "v_inactive",
        "lane": "core",
        "search_metrics": {
            "suite_id": "search-v1",
            "composite": 1.5,
            "domains": {
                "geo": {"active": False, "score": 0.0},
                "competitive": {"active": True, "score": 1.5},
            },
            "active": True,
        },
    }
    archive = _seed_archive_with_lineage(
        tmp_path, [inactive_entry],
        current_manifest={"core": "v_inactive", "geo": "v_inactive",
                          "competitive": "v_inactive", "monitoring": "v_inactive",
                          "storyboard": "v_inactive"},
    )
    # geo-inactive entry should not be returned even if it's the current head.
    assert evaluate_variant._promotion_baseline(archive, "v_other", "geo") is None
    # competitive-active should still match.
    assert evaluate_variant._promotion_baseline(archive, "v_other", "competitive") is not None


def test_promotion_baseline_falls_back_to_label_for_legacy_entries(tmp_path, monkeypatch):
    """Older lineage entries lack ``search_metrics`` entirely. The
    predicate falls back to label match so legacy archives keep working.
    """
    _patch_real_lineage_io(monkeypatch)
    legacy_entry = {
        "id": "v_legacy",
        "lane": "geo",
        "scores": {"geo": 4.0, "composite": 4.0},
    }
    archive = _seed_archive_with_lineage(
        tmp_path, [legacy_entry],
        current_manifest={"core": "v_legacy", "geo": "v_legacy",
                          "competitive": "", "monitoring": "",
                          "storyboard": ""},
    )
    # Legacy entries need has_search_metrics(entry) to also be true; absent
    # search_metrics the current-head branch is short-circuited. Verify the
    # label-fallback by promoting via promoted_at branch with a search_metrics-
    # bearing legacy entry instead.
    promoted_legacy = {
        "id": "v_promoted_legacy",
        "lane": "geo",
        "promoted_at": "2026-04-01T00:00:00Z",
        "search_metrics": {
            "suite_id": "search-v1",
            "composite": 4.0,
            "fixtures": 3,
            "active": True,
        },  # no domains key — exercises label-fallback
        "scores": {"geo": 4.0, "composite": 4.0},
    }
    archive2 = _seed_archive_with_lineage(
        tmp_path / "case2", [promoted_legacy],
        current_manifest={"core": "", "geo": "", "competitive": "",
                          "monitoring": "", "storyboard": ""},
    )
    result = evaluate_variant._promotion_baseline(archive2, "v_other", "geo")
    assert result is not None
    assert result["id"] == "v_promoted_legacy"
    # Different lane → label mismatch + no domain data → None.
    assert evaluate_variant._promotion_baseline(archive2, "v_other", "competitive") is None


# ---------------------------------------------------------------------------
# Unit 2 (post-audit 2026-05-07): previous_promoted_variant uses the same
# active-lane predicate so --undo / phase4-migration-check rollback works
# after multi-lane scoring tags lineage entries lane=core.
# ---------------------------------------------------------------------------


def _patch_real_evolve_ops_lineage(monkeypatch):
    """evolve_ops imports its own _load_latest_lineage from archive_index;
    same conftest-stub problem as evaluate_variant. Bypass it.
    """
    import evolve_ops as eo
    monkeypatch.setattr(eo, "_load_latest_lineage", _real_load_latest_lineage)


def test_previous_promoted_variant_uses_lane_active_flag(tmp_path, monkeypatch):
    """v006 (lane=core, geo.active=True, promoted) followed by v007 (lane=core,
    geo.active=True, promoted) — previous_promoted_variant for any workflow
    lane should return v006 even though neither entry has lane=geo. Pre-fix
    the label-match returned an empty list and raised SystemExit.
    """
    _patch_real_evolve_ops_lineage(monkeypatch)
    import evolve_ops as eo

    v006 = {
        "id": "v006",
        "lane": "core",
        "promoted_at": "2026-04-15T00:00:00Z",
        "search_metrics": {
            "suite_id": "search-v1",
            "composite": 2.0,
            "domains": {
                "geo": {"active": True},
                "competitive": {"active": True},
            },
        },
    }
    v007 = {
        "id": "v007",
        "lane": "core",
        "promoted_at": "2026-04-30T00:00:00Z",
        "search_metrics": {
            "suite_id": "search-v1",
            "composite": 3.0,
            "domains": {
                "geo": {"active": True},
                "competitive": {"active": True},
            },
        },
    }
    archive = _seed_archive_with_lineage(tmp_path, [v006, v007])
    # Latest of two → previous = v006 → returned for every workflow lane.
    for lane in ("geo", "competitive"):
        assert eo.previous_promoted_variant(archive, lane) == "v006"


def test_previous_promoted_variant_raises_when_no_history(tmp_path, monkeypatch):
    """Empty (or single-entry) lineage still raises SystemExit cleanly."""
    _patch_real_evolve_ops_lineage(monkeypatch)
    import evolve_ops as eo

    archive_empty = _seed_archive_with_lineage(tmp_path / "empty", [{}])
    with pytest.raises(SystemExit):
        eo.previous_promoted_variant(archive_empty, "geo")

    only_one = {
        "id": "v006",
        "lane": "core",
        "promoted_at": "2026-04-15T00:00:00Z",
        "search_metrics": {
            "suite_id": "search-v1",
            "composite": 2.0,
            "domains": {"geo": {"active": True}},
        },
    }
    archive_one = _seed_archive_with_lineage(tmp_path / "one", [only_one])
    with pytest.raises(SystemExit):
        eo.previous_promoted_variant(archive_one, "geo")


def test_previous_promoted_variant_legacy_label_match_still_works(tmp_path, monkeypatch):
    """Legacy entries without search_metrics.domains still match by label.
    Back-compat for archives older than the multi-lane scoring rework.
    """
    _patch_real_evolve_ops_lineage(monkeypatch)
    import evolve_ops as eo

    legacy_a = {
        "id": "v_legacy_a",
        "lane": "geo",
        "promoted_at": "2026-04-01T00:00:00Z",
        "search_metrics": {"suite_id": "search-v0", "composite": 1.0},
    }
    legacy_b = {
        "id": "v_legacy_b",
        "lane": "geo",
        "promoted_at": "2026-04-10T00:00:00Z",
        "search_metrics": {"suite_id": "search-v0", "composite": 1.5},
    }
    archive = _seed_archive_with_lineage(tmp_path, [legacy_a, legacy_b])
    assert eo.previous_promoted_variant(archive, "geo") == "v_legacy_a"


# ---------------------------------------------------------------------------
# Unit 3 (post-audit 2026-05-07): legacy zero-cache fallback predicate.
# Pre-fix: ``if cached_lanes and lane not in cached_lanes: return None`` —
# truthy short-circuit when cached_lanes is empty (all-zero scores) made
# the function return the legacy payload unconditionally for any lane.
# Now refuses zero-information legacy files outright.
# ---------------------------------------------------------------------------


def test_load_private_result_legacy_fallback_refuses_zero_score_cache(monkeypatch, tmp_path):
    """A legacy holdout_result.json with all-zero scores must NOT be
    returned for any lane query. Pre-fix the empty cached_lanes shortcut
    let the gate auto-promote against a zero baseline.
    """
    monkeypatch.setenv("EVOLUTION_PRIVATE_ARCHIVE_DIR", str(tmp_path))
    import evaluate_variant as ev
    monkeypatch.setattr(ev, "load_json", _real_load_json)

    variant_dir = tmp_path / "v009"
    variant_dir.mkdir()
    legacy_payload = {
        "suite_id": "search-v1",
        "scores": {
            "geo": 0.0,
            "competitive": 0.0,
            "monitoring": 0.0,
            "storyboard": 0.0,
            "composite": 0.0,
        },
    }
    (variant_dir / "holdout_result.json").write_text(json.dumps(legacy_payload))

    for lane in ("geo", "competitive", "monitoring", "storyboard", "core"):
        result = ev._load_private_result("v009", "holdout", "search-v1", lane=lane)
        assert result is None, f"zero-score legacy cache must be refused for {lane}"


def test_load_private_result_legacy_fallback_refuses_when_scores_dict_missing(monkeypatch, tmp_path):
    """Legacy file without a ``scores`` dict (or with non-dict) must be
    refused too — same zero-information argument.
    """
    monkeypatch.setenv("EVOLUTION_PRIVATE_ARCHIVE_DIR", str(tmp_path))
    import evaluate_variant as ev
    monkeypatch.setattr(ev, "load_json", _real_load_json)

    variant_dir = tmp_path / "v010"
    variant_dir.mkdir()
    legacy_payload = {"suite_id": "search-v1"}  # no scores key
    (variant_dir / "holdout_result.json").write_text(json.dumps(legacy_payload))

    assert ev._load_private_result("v010", "holdout", "search-v1", lane="geo") is None


# ---------------------------------------------------------------------------
# Unit 4 (post-audit 2026-05-07): _per_fixture_scores lane-projection so
# the promotion judge for --lane geo doesn't see baseline fixtures from
# competitive + monitoring + storyboard mixed in.
# ---------------------------------------------------------------------------


def _entry_with_multi_lane_fixtures():
    return {
        "id": "v006",
        "lane": "core",
        "search_metrics": {
            "suite_id": "search-v1",
            "composite": 2.7283,
            "domains": {
                "geo": {
                    "active": True,
                    "fixtures_detail": {
                        "geo-rakuten": {"score": 7.0, "secondary_score": 6.5},
                        "geo-bmw": {"score": 4.25, "secondary_score": 4.1},
                    },
                },
                "competitive": {
                    "active": True,
                    "fixtures_detail": {
                        "comp-shopify": {"score": 6.5, "secondary_score": 6.0},
                    },
                },
                "monitoring": {
                    "active": True,
                    "fixtures_detail": {
                        "monitoring-rippling": {"score": 1.4, "secondary_score": 1.2},
                    },
                },
            },
        },
    }


def test_per_fixture_scores_lane_projection_geo():
    """``lane='geo'`` must restrict the result to geo fixtures only.
    Pre-fix the function returned ALL active-domain fixtures, polluting
    the promotion-judge payload with cross-lane noise.
    """
    import evolve_ops as eo

    entry = _entry_with_multi_lane_fixtures()
    geo_only = eo._per_fixture_scores(entry, lane="geo")
    assert set(geo_only.keys()) == {"geo-rakuten", "geo-bmw"}
    assert geo_only["geo-rakuten"] == 7.0


def test_per_fixture_scores_lane_competitive():
    """Single-domain restriction works for any workflow lane."""
    import evolve_ops as eo

    entry = _entry_with_multi_lane_fixtures()
    comp = eo._per_fixture_scores(entry, lane="competitive")
    assert set(comp.keys()) == {"comp-shopify"}
    assert comp["comp-shopify"] == 6.5


def test_per_fixture_scores_lane_none_returns_all():
    """Back-compat: default ``lane=None`` returns every active-domain
    fixture (matches pre-fix behavior — used by emit_saturation_cycle_events
    for cross-lane saturation tracking).
    """
    import evolve_ops as eo

    entry = _entry_with_multi_lane_fixtures()
    all_fixtures = eo._per_fixture_scores(entry)
    assert set(all_fixtures.keys()) == {
        "geo-rakuten", "geo-bmw", "comp-shopify", "monitoring-rippling",
    }


def test_per_fixture_scores_lane_core_returns_all_active_domains():
    """``lane='core'`` returns all domains — core lane scored cross-lane
    and the promotion judge for core SHOULD see all active-domain
    fixtures (no restriction).
    """
    import evolve_ops as eo

    entry = _entry_with_multi_lane_fixtures()
    core = eo._per_fixture_scores(entry, lane="core")
    assert set(core.keys()) == {
        "geo-rakuten", "geo-bmw", "comp-shopify", "monitoring-rippling",
    }


def test_per_fixture_scores_lane_unknown_returns_empty():
    """Lane not present in domains → empty dict (no fixtures to project)."""
    import evolve_ops as eo

    entry = _entry_with_multi_lane_fixtures()
    # storyboard not in fixture data → no fixtures.
    assert eo._per_fixture_scores(entry, lane="storyboard") == {}


def test_per_fixture_scores_secondary_key_with_lane():
    """secondary_score key + lane projection both honored together."""
    import evolve_ops as eo

    entry = _entry_with_multi_lane_fixtures()
    geo_secondary = eo._per_fixture_scores(entry, key="secondary_score", lane="geo")
    assert geo_secondary == {"geo-rakuten": 6.5, "geo-bmw": 4.1}
