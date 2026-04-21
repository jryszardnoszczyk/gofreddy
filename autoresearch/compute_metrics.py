"""Cross-variant evolution metrics (Fix 8 + 9).

Aggregates per-variant ``scores.json`` outputs into generation-level rows so we
can watch inner-outer correlation, cross-model stdev per criterion, and variant
fixture-SD drift without depending on the archived (meta-visible) state.

Outputs live under ``autoresearch/metrics/`` (outside the archive) so they are
NOT copied into the proposer's meta workspace. This keeps the evolutionary
feedback loop blind to its own diagnostic instrumentation.
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path
from typing import Any


AUTORESEARCH_DIR = Path(__file__).resolve().parent
ARCHIVE_DIR = AUTORESEARCH_DIR / "archive"
METRICS_DIR = AUTORESEARCH_DIR / "metrics"
METRICS_DIR.mkdir(exist_ok=True)

_GENERATIONS_LOG = METRICS_DIR / "generations.jsonl"
_ALERTS_LOG = METRICS_DIR / "alerts.jsonl"

# Alert thresholds
INNER_OUTER_DRIFT_THRESHOLD = 0.35
RUBRIC_AMBIGUITY_SD_THRESHOLD = 0.25
UNEVEN_GENERALIZATION_FIXTURE_SD = 0.30
UNEVEN_GENERALIZATION_COMPOSITE = 0.6


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 3 or len(ys) != n:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    denom = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
    return round(num / denom, 3) if denom else None


def _load_variant_scores(variant_id: str) -> dict[str, Any] | None:
    path = ARCHIVE_DIR / variant_id / "scores.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def _extract_variant_row(variant_id: str, data: dict[str, Any]) -> dict[str, Any]:
    keep_rates = [
        entry.get("keep_rate")
        for entry in (data.get("inner_metrics") or {}).values()
        if isinstance(entry, dict) and isinstance(entry.get("keep_rate"), (int, float))
    ]
    mean_keep = statistics.mean(keep_rates) if keep_rates else None
    domain_sds = [
        float(info.get("fixture_sd"))
        for info in (data.get("domains") or {}).values()
        if isinstance(info, dict) and isinstance(info.get("fixture_sd"), (int, float))
    ]
    max_fixture_sd = max(domain_sds) if domain_sds else 0.0
    composite = float(data.get("composite", 0.0) or 0.0)
    return {
        "variant_id": variant_id,
        "keep_rate": mean_keep,
        "composite": composite,
        "max_fixture_sd": round(max_fixture_sd, 4),
    }


def compute_generation_metrics(
    lane: str,
    gen_id: int,
    variant_ids: list[str],
    criterion_sds: dict[str, dict[str, float]] | None = None,
) -> dict[str, Any]:
    """Build a generation-level metrics row.

    ``criterion_sds`` maps variant_id → {criterion_id → stdev} from the
    evaluation repository. The caller fetches these out-of-band (Postgres is
    the source of truth for per-sample ensemble data).
    """
    rows: list[dict[str, Any]] = []
    for vid in variant_ids:
        data = _load_variant_scores(vid)
        if data is None:
            continue
        rows.append(_extract_variant_row(vid, data))

    keeps = [r["keep_rate"] for r in rows if r["keep_rate"] is not None]
    composites = [r["composite"] for r in rows if r["keep_rate"] is not None]

    per_criterion: dict[str, list[float]] = {}
    for variant_map in (criterion_sds or {}).values():
        for cid, sd in variant_map.items():
            per_criterion.setdefault(cid, []).append(float(sd))
    criterion_mean_sd = {
        cid: round(statistics.mean(sds), 3)
        for cid, sds in per_criterion.items()
        if sds
    }

    return {
        "lane": lane,
        "gen_id": gen_id,
        "n": len(rows),
        "inner_outer_corr": _pearson(keeps, composites),
        "mean_keep": round(statistics.mean(keeps), 3) if keeps else None,
        "mean_composite": round(statistics.mean(composites), 3) if composites else None,
        "criterion_mean_sd": criterion_mean_sd,
        "rows": rows,
    }


def append_generation_row(row: dict[str, Any]) -> None:
    with _GENERATIONS_LOG.open("a") as fh:
        fh.write(json.dumps(row) + "\n")


def _recent_rows(lane: str, limit: int = 5) -> list[dict[str, Any]]:
    if not _GENERATIONS_LOG.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in _GENERATIONS_LOG.read_text().splitlines():
        try:
            entry = json.loads(line)
        except Exception:
            continue
        if entry.get("lane") == lane:
            rows.append(entry)
    return rows[-limit:]


def _emit_alert(alert: dict[str, Any]) -> None:
    with _ALERTS_LOG.open("a") as fh:
        fh.write(json.dumps(alert) + "\n")
    print(f"METRIC ALERT: {alert['code']} — {alert['detail']}", file=sys.stderr)


def check_alerts(row: dict[str, Any]) -> None:
    """Raise stderr + alerts.jsonl entries for any crossed threshold."""
    recent = _recent_rows(row["lane"])
    lane = row["lane"]
    gen = row["gen_id"]

    # Inner-outer drift: two consecutive generations below threshold.
    corr = row.get("inner_outer_corr")
    if corr is not None and corr < INNER_OUTER_DRIFT_THRESHOLD:
        prior = recent[-2] if len(recent) >= 2 else None
        prior_corr = prior.get("inner_outer_corr") if prior else None
        if prior_corr is not None and prior_corr < INNER_OUTER_DRIFT_THRESHOLD:
            _emit_alert({
                "code": "inner_outer_drift",
                "lane": lane,
                "gen_id": gen,
                "detail": f"inner_outer_corr={corr} (prior={prior_corr})",
            })

    # Rubric ambiguity: criterion mean SD above threshold.
    for cid, sd in row.get("criterion_mean_sd", {}).items():
        if sd > RUBRIC_AMBIGUITY_SD_THRESHOLD:
            _emit_alert({
                "code": "rubric_ambiguity_candidate",
                "lane": lane,
                "gen_id": gen,
                "criterion_id": cid,
                "mean_sd": sd,
                "detail": f"{cid} mean_sd={sd} > {RUBRIC_AMBIGUITY_SD_THRESHOLD}",
            })

    # Uneven generalization: any variant with high fixture_sd despite high composite.
    for r in row.get("rows", []):
        if (
            r.get("max_fixture_sd", 0) > UNEVEN_GENERALIZATION_FIXTURE_SD
            and r.get("composite", 0) > UNEVEN_GENERALIZATION_COMPOSITE
        ):
            _emit_alert({
                "code": "uneven_generalization",
                "lane": lane,
                "gen_id": gen,
                "variant_id": r["variant_id"],
                "detail": (
                    f"variant={r['variant_id']} max_fixture_sd={r['max_fixture_sd']} "
                    f"composite={r['composite']}"
                ),
            })


def record_generation(
    lane: str,
    gen_id: int,
    variant_ids: list[str],
    criterion_sds: dict[str, dict[str, float]] | None = None,
) -> dict[str, Any]:
    """Top-level entry used from evolve.py after each generation completes."""
    row = compute_generation_metrics(lane, gen_id, variant_ids, criterion_sds)
    append_generation_row(row)
    check_alerts(row)
    return row
