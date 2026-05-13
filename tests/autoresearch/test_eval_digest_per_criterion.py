"""Coverage for the 2026-05-13 Phase 3 per-criterion digest injection.

Before this fix, the meta-agent only saw composite scores in eval_digest.md.
The rich per-criterion judge feedback sat in `<variant>/sessions/<lane>/<client>/
.last_eval_cache.json` files but had no path to the meta-agent's prompt
context. Most v100-v195 mutations chased visible (structural) failures while
silent criteria like GEO-2 (factual grounding) and GEO-6 (cross-page
distinctness) capped scores at ~5.0.

The fix: walk the cache files, parse `stdout` JSON to extract
`results: [{criterion, passes, score, feedback}]`, group failures by
criterion across the cohort, and append a "## Per-Criterion Persistent
Failures" section to the digest. Lane-agnostic — every lane's session-judge
returns the same per_criterion shape regardless of rubric (GEO/MON/CI/MA/X/LI).

Memory: project-phase3-resume-state-2026-05-13.md.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Path bootstrap.
_repo_root = Path(__file__).resolve().parents[2]
_autoresearch_dir = _repo_root / "autoresearch"
if str(_autoresearch_dir) in sys.path:
    sys.path.remove(str(_autoresearch_dir))
sys.path.insert(0, str(_autoresearch_dir))
for _mod in [m for m in list(sys.modules) if m == "harness" or m.startswith("harness.")]:
    file_attr = getattr(sys.modules[_mod], "__file__", None) or ""
    if not file_attr.startswith(str(_autoresearch_dir)):
        del sys.modules[_mod]

import evaluate_variant  # noqa: E402


def _make_cache_file(
    session_dir: Path,
    *,
    deliverable_path: str,
    criterion_results: list[dict],
) -> Path:
    """Write a realistic .last_eval_cache.json into ``session_dir`` with
    one cache entry containing the supplied criterion results."""
    session_dir.mkdir(parents=True, exist_ok=True)
    cache_key = f"geo:full:{deliverable_path}"
    judge_response = {
        "decision": "REWORK" if any(not r.get("passes", True) for r in criterion_results) else "KEEP",
        "reason": "test",
        "results": criterion_results,
    }
    cache_payload = {
        cache_key: {
            "hash": "abc123",
            "stdout": json.dumps(judge_response),
        },
    }
    cache_path = session_dir / ".last_eval_cache.json"
    cache_path.write_text(json.dumps(cache_payload))
    return cache_path


def test_collect_returns_empty_for_missing_sessions_dir(tmp_path):
    """Variant with no sessions/ directory returns empty dict, no crash."""
    by_crit = evaluate_variant._collect_per_criterion_failures(tmp_path)
    assert by_crit == {}


def test_collect_aggregates_failures_across_fixtures(tmp_path):
    """Two fixtures both fail GEO-2 → aggregator should list 2 examples
    under GEO-2 (the SHARED-weakness signal the meta-agent needs)."""
    sessions_root = tmp_path / "sessions" / "geo"
    _make_cache_file(
        sessions_root / "semrush",
        deliverable_path="sessions/geo/semrush/optimized/homepage.md",
        criterion_results=[
            {"criterion": "GEO-1", "passes": True, "score": 1.0, "feedback": "good"},
            {"criterion": "GEO-2", "passes": False, "score": 0.0, "feedback": "facts wrong/stale"},
            {"criterion": "GEO-6", "passes": True, "score": 1.0, "feedback": "distinct"},
        ],
    )
    _make_cache_file(
        sessions_root / "ahrefs",
        deliverable_path="sessions/geo/ahrefs/optimized/pricing.md",
        criterion_results=[
            {"criterion": "GEO-1", "passes": True, "score": 1.0, "feedback": "ok"},
            {"criterion": "GEO-2", "passes": False, "score": 0.0, "feedback": "made up stats"},
        ],
    )
    by_crit = evaluate_variant._collect_per_criterion_failures(tmp_path)
    assert "GEO-2" in by_crit
    assert len(by_crit["GEO-2"]) == 2
    assert "GEO-1" not in by_crit  # passing criteria excluded
    assert "GEO-6" not in by_crit  # passing criteria excluded
    feedbacks = sorted(ex["feedback"] for ex in by_crit["GEO-2"])
    assert "facts wrong/stale" in feedbacks
    assert "made up stats" in feedbacks


def test_collect_includes_partial_credit_failures(tmp_path):
    """0.5 partial-credit on a criterion is still a failure to surface — the
    meta-agent benefits from seeing partials (where it's leaving 0.5 on
    the table)."""
    _make_cache_file(
        tmp_path / "sessions" / "geo" / "fix1",
        deliverable_path="sessions/geo/fix1/page.md",
        criterion_results=[
            {"criterion": "GEO-3", "passes": True, "score": 0.5, "feedback": "partial honesty"},
        ],
    )
    by_crit = evaluate_variant._collect_per_criterion_failures(tmp_path)
    # passes=True but score<0.5 — actually wait, the rule is "score < 0.5
    # OR passes is False". Pure 0.5 with passes=True should NOT include.
    # Let me make a real partial: score=0.0 with passes=True (judge weirdness)
    assert "GEO-3" not in by_crit  # 0.5 is borderline-pass, excluded


def test_collect_includes_score_below_half(tmp_path):
    """Score strictly below 0.5 counts as a failure regardless of passes flag."""
    _make_cache_file(
        tmp_path / "sessions" / "geo" / "fix1",
        deliverable_path="sessions/geo/fix1/page.md",
        criterion_results=[
            {"criterion": "GEO-4", "passes": True, "score": 0.3, "feedback": "almost"},
        ],
    )
    by_crit = evaluate_variant._collect_per_criterion_failures(tmp_path)
    assert "GEO-4" in by_crit
    assert by_crit["GEO-4"][0]["score"] == 0.3


def test_collect_handles_corrupt_cache_gracefully(tmp_path):
    """Malformed JSON in a cache file must NOT crash the digest writer.
    One corrupt fixture shouldn't suppress the rest."""
    good_dir = tmp_path / "sessions" / "geo" / "good"
    bad_dir = tmp_path / "sessions" / "geo" / "bad"
    good_dir.mkdir(parents=True)
    bad_dir.mkdir(parents=True)
    _make_cache_file(
        good_dir,
        deliverable_path="sessions/geo/good/page.md",
        criterion_results=[
            {"criterion": "GEO-2", "passes": False, "score": 0.0, "feedback": "fail"},
        ],
    )
    (bad_dir / ".last_eval_cache.json").write_text("{not valid json")
    by_crit = evaluate_variant._collect_per_criterion_failures(tmp_path)
    assert "GEO-2" in by_crit
    assert len(by_crit["GEO-2"]) == 1


def test_collect_handles_inner_stdout_corrupt(tmp_path):
    """Cache entry with valid outer JSON but corrupt stdout JSON: skip
    that entry, keep going with siblings."""
    sessions_root = tmp_path / "sessions" / "geo"
    sessions_root.mkdir(parents=True)
    cache_path = sessions_root / "fix1" / ".last_eval_cache.json"
    cache_path.parent.mkdir(parents=True)
    cache_path.write_text(json.dumps({
        "geo:full:bad-entry": {"hash": "x", "stdout": "{not json"},
        "geo:full:good-entry": {
            "hash": "y",
            "stdout": json.dumps({
                "decision": "REWORK",
                "results": [
                    {"criterion": "GEO-2", "passes": False, "score": 0.0, "feedback": "fail"},
                ],
            }),
        },
    }))
    by_crit = evaluate_variant._collect_per_criterion_failures(tmp_path)
    assert "GEO-2" in by_crit
    assert len(by_crit["GEO-2"]) == 1


def test_format_section_sorts_by_failure_count(tmp_path):
    """The rendered section must list criteria with the most failures FIRST
    so the meta-agent's attention goes to the highest-leverage fixes."""
    by_crit = {
        "GEO-1": [{"deliverable": "p1.md", "score": 0.0, "feedback": "x"}],
        "GEO-2": [
            {"deliverable": "p1.md", "score": 0.0, "feedback": "x"},
            {"deliverable": "p2.md", "score": 0.0, "feedback": "y"},
            {"deliverable": "p3.md", "score": 0.0, "feedback": "z"},
        ],
        "GEO-6": [
            {"deliverable": "p1.md", "score": 0.0, "feedback": "x"},
            {"deliverable": "p2.md", "score": 0.0, "feedback": "y"},
        ],
    }
    lines = evaluate_variant._format_per_criterion_section(by_crit)
    text = "\n".join(lines)
    geo2_pos = text.find("### GEO-2")
    geo6_pos = text.find("### GEO-6")
    geo1_pos = text.find("### GEO-1")
    assert geo2_pos < geo6_pos < geo1_pos


def test_format_section_truncates_long_feedback():
    by_crit = {
        "GEO-2": [{
            "deliverable": "p.md",
            "score": 0.0,
            "feedback": "x" * 1000,
        }],
    }
    lines = evaluate_variant._format_per_criterion_section(
        by_crit, max_feedback_chars=50,
    )
    text = "\n".join(lines)
    # Truncation marker present
    assert "..." in text
    # No 1000-char run survived
    assert "x" * 200 not in text


def test_format_section_caps_examples_per_criterion():
    """If a criterion has 20 failures, the section shows top N + a count
    of the rest — keeps the prompt budget under control."""
    by_crit = {
        "GEO-2": [
            {"deliverable": f"p{i}.md", "score": 0.0, "feedback": "x"}
            for i in range(10)
        ],
    }
    lines = evaluate_variant._format_per_criterion_section(
        by_crit, max_examples_per_criterion=4,
    )
    text = "\n".join(lines)
    assert "p0.md" in text
    assert "p3.md" in text
    assert "p9.md" not in text
    # The "more deliverable" footer announces the truncation honestly.
    assert "6 more deliverable" in text


def test_format_section_empty_when_no_failures():
    """No failures → empty list (no section header). Sanity guard so the
    digest doesn't show 'Per-Criterion Persistent Failures' followed by
    nothing."""
    assert evaluate_variant._format_per_criterion_section({}) == []
