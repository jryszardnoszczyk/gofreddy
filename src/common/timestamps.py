"""Timestamp utilities for evidence timeline construction.

Provides M:SS-to-seconds conversion and timeline builder that merges
moderation flags, risk detections, and brand mentions into a chronological
timeline with co-location grouping.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from ..schemas import BrandMention, ModerationDetection, RiskDetection

logger = logging.getLogger(__name__)

_MSS_RE = re.compile(r"^(\d{1,2}):(\d{2})$")

_MAX_TIMELINE_ENTRIES = 500  # Defense-in-depth limit


def mss_to_seconds(ts: str | None) -> int | None:
    """Convert M:SS or MM:SS to integer seconds. Returns None for invalid/missing."""
    if ts is None:
        return None
    match = _MSS_RE.match(ts.strip())
    if not match:
        return None
    return int(match.group(1)) * 60 + int(match.group(2))


def build_evidence_timeline(
    moderation_flags: list[ModerationDetection],
    risks: list[RiskDetection],
    brand_mentions: list[BrandMention] | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Build chronological timeline from multiple JSONB sources.

    Returns (anchored_groups, unanchored_findings).
    anchored_groups: list of dicts with timestamp_seconds + findings list, sorted ASC.
    unanchored_findings: list of finding dicts with null/malformed timestamps.
    """
    anchored: list[tuple[int, dict[str, Any]]] = []
    unanchored: list[dict[str, Any]] = []

    # Process moderation flags
    for m in moderation_flags:
        seconds = mss_to_seconds(m.timestamp_start)
        end_seconds = mss_to_seconds(m.timestamp_end)
        finding: dict[str, Any] = {
            "type": "moderation",
            "category": m.moderation_class.value if hasattr(m.moderation_class, "value") else str(m.moderation_class),
            "severity": m.severity.value if hasattr(m.severity, "value") else str(m.severity),
            "confidence": m.confidence,
            "evidence": m.evidence,
            "timestamp_end_seconds": end_seconds,
        }
        if seconds is not None:
            anchored.append((seconds, finding))
        else:
            if m.timestamp_start is not None:
                logger.warning("Malformed timestamp in moderation flag: %s", m.timestamp_start)
            unanchored.append(finding)

    # Process risk detections
    for r in risks:
        seconds = mss_to_seconds(r.timestamp_start)
        end_seconds = mss_to_seconds(r.timestamp_end)
        finding = {
            "type": "risk",
            "category": r.category.value if hasattr(r.category, "value") else str(r.category),
            "severity": r.severity.value if hasattr(r.severity, "value") else str(r.severity),
            "confidence": r.confidence,
            "evidence": r.evidence,
            "timestamp_end_seconds": end_seconds,
        }
        if seconds is not None:
            anchored.append((seconds, finding))
        else:
            if r.timestamp_start is not None:
                logger.warning("Malformed timestamp in risk detection: %s", r.timestamp_start)
            unanchored.append(finding)

    # Process brand mentions (gracefully absent)
    for b in brand_mentions or []:
        seconds = mss_to_seconds(b.timestamp_start)
        finding = {
            "type": "brand",
            "category": "brand_mention",
            "severity": None,
            "confidence": b.confidence,
            "evidence": b.evidence,
            "timestamp_end_seconds": None,
            "brand_name": b.brand_name,
            "sentiment": b.sentiment.value if hasattr(b.sentiment, "value") else str(b.sentiment),
        }
        if seconds is not None:
            anchored.append((seconds, finding))
        else:
            if b.timestamp_start is not None:
                logger.warning("Malformed timestamp in brand mention: %s", b.timestamp_start)
            unanchored.append(finding)

    # Apply defense-in-depth limit
    if len(anchored) > _MAX_TIMELINE_ENTRIES:
        logger.warning("Timeline truncated: %d anchored entries exceeded limit %d", len(anchored), _MAX_TIMELINE_ENTRIES)
        anchored = anchored[:_MAX_TIMELINE_ENTRIES]
    if len(unanchored) > _MAX_TIMELINE_ENTRIES:
        logger.warning("Timeline truncated: %d unanchored entries exceeded limit %d", len(unanchored), _MAX_TIMELINE_ENTRIES)
        unanchored = unanchored[:_MAX_TIMELINE_ENTRIES]

    # Sort by timestamp, group co-located (same second)
    anchored.sort(key=lambda x: x[0])
    groups: list[dict[str, Any]] = []
    for seconds, finding in anchored:
        if groups and groups[-1]["timestamp_seconds"] == seconds:
            groups[-1]["findings"].append(finding)
        else:
            groups.append({"timestamp_seconds": seconds, "findings": [finding]})

    return groups, unanchored
