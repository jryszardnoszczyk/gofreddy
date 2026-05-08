#!/usr/bin/env python3
"""Pre-L2 F4 gate: judge stability calibration.

Per master plan v13 §7.3 + the document-review feasibility-reviewer P0
finding. Score each draft N times through the evolution judge and report
per-dimension variance, cohort-fit variance, and judge-family agreement.

If any dimension's max variance ≥ 2.0 the script exits 1 — the rubric
anchor is too noisy for the evolution loop's promotion gate. ≤1.5 max
across all dimensions exits 0.

Usage:
  EVOLUTION_JUDGE_URL=http://localhost:7200 \\
  EVOLUTION_INVOKE_TOKEN=... \\
  python3 scripts/calibrate_judge_stability.py --domain x_engine

  --domain x_engine|linkedin_engine
  --drafts-dir <path>   (default: tests/fixtures/calibration/<domain>/)
  --runs N              (default: 2 — independent invocations per draft)
  --output <path>       (markdown report; default: stdout)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

DEFAULT_JUDGE_URL = "http://localhost:7200"
DEFAULT_FIXTURES_ROOT = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "calibration"

PASS_THRESHOLD = 1.5
FAIL_THRESHOLD = 2.0

X_DIMENSIONS = ("X-1", "X-2", "X-3", "X-4", "X-5", "X-6")
LI_DIMENSIONS = ("LI-1", "LI-2", "LI-3", "LI-4", "LI-5", "LI-6")
CROSS_ITEM = {"x_engine": "X-6", "linkedin_engine": "LI-6"}


class CalibrationError(RuntimeError):
    """Raised when calibration cannot be completed (config, network, parse)."""


def _domain_dimensions(domain: str) -> tuple[str, ...]:
    if domain == "x_engine":
        return X_DIMENSIONS
    if domain == "linkedin_engine":
        return LI_DIMENSIONS
    raise CalibrationError(
        f"unknown domain {domain!r} (expected 'x_engine' or 'linkedin_engine')"
    )


def _default_post(url: str, body: dict[str, Any], *, token: str, timeout: int) -> dict[str, Any]:
    payload = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise CalibrationError(
            f"judge HTTP {exc.code}: {exc.reason}"
        ) from exc
    except urllib.error.URLError as exc:
        raise CalibrationError(
            f"judge unreachable at {url}: {exc.reason}"
        ) from exc
    try:
        return json.loads(data)
    except json.JSONDecodeError as exc:
        raise CalibrationError(
            f"judge returned non-JSON body (first 200): {data[:200]!r}"
        ) from exc


def _read_drafts(drafts_dir: Path) -> list[tuple[str, str, str]]:
    """Return [(draft_id, filename, text), ...] sorted by stem."""
    if not drafts_dir.exists():
        raise CalibrationError(f"drafts directory not found: {drafts_dir}")
    drafts = sorted(drafts_dir.glob("*.md"))
    if not drafts:
        raise CalibrationError(f"no *.md drafts in {drafts_dir}")
    return [(p.stem, p.name, p.read_text(encoding="utf-8")) for p in drafts]


def _build_request(
    domain: str, draft_id: str, draft_filename: str, draft_text: str
) -> dict[str, Any]:
    """Mirror the autoresearch/evaluate_variant.py request shape."""
    fixture_payload = {
        "fixture_id": f"calibration-{draft_id}",
        "suite_id": "calibration-v1",
        "client": "calibration",
        "context": "judge-stability",
        "version": "v1",
        "domain": domain,
    }
    return {
        "domain": domain,
        "session_dir": f"calibration/{draft_id}",
        "session_ref": f"calibration/{draft_id}",
        "fixture_id": fixture_payload["fixture_id"],
        "fixture": fixture_payload,
        "suite_id": "calibration-v1",
        "campaign_id": None,
        "variant_id": None,
        "artifacts": {f"drafts/{draft_filename}": draft_text},
    }


def _extract_scores(
    family_response: dict[str, Any], dimensions: tuple[str, ...]
) -> dict[str, float | None]:
    """From a primary/secondary response, extract {criterion_id: score}."""
    out: dict[str, float | None] = {dim: None for dim in dimensions}
    per_criterion = family_response.get("per_criterion") or []
    if not isinstance(per_criterion, list):
        return out
    for entry in per_criterion:
        if not isinstance(entry, dict):
            continue
        cid = entry.get("criterion") or entry.get("criterion_id")
        if cid in out:
            score_raw = entry.get("score")
            try:
                out[cid] = float(score_raw)
            except (TypeError, ValueError):
                out[cid] = None
    return out


def _aggregate_score(family_response: dict[str, Any]) -> float | None:
    raw = family_response.get("aggregate_score")
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _per_dimension_variance(
    runs_scores: list[dict[str, float | None]],
) -> dict[str, float | None]:
    """Range (max - min) across N runs for each dimension. None if any run missing."""
    if not runs_scores:
        return {}
    out: dict[str, float | None] = {}
    for cid in runs_scores[0]:
        vals: list[float] = []
        complete = True
        for run in runs_scores:
            v = run.get(cid)
            if v is None:
                complete = False
                break
            vals.append(v)
        out[cid] = (max(vals) - min(vals)) if complete and vals else None
    return out


def calibrate(
    domain: str,
    drafts_dir: Path,
    runs: int,
    *,
    judge_url: str,
    token: str,
    timeout: int = 600,
    post_fn: Callable[[str, dict[str, Any]], dict[str, Any]] | None = None,
    raw_dir: Path | None = None,
) -> dict[str, Any]:
    """Run calibration and return a structured report dict.

    If ``raw_dir`` is provided, the full primary+secondary response for every
    draft+run is written to ``raw_dir/<draft_id>.run<i>.json`` for forensic
    inspection. Useful when calibration FAILs and you need to know which
    rationale drove the variance.
    """
    if runs < 2:
        raise CalibrationError("--runs must be >= 2 (variance needs at least 2 samples)")
    dimensions = _domain_dimensions(domain)
    cross_item = CROSS_ITEM[domain]
    drafts = _read_drafts(drafts_dir)

    endpoint = f"{judge_url.rstrip('/')}/invoke/score"
    if post_fn is None:
        def post_fn(url: str, body: dict[str, Any]) -> dict[str, Any]:
            return _default_post(url, body, token=token, timeout=timeout)

    if raw_dir is not None:
        raw_dir.mkdir(parents=True, exist_ok=True)

    per_draft: list[dict[str, Any]] = []
    for draft_id, draft_filename, draft_text in drafts:
        request_body = _build_request(domain, draft_id, draft_filename, draft_text)
        run_responses: list[dict[str, Any]] = []
        for run_idx in range(runs):
            response = post_fn(endpoint, request_body)
            run_responses.append(response)
            if raw_dir is not None:
                (raw_dir / f"{draft_id}.run{run_idx + 1}.json").write_text(
                    json.dumps(response, indent=2, sort_keys=True),
                    encoding="utf-8",
                )

        primary_runs = [
            _extract_scores(r.get("primary") or {}, dimensions) for r in run_responses
        ]
        secondary_runs = [
            _extract_scores(r.get("secondary") or {}, dimensions) for r in run_responses
        ]
        primary_aggregates = [_aggregate_score(r.get("primary") or {}) for r in run_responses]
        secondary_aggregates = [
            _aggregate_score(r.get("secondary") or {}) for r in run_responses
        ]

        per_draft.append(
            {
                "draft_id": draft_id,
                "primary_runs": primary_runs,
                "secondary_runs": secondary_runs,
                "primary_aggregates": primary_aggregates,
                "secondary_aggregates": secondary_aggregates,
                "primary_variance": _per_dimension_variance(primary_runs),
                "secondary_variance": _per_dimension_variance(secondary_runs),
            }
        )

    # Per-dimension variance summarized across drafts (primary judge only).
    # The cross-item dim (X-6 / LI-6) is EXCLUDED from per-draft variance —
    # it's marked `is_cross_item=True` in RUBRICS and is structurally
    # unscoreable on a single-fixture session (both judges flag this on N=1
    # cohorts). Per-draft variance for cross-item dims is sampling noise, not
    # rubric instability. Cross-item stability is captured separately in
    # `cohort_score_variance` below (variance of the per-draft scores
    # themselves, scored as a cohort).
    dim_summary: dict[str, dict[str, Any]] = {}
    for dim in dimensions:
        if dim == cross_item:
            # Reported separately as cohort_score_variance.
            dim_summary[dim] = {
                "avg": None,
                "max": None,
                "ge2_count": 0,
                "samples": 0,
                "excluded": "cross_item — see cohort_score_variance",
            }
            continue
        vals: list[float] = []
        ge2 = 0
        for d in per_draft:
            v = d["primary_variance"].get(dim)
            if v is None:
                continue
            vals.append(v)
            if v >= FAIL_THRESHOLD:
                ge2 += 1
        if vals:
            dim_summary[dim] = {
                "avg": sum(vals) / len(vals),
                "max": max(vals),
                "ge2_count": ge2,
                "samples": len(vals),
            }
        else:
            dim_summary[dim] = {
                "avg": None,
                "max": None,
                "ge2_count": 0,
                "samples": 0,
            }

    # Cohort-fit: spread of the cross-item score across the cohort (variance
    # of [draft1_score, draft2_score, ..., draftN_score] within a SINGLE run,
    # averaged across runs). High spread = anchor differentiates drafts; near
    # zero = anchor doesn't see cohort signal. This replaces the meaningless
    # "per-draft variance of N=1 cohort" — the cross-item dim is now scored
    # against its actual semantic axis.
    cohort_score_per_run: list[list[float]] = []
    for run_idx in range(runs):
        scores_this_run: list[float] = []
        for d in per_draft:
            primary_runs = d.get("primary_runs") or []
            if run_idx >= len(primary_runs):
                continue
            v = primary_runs[run_idx].get(cross_item)
            if v is not None:
                scores_this_run.append(v)
        if scores_this_run:
            cohort_score_per_run.append(scores_this_run)
    cohort_spread_per_run = [
        max(s) - min(s) for s in cohort_score_per_run if len(s) >= 2
    ]
    cohort_summary = {
        "dimension": cross_item,
        "spread_per_run": cohort_spread_per_run,
        "spread_avg": (
            sum(cohort_spread_per_run) / len(cohort_spread_per_run)
            if cohort_spread_per_run
            else None
        ),
        "samples": len(cohort_spread_per_run),
    }

    # Judge-family agreement: per draft, |avg(primary) - avg(secondary)|.
    judge_agreement: list[dict[str, Any]] = []
    for d in per_draft:
        p_vals = [v for v in d["primary_aggregates"] if v is not None]
        s_vals = [v for v in d["secondary_aggregates"] if v is not None]
        if not p_vals or not s_vals:
            judge_agreement.append(
                {
                    "draft_id": d["draft_id"],
                    "primary": None,
                    "secondary": None,
                    "abs_diff": None,
                }
            )
            continue
        p_avg = sum(p_vals) / len(p_vals)
        s_avg = sum(s_vals) / len(s_vals)
        judge_agreement.append(
            {
                "draft_id": d["draft_id"],
                "primary": p_avg,
                "secondary": s_avg,
                "abs_diff": abs(p_avg - s_avg),
            }
        )

    # Cross-item dims excluded from PASS/WARN/FAIL — they're scored on the
    # cohort axis (cohort_summary), not on per-draft variance.
    scoreable_dims = {
        dim: summary
        for dim, summary in dim_summary.items()
        if not summary.get("excluded")
    }
    failed_dims = [
        dim
        for dim, summary in scoreable_dims.items()
        if summary["max"] is not None and summary["max"] >= FAIL_THRESHOLD
    ]
    warn_dims = [
        dim
        for dim, summary in scoreable_dims.items()
        if summary["max"] is not None
        and PASS_THRESHOLD < summary["max"] < FAIL_THRESHOLD
    ]
    # data_unavailable: judge returned no recognized per-criterion scores for
    # ANY scoreable dim. Distinct from PASS — we can't certify stability
    # without samples. Usual cause: stale judge service or criterion-name
    # drift between rubric IDs and judge response.
    data_unavailable = all(summary["samples"] == 0 for summary in scoreable_dims.values())
    all_pass = (
        not failed_dims
        and not warn_dims
        and not data_unavailable
        and all(summary["max"] is not None for summary in scoreable_dims.values())
    )

    return {
        "domain": domain,
        "runs": runs,
        "draft_count": len(drafts),
        "dimensions": list(dimensions),
        "cross_item": cross_item,
        "per_draft": per_draft,
        "dim_variance": dim_summary,
        "cohort_variance": cohort_summary,
        "judge_agreement": judge_agreement,
        "failed_dims": failed_dims,
        "warn_dims": warn_dims,
        "data_unavailable": data_unavailable,
        "all_pass": all_pass,
    }


def _fmt(v: float | None, places: int = 2) -> str:
    return "—" if v is None else f"{v:.{places}f}"


def render_markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# Judge stability calibration — {report['domain']}")
    lines.append("")
    lines.append(f"- Runs per draft: {report['runs']}")
    lines.append(f"- Drafts: {report['draft_count']}")
    lines.append(f"- Cross-item dimension: {report['cross_item']}")
    lines.append("")

    if report["all_pass"]:
        lines.append(
            "**Verdict: PASS** — all dimensions ≤ 1.5 max variance. "
            "Anchors are stable enough to drive promotion gating."
        )
    elif report.get("data_unavailable"):
        lines.append(
            "**Verdict: DATA_UNAVAILABLE** — judge returned 0 recognized "
            f"per-criterion scores for any of {report['dimensions']}. "
            "Likely causes: (a) judge service is using a stale variant_scorer "
            "from before the templated dispatch shipped (restart needed); "
            "(b) judge response uses different criterion names than the "
            "rubric IDs. Cannot certify stability without samples."
        )
    elif report["failed_dims"]:
        dims_str = ", ".join(report["failed_dims"])
        lines.append(
            f"**Verdict: FAIL** — dimensions ≥ 2.0 max variance: {dims_str}. "
            f"Rewrite the rubric anchors before evolution."
        )
    else:
        warn = ", ".join(report["warn_dims"]) or "(none)"
        lines.append(
            f"**Verdict: WARN** — borderline dimensions in (1.5, 2.0): {warn}. "
            f"Tighten anchors before relying on tight promotion gates."
        )
    lines.append("")

    lines.append("## Per-dimension variance (primary judge)")
    lines.append("")
    lines.append(
        "Cross-item dim (the lane's last criterion) is reported separately "
        "below — its semantic axis is cohort-spread, not per-draft swing."
    )
    lines.append("")
    lines.append("| dim | avg variance | max variance | drafts ≥ 2.0 |")
    lines.append("|---|---:|---:|---:|")
    for dim in report["dimensions"]:
        v = report["dim_variance"][dim]
        if v.get("excluded"):
            lines.append(f"| {dim} | — | — | (cross-item; see below) |")
            continue
        lines.append(
            f"| {dim} | {_fmt(v['avg'])} | {_fmt(v['max'])} | {v['ge2_count']} |"
        )
    lines.append("")

    lines.append(
        f"## Cohort-fit spread ({report['cohort_variance']['dimension']})"
    )
    lines.append("")
    cv = report["cohort_variance"]
    lines.append(
        "Spread = max(score) − min(score) across drafts within one run. "
        "Tracks whether the anchor differentiates the cohort. Near-zero "
        "spread on a varied cohort suggests the anchor isn't seeing "
        "differentiation; high spread suggests it is."
    )
    lines.append("")
    lines.append(f"- spread per run: {cv['spread_per_run']}")
    lines.append(f"- avg spread: {_fmt(cv['spread_avg'])}")
    lines.append(f"- runs with cohort signal: {cv['samples']}")
    lines.append("")

    lines.append("## Judge-family agreement")
    lines.append("")
    lines.append("| draft | primary avg | secondary avg | abs(Δ) |")
    lines.append("|---|---:|---:|---:|")
    for ja in report["judge_agreement"]:
        lines.append(
            f"| {ja['draft_id']} | {_fmt(ja['primary'])} | "
            f"{_fmt(ja['secondary'])} | {_fmt(ja['abs_diff'])} |"
        )
    lines.append("")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="calibrate_judge_stability",
        description=(
            "Score each calibration draft N times through the evolution judge "
            "and report per-dimension variance + cohort-fit + judge-family "
            "agreement. Pre-L2-evolution F4 gate."
        ),
    )
    parser.add_argument(
        "--domain",
        choices=("x_engine", "linkedin_engine"),
        required=True,
    )
    parser.add_argument(
        "--drafts-dir",
        type=Path,
        default=None,
        help="Defaults to tests/fixtures/calibration/<domain>/",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=3,
        help=(
            "Independent judge invocations per draft (default 3). 2 runs "
            "produced verdict swings on this lane between consecutive "
            "calibrations — sampling noise dominated. 3 is the floor for "
            "a stable verdict against this judge stack."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Path for the markdown report; defaults to stdout.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Per-call HTTP timeout in seconds (default 600).",
    )
    parser.add_argument(
        "--save-raw",
        type=Path,
        default=None,
        help=(
            "Directory to save full primary+secondary judge responses per "
            "draft per run. One file per (draft, run): "
            "<draft_id>.run<i>.json. Use to inspect rationales when "
            "calibration FAILs and you need to know which dimension drove "
            "the variance."
        ),
    )
    args = parser.parse_args(argv)

    drafts_dir = args.drafts_dir or (DEFAULT_FIXTURES_ROOT / args.domain)
    judge_url = os.environ.get("EVOLUTION_JUDGE_URL", DEFAULT_JUDGE_URL)
    token = os.environ.get("EVOLUTION_INVOKE_TOKEN", "")

    try:
        report = calibrate(
            args.domain,
            drafts_dir,
            args.runs,
            judge_url=judge_url,
            token=token,
            timeout=args.timeout,
            raw_dir=args.save_raw,
        )
    except CalibrationError as exc:
        print(f"calibration failed: {exc}", file=sys.stderr)
        return 2

    output = render_markdown(report)
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output)

    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
