from __future__ import annotations

import json
from pathlib import Path

from .session_eval_common import (
    SessionEvalSpec,
    artifact_or_failure,
    load_results_entries,
    truncate,
)


# Structural-validator bullets — see session_eval_geo.STRUCTURAL_DOC_FACTS for
# the contract these enforce. ``autoresearch.regen_program_docs`` reads this
# tuple when stamping the AUTOGEN block in ``programs/monitoring-session.md``.
STRUCTURAL_DOC_FACTS: tuple[str, ...] = (
    "`session.md` exists.",
    "`results.jsonl` is non-empty and parseable.",
    "At least one `results.jsonl` entry has `type: select_mentions`.",
    "Clustering evidence is present — either `stories/*.json` files or a `digest.md` (low-volume weeks may skip clustering).",
    "Synthesis evidence is present — `digest.md` is the synthesized deliverable.",
    "Recommendation evidence is present — `recommendations/` files, a `results.jsonl` entry with `type: recommend`, or `digest.md`.",
    "`digest.md` exists.",
    "`findings.md` exists.",
    "Session status is terminal — `## Status: COMPLETE` in `session.md` or `digest.md` present.",
    "If any `recommendations/` files exist, `executive_summary.md` and `action_items.md` are both present.",
    "Source coverage — the latest `select_mentions` entry reports ≥2 sources, or `digest.md` is present (low-volume fallback).",
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
        "Developments are expressed as deltas from a defined baseline (prior week, 4-week "
        "trailing average, peer set), not absolute counts. '230 mentions this week vs 41-week "
        "rolling 130' not '230 mentions.' Per Brandwatch crisis-alert methodology + Sprout SoV "
        "practice + ESOV interpretation rule: without a baseline, a number is not a signal. "
        "For first digests, baseline = stated expectation."
    ),
    "MON-2": (
        "Each surfaced development is explicitly tiered (crisis / opportunity / watch / noise) "
        "with defensible classification — anchored in named evidence (source count, coverage "
        "duration, harm-axis severity, emotionality-axis severity per Cision React Score). SCCT "
        "cluster (Victim / Accidental / Intentional-Preventable per Coombs) stated where "
        "attribution matters. Coverage gaps explicitly modify severity."
    ),
    "MON-3": (
        "The highest-stakes development opens the digest in position one, explicitly framed as "
        "lede ('This week's lede: [X], because [stakes-rationale]'). Structural emphasis — "
        "position, length, headline weight — is proportional to stakes, not volume. Per "
        "FullIntel executive-briefing template + PDB precedent + SVB/USSS post-mortems "
        "(buried lede = ceded narrative). 'Nothing extraordinary happened' said plainly when true."
    ),
    "MON-4": (
        "Each action item follows the FAA Airworthiness Directive structure: (a) specific "
        "named owner or role with single decision-making authority, not 'the team'; (b) "
        "compliance time with explicit terminating condition ('by Friday 17:00 OR escalate'); "
        "(c) specific consequence-of-inaction the responsible party would want to avoid. Per "
        "14 CFR Part 39 + FullIntel + Tylenol 1982 precedent. 'Continue to monitor' fails."
    ),
    "MON-5": (
        "The digest surfaces at least one compound narrative where joint signal across "
        "stories carries an implication neither shows alone (causal chain, trend amplification, "
        "or structural risk visible only at cross-story level). At least one compound narrative "
        "includes a falsifiable forward projection ('if signal X by date Y, projection holds'). "
        "Per Harvard Law Narrative Contradictions + Ansoff weak signals + Dezenhall iceberg."
    ),
    "MON-6": (
        "Numbers are paired with interpretation that names a specific client decision they "
        "would change ('32% increase represents significant growth' fails). At least one "
        "statistic pre-empts a reader's likely alternative interpretation. At least one "
        "absent expected signal is flagged AND interpreted ('Competitor X went quiet, "
        "consistent with Y or Z'). Per FullIntel + AMEC outcomes-over-outputs + PDB blank-"
        "page convention + Edelman ethics-vs-competence + Sandman outrage-vs-hazard."
    ),
}

PER_STORY_CRITERIA = ("MON-1", "MON-2", "MON-4", "MON-6")


def structural_gate(mode: str, artifact: Path, session_dir: Path) -> list[str]:
    if mode == "per-story":
        return artifact_or_failure(artifact, min_bytes=10) or []

    failures: list[str] = []
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
    # MON-7 cross-item (temporal arc across prior digests) DROPPED 2026-05-15 per
    # Phase 4 redesign. No replacement cross-item criterion — MON-5 (compound
    # narrative) is within-session cross-story, not cross-digest.
    cross_item_criteria={},
)
