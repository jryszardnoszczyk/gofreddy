"""Stream A axis-distinctness regression test.

Background: Stream A plan §6.A2 — once `AUTORESEARCH_EVAL_FIX_AXIS_COLLAPSE`
is on, fresh evaluator runs should produce *distinct* per-criterion scores
within a single eval. A `158/158`-style flat sample is the symptom that the
axis-collapse bug has come back.

This file ships two checks:

1. ``test_axis_collapse_fix_path_produces_distinct_scores`` — unit-level
   regression against the bridge logic in
   ``cli/freddy/commands/evaluate.py``. Always runs.

2. ``test_archived_evals_show_axis_variance`` — operational sweep-time
   check that scans ``autoresearch/archive/v*/sessions/*/evals/*.json``
   for the bug signature. Disabled by default (older archives contain
   pre-fix evals with 100% axis collapse, which is expected); enable by
   setting ``AUTORESEARCH_ARCHIVE_AXIS_CHECK=1`` after a fresh sweep.
"""
from __future__ import annotations

import json
import os
from glob import glob
from pathlib import Path

import pytest

from cli.freddy.commands.evaluate import _per_criterion_results


_ARCHIVE_GLOB = "autoresearch/archive/v*/sessions/*/*/evals/*.json"


def test_axis_collapse_fix_path_produces_distinct_scores() -> None:
    """The bridge's per-criterion unpack must produce score variance when
    the judge's ``per_criterion`` array carries differing verdicts."""
    verdict = {
        "overall": "rework",
        "per_criterion": [
            {"criterion_id": "GEO-1", "verdict": "pass"},
            {"criterion_id": "GEO-2", "verdict": "fail"},
            {"criterion_id": "GEO-3", "verdict": "rework"},
        ],
    }
    results = _per_criterion_results(verdict, ["GEO-1", "GEO-2", "GEO-3"])
    assert results is not None, "fix path should fire on full per_criterion"
    scores = {r["criterion_id"]: r["normalized_score"] for r in results}
    assert scores == {"GEO-1": 1.0, "GEO-2": 0.0, "GEO-3": 0.5}
    assert len(set(scores.values())) >= 2, "axis collapse — scores broadcast across criteria"


@pytest.mark.skipif(
    os.environ.get("AUTORESEARCH_ARCHIVE_AXIS_CHECK", "").strip().lower() not in {"1", "on", "true", "yes"},
    reason=(
        "Sweep-time check; enable with AUTORESEARCH_ARCHIVE_AXIS_CHECK=1 after a fresh sweep. "
        "Older archives still contain pre-fix evals (Bug 1) so a CI-by-default run would always fail."
    ),
)
def test_archived_evals_show_axis_variance() -> None:
    """Across freshly-collected eval files, at least 50% must show
    per-criterion score variance (more than one unique score). A flat
    distribution is the axis-collapse bug signature."""
    repo_root = Path(__file__).resolve().parent.parent
    paths = sorted(glob(str(repo_root / _ARCHIVE_GLOB)))
    eligible: list[Path] = []
    varied_count = 0
    for raw in paths:
        path = Path(raw)
        try:
            payload = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        results = payload.get("results")
        if not isinstance(results, list) or not results:
            continue
        scores = [r.get("score") for r in results if isinstance(r, dict) and isinstance(r.get("score"), (int, float))]
        if len(scores) < 2:
            continue
        eligible.append(path)
        if len(set(scores)) > 1:
            varied_count += 1
    assert eligible, "no eval files with ≥2 scored criteria; nothing to check"
    fraction = varied_count / len(eligible)
    assert fraction >= 0.50, (
        f"Only {varied_count}/{len(eligible)} eval files ({fraction:.0%}) show per-axis "
        "variance — axis-collapse bug may have returned. See docs/plans/"
        "2026-05-11-002-eval-pipeline-bug-fixes-plan.md §6.A2."
    )
