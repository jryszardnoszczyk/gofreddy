"""FindingsBrief schema (R21) — cross-lane handoff contract.

A `FindingsBrief` is the structured handoff between a source lane (geo,
monitoring, marketing_audit) and a consumer lane (article_engine,
site_engine). The source lane emits briefs at *promotion time only*
(D8); the consumer reads from the source lane's promoted archive.

Per the plan §Implementation Units U4 and the dependency graph:
- geo (U9) emits SEO topic briefs targeted at article_engine
- monitoring (U10) emits regulatory event briefs targeted at article_engine
- marketing_audit (U10b) emits section-level briefs targeted at site_engine
- article_engine + site_engine consume via the reader (top-K by priority)

Source pointers carry provenance back to the source lane's variant
output for citation density + audit-trail integrity. `valid_until`
opt-out: when None, briefs never stale.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


Priority = Literal["high", "medium", "low"]


# Ordering for priority-sort. Lower numeric value = higher priority.
_PRIORITY_ORDER: dict[str, int] = {"high": 0, "medium": 1, "low": 2}


class FindingsBrief(BaseModel):
    """A single brief emitted by a source lane at promotion time."""

    model_config = ConfigDict(frozen=True, extra="allow")

    schema_version: int = Field(
        default=1,
        description=(
            "Brief schema version. Briefs are immutable lineage artifacts "
            "on disk per D8; v1.5+ readers MUST log a distinct warning "
            "when encountering schema_version > reader-known so the "
            "consumer can distinguish 'no briefs emitted' from 'all "
            "briefs are shape-stale and unreadable' (AC-4)."
        ),
    )
    brief_id: str = Field(
        ...,
        description=(
            "Slug-shaped unique identifier. Convention: "
            "'<source_lane>-<topic_slug>-<YYYYMMDD>' or "
            "'<source_lane>-<variant_id>-<seq>'."
        ),
    )
    source_lane: str = Field(
        ...,
        description="Lane that emitted this brief (e.g. 'geo', 'monitoring').",
    )
    priority: Priority = Field(
        ...,
        description=(
            "Operator-assigned priority. Reader sorts high → medium → low; "
            "consumer applies top-K filter from ClientConfig.brief_consumption."
        ),
    )

    # Topic shape mirrors the R21 minimum field set: a structured title +
    # summary so consumers can produce coherent content without re-parsing
    # the source artifact.
    topic_title: str = Field(..., description="One-line headline of the topic.")
    topic_summary: str = Field(
        ...,
        description="2-4 sentence summary; consumer's primary context payload.",
    )

    target_lanes: list[str] = Field(
        ...,
        description=(
            "Lanes the source emitter recommends as consumers. Consumer-side "
            "may ignore; the field documents intent, not enforcement."
        ),
    )
    target_formats: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Per-lane format hint, e.g. {'article_engine': 'blog'}. Optional."
        ),
    )

    voice_persona_ref: str | None = Field(
        default=None,
        description=(
            "Persona slug to use when consuming this brief. Optional — "
            "when None, consumer falls back to ClientConfig.voice_persona_ref."
        ),
    )

    source_pointers: list[str] = Field(
        default_factory=list,
        description=(
            "Citation provenance: paths or URLs back to the source lane's "
            "variant output. Used by article_engine AE-3 citation verifier "
            "and by audit-trail traversal."
        ),
    )
    success_notes: str = Field(
        default="",
        description=(
            "What 'success' looks like for a consumer that picks up this "
            "brief (e.g. 'cover the Schrems-II implications for SaaS data "
            "transfers; 1500-2200 words; cite the EDPB guidelines'). "
            "Operator-curated by the source lane's agent prompt."
        ),
    )

    produced_at: datetime = Field(
        ...,
        description="UTC timestamp when the brief was emitted (D8 promote-time).",
    )
    valid_until: datetime | None = Field(
        default=None,
        description=(
            "Optional staleness boundary. When set and current time > "
            "valid_until, the reader skips the brief with a log warning."
        ),
    )

    @field_validator("brief_id")
    @classmethod
    def _brief_id_is_slug_shaped(cls, v: str) -> str:
        if not v or any(c.isspace() for c in v):
            raise ValueError(f"brief_id must be non-empty with no whitespace; got {v!r}")
        return v

    @field_validator("source_lane")
    @classmethod
    def _source_lane_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("source_lane must be non-empty")
        return v.strip()


def priority_sort_key(brief: FindingsBrief) -> tuple[int, datetime]:
    """Stable sort key: priority ascending (high → low), then produced_at
    ascending (older briefs first within a priority bucket).

    Exposed as a top-level helper so consumers (article_engine, site_engine)
    apply a deterministic sort even when they read from multiple sources
    and merge — the helper is a one-import substitute for re-implementing
    the sort inline.
    """
    return (_PRIORITY_ORDER.get(brief.priority, 99), brief.produced_at)


__all__ = [
    "FindingsBrief",
    "Priority",
    "priority_sort_key",
]
