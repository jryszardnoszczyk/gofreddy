"""Stream A A4 — holdout lineage update behavior.

Background: Stream A plan §6.A4 — before the fix, `lineage.jsonl` entries
all carry ``holdout_metrics: {"ran": false}`` even when the holdout suite
has actually run (truth was only in the private finalize cache). After
the fix, `evaluate_variant.evaluate_holdout` calls
`_update_lineage_holdout_metrics` to append a refreshed lineage entry
exposing ``holdout_composite`` and friends to the v2 plan's U10 gate.

Gated by ``AUTORESEARCH_EVAL_FIX_HOLDOUT``.
"""
from __future__ import annotations

import json
import os
from glob import glob
from pathlib import Path

import pytest

import autoresearch.evaluate_variant as ev


def test_holdout_fix_flag_off_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AUTORESEARCH_EVAL_FIX_HOLDOUT", raising=False)
    assert ev._holdout_fix_enabled() is False


@pytest.mark.parametrize("value", ["1", "on", "true", "yes", "ON", "True"])
def test_holdout_fix_flag_truthy_values(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("AUTORESEARCH_EVAL_FIX_HOLDOUT", value)
    assert ev._holdout_fix_enabled() is True


@pytest.mark.parametrize("value", ["0", "off", "false", "no", "", "maybe"])
def test_holdout_fix_flag_falsy_values(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("AUTORESEARCH_EVAL_FIX_HOLDOUT", value)
    assert ev._holdout_fix_enabled() is False


def _existing_search_entry() -> dict:
    return {
        "id": "v042",
        "lane": "geo",
        "parent": "v007",
        "scores": {"geo": 6.5, "composite": 6.5},
        "search_metrics": {
            "suite_id": "search-v1",
            "composite": 6.5,
            "domains": {"geo": {"score": 6.5, "fixtures": 3, "active": True}},
        },
        "holdout_metrics": {"ran": False},
        "promotion_summary": {"eligible_for_promotion": False, "reason": "holdout_required"},
    }


def test_update_lineage_holdout_metrics_appends_refreshed_entry(monkeypatch: pytest.MonkeyPatch) -> None:
    """The helper loads the latest lineage entry for the variant, swaps the
    holdout block, and appends. Other fields are preserved verbatim."""
    captured: list[dict] = []

    monkeypatch.setattr(ev, "load_latest_lineage", lambda _archive_dir: {"v042": _existing_search_entry()})
    monkeypatch.setattr(ev, "append_lineage_entry", lambda _archive_dir, entry: captured.append(entry))

    ev._update_lineage_holdout_metrics(
        archive_dir=Path("/tmp/fake-archive"),
        variant_id="v042",
        existing_entry=_existing_search_entry(),
        holdout_scores={"geo": 4.77, "composite": 4.77},
        baseline_holdout_scores={"geo": 0.01, "composite": 0.01},
        baseline_variant_id="v007",
        suite_manifest={"suite_id": "holdout-v1"},
        eligible=True,
        reason="holdout_passed",
        lane="geo",
        evaluated_at="2026-05-09T14:56:03+00:00",
    )

    assert len(captured) == 1, captured
    entry = captured[0]
    # The refreshed entry preserves the variant id + every non-holdout field.
    assert entry["id"] == "v042"
    assert entry["parent"] == "v007"
    assert entry["scores"] == {"geo": 6.5, "composite": 6.5}
    # And exposes the real holdout outcome.
    hm = entry["holdout_metrics"]
    assert hm["ran"] is True
    assert hm["suite_id"] == "holdout-v1"
    assert hm["lane"] == "geo"
    assert hm["holdout_composite"] == 4.77
    assert hm["baseline_holdout_composite"] == 0.01
    assert hm["baseline_variant_id"] == "v007"
    assert hm["eligible_for_promotion"] is True
    assert hm["reason"] == "holdout_passed"
    assert hm["evaluated_at"] == "2026-05-09T14:56:03+00:00"
    # Top-level composite mirrors holdout_metrics so `evolve_ops._holdout_composite`
    # (which reads `entry.get("holdout_composite")`) sees the value too.
    assert entry["holdout_composite"] == 4.77
    assert entry["baseline_holdout_composite"] == 0.01


def test_update_lineage_holdout_metrics_no_op_without_existing_entry(monkeypatch: pytest.MonkeyPatch) -> None:
    """Defensive: when there is no prior lineage record (e.g. test fixture or
    a corrupted archive), the helper writes nothing rather than inventing a
    half-baked entry."""
    captured: list[dict] = []
    monkeypatch.setattr(ev, "load_latest_lineage", lambda _archive_dir: {})
    monkeypatch.setattr(ev, "append_lineage_entry", lambda _archive_dir, entry: captured.append(entry))

    ev._update_lineage_holdout_metrics(
        archive_dir=Path("/tmp/fake-archive"),
        variant_id="v999",
        existing_entry={},
        holdout_scores={"geo": 1.0, "composite": 1.0},
        baseline_holdout_scores=None,
        baseline_variant_id=None,
        suite_manifest={"suite_id": "holdout-v1"},
        eligible=False,
        reason="first_variant_holdout_zero_score",
        lane="geo",
        evaluated_at=None,
    )
    assert captured == []


def test_update_lineage_holdout_metrics_handles_missing_baseline(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[dict] = []
    monkeypatch.setattr(ev, "load_latest_lineage", lambda _archive_dir: {"v042": _existing_search_entry()})
    monkeypatch.setattr(ev, "append_lineage_entry", lambda _archive_dir, entry: captured.append(entry))

    ev._update_lineage_holdout_metrics(
        archive_dir=Path("/tmp/fake-archive"),
        variant_id="v042",
        existing_entry=_existing_search_entry(),
        holdout_scores={"geo": 4.77, "composite": 4.77},
        baseline_holdout_scores=None,  # first-of-lane: no baseline yet
        baseline_variant_id=None,
        suite_manifest={"suite_id": "holdout-v1"},
        eligible=True,
        reason="first_variant_holdout_passed",
        lane="geo",
        evaluated_at="2026-05-11T12:00:00+00:00",
    )
    hm = captured[0]["holdout_metrics"]
    assert hm["baseline_holdout_composite"] is None
    assert hm["baseline_variant_id"] is None
    assert "baseline_holdout_composite" not in captured[0], (
        "no baseline → don't mirror baseline_holdout_composite to the top level"
    )


@pytest.mark.skipif(
    os.environ.get("AUTORESEARCH_ARCHIVE_HOLDOUT_CHECK", "").strip().lower() not in {"1", "on", "true", "yes"},
    reason=(
        "Sweep-time invariant; enable with AUTORESEARCH_ARCHIVE_HOLDOUT_CHECK=1 after a fresh sweep. "
        "Older archives still carry pre-fix lineage entries (Bug 2) so a CI-by-default run would always fail."
    ),
)
def test_no_variant_promoted_with_zero_holdout() -> None:
    """Stream A plan §6.A4: after the fix, no new variant should land in
    ``lineage.jsonl`` flagged as promoted while reporting zero holdout —
    unless it carries an explicit ``holdout_skipped`` flag."""
    repo_root = Path(__file__).resolve().parents[2]
    lineage_path = repo_root / "autoresearch" / "archive" / "lineage.jsonl"
    if not lineage_path.exists():
        pytest.skip(f"no lineage at {lineage_path}")
    offenders: list[str] = []
    for raw_line in lineage_path.read_text().splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("status") == "promoted" and not entry.get("holdout_skipped"):
            composite = entry.get("holdout_composite", 0) or 0
            if composite <= 0:
                offenders.append(str(entry.get("id") or "<unknown>"))
    assert not offenders, (
        f"{len(offenders)} promoted variants carry zero holdout — Bug 2 may have returned: "
        f"{offenders[:5]}…"
    )
