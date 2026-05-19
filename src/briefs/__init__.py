"""Findings-brief contract (R21) — cross-lane handoff substrate."""

from src.briefs.emitter import emit_brief
from src.briefs.lane_promotion import (
    emit_briefs_from_variant,
    make_brief_emitting_promote,
)
from src.briefs.reader import read_briefs
from src.briefs.schema import FindingsBrief, Priority

__all__ = [
    "FindingsBrief",
    "Priority",
    "emit_brief",
    "emit_briefs_from_variant",
    "make_brief_emitting_promote",
    "read_briefs",
]
