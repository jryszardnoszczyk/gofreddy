"""Calibration tests for extract_reasoning.py per spec §A8.1.

These tests validate against frozen-in-archive session transcripts. They are
INTEGRATION tests against real artifacts, not unit tests against synthetic
data — the calibration target is "extract real reasoning from real Codex CLI
output," and synthetic fixtures would just paper over the regex tuning.

Coverage:
  1. cross-lane: same script runs on geo + competitive + monitoring + storyboard
  2. classifier first-clause rule (the A8.1 bug fix)
  3. pivot detection recall on a known transition
  4. token extraction
  5. tool-call counting
"""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # autoresearch/
SCRIPT = Path(__file__).resolve().parent.parent / "extract_reasoning.py"


def run_extract(session_dir: Path) -> dict:
    """Run extract_reasoning.py as a subprocess and return parsed JSON."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(session_dir)],
        capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout)


# ---------- cross-lane: same script, four very different lane outputs ----------

def test_geo_lane_extraction():
    sd = ROOT / "archive" / "v009" / "sessions" / "geo" / "nubank"
    if not sd.exists():
        return  # archive not available in this checkout
    out = run_extract(sd)
    assert out["iteration_count"] == 5, f"expected 5 iter, got {out['iteration_count']}"
    assert out["totals"]["reasoning_beats"] >= 30
    assert out["totals"]["tool_calls"] >= 80
    assert out["totals"]["tokens"] > 100  # ~201K for nubank


def test_competitive_lane_extraction():
    sd = ROOT / "archive" / "v010" / "sessions" / "competitive" / "figma"
    if not sd.exists():
        return
    out = run_extract(sd)
    assert out["iteration_count"] >= 4, "competitive figma has at least 4 logged iters"
    assert out["totals"]["reasoning_beats"] >= 30
    assert out["totals"]["tool_calls"] >= 80


def test_monitoring_lane_extraction():
    sd = ROOT / "archive" / "v006" / "sessions" / "monitoring" / "Shopify"
    if not sd.exists():
        return
    out = run_extract(sd)
    # Monitoring uses 6 typed phases (select_mentions, cluster_stories, etc.)
    # not "iteration:N" entries; iteration_count counts log files.
    assert "totals" in out
    assert out["totals"]["reasoning_beats"] >= 20


def test_storyboard_lane_extraction():
    sd = ROOT / "archive" / "v006" / "sessions" / "storyboard" / "MrBeast"
    if not sd.exists():
        return
    out = run_extract(sd)
    assert "totals" in out
    assert out["totals"]["reasoning_beats"] >= 10


# ---------- classifier first-clause rule (A8.1 fix) ----------

def test_classifier_first_clause_anti_hit_failure():
    """The specific bug from spec A8.1 calibration:
    "I have enough for a degraded but real baseline: confirmed cached metadata,
    confirmed static schema absence, failed rendered/robots/PageSpeed checks"
    should classify as `ship` (first clause "I have enough"), not `hit_failure`
    despite the word "failed" appearing later.
    """
    sys.path.insert(0, str(SCRIPT.parent))
    from extract_reasoning import classify_beat
    text = ("I have enough for a degraded but real baseline: confirmed cached "
            "metadata, confirmed static schema absence, failed rendered/robots/"
            "PageSpeed checks, and concrete next fixes.")
    assert classify_beat(text, idx=4) == "ship", \
        f"expected 'ship' (first clause 'I have enough'), got {classify_beat(text, 4)}"


def test_classifier_first_move_at_index_0():
    sys.path.insert(0, str(SCRIPT.parent))
    from extract_reasoning import classify_beat
    text = ("I'll read the persisted state and recent phase log first, then "
            "pick the single next phase to complete in this subprocess.")
    assert classify_beat(text, idx=0) == "first_move"


def test_classifier_genuine_hit_failure():
    sys.path.insert(0, str(SCRIPT.parent))
    from extract_reasoning import classify_beat
    text = ("Keyword-level visibility appears broken in this runtime: one "
            "retry still collapsed to the brand-only query and another hit "
            "connection_error.")
    # "appears broken" is a hit_failure pattern (the cli/api returned/failed)
    result = classify_beat(text, idx=2)
    # acceptable: hit_failure or other (not first_move/decide for a current-tense failure)
    assert result in ("hit_failure", "other"), f"got {result}"


def test_classifier_decide_pattern():
    sys.path.insert(0, str(SCRIPT.parent))
    from extract_reasoning import classify_beat
    text = ("The ledger shows discovery, competitive, and SEO baseline are "
            "done. I'm going to complete the next single phase: optimize the "
            "primary `conta` page, using only measured facts from the cached "
            "page and visibility file.")
    # second sentence is a decide pattern; first is descriptive — accept either
    result = classify_beat(text, idx=1)
    assert result in ("decide", "other"), f"got {result}"


# ---------- pivot detection recall ----------

def test_pivot_detected_in_geo_nubank():
    """The structural-gate-fail → recover transition in iter 4 of nubank
    must be caught by the pivot detector."""
    sd = ROOT / "archive" / "v009" / "sessions" / "geo" / "nubank"
    if not sd.exists():
        return
    out = run_extract(sd)
    pivots = out.get("pivots", [])
    assert any(p["iteration"] == 4 for p in pivots), \
        "expected at least one pivot in iteration 4 (structural-gate fail → recover)"


# ---------- output shape ----------

def test_output_schema_stable():
    sd = ROOT / "archive" / "v009" / "sessions" / "geo" / "nubank"
    if not sd.exists():
        return
    out = run_extract(sd)
    assert {"session_dir", "iteration_count", "totals", "iterations", "pivots"} <= out.keys()
    assert {"reasoning_beats", "tool_calls", "tokens"} <= out["totals"].keys()
    for it in out["iterations"]:
        assert {"iteration", "phase", "status", "reasoning_beats", "tool_calls",
                "tool_count", "token_count"} <= it.keys()
        for b in it["reasoning_beats"]:
            assert {"iteration", "kind", "text", "line_no"} <= b.keys()


if __name__ == "__main__":
    # When run directly: execute all test_* functions, print results.
    funcs = [(n, f) for n, f in globals().items() if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in funcs:
        try:
            fn()
            print(f"  ✓ {name}")
        except AssertionError as e:
            print(f"  ✗ {name}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ⨯ {name}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{len(funcs) - failed}/{len(funcs)} passed")
    sys.exit(0 if failed == 0 else 1)
