"""Tests for the operator-facing tool_health surface in archive_index.py.

Phase 2 Unit 6 surfaces ``tool_error_rate`` from ``metrics/<domain>.jsonl``
as a top-level ``tool_health`` field on each variant's index entry, plus
a 3-tier band (``clean``/``degraded``/``unusable``). These tests cover
the band thresholds and the per-domain + aggregate roll-up.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def _make_metrics(variant_dir: Path, domain: str, rows: list[dict]) -> None:
    metrics_dir = variant_dir / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    path = metrics_dir / f"{domain}.jsonl"
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")


def test_tool_health_band_thresholds() -> None:
    """Band thresholds match the operator-facing spec in
    docs/plans/2026-05-08-002 §Unit 6: <0.1=clean, 0.1-0.5=degraded,
    >=0.5=unusable."""
    from autoresearch.archive_index import _tool_health_band

    assert _tool_health_band(0.0) == "clean"
    assert _tool_health_band(0.099) == "clean"
    assert _tool_health_band(0.1) == "degraded"
    assert _tool_health_band(0.4999) == "degraded"
    assert _tool_health_band(0.5) == "unusable"
    assert _tool_health_band(1.0) == "unusable"


def test_tool_health_summary_aggregates_per_domain(tmp_path: Path) -> None:
    """The summary aggregates across all (domain, client) sessions and
    surfaces each domain's rate alongside the cross-domain rollup."""
    from autoresearch.archive_index import _tool_health_summary

    archive = tmp_path / "archive"
    variant = archive / "v999"
    _make_metrics(variant, "geo", [
        {"client": "nubank", "iterations_total": 5, "tool_error_count": 1, "tool_error_rate": 0.2},
        {"client": "semrush", "iterations_total": 5, "tool_error_count": 0, "tool_error_rate": 0.0},
    ])
    _make_metrics(variant, "competitive", [
        {"client": "nubank", "iterations_total": 4, "tool_error_count": 3, "tool_error_rate": 0.75},
    ])

    summary = _tool_health_summary(archive, "v999")
    assert summary is not None
    assert summary["per_domain"]["geo"]["tool_error_count"] == 1
    assert summary["per_domain"]["geo"]["samples"] == 10
    assert summary["per_domain"]["geo"]["tool_error_rate"] == pytest.approx(0.1, abs=1e-4)
    assert summary["per_domain"]["geo"]["band"] == "degraded"
    assert summary["per_domain"]["competitive"]["band"] == "unusable"
    # Aggregate: (1 + 3) / (10 + 4) = 4/14 ≈ 0.2857
    assert summary["aggregate"]["tool_error_count"] == 4
    assert summary["aggregate"]["samples"] == 14
    assert summary["aggregate"]["tool_error_rate"] == pytest.approx(0.2857, abs=1e-4)
    assert summary["aggregate"]["band"] == "degraded"


def test_tool_health_returns_none_when_field_missing(tmp_path: Path) -> None:
    """A variant whose metrics jsonl rows predate Phase 1 (no
    tool_error_rate field) returns None instead of fabricating zeros —
    avoids implying clean operation when the data simply isn't there."""
    from autoresearch.archive_index import _tool_health_summary

    archive = tmp_path / "archive"
    variant = archive / "v900"
    _make_metrics(variant, "geo", [
        {"client": "ahrefs", "iterations_total": 6, "iterations_productive": 2},
    ])

    assert _tool_health_summary(archive, "v900") is None


def test_tool_health_returns_none_when_no_metrics_dir(tmp_path: Path) -> None:
    """Variants that haven't run any sessions yet have no metrics dir —
    the summary returns None gracefully."""
    from autoresearch.archive_index import _tool_health_summary

    archive = tmp_path / "archive"
    (archive / "v901").mkdir(parents=True)
    assert _tool_health_summary(archive, "v901") is None
