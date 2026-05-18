"""Findings-brief contract (R21) — cross-lane handoff substrate."""

from src.briefs.emitter import emit_brief
from src.briefs.reader import read_briefs
from src.briefs.schema import FindingsBrief, Priority

__all__ = [
    "FindingsBrief",
    "Priority",
    "emit_brief",
    "read_briefs",
]
