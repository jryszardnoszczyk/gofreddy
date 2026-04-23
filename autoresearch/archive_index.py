#!/usr/bin/env python3
"""Public archive indexing and manifest generation for autoresearch."""

from __future__ import annotations

import argparse
import difflib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from frontier import (
    DOMAINS,
    LANES,
    best_variant_in_lane,
    composite_score,
    domain_score,
    entry_lane,
    has_search_metrics,
    objective_score,
)
from lane_paths import path_owned_by_lane
from lane_runtime import load_current_manifest

IGNORED_DIRS = {"__pycache__", "sessions", "metrics", "runs"}
IGNORED_FILES = {
    ".DS_Store",
    "meta-session.log",
    "mutation_plan.json",
    "scores.json",
}
LANE_WORKSPACE_KEEP_FILES = {"meta.md", "scores.json"}


def _archive_path(archive_dir: str | Path) -> Path:
    return Path(archive_dir).resolve()


def lineage_file(archive_dir: str | Path) -> Path:
    return _archive_path(archive_dir) / "lineage.jsonl"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return default


def current_variant_id(archive_dir: str | Path, lane: str | None = None) -> str | None:
    manifest = load_current_manifest(archive_dir)
    if isinstance(manifest, dict):
        target_lane = (lane or "core").strip().lower()
        variant_id = str(manifest.get(target_lane) or "").strip()
        return variant_id or None
    return None


def load_lineage_history(archive_dir: str | Path) -> list[dict[str, Any]]:
    path = lineage_file(archive_dir)
    if not path.exists():
        return []
    entries: list[dict[str, Any]] = []
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and payload.get("id"):
            entries.append(payload)
    return entries


def load_latest_lineage(archive_dir: str | Path) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for entry in load_lineage_history(archive_dir):
        latest[str(entry["id"])] = entry
    return latest


def ordered_latest_entries(archive_dir: str | Path) -> list[dict[str, Any]]:
    entries = list(load_latest_lineage(archive_dir).values())
    return sorted(entries, key=lambda entry: (str(entry.get("timestamp") or ""), str(entry.get("id") or "")))


def append_lineage_entries(archive_dir: str | Path, entries: list[dict[str, Any]]) -> None:
    path = lineage_file(archive_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        for entry in entries:
            handle.write(json.dumps(entry, sort_keys=False) + "\n")


def append_lineage_entry(archive_dir: str | Path, entry: dict[str, Any]) -> None:
    append_lineage_entries(archive_dir, [entry])


def _is_ignored(path: Path) -> bool:
    if path.name in IGNORED_FILES:
        return True
    if any(part in IGNORED_DIRS for part in path.parts):
        return True
    if path.suffix in {".pyc", ".tmp", ".log"}:
        return True
    return False


def _variant_file_map(variant_dir: Path) -> dict[str, Path]:
    files: dict[str, Path] = {}
    for path in sorted(variant_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(variant_dir)
        if _is_ignored(rel):
            continue
        files[str(rel)] = path
    return files


def _read_text_lines(path: Path) -> list[str]:
    try:
        return path.read_text().splitlines()
    except UnicodeDecodeError:
        return []


def _diffstat_for_pair(old_path: Path | None, new_path: Path | None) -> tuple[int, int]:
    if old_path is None and new_path is None:
        return 0, 0
    if old_path is None:
        return len(_read_text_lines(new_path)), 0
    if new_path is None:
        return 0, len(_read_text_lines(old_path))
    before = _read_text_lines(old_path)
    after = _read_text_lines(new_path)
    insertions = 0
    deletions = 0
    for line in difflib.ndiff(before, after):
        if line.startswith("+ "):
            insertions += 1
        elif line.startswith("- "):
            deletions += 1
    return insertions, deletions


def summarize_variant_diff(
    archive_dir: str | Path,
    variant_id: str,
    parent_id: str | None,
) -> tuple[list[str], dict[str, int]]:
    if not parent_id:
        return [], {"insertions": 0, "deletions": 0}
    archive_root = _archive_path(archive_dir)
    parent_dir = archive_root / parent_id
    variant_dir = archive_root / variant_id
    if not parent_dir.is_dir() or not variant_dir.is_dir():
        return [], {"insertions": 0, "deletions": 0}

    parent_files = _variant_file_map(parent_dir)
    variant_files = _variant_file_map(variant_dir)
    changed_files = sorted(set(parent_files) | set(variant_files))
    changed_files = [
        rel_path
        for rel_path in changed_files
        if parent_files.get(rel_path) is None
        or variant_files.get(rel_path) is None
        or parent_files[rel_path].read_bytes() != variant_files[rel_path].read_bytes()
    ]

    insertions = 0
    deletions = 0
    for rel_path in changed_files:
        added, removed = _diffstat_for_pair(parent_files.get(rel_path), variant_files.get(rel_path))
        insertions += added
        deletions += removed
    return changed_files, {"insertions": insertions, "deletions": deletions}


def traces_for_variant(archive_dir: str | Path, variant_id: str) -> list[str]:
    variant_dir = _archive_path(archive_dir) / variant_id
    traces: list[str] = []
    meta_log = variant_dir / "meta-session.log"
    if meta_log.exists():
        traces.append("meta-session.log")
    for path in sorted((variant_dir / "sessions").rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(variant_dir)
        if rel.name in {"results.jsonl", "session_summary.json", "eval_feedback.json"}:
            traces.append(str(rel))
    metrics_dir = variant_dir / "metrics"
    if metrics_dir.exists():
        for path in sorted(metrics_dir.glob("*.jsonl")):
            traces.append(str(path.relative_to(variant_dir)))
    return traces


def prepare_meta_workspace(
    archive_dir: str | Path,
    variant_id: str,
    workspace_root: str | Path,
    lane: str | None = None,
) -> tuple[Path, Path]:
    """Create a sanitized proposer-visible archive snapshot for one variant."""
    archive_root = _archive_path(archive_dir)
    workspace_root = Path(workspace_root).resolve()
    visible_root = workspace_root / "archive"
    visible_root.mkdir(parents=True, exist_ok=True)

    for filename in ("index.json", "frontier.json"):
        source = archive_root / filename
        if source.exists():
            shutil.copy2(source, visible_root / filename)

    for entry in ordered_latest_entries(archive_root):
        entry_variant_id = str(entry.get("id") or "")
        if not entry_variant_id:
            continue
        source_dir = archive_root / entry_variant_id
        if not source_dir.is_dir():
            continue
        shutil.copytree(source_dir, visible_root / entry_variant_id, dirs_exist_ok=True)

    requested_variant_dir = archive_root / variant_id
    if requested_variant_dir.is_dir():
        shutil.copytree(requested_variant_dir, visible_root / variant_id, dirs_exist_ok=True)

    # Defense-in-depth (Unit 13, R21): remove any harness/ directory that
    # might have made it into the workspace.  The proposer must never see
    # harness files — the frozen evaluator templates live there.
    _harness_in_workspace = workspace_root / "harness"
    if _harness_in_workspace.is_dir():
        shutil.rmtree(_harness_in_workspace)

    variant_workspace = visible_root / variant_id
    if not variant_workspace.is_dir():
        raise FileNotFoundError(f"Variant workspace was not created for {variant_id}")
    if lane is not None:
        for rel_path, path in list(_variant_file_map(variant_workspace).items()):
            if rel_path in LANE_WORKSPACE_KEEP_FILES:
                continue
            if path_owned_by_lane(rel_path, lane):
                continue
            path.unlink(missing_ok=True)
            parent = path.parent
            while parent != variant_workspace and parent.exists() and not any(parent.iterdir()):
                parent.rmdir()
                parent = parent.parent
    return visible_root, variant_workspace


def sync_variant_workspace(
    source_variant_dir: str | Path,
    target_variant_dir: str | Path,
    lane: str | None = None,
) -> None:
    """Sync editable variant files back from a sanitized proposer workspace."""
    source_variant_dir = Path(source_variant_dir).resolve()
    target_variant_dir = Path(target_variant_dir).resolve()
    target_variant_dir.mkdir(parents=True, exist_ok=True)

    source_files = _variant_file_map(source_variant_dir)
    target_files = _variant_file_map(target_variant_dir)
    if lane is not None:
        source_files = {
            rel_path: path
            for rel_path, path in source_files.items()
            if path_owned_by_lane(rel_path, lane)
        }
        target_files = {
            rel_path: path
            for rel_path, path in target_files.items()
            if path_owned_by_lane(rel_path, lane)
        }

    for rel_path in sorted(set(target_files) - set(source_files), reverse=True):
        target_path = target_variant_dir / rel_path
        target_path.unlink(missing_ok=True)
        parent = target_path.parent
        while parent != target_variant_dir and parent.exists() and not any(parent.iterdir()):
            parent.rmdir()
            parent = parent.parent

    for rel_path, source_path in source_files.items():
        target_path = target_variant_dir / rel_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)


def public_entry_summary(
    archive_dir: str | Path,
    entry: dict[str, Any],
) -> dict[str, Any]:
    variant_id = str(entry["id"])
    changed_files, diffstat = summarize_variant_diff(archive_dir, variant_id, entry.get("parent"))
    search_metrics = entry.get("search_metrics")
    composite = composite_score(entry)
    search_summary = {
        "composite": composite,
        "wall_time_seconds": None,
        # Inner-vs-outer correlation telemetry (R-#14, Unit 3). Surfaced as
        # observation for the no-caps premise revisit; index consumers can read
        # the delta without opening scores.json. None when the variant
        # predates the telemetry or produced no substantive phase rows.
        "mean_pass_rate_delta": None,
        "mean_inner_pass_rate": None,
        "mean_outer_pass_rate": None,
    }
    if isinstance(search_metrics, dict):
        search_summary.update(
            {
                "composite": search_metrics.get("composite", composite),
                "wall_time_seconds": search_metrics.get("wall_time_seconds"),
                "mean_pass_rate_delta": search_metrics.get("mean_pass_rate_delta"),
                "mean_inner_pass_rate": search_metrics.get("mean_inner_pass_rate"),
                "mean_outer_pass_rate": search_metrics.get("mean_outer_pass_rate"),
            }
        )

    return {
        "variant_id": variant_id,
        "lane": entry.get("lane"),
        "parent": entry.get("parent"),
        "created_at": entry.get("timestamp"),
        "meta_backend": entry.get("backend"),
        "meta_model": entry.get("model"),
        "eval_target": entry.get("eval_target"),
        "search_suite_id": search_metrics.get("suite_id") if isinstance(search_metrics, dict) else None,
        "search_summary": search_summary,
        "changed_files": changed_files,
        "diffstat": diffstat,
        "artifacts": {
            "meta_session_log": "meta-session.log" if (_archive_path(archive_dir) / variant_id / "meta-session.log").exists() else None,
            "scores": "scores.json" if (_archive_path(archive_dir) / variant_id / "scores.json").exists() else None,
            "mutation_plan": "mutation_plan.json" if (_archive_path(archive_dir) / variant_id / "mutation_plan.json").exists() else None,
            "traces": traces_for_variant(archive_dir, variant_id),
        },
    }


def _summarize_lane_best(member: dict[str, Any]) -> dict[str, Any]:
    search_metrics = member.get("search_metrics") if isinstance(member.get("search_metrics"), dict) else {}
    return {
        "id": member.get("id"),
        "lane": entry_lane(member),
        "parent": member.get("parent"),
        "timestamp": member.get("timestamp"),
        "search_suite_id": search_metrics.get("suite_id"),
        "composite": composite_score(member),
        "objective_score": objective_score(member),
        "wall_time_seconds": search_metrics.get("wall_time_seconds"),
        "domains": {domain: domain_score(member, domain) for domain in DOMAINS},
    }


def refresh_archive_outputs(
    archive_dir: str | Path,
    suite_manifest: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    archive_root = _archive_path(archive_dir)
    entries = ordered_latest_entries(archive_root)
    frontier_payload = None

    if suite_manifest is not None and entries:
        suite_id = None
        if isinstance(suite_manifest, dict):
            raw_suite_id = suite_manifest.get("suite_id")
            if isinstance(raw_suite_id, str) and raw_suite_id:
                suite_id = raw_suite_id

        # Phase 2 (Unit 4 + Unit 5): per-lane single-best replaces the
        # 3-objective Pareto snapshot.
        lane_bests: dict[str, dict[str, Any] | None] = {}
        for lane in LANES:
            best = best_variant_in_lane(entries, lane, suite_id=suite_id)
            lane_bests[lane] = _summarize_lane_best(best) if best else None

        frontier_payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "variant_count": len(entries),
            "lanes": lane_bests,
        }
        (archive_root / "frontier.json").write_text(json.dumps(frontier_payload, indent=2) + "\n")

    index_variants = [public_entry_summary(archive_root, entry) for entry in entries]

    index_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "variant_count": len(entries),
        "variants": index_variants,
    }
    (archive_root / "index.json").write_text(json.dumps(index_payload, indent=2) + "\n")
    return entries, frontier_payload


def entries_by_status(archive_dir: str | Path, status: str) -> list[dict[str, Any]]:
    """Return lineage entries whose ``status`` field matches *status*."""
    return [
        entry
        for entry in ordered_latest_entries(archive_dir)
        if str(entry.get("status", "")).strip().lower() == status.strip().lower()
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh public autoresearch archive indexes.")
    parser.add_argument("archive_dir", help="Path to the archive directory.")
    parser.add_argument(
        "--suite-manifest",
        help="Optional search suite manifest used to refresh frontier membership.",
    )
    args = parser.parse_args()

    suite_manifest = load_json(Path(args.suite_manifest), default=None) if args.suite_manifest else None
    refresh_archive_outputs(args.archive_dir, suite_manifest=suite_manifest)


if __name__ == "__main__":
    main()
