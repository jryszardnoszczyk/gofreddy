from __future__ import annotations

import json
from pathlib import Path

from .session_eval_common import (
    CrossItemCriterion,
    SessionEvalSpec,
    load_results_entries,
    truncate,
)

# Module-level cache: parse results.jsonl once per session_dir per evaluation.
# Keyed by resolved path string so callers don't re-parse for each function.
_results_cache: dict[str, list[dict]] = {}


def _get_results(session_dir: Path) -> list[dict]:
    key = str(session_dir.resolve())
    cached = _results_cache.get(key)
    if cached is not None:
        return cached
    entries = load_results_entries(session_dir)
    _results_cache[key] = entries
    return entries


def clear_results_cache(session_dir: Path | None = None) -> None:
    if session_dir is None:
        _results_cache.clear()
    else:
        _results_cache.pop(str(session_dir.resolve()), None)


CRITERIA: dict[str, str] = {
    "MON-1": (
        "It tells you what changed this period. Surfaces the backward-looking delta — what "
        "is different compared to prior weeks or baseline expectations — with direction and "
        "magnitude, not just current state. \"Sentiment shifted from 41% to 62% positive\" "
        "not \"sentiment is 62% positive.\" For first-week digests, it identifies what in "
        "the current data deviates from what a naive observer would expect."
    ),
    "MON-2": (
        "It classifies severity correctly, with explicit confidence and stated limitations. "
        "Every signal gets a defensible classification: crisis, opportunity, or noise. "
        "Confidence levels (HIGH/MEDIUM/LOW) are stated inline with the basis — not in a "
        "separate section. Coverage gaps directly modify severity assessments: a crisis call "
        "on single-source data is flagged as provisional. When classification is a judgment "
        "call, the digest names the alternative reading."
    ),
    "MON-3": (
        "It names the one thing that matters most this week. Before the detail, the reader "
        "knows the single highest-stakes development and why it outranks everything else. If "
        "nothing extraordinary happened, it says that plainly."
    ),
    "MON-4": (
        "Action items are specific, prioritized, and time-bound. Each one names who should "
        "act, by when, and what happens if they don't. Items that can't wait until next week "
        "are flagged as such."
    ),
    "MON-5": (
        "It connects dots the reader wouldn't connect themselves — and projects where those "
        "connections lead. Cross-story pattern recognition that surfaces compound narratives "
        "(two signals together reveal something neither shows alone) AND names upcoming "
        "catalysts, developing threats, or competitor moves that will shape next week. "
        "Forward projections are conditional and falsifiable, not vague (\"this could "
        "escalate\")."
    ),
    "MON-6": (
        "Every number answers \"so what?\" and every absence is examined. Quantifies with "
        "interpretation, not decoration. Flags where expected signal is missing — the "
        "campaign that generated no coverage, the competitor that went quiet — because "
        "silence is often the most important data point."
    ),
    "MON-7": (
        "It connects to the arc of prior digests. Tracks whether last week's watchlist items "
        "escalated, stayed flat, or resolved. Follows up on previously recommended actions — "
        "was it taken, was it effective, or was it silently dropped? For first-week digests, "
        "it establishes tracking baselines that future digests can measure against."
    ),
    "MON-8": (
        "Word count is proportional to importance, not to data volume. The digest spends "
        "space on what matters most and compresses or omits what doesn't. The ratio of "
        "unique analytical insight to total words is high. Editorial restraint is visible — "
        "some available data was deliberately left out, making the remaining content sharper. "
        "The structure serves the content, not the reverse."
    ),
}

PER_STORY_CRITERIA = ("MON-1", "MON-2", "MON-4", "MON-6")


def structural_gate(mode: str, artifact: Path, session_dir: Path) -> list[str]:
    if mode == "per-story":
        failures = []
        if not artifact.exists():
            failures.append(f"Artifact not found: {artifact}")
        elif artifact.stat().st_size < 10:
            failures.append(f"Artifact is empty or trivial: {artifact}")
        return failures

    failures = []
    results = _get_results(session_dir)

    # Single-pass grouping by entry type
    by_type: dict[str, list[dict]] = {}
    for entry in results:
        entry_type = entry.get("type")
        if entry_type:
            by_type.setdefault(entry_type, []).append(entry)

    select_entries = by_type.get("select_mentions", [])
    latest_select = select_entries[-1] if select_entries else {}
    mentions_loaded = int(latest_select.get("mentions_loaded", 0) or 0)
    is_low_volume = bool(select_entries) and mentions_loaded < 30
    synth = by_type.get("synthesize", [])
    recommend_entries = by_type.get("recommend", [])

    if not (session_dir / "session.md").exists():
        failures.append("session.md missing")
    if len(results) == 0:
        failures.append("results.jsonl empty or missing")
    if not select_entries:
        failures.append("No select_mentions entry in results")
    if not is_low_volume and not by_type.get("cluster_stories"):
        failures.append("No cluster_stories entry in results")
    if not is_low_volume and len(synth) == 0:
        failures.append("No synthesize entry in results")
    if not is_low_volume and not recommend_entries:
        failures.append("No recommend entry in results")
    if not (session_dir / "digest.md").exists():
        failures.append("digest.md missing")
    if not (session_dir / "findings.md").exists():
        failures.append("findings.md missing")

    session_md = session_dir / "session.md"
    if session_md.exists() and "## Status: COMPLETE" not in session_md.read_text(encoding="utf-8", errors="replace"):
        failures.append("Session status is not COMPLETE")

    stories_dir = session_dir / "stories"
    synth_dir = session_dir / "synthesized"
    story_count = len(list(stories_dir.glob("story-*.json"))) if stories_dir.exists() else 0
    synth_count = len(list(synth_dir.glob("*.md"))) if synth_dir.exists() else 0
    if story_count > 0 and synth_count < story_count * 0.5:
        failures.append(f"Only {synth_count} synthesized vs {story_count} stories (<50%)")

    if any(entry.get("attempt", 1) > 3 for entry in synth):
        failures.append(f"{len([entry for entry in synth if entry.get('attempt', 1) > 3])} stories with >3 rework attempts")

    rec_dir = session_dir / "recommendations"
    has_rec = any(entry.get("status") == "kept" for entry in recommend_entries)
    if has_rec or is_low_volume:
        if not (rec_dir / "executive_summary.md").exists():
            failures.append("recommendations/executive_summary.md missing")
        if not (rec_dir / "action_items.md").exists():
            failures.append("recommendations/action_items.md missing")
    if is_low_volume and not (session_dir / "synthesized" / "digest-meta.json").exists():
        failures.append("synthesized/digest-meta.json missing for low-volume digest")
    if select_entries and not is_low_volume and int(latest_select.get("sources", 0) or 0) < 2:
        failures.append(f"Only {int(latest_select.get('sources', 0) or 0)} source(s) (need 2+)")
    return failures


def load_source_data(mode: str, _artifact: Path, session_dir: Path) -> str:
    parts: list[str] = []
    if mode == "per-story":
        for entry in reversed(_get_results(session_dir)):
            if entry.get("type") == "select_mentions":
                parts.append(f"## Raw Mentions Data\n```json\n{json.dumps(entry, indent=2)[:3000]}\n```")
                break
        return "\n\n".join(parts)

    for rel_path in ["findings.md", "recommendations/executive_summary.md", "recommendations/action_items.md"]:
        path = session_dir / rel_path
        if not path.exists():
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        parts.append(f"## {rel_path}\n{truncate(content, 1500)}")
    mdir = session_dir / "mentions"
    if mdir.exists():
        for path in sorted(mdir.glob("*.json"))[:5]:
            try: parts.append(f"## Raw Signal: {path.stem}\n{path.read_text(encoding='utf-8', errors='replace')[:500]}")
            except OSError: continue
    cross = session_dir / "recommendations" / "cross_story_patterns.md"
    if cross.exists():
        try: parts.append(f"## Cross-Story Patterns\n{cross.read_text(encoding='utf-8', errors='replace')[:1000]}")
        except OSError: pass
    return "\n\n".join(parts)


SPEC = SessionEvalSpec(
    domain="monitoring",
    domain_name="Monitoring Digest",
    criteria=CRITERIA,
    structural_gate=structural_gate,
    load_source_data=load_source_data,
    per_story_criteria=PER_STORY_CRITERIA,
    cross_item_criteria={"MON-7": CrossItemCriterion(glob="../*/digest.md", max_items=1, words_per_item=1000)},
)
