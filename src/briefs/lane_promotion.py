"""Promote-time brief emission for source lanes (U9 / U10 / U10b).

Per D8: cross-lane briefs are emitted ONLY when a variant is promoted
to baseline. Variant-emitted briefs are visible inside that variant's
evaluation only; they do not escape to consumers until promotion.

Lanes that emit briefs (geo, monitoring, marketing_audit) wire a
`custom_promote` callable on their LaneSpec that:
  1. Reads brief_candidates.jsonl from the promoted variant's session dir.
  2. Validates each candidate against FindingsBrief.
  3. Emits each valid brief via `src.briefs.emit_brief` to the lane's
     `current_runtime/briefs/` directory where consumers read it.
  4. Returns True to allow the promotion to proceed.

Malformed candidates are skipped with a log warning per D9 graceful
degradation — a single bad row never blocks promotion.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from pydantic import ValidationError

from src.briefs.emitter import emit_brief
from src.briefs.schema import FindingsBrief

logger = logging.getLogger(__name__)


def _candidate_paths(archive_dir: Path, variant_id: str, source_lane: str) -> list[Path]:
    """Find brief_candidates.jsonl across a variant's session subdirs.

    Convention: agent writes brief candidates to
    ``<archive_dir>/<variant_id>/sessions/<lane>/<client>/brief_candidates.jsonl``.
    A variant may have multiple clients in one run (fixture sweep), so
    we walk all matching paths.
    """
    variant_root = archive_dir / variant_id
    if not variant_root.is_dir():
        return []
    sessions_root = variant_root / "sessions" / source_lane
    if not sessions_root.is_dir():
        return []
    return sorted(sessions_root.glob("*/brief_candidates.jsonl"))


def emit_briefs_from_variant(
    archive_dir: Path, variant_id: str, source_lane: str,
) -> int:
    """Walk the promoted variant's session output for brief candidates +
    emit each valid one to the lane's current_runtime briefs dir.

    Returns the count of briefs successfully emitted (0 when no
    candidates exist — agent didn't identify any topics worth handing
    off).
    """
    candidates = _candidate_paths(archive_dir, variant_id, source_lane)
    if not candidates:
        logger.info(
            "no brief_candidates.jsonl found for %s/%s — nothing to emit",
            source_lane, variant_id,
        )
        return 0

    # Briefs land in current_runtime/briefs so the reader's
    # src.briefs.reader.read_briefs(source_lane, archive_root) call sees
    # them (the reader walks <archive_root>/briefs/*.json).
    briefs_archive_root = archive_dir / "current_runtime"
    emitted_count = 0
    for cand_path in candidates:
        try:
            text = cand_path.read_text(encoding="utf-8")
        except OSError as exc:
            logger.warning("could not read %s: %s; skipping", cand_path, exc)
            continue

        for line_no, raw_line in enumerate(text.splitlines(), start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                logger.warning(
                    "malformed brief candidate at %s:%d (%s); skipping",
                    cand_path, line_no, exc,
                )
                continue
            try:
                brief = FindingsBrief.model_validate(payload)
            except ValidationError as exc:
                logger.warning(
                    "brief candidate at %s:%d failed schema validation (%d errors); skipping",
                    cand_path, line_no, exc.error_count(),
                )
                continue

            try:
                emit_brief(brief, briefs_archive_root)
            except FileExistsError:
                logger.info(
                    "brief %s already emitted; skipping duplicate",
                    brief.brief_id,
                )
                continue
            emitted_count += 1

    logger.info(
        "emitted %d brief(s) for %s/%s", emitted_count, source_lane, variant_id,
    )
    return emitted_count


def make_brief_emitting_promote(source_lane: str):
    """Build a `custom_promote(archive_dir, variant_id, lane) -> bool`
    callable that emits briefs on promotion + returns True.

    Lane-specific module imports this and assigns the result to
    LaneSpec.custom_promote via _wire_<lane>_callables().
    """
    def _promote(archive_dir, variant_id: str, lane: str) -> bool:
        # archive_dir may be a Path or str (substrate passes either).
        path = archive_dir if isinstance(archive_dir, Path) else Path(str(archive_dir))
        try:
            emit_briefs_from_variant(path, variant_id, source_lane)
        except Exception:
            # Per CLAUDE.md Rule 12: fail loud at the helper boundary but
            # don't block the promotion — log + continue. A broken brief
            # emitter shouldn't prevent a legitimate variant from being
            # promoted.
            logger.exception(
                "brief emission failed for %s/%s; promotion continues",
                source_lane, variant_id,
            )
        return True

    _promote.__name__ = f"_{source_lane}_promote_with_briefs"
    return _promote


__all__ = [
    "emit_briefs_from_variant",
    "make_brief_emitting_promote",
]
