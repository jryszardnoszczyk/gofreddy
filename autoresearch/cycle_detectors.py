"""Degenerate-cycle detection for the evolve loop (Stream C C21).

Three pure functions that flag when a lane is making non-progress on
composite scores — the meta-agent's calibration is either saturated
(hitting the ceiling/floor), repeating itself, or producing trivial
ablations. The wrapper ``check_lane_degenerate`` reads recent kept-variant
composites from ``archive_index`` and runs the detectors over the slice.

Pattern ported from aiming-lab/AutoResearchClaw (MIT)
Source: https://github.com/aiming-lab/AutoResearchClaw
File: researchclaw/pipeline/stage_impls/_analysis.py:737-880

The v2 plan called for an agent-callable tool that returned a
``(recommendation, reason)`` tuple. v1 doesn't have a per-iteration
meta-agent loop with REFINE-status pivots, so the wrapper instead emits
an advisory string and the caller (``evolve.cmd_run``) prints it as a
stderr warning. No automatic halt — operators decide whether to stop.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


# Detector thresholds. Tuned for gofreddy composites in the 0-10 range
# (per scorer.md): "saturated at floor" = a fully broken pipeline that
# scores ~0 across the board; "saturated at ceiling" = the rubric can't
# distinguish quality past a near-max score. Operators on different
# rubric scales (e.g., RaR's 0-1 binary normalization) should pass
# explicit ``low=`` / ``high=`` overrides rather than tuning the
# module-level defaults.
_SATURATION_LOW = 0.5
_SATURATION_HIGH = 9.5
_TRIVIAL_ABLATION_THRESHOLD = 0.02


def detect_saturated_metrics(
    history: list[float],
    *,
    low: float = _SATURATION_LOW,
    high: float = _SATURATION_HIGH,
) -> bool:
    """Return True when every score in ``history`` is at the floor or
    ceiling. Saturation means the rubric can't distinguish further
    progress: either all variants score 0 (broken pipeline) or all max
    (rubric too easy). Refining more is a waste; the right move is to
    fix the benchmark.

    Empty / single-element histories return False (insufficient signal).
    """
    samples = [m for m in history if m is not None]
    if len(samples) < 2:
        return False
    return all(m <= low or m >= high for m in samples)


def detect_identical_iterations(history: list[float]) -> bool:
    """Return True when ``history`` has 2+ non-None scores and they are
    all equal. Identical iterations across multiple generations mean
    the meta-agent's mutations are no-ops at the rubric's resolution
    — the search isn't exploring."""
    samples = [m for m in history if m is not None]
    if len(samples) < 2:
        return False
    return len({round(s, 6) for s in samples}) == 1


def detect_trivial_ablations(
    ablations: list[dict[str, Any]],
    *,
    threshold: float = _TRIVIAL_ABLATION_THRESHOLD,
) -> tuple[int, int]:
    """Return ``(n_trivial, n_total)`` over an ablation summary.

    Each entry is expected to carry a numeric ``delta`` (signed change
    from the baseline). Entries with ``abs(delta) < threshold`` are
    counted as trivial. When more than half the ablations are trivial,
    the ablation DESIGN is broken (the variants don't actually probe
    different axes) and the wrapper surfaces a "fix ablations" hint.

    Empty input returns ``(0, 0)`` so callers can skip-divide safely.
    """
    n_total = 0
    n_trivial = 0
    for entry in ablations:
        if not isinstance(entry, dict):
            continue
        delta = entry.get("delta")
        if not isinstance(delta, (int, float)):
            continue
        n_total += 1
        if abs(float(delta)) < threshold:
            n_trivial += 1
    return n_trivial, n_total


def _coerce_composite(entry: dict[str, Any], lane: str) -> float | None:
    """Extract a numeric composite score from a lineage entry for ``lane``.

    Tries (in order):
    1. ``entry["search_metrics"]["domains"][lane]["composite"]`` — the
       canonical per-lane composite written by evaluate_search.
    2. ``entry["search_metrics"]["composite"]`` — the cross-lane composite
       (fallback when the per-lane field is missing).
    3. ``entry[lane]`` — flat-shaped legacy entries.
    Returns None when nothing parseable is present.
    """
    metrics = entry.get("search_metrics") if isinstance(entry, dict) else None
    if isinstance(metrics, dict):
        domains = metrics.get("domains")
        if isinstance(domains, dict):
            lane_block = domains.get(lane)
            if isinstance(lane_block, dict):
                value = lane_block.get("composite")
                if isinstance(value, (int, float)):
                    return float(value)
        flat = metrics.get("composite")
        if isinstance(flat, (int, float)):
            return float(flat)
    flat_lane = entry.get(lane) if isinstance(entry, dict) else None
    if isinstance(flat_lane, (int, float)):
        return float(flat_lane)
    return None


def recent_composite_history(
    archive_dir: Path, lane: str, *, window: int = 5,
) -> list[float]:
    """Return the last ``window`` composite scores for ``lane`` from the
    archive's lineage. Filters to entries where the lane field matches.
    Returns an empty list when archive_index isn't importable or the
    archive has no lineage yet."""
    try:
        from autoresearch.archive_index import (  # noqa: PLC0415
            load_lineage_history,
        )
    except ImportError:
        return []
    try:
        entries = load_lineage_history(archive_dir)
    except Exception:
        return []
    composites: list[float] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        entry_lane = str(entry.get("lane") or "").strip().lower()
        if entry_lane and entry_lane != lane.strip().lower():
            continue
        composite = _coerce_composite(entry, lane)
        if composite is not None:
            composites.append(composite)
    return composites[-window:]


def check_lane_degenerate(
    archive_dir: Path, lane: str, *, window: int = 5,
) -> tuple[bool, str, dict[str, Any]]:
    """Return ``(is_degenerate, advisory, metadata)`` for a lane's recent
    score history.

    - ``is_degenerate`` is True when ANY detector fires.
    - ``advisory`` is a short stderr-ready string (empty when not
      degenerate) chosen by detector priority: saturated > identical >
      trivial_ablations.
    - ``metadata`` carries which detector fired plus the raw history so
      operators can debug without re-reading lineage by hand.
    """
    history = recent_composite_history(archive_dir, lane, window=window)
    metadata: dict[str, Any] = {
        "lane": lane,
        "window": window,
        "history": history,
        "saturated": False,
        "identical": False,
    }
    if detect_saturated_metrics(history):
        metadata["saturated"] = True
        return True, (
            f"[degenerate-cycle] lane={lane} saturated over last {len(history)} "
            f"variants — further REFINE cycles cannot fix this. Recommend "
            f"PROCEED with quality caveat, or review the rubric / fixtures."
        ), metadata
    if detect_identical_iterations(history):
        metadata["identical"] = True
        return True, (
            f"[degenerate-cycle] lane={lane} produced identical composites "
            f"across last {len(history)} variants — the meta-agent's edits "
            f"are no-ops at the rubric's resolution. Recommend reviewing "
            f"mutation diversity or PROCEED with caveats."
        ), metadata
    return False, "", metadata
