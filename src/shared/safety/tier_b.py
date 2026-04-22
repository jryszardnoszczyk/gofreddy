"""Tier B safety primitives — sandboxed-write inside a lane-scoped runtime dir.

Pipelines using Tier B partition a sandbox directory by *lane* (autoresearch
calls them workflow lanes: ``geo``, ``competitive``, ``monitoring``,
``storyboard``). Each lane owns a fixed prefix set; cross-lane writes are
filtered out at sync time so a workflow agent cannot contaminate another
lane's files. Pipelines pass their own lane configuration — nothing here is
autoresearch-specific.

Two primitives:

* :func:`path_owned_by_lane` — boolean ownership check, used to filter
  individual file paths during sandbox sync.
* :func:`sync_filtered` — copy + delete pass that materializes a source tree
  into a target tree, applying the lane filter and a caller-supplied
  protected-path predicate.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Callable, Iterable, Mapping, Optional


def normalize_lane(
    lane: str | None, *, lanes: tuple[str, ...], default: str = "core"
) -> str:
    """Return ``lane`` lowercased or ``default``; raise ``ValueError`` if unknown.

    ``lanes`` must be the full ordered tuple including the default lane (the
    autoresearch convention is ``("core", "geo", ...)``). Callers thread their
    own lane set through so this primitive never hardcodes any pipeline's
    workflow vocabulary.
    """
    normalized = (lane or default).strip().lower()
    if normalized not in lanes:
        raise ValueError(f"Unknown lane: {lane}")
    return normalized


def _matches_prefix(rel_path: str, prefix: str) -> bool:
    normalized = prefix.strip("/")
    if not normalized:
        return False
    return rel_path == normalized or rel_path.startswith(f"{normalized}/")


def path_owned_by_lane(
    rel_path: str | Path,
    lane: str,
    *,
    lanes: tuple[str, ...],
    workflow_prefixes: Mapping[str, tuple[str, ...]],
    excluded_prefixes: tuple[str, ...] = (),
    default_lane: str = "core",
) -> bool:
    """Return True if ``rel_path`` is owned by ``lane`` under this prefix scheme.

    * ``excluded_prefixes`` are infrastructure paths (e.g. ``harness``) excluded
      from every lane including ``default_lane`` — the default lane owns
      everything that's not a workflow path AND not infrastructure.
    * ``workflow_prefixes`` maps each non-default lane to its owned prefix
      tuple. Default-lane ownership is computed as the complement: everything
      not owned by any workflow lane (and not infrastructure).
    """
    lane = normalize_lane(lane, lanes=lanes, default=default_lane)
    rel_value = Path(rel_path).as_posix().lstrip("./")

    if any(_matches_prefix(rel_value, prefix) for prefix in excluded_prefixes):
        return False

    if lane == default_lane:
        workflow_lanes = tuple(name for name in lanes if name != default_lane)
        return not any(
            _matches_prefix(rel_value, prefix)
            for workflow_lane in workflow_lanes
            for prefix in workflow_prefixes.get(workflow_lane, ())
        )
    return any(_matches_prefix(rel_value, prefix) for prefix in workflow_prefixes.get(lane, ()))


def _iter_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if path.is_file():
            yield path


def sync_filtered(
    source_root: Path,
    target_root: Path,
    *,
    lane: Optional[str] = None,
    is_protected: Callable[[Path], bool],
    is_owned: Optional[Callable[[Path, str], bool]] = None,
) -> None:
    """Materialize ``source_root`` into ``target_root`` with lane + protected filtering.

    Mirrors ``autoresearch/lane_runtime.py``'s ``_sync_filtered`` (extracted
    here for cross-pipeline reuse): walks both trees, drops protected paths
    and (when ``lane`` is set) cross-lane paths from consideration, deletes
    target-only files (collapsing newly-empty directories upward), then copies
    source files over. ``shutil.copy2`` preserves metadata; on a crash mid-copy
    the target is half-synced and the next run re-syncs.

    ``is_protected`` runs against the *relative* path. ``is_owned`` runs against
    the relative path + the lane string when ``lane`` is provided; pass the
    autoresearch ``path_owned_by_lane`` (with its prefix maps bound) here.
    """
    def collect(root: Path) -> dict[str, Path]:
        files: dict[str, Path] = {}
        for path in _iter_files(root):
            rel = path.relative_to(root)
            if is_protected(rel):
                continue
            if lane and is_owned and not is_owned(rel, lane):
                continue
            files[rel.as_posix()] = path
        return files

    source_files = collect(source_root)
    target_files = collect(target_root)

    for rel_text in sorted(set(target_files) - set(source_files), reverse=True):
        target_path = target_root / rel_text
        target_path.unlink(missing_ok=True)
        parent = target_path.parent
        while parent != target_root and parent.exists() and not any(parent.iterdir()):
            parent.rmdir()
            parent = parent.parent

    for rel_text, source_path in source_files.items():
        target_path = target_root / rel_text
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)
