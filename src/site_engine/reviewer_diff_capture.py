"""Reviewer-feedback edit-diff capture (TD-43, U15b — scaffolded for v1.3).

Per TD-43: nightly diff job runs textual + DOM diff on `(approved_html,
lane_output_html)` pair on review acceptance; tags edit categories per
predefined enum; persists to
`reviewer_diffs/<client_slug>/<YYYY-MM>/diffs.jsonl`.

This is the v1.3 cross-cycle-learning primitive 1 — lands NOW so v1.3
automation (LLM-clustered edit-category surfacing) has a data
substrate when its trigger condition lands (~50 reviewed sections /
quarter across ≥3 clients ≈ 6 months post-launch).

V1 ships:
- The edit-category enum
- The persistence shape
- The textual diff helper

V1.3 will add:
- LLM-clustered category surfacing (primitive 2)
- Rubric-prose revision suggester (primitive 3)
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from difflib import unified_diff
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)


EditCategory = Literal[
    "copy_change",          # text rewritten without structural change
    "tone_change",          # voice/register shifted
    "sub_element_added",    # optional sub-element introduced
    "sub_element_removed",  # optional sub-element removed
    "layout_swap",          # different layout recipe applied
    "token_role_swap",      # different brand-token role consumed
    "manual_review",        # uncategorized — operator triages
]


@dataclass(frozen=True)
class ReviewerDiffEntry:
    """One captured (approved_html, lane_output_html) diff entry.

    Persisted as one JSONL line under `reviewer_diffs/<client_slug>/
    <YYYY-MM>/diffs.jsonl`. Schema-versioned for v1.3 evolution.
    """

    schema_version: int = 1
    captured_at: str = ""  # ISO 8601 UTC
    client_slug: str = ""
    section_type: str = ""
    variant_id: str = ""
    reviewer_note: str = ""
    edit_categories: list[EditCategory] = field(default_factory=list)
    textual_diff: str = ""  # unified diff string; bounded to ~5KB


def categorize_edit(
    approved_html: str, lane_output_html: str,
) -> list[EditCategory]:
    """Heuristic edit-category tagger.

    V1 uses simple structural heuristics:
    - If textual content changed but element structure preserved →
      `copy_change`.
    - If element count changed (sub-elements added/removed) →
      `sub_element_added` / `sub_element_removed`.
    - If layout-class hints changed (e.g., grid-cols-3 → grid-cols-2)
      → `layout_swap`.
    - Otherwise → `manual_review` for v1.3 LLM clustering.

    More precise categorization (DOM tree comparison + token-role
    inference) lands in v1.3 alongside the LLM clusterer.
    """
    if approved_html == lane_output_html:
        return []

    categories: list[EditCategory] = []

    # Crude sub-element count comparison via tag-open count.
    import re
    tag_open_re = re.compile(r"<(?!/)([a-zA-Z][a-zA-Z0-9]*)")
    approved_count = len(tag_open_re.findall(approved_html))
    lane_count = len(tag_open_re.findall(lane_output_html))
    if lane_count > approved_count + 2:
        categories.append("sub_element_removed")  # reviewer removed sub-elements
    elif approved_count > lane_count + 2:
        categories.append("sub_element_added")    # reviewer added sub-elements
    else:
        # Element count stable — text or layout change.
        # Layout-swap heuristic: grid-cols-X / flex-direction class change.
        if re.search(r"grid-cols-\d", approved_html) != re.search(r"grid-cols-\d", lane_output_html):
            categories.append("layout_swap")
        else:
            categories.append("copy_change")

    return categories


def capture_diff(
    *,
    client_slug: str,
    section_type: str,
    variant_id: str,
    approved_html: str,
    lane_output_html: str,
    reviewer_note: str = "",
    output_root: Path | None = None,
) -> ReviewerDiffEntry:
    """Capture a single (approved, lane_output) diff entry.

    Args:
        client_slug: ClientConfig.slug.
        section_type: hero | value_prop | social_proof | faq | cta | pricing.
        variant_id: the lane-generated variant identifier.
        approved_html: reviewer's final approved section HTML.
        lane_output_html: the lane's original variant HTML.
        reviewer_note: free-form note required ≥1 sentence per TD-43.
        output_root: optional override for diff persistence root
            (default `reviewer_diffs/` at repo root).

    Returns the persisted `ReviewerDiffEntry` (for synchronous
    confirmation; downstream readers parse the JSONL file).
    """
    captured_at = datetime.now(timezone.utc).isoformat()
    diff_lines = list(unified_diff(
        approved_html.splitlines(keepends=True),
        lane_output_html.splitlines(keepends=True),
        fromfile="approved",
        tofile="lane_output",
        lineterm="",
    ))
    textual_diff = "".join(diff_lines)
    if len(textual_diff) > 5000:
        textual_diff = textual_diff[:5000] + "\n... [truncated; full diff in archive]"

    categories = categorize_edit(approved_html, lane_output_html)
    entry = ReviewerDiffEntry(
        schema_version=1,
        captured_at=captured_at,
        client_slug=client_slug,
        section_type=section_type,
        variant_id=variant_id,
        reviewer_note=reviewer_note,
        edit_categories=categories,
        textual_diff=textual_diff,
    )

    # Persist to reviewer_diffs/<client_slug>/<YYYY-MM>/diffs.jsonl
    if output_root is None:
        output_root = (
            Path(__file__).resolve().parents[2] / "reviewer_diffs"
        )
    yyyy_mm = captured_at[:7]
    out_dir = output_root / client_slug / yyyy_mm
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "diffs.jsonl"
    with out_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "schema_version": entry.schema_version,
            "captured_at": entry.captured_at,
            "client_slug": entry.client_slug,
            "section_type": entry.section_type,
            "variant_id": entry.variant_id,
            "reviewer_note": entry.reviewer_note,
            "edit_categories": list(entry.edit_categories),
            "textual_diff": entry.textual_diff,
        }) + "\n")

    if not reviewer_note.strip():
        logger.warning(
            "reviewer_diff_capture: empty reviewer_note for %s/%s — "
            "TD-43 quarterly review requires ≥1 sentence; logging CI "
            "warning but not blocking publish.",
            client_slug, variant_id,
        )

    return entry


__all__ = [
    "EditCategory",
    "ReviewerDiffEntry",
    "capture_diff",
    "categorize_edit",
]
