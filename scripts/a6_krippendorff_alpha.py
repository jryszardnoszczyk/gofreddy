#!/usr/bin/env python3
"""Stream A A6 — Krippendorff α measurement across 4 lanes.

Per Stream A plan (`docs/plans/2026-05-11-002-eval-pipeline-bug-fixes-plan.md`) §6.A6.
Re-runs each fixture N times against the evolution judge and computes per-axis
Krippendorff α (interval scale) per lane.

Mirrors the artifact-marshalling pattern from
`autoresearch/evaluate_variant.py:_score_session` so the judge sees the same
content evolutionary scoring would see — otherwise α is measured against
empty input and tells us nothing.

Usage:
  source ~/.config/gofreddy/judges.env
  AUTORESEARCH_EVAL_FIX_AXIS_COLLAPSE=on \\
  python3 scripts/a6_krippendorff_alpha.py \\
    --runs 5 \\
    --output /tmp/A6-alpha-measurement.md

Budget: ~10 fixtures × 5 reruns × ~36s wall ≈ ~30 min wall.
Cost ~$0.50–$1 per call × 50 calls ≈ ~$25–50.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


_TEXT_EXTS = {
    ".md", ".markdown", ".json", ".jsonl", ".yaml", ".yml",
    ".txt", ".csv", ".tsv", ".html", ".htm", ".xml", ".srt", ".vtt",
}
_MAX_PAYLOAD_BYTES = 800_000
_MAX_FILE_BYTES = 200_000


@dataclass(frozen=True)
class FixtureSpec:
    lane: str
    fixture_id: str
    session_dir: Path
    rubric_ids: tuple[str, ...]
    suite_id: str = "search-v1"


def _gen_ids(prefix: str) -> tuple[str, ...]:
    return tuple(f"{prefix}-{i}" for i in range(1, 9))


# Anchored to actual on-disk sessions in autoresearch/archive/v006/sessions/.
# Picks favor stable, populated sessions; avoids the fragile-fixtures set from A5.
ROOT = Path("/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/autoresearch/archive/v006/sessions")
DEFAULT_FIXTURES: tuple[FixtureSpec, ...] = (
    # geo (×2): ahrefs (sd 0.20 from A5 audit baseline) + mayoclinic
    FixtureSpec("geo", "geo-ahrefs", ROOT / "geo" / "ahrefs", _gen_ids("GEO")),
    FixtureSpec("geo", "geo-mayoclinic", ROOT / "geo" / "mayoclinic", _gen_ids("GEO")),
    # monitoring (×3): use healthy siblings of ramp-arc-t1
    FixtureSpec("monitoring", "monitoring-rippling", ROOT / "monitoring" / "Rippling", _gen_ids("MON")),
    FixtureSpec("monitoring", "monitoring-shopify",  ROOT / "monitoring" / "Shopify", _gen_ids("MON")),
    FixtureSpec("monitoring", "monitoring-notion",   ROOT / "monitoring" / "Notion", _gen_ids("MON")),
    # marketing_audit (×3)
    FixtureSpec("marketing_audit", "marketing_audit-anthropic", ROOT / "marketing_audit" / "Anthropic", _gen_ids("MA")),
    FixtureSpec("marketing_audit", "marketing_audit-dwf",       ROOT / "marketing_audit" / "DWF", _gen_ids("MA")),
    FixtureSpec("marketing_audit", "marketing_audit-perplexity", ROOT / "marketing_audit" / "Perplexity", _gen_ids("MA")),
    # competitive (×2)
    FixtureSpec("competitive", "competitive-canva", ROOT / "competitive" / "canva", _gen_ids("CMP")),
    FixtureSpec("competitive", "competitive-sap",   ROOT / "competitive" / "sap", _gen_ids("CMP")),
)


def _load_artifacts(session_dir: Path) -> dict[str, Any]:
    """Slurp text artifacts from session_dir under the autoresearch caps."""
    payload: dict[str, Any] = {}
    total = 0
    skipped_binary = skipped_too_large = 0
    truncated = False
    try:
        for path in sorted(session_dir.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(session_dir).as_posix()
            if rel.startswith("logs/"):
                continue
            if path.suffix.lower() not in _TEXT_EXTS:
                skipped_binary += 1
                continue
            try:
                size = path.stat().st_size
                if size > _MAX_FILE_BYTES:
                    skipped_too_large += 1
                    continue
                if total + size > _MAX_PAYLOAD_BYTES:
                    truncated = True
                    break
                payload[rel] = path.read_text(encoding="utf-8", errors="replace")
                total += size
            except (OSError, UnicodeError):
                continue
    except OSError:
        pass
    if truncated or skipped_binary or skipped_too_large:
        payload["__payload_meta__"] = {
            "total_bytes": total,
            "skipped_binary": skipped_binary,
            "skipped_too_large": skipped_too_large,
            "truncated": truncated,
        }
    return payload


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


def _post_score(payload: dict[str, Any], timeout: float = 600.0) -> dict[str, Any]:
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
    """Extract per-criterion scores. Prefer secondary (which uses lane-prefix
    criterion IDs like GEO-1) over primary (which uses generic names)."""
    for source in ("secondary", "primary"):
        block = verdict.get(source)
        if isinstance(block, dict):
            pc = block.get("per_criterion")
            if isinstance(pc, list) and pc:
                out: dict[str, float] = {}
                for item in pc:
                    if not isinstance(item, dict):
                        continue
                    raw = str(item.get("criterion") or "").strip()
                    cid = raw.split()[0] if raw else ""
                    score = item.get("score")
                    if cid and isinstance(score, (int, float)):
                        out[cid] = float(score)
                if out:
                    return out
    return {}


def _interval_alpha(rows: list[list[float | None]]) -> float | None:
    """Krippendorff α for interval data."""
    flat: list[tuple[int, float]] = []
    for unit, scores in enumerate(rows):
        for v in scores:
            if v is not None:
                flat.append((unit, float(v)))
    if len(flat) < 2:
        return None
    grand_mean = statistics.mean(v for _, v in flat)
    by_unit: dict[int, list[float]] = defaultdict(list)
    for u, v in flat:
        by_unit[u].append(v)
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
    n_total = len(flat)
    if n_total < 2:
        return None
    de = (2.0 / (n_total - 1)) * sum((v - grand_mean) ** 2 for _, v in flat)
    if de == 0:
        return None
    return 1.0 - (do_obs / de)


def _cv(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    mean = statistics.mean(values)
    if mean == 0:
        return None
    return statistics.stdev(values) / mean


def main() -> None:
    parser = argparse.ArgumentParser(description="Stream A A6: Krippendorff α measurement.")
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--output", default="/tmp/A6-alpha-measurement.md")
    parser.add_argument("--lane", default=None, help="Run only fixtures in this lane (debug).")
    parser.add_argument("--max-fixtures", type=int, default=None, help="Cap fixtures (debug).")
    args = parser.parse_args()

    fixtures = list(DEFAULT_FIXTURES)
    if args.lane:
        fixtures = [f for f in fixtures if f.lane == args.lane]
    if args.max_fixtures:
        fixtures = fixtures[: args.max_fixtures]
    if not fixtures:
        raise SystemExit("No fixtures selected")

    # Pre-check sessions exist
    missing = [str(f.session_dir) for f in fixtures if not f.session_dir.is_dir()]
    if missing:
        print(f"warning: {len(missing)} session dirs missing — they'll be skipped:", file=sys.stderr)
        for m in missing[:5]:
            print(f"  {m}", file=sys.stderr)
        fixtures = [f for f in fixtures if f.session_dir.is_dir()]

    rows_per_lane_axis: dict[tuple[str, str], list[list[float | None]]] = defaultdict(list)
    cv_per_fixture: list[tuple[str, str, float | None]] = []
    raw_log: list[dict[str, Any]] = []
    started = time.monotonic()

    for spec in fixtures:
        elapsed = int(time.monotonic() - started)
        print(f"[+{elapsed}s] [{spec.lane}] {spec.fixture_id}: loading artifacts ...", file=sys.stderr)
        artifacts = _load_artifacts(spec.session_dir)
        print(f"  artifacts: {len([k for k in artifacts if k != '__payload_meta__'])} files, "
              f"{artifacts.get('__payload_meta__', {}).get('total_bytes', sum(len(v) for k, v in artifacts.items() if isinstance(v, str)))} bytes",
              file=sys.stderr)
        runs_per_axis: dict[str, list[float]] = defaultdict(list)
        composite_runs: list[float] = []
        for run_idx in range(args.runs):
            payload = {
                "domain": spec.lane,
                "session_dir": str(spec.session_dir),
                "session_ref": str(spec.session_dir),
                "fixture_id": spec.fixture_id,
                "fixture": {
                    "fixture_id": spec.fixture_id,
                    "domain": spec.lane,
                    "suite_id": spec.suite_id,
                },
                "suite_id": spec.suite_id,
                "campaign_id": "a6-alpha",
                "variant_id": f"a6-{spec.fixture_id}-r{run_idx}",
                "artifacts": artifacts,
            }
            t0 = time.monotonic()
            try:
                verdict = _post_score(payload)
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
                print(f"    run {run_idx}: ERROR {exc}", file=sys.stderr)
                raw_log.append({"fixture": spec.fixture_id, "run": run_idx, "error": str(exc)})
                continue
            dt = time.monotonic() - t0
            axis_scores = _per_axis_scores(verdict)
            agg = (verdict.get("aggregate") or {}).get("aggregate_score")
            if isinstance(agg, (int, float)):
                composite_runs.append(float(agg))
            collected = 0
            for cid in spec.rubric_ids:
                if cid in axis_scores:
                    runs_per_axis[cid].append(axis_scores[cid])
                    collected += 1
            print(f"    run {run_idx}: {dt:.1f}s collected={collected}/{len(spec.rubric_ids)} agg={agg}", file=sys.stderr)
            raw_log.append({
                "fixture": spec.fixture_id,
                "run": run_idx,
                "axis_scores": axis_scores,
                "aggregate_score": agg,
                "duration": round(dt, 2),
            })
        if not runs_per_axis:
            print(f"    {spec.fixture_id}: NO axis scores collected — skipping", file=sys.stderr)
            continue
        for cid in spec.rubric_ids:
            scores = runs_per_axis.get(cid, [])
            padded: list[float | None] = list(scores) + [None] * (args.runs - len(scores))
            rows_per_lane_axis[(spec.lane, cid)].append(padded)
        cv_per_fixture.append((spec.lane, spec.fixture_id, _cv(composite_runs)))

    # Build report
    total_seconds = int(time.monotonic() - started)
    lines: list[str] = []
    lines.append("# A6 — Krippendorff α measurement")
    lines.append("")
    lines.append(f"- Runs per fixture: {args.runs}")
    lines.append(f"- Total wall time: {total_seconds // 60}m {total_seconds % 60}s")
    lines.append(f"- Fixtures attempted: {len(fixtures)}")
    lines.append("")
    lines.append("## Per-axis α per lane")
    lines.append("")
    lines.append("| Lane | Axis | α (interval) | n fixtures | flag |")
    lines.append("|---|---|---|---|---|")
    for (lane, axis) in sorted(rows_per_lane_axis.keys()):
        rows = rows_per_lane_axis[(lane, axis)]
        alpha = _interval_alpha(rows)
        if alpha is None:
            flag = "n/a"
            astr = "n/a"
        else:
            flag = "✓ stable" if alpha >= 0.7 else ("⚠ panel" if alpha >= 0.5 else "✗ rewrite")
            astr = f"{alpha:.3f}"
        lines.append(f"| {lane} | {axis} | {astr} | {len(rows)} | {flag} |")
    lines.append("")
    lines.append("## Per-fixture composite CV")
    lines.append("")
    lines.append("| Lane | Fixture | CV |")
    lines.append("|---|---|---|")
    for lane, fid, cv in cv_per_fixture:
        cv_str = "n/a" if cv is None else f"{cv:.4f}"
        lines.append(f"| {lane} | {fid} | {cv_str} |")
    lines.append("")
    lines.append("## Stream C decision matrix (plan §6.A7)")
    lines.append("")
    lines.append("- α ≥ 0.7 on every essential axis: skip panel-of-3 in v1.")
    lines.append("- 0.5 ≤ α < 0.7: panel-of-3 justified.")
    lines.append("- α < 0.5 on any essential axis: rewrite that rubric prose first.")

    Path(args.output).write_text("\n".join(lines) + "\n")
    # Also write raw transcripts for traceability.
    raw_path = Path(args.output).with_suffix(".raw.jsonl")
    raw_path.write_text("\n".join(json.dumps(r) for r in raw_log) + "\n")
    print(f"Wrote {args.output} and {raw_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
