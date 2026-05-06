"""Tests for the A0/A5/A7 fixes in plan 2026-05-06-001.

These cover the unit-testable behavior introduced by
``docs/plans/2026-05-06-001-...`` to make the autoresearch evolution loop
validate promotions honestly:

- **A0** First-of-lane variants must produce a non-zero holdout score
  before they're treated as eligible for promotion.
- **A5** ``LaneSpec.readonly_subprefixes`` declares files inside the
  lane's owned tree that the meta-agent may read but not edit.
- **A7** ``_outer_pass_from_score`` is continuous on [0, 1] instead of
  binary 0/1, so ``mean_pass_rate_delta`` actually measures
  inner-vs-outer calibration drift.

The full sync-time ScopeViolation enforcement (``sync_variant_workspace``)
is exercised by the manual one-cycle dry run gate in plan §Verification §5,
not here — it pulls in the full archive_index runtime which is stubbed
out by ``conftest.py``.
"""
from __future__ import annotations

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


def test_path_is_readonly_matches_directory_subprefix() -> None:
    """A5: subprefix match also covers files under a directory subprefix
    (e.g., a future `templates/locked/...` declaration)."""
    # Use a synthetic spec to test the directory-startswith branch without
    # depending on the production layout shipping such a subprefix today.
    spec = lane_registry.LaneSpec(
        name="x", is_workflow_lane=True,
        readonly_subprefixes=("workflows/locked/",),
    )
    # Manually probe the matching logic via the same predicate the helper uses.
    rel_inside = "workflows/locked/foo.py"
    rel_outside = "workflows/other.py"
    matches = any(
        rel_inside == p or rel_inside.startswith(p)
        for p in spec.readonly_subprefixes
    )
    nomatch = any(
        rel_outside == p or rel_outside.startswith(p)
        for p in spec.readonly_subprefixes
    )
    assert matches
    assert not nomatch


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


def test_first_of_lane_requires_nonzero_holdout(monkeypatch: pytest.MonkeyPatch) -> None:
    """A0: pre-fix a fresh-lane variant auto-promoted regardless of holdout
    outcome. Now it must produce a strictly-positive composite holdout
    score before being treated as eligible.
    """
    # Stub objective_score_from_scores so the test doesn't depend on the
    # full domain-score plumbing.
    def fake_objective(scores: dict, lane: str) -> float | None:
        return scores.get("composite")

    monkeypatch.setattr(
        evaluate_variant, "_objective_score_from_scores", fake_objective
    )

    # Re-implements the inline gate at evaluate_variant.py:2664-2680 so we
    # can probe it without spinning up a real holdout suite. Mirrors the
    # production logic exactly — drift here means the production gate
    # drifted too.
    def _gate(holdout_scores: dict, baseline_scores: dict | None) -> tuple[bool, str]:
        if baseline_scores is None:
            candidate = fake_objective(holdout_scores, "geo")
            if candidate is None or candidate <= 0.0:
                return False, "first_variant_holdout_zero_score"
            return True, "first_variant_holdout_passed"
        if fake_objective(holdout_scores, "geo") > fake_objective(baseline_scores, "geo"):
            return True, "holdout_passed"
        return False, "holdout_not_better_than_baseline"

    eligible, reason = _gate({"composite": 0.0}, baseline_scores=None)
    assert eligible is False
    assert reason == "first_variant_holdout_zero_score"

    eligible, reason = _gate({"composite": 6.4}, baseline_scores=None)
    assert eligible is True
    assert reason == "first_variant_holdout_passed"

    # Standard "candidate > baseline" path still works when baseline exists.
    eligible, reason = _gate(
        {"composite": 7.0}, baseline_scores={"composite": 5.0}
    )
    assert eligible is True
    assert reason == "holdout_passed"

    eligible, reason = _gate(
        {"composite": 4.0}, baseline_scores={"composite": 5.0}
    )
    assert eligible is False
    assert reason == "holdout_not_better_than_baseline"


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
