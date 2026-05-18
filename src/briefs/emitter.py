"""Brief emitter — promoted-baseline only (D8).

Source lanes call `emit_brief(...)` from their promotion-time hook
(`custom_promote` on LaneSpec, or the session-end hook for lanes that
roll their own). Variant-emitted briefs never escape their evaluation
scope — only promoted ones become visible to downstream consumers.

Serialized as JSON to `<archive_root>/<source_lane>/briefs/<brief_id>.json`
where `<archive_root>` is typically `autoresearch/archive_<lane>/v<NNN>/`.
The reader (`src.briefs.reader.read_briefs`) walks the same convention.
"""

from __future__ import annotations

import logging
from pathlib import Path

from src.briefs.schema import FindingsBrief

logger = logging.getLogger(__name__)


def emit_brief(brief: FindingsBrief, archive_root: Path) -> Path:
    """Write `brief` as JSON to `<archive_root>/briefs/<brief_id>.json`.

    Args:
        brief: validated FindingsBrief.
        archive_root: the source lane's archive directory (typically
            `autoresearch/archive_<lane>/v<NNN>/` for promotion-time
            writes, or `autoresearch/archive_<lane>/current_runtime/`
            for the reader-visible current head).

    Returns:
        The absolute path to the written file.

    Raises:
        FileExistsError: if a brief with the same brief_id already
            exists at the target path (D8 invariant: briefs are
            promote-time emissions; re-emitting the same brief_id
            indicates a callsite bug, not a legitimate update).
    """
    briefs_dir = archive_root / "briefs"
    briefs_dir.mkdir(parents=True, exist_ok=True)

    target = briefs_dir / f"{brief.brief_id}.json"
    if target.exists():
        raise FileExistsError(
            f"brief already exists at {target}. Briefs are promote-time "
            f"only (D8); re-emitting the same brief_id indicates a "
            f"callsite bug. Use a fresh brief_id (include the variant id "
            f"+ a sequence suffix) if you legitimately need to emit a "
            f"replacement."
        )

    target.write_text(brief.model_dump_json(indent=2))
    logger.info(
        "emitted brief %s (priority=%s, source_lane=%s, target_lanes=%s)",
        brief.brief_id, brief.priority, brief.source_lane, brief.target_lanes,
    )
    return target


__all__ = ["emit_brief"]
