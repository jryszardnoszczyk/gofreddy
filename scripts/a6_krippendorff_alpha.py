#!/usr/bin/env python3
"""Stream A A6 — Krippendorff α measurement across 4 lanes.

Per Stream A plan (`docs/plans/2026-05-11-002-eval-pipeline-bug-fixes-plan.md`) §6.A6.
Re-runs each fixture N times against the evolution judge at temperature=0.3
(per Rating Roulette's finding that T=0 degrades agreement). Computes per-axis
Krippendorff α (interval scale) per lane and writes a markdown report.

Pre-flight (operator):
  - Stream A A2 must have shipped: AUTORESEARCH_EVAL_FIX_AXIS_COLLAPSE=on
  - Stream A A4 must have shipped: AUTORESEARCH_EVAL_FIX_HOLDOUT=on (optional
    for α measurement but recommended so reruns don't poison lineage)
  - Judge service up at EVOLUTION_JUDGE_URL, with EVOLUTION_INVOKE_TOKEN.

Usage:
  AUTORESEARCH_EVAL_FIX_AXIS_COLLAPSE=on \\
  EVOLUTION_JUDGE_URL=http://localhost:7200 \\
  EVOLUTION_INVOKE_TOKEN=... \\
  python3 scripts/a6_krippendorff_alpha.py \\
    --runs 5 \\
    --output /tmp/A6-alpha-measurement.md

Budget: ~10 fixtures × 5 reruns × 8 axes × ~1500 tokens ≈ ~600K judge tokens.
At Sonnet pricing (~$5/M input + $15/M output, mostly input here), expect
roughly $20-40 total. Wall time ~2-3h with current concurrency.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class FixtureSpec:
    lane: str
    fixture_id: str
    session_dir: str  # relative to archive, used as session_ref
    rubric_ids: tuple[str, ...]


# Curated stable fixtures per lane (plan §6.A6 calls for ~10 across 4 lanes).
# Picks favor high-quality, recent fixtures with stable structural pass
# patterns — avoid the fragile-fixtures set from A5.
DEFAULT_FIXTURES: tuple[FixtureSpec, ...] = (
    # geo (×2)
    FixtureSpec("geo", "geo-ahrefs-pricing",
                "autoresearch/archive/v006/sessions/geo/ahrefs",
                tuple(f"GEO-{i}" for i in range(1, 9))),
    FixtureSpec("geo", "geo-ahrefs-site-explorer",
                "autoresearch/archive/v006/sessions/geo/ahrefs",
                tuple(f"GEO-{i}" for i in range(1, 9))),
    # monitoring (×3) — healthy siblings, skip ramp-arc-t1 per A5
    FixtureSpec("monitoring", "monitoring-ramp-arc-t0",
                "autoresearch/archive/v006/sessions/monitoring/ramp-arc-t0",
                tuple(f"MON-{i}" for i in range(1, 9))),
    FixtureSpec("monitoring", "monitoring-rippling-firstweek",
                "autoresearch/archive/v006/sessions/monitoring/rippling-firstweek",
                tuple(f"MON-{i}" for i in range(1, 9))),
    FixtureSpec("monitoring", "monitoring-shopify-2026w12",
                "autoresearch/archive/v006/sessions/monitoring/shopify-2026w12",
                tuple(f"MON-{i}" for i in range(1, 9))),
    # marketing_audit (×3)
    FixtureSpec("marketing_audit", "marketing_audit-anthropic",
                "autoresearch/archive/v006/sessions/marketing_audit/anthropic",
                tuple(f"MA-{i}" for i in range(1, 9))),
    FixtureSpec("marketing_audit", "marketing_audit-dwf",
                "autoresearch/archive/v006/sessions/marketing_audit/dwf",
                tuple(f"MA-{i}" for i in range(1, 9))),
    FixtureSpec("marketing_audit", "marketing_audit-perplexity",
                "autoresearch/archive/v006/sessions/marketing_audit/perplexity",
                tuple(f"MA-{i}" for i in range(1, 9))),
    # competitive (×2)
    FixtureSpec("competitive", "competitive-opaque",
                "autoresearch/archive/v006/sessions/competitive/opaque",
                tuple(f"CMP-{i}" for i in range(1, 9))),
    FixtureSpec("competitive", "competitive-nubank",
                "autoresearch/archive/v006/sessions/competitive/nubank",
                tuple(f"CMP-{i}" for i in range(1, 9))),
)


def _judge_url() -> str:
    url = os.environ.get("EVOLUTION_JUDGE_URL", "").strip()
    if not url:
        raise SystemExit("EVOLUTION_JUDGE_URL is unset")
    return url


def _judge_token() -> str:
    token = os.environ.get("EVOLUTION_INVOKE_TOKEN", "").strip()
    if not token:
        raise SystemExit("EVOLUTION_INVOKE_TOKEN is unset")
    return token


def _post_score(payload: dict[str, Any], timeout: float = 300.0) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{_judge_url()}/invoke/score",
        data=data,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {_judge_token()}"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())


def _per_axis_scores(verdict: dict[str, Any]) -> dict[str, float]:
    """Extract per-criterion scores from a judge verdict.

    Tries the variant_scorer-native `primary.per_criterion[]` (where each
    entry has criterion+score) first, falls back to `aggregate.per_criterion`,
    and finally to top-level `per_criterion` for older judge deployments.
    """
    for source in ("primary", "aggregate"):
        block = verdict.get(source)
        if isinstance(block, dict):
            pc = block.get("per_criterion")
            if isinstance(pc, list):
                return _extract(pc)
    pc = verdict.get("per_criterion")
    if isinstance(pc, list):
        return _extract(pc)
    return {}


def _extract(per_criterion: list[Any]) -> dict[str, float]:
    out: dict[str, float] = {}
    for item in per_criterion:
        if not isinstance(item, dict):
            continue
        cid = str(item.get("criterion") or item.get("criterion_id") or "").strip()
        score = item.get("score") or item.get("normalized_score")
        if cid and isinstance(score, (int, float)):
            out[cid] = float(score)
    return out


def _interval_alpha(rows: list[list[float | None]]) -> float | None:
    """Krippendorff α for interval data.

    rows: list of axis observations, each a list of N rerun scores (None = missing).
    Returns alpha in [-1, 1] or None when the calculation is undefined.
    """
    # Flatten to (unit, value) pairs.
    flat: list[tuple[int, float]] = []
    for unit, scores in enumerate(rows):
        for v in scores:
            if v is not None:
                flat.append((unit, float(v)))
    if len(flat) < 2:
        return None
    # Overall mean.
    grand_mean = statistics.mean(v for _, v in flat)
    # Disagreement-observed: sum over pairs (within-unit) of squared diffs.
    by_unit: dict[int, list[float]] = defaultdict(list)
    for u, v in flat:
        by_unit[u].append(v)
    n_total = len(flat)
    # Observed disagreement: weighted within-unit pair sum / total pairs.
    do_num = 0.0
    do_den = 0.0
    for vs in by_unit.values():
        if len(vs) < 2:
            continue
        for i in range(len(vs)):
            for j in range(i + 1, len(vs)):
                do_num += (vs[i] - vs[j]) ** 2
                do_den += 1.0
    if do_den == 0:
        return None
    do_obs = do_num / do_den
    # Expected disagreement: variance scaled by 2 (interval metric).
    if n_total < 2:
        return None
    de = (2.0 / (n_total - 1)) * sum((v - grand_mean) ** 2 for _, v in flat)
    if de == 0:
        return None
    return 1.0 - (do_obs / de)


def _coefficient_of_variation(scores: list[float]) -> float | None:
    if len(scores) < 2:
        return None
    mean = statistics.mean(scores)
    if mean == 0:
        return None
    return statistics.stdev(scores) / mean


def main() -> None:
    parser = argparse.ArgumentParser(description="Stream A A6: Krippendorff α measurement.")
    parser.add_argument("--runs", type=int, default=5, help="Reruns per fixture (default 5).")
    parser.add_argument("--temperature", type=float, default=0.3,
                        help="Judge temperature (plan §6.A6: T=0.3).")
    parser.add_argument("--output", default="/tmp/A6-alpha-measurement.md",
                        help="Output report path.")
    parser.add_argument("--fixtures-json", default=None,
                        help="Override fixture list with a JSON file (list of FixtureSpec dicts).")
    parser.add_argument("--lane", default=None,
                        help="Run only fixtures in this lane (debug).")
    args = parser.parse_args()

    fixtures = list(DEFAULT_FIXTURES)
    if args.fixtures_json:
        raw = json.loads(Path(args.fixtures_json).read_text())
        fixtures = [FixtureSpec(**item) for item in raw]
    if args.lane:
        fixtures = [f for f in fixtures if f.lane == args.lane]
    if not fixtures:
        raise SystemExit("No fixtures selected")

    # Per (lane, axis): list of per-unit (fixture) score sequences for α.
    rows_per_lane_axis: dict[tuple[str, str], list[list[float | None]]] = defaultdict(list)
    cv_per_fixture: list[tuple[str, str, float | None]] = []
    skipped: list[tuple[str, str]] = []

    for spec in fixtures:
        print(f"[{spec.lane}] {spec.fixture_id}: scoring {args.runs}× ...", file=sys.stderr)
        runs_per_axis: dict[str, list[float]] = defaultdict(list)
        composite_runs: list[float] = []
        for run_idx in range(args.runs):
            payload = {
                "session_ref": spec.session_dir,
                "domain": spec.lane,
                "fixture": {"id": spec.fixture_id},
                "lane": spec.lane,
                "seeds": [run_idx],
                "artifacts": {},
                "temperature": args.temperature,
            }
            try:
                verdict = _post_score(payload)
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
                print(f"    run {run_idx}: error {exc}", file=sys.stderr)
                continue
            axis_scores = _per_axis_scores(verdict)
            if not axis_scores:
                print(f"    run {run_idx}: no per-axis scores in response", file=sys.stderr)
                continue
            for cid in spec.rubric_ids:
                if cid in axis_scores:
                    runs_per_axis[cid].append(axis_scores[cid])
            aggregate = verdict.get("aggregate") or {}
            if isinstance(aggregate, dict):
                agg_score = aggregate.get("aggregate_score")
                if isinstance(agg_score, (int, float)):
                    composite_runs.append(float(agg_score))
        # Add this fixture's per-axis sequences to the lane α rows.
        if not runs_per_axis:
            skipped.append((spec.lane, spec.fixture_id))
            continue
        for cid in spec.rubric_ids:
            scores = runs_per_axis.get(cid, [])
            # Pad to args.runs length with None for missing reruns
            padded: list[float | None] = list(scores) + [None] * (args.runs - len(scores))
            rows_per_lane_axis[(spec.lane, cid)].append(padded)
        cv_per_fixture.append((spec.lane, spec.fixture_id, _coefficient_of_variation(composite_runs)))

    # Per-lane per-axis α.
    lines: list[str] = []
    lines.append(f"# A6 — Krippendorff α measurement")
    lines.append("")
    lines.append(f"Runs per fixture: {args.runs}; temperature: {args.temperature}")
    lines.append(f"Fixtures attempted: {len(fixtures)}; skipped: {len(skipped)}")
    if skipped:
        lines.append("")
        lines.append("Skipped (no per-axis response):")
        for lane, fid in skipped:
            lines.append(f"  - {lane}: {fid}")
    lines.append("")
    lines.append("## Per-axis α per lane")
    lines.append("")
    lines.append("| Lane | Axis | α (interval) | n fixtures |")
    lines.append("|---|---|---|---|")
    for (lane, axis) in sorted(rows_per_lane_axis.keys()):
        rows = rows_per_lane_axis[(lane, axis)]
        alpha = _interval_alpha(rows)
        flag = "✓" if (alpha is not None and alpha >= 0.7) else ("⚠️" if (alpha is not None and alpha >= 0.5) else "❌")
        lines.append(f"| {lane} | {axis} | {alpha if alpha is None else f'{alpha:.3f}'} {flag} | {len(rows)} |")
    lines.append("")
    lines.append("## Per-fixture composite CV")
    lines.append("")
    lines.append("| Lane | Fixture | CV |")
    lines.append("|---|---|---|")
    for lane, fid, cv in cv_per_fixture:
        cv_str = "n/a" if cv is None else f"{cv:.4f}"
        lines.append(f"| {lane} | {fid} | {cv_str} |")
    lines.append("")
    lines.append("## Stream C decision (see plan §6.A7)")
    lines.append("")
    lines.append("- If every essential axis has α ≥ 0.7: single frontier judge suffices; defer C0/C6 panel.")
    lines.append("- If 0.5 ≤ α < 0.7: panel-of-3 justified.")
    lines.append("- If α < 0.5 on any essential axis: rewrite the failing rubric prose first.")

    Path(args.output).write_text("\n".join(lines) + "\n")
    print(f"Wrote {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
