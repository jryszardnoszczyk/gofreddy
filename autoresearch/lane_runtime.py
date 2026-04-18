from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Iterable

import lane_paths


LANES = ("core", "geo", "competitive", "monitoring", "storyboard")
CURRENT_MANIFEST = "current.json"
MATERIALIZED_DIRNAME = "current_runtime"
PROTECTED_RUNTIME_DIRS = {"sessions", "metrics", "runs", "__pycache__", "archived_sessions"}
PROTECTED_RUNTIME_FILES = {"scores.json", "meta-session.log", "mutation_plan.json"}


def archive_path(archive_dir: str | Path) -> Path:
    return Path(archive_dir).resolve()


def current_manifest_path(archive_dir: str | Path) -> Path:
    return archive_path(archive_dir) / CURRENT_MANIFEST


def materialized_runtime_dir(archive_dir: str | Path) -> Path:
    return archive_path(archive_dir) / MATERIALIZED_DIRNAME


def has_lane_manifest(archive_dir: str | Path) -> bool:
    return current_manifest_path(archive_dir).exists()


def load_current_manifest(archive_dir: str | Path) -> dict[str, str] | None:
    path = current_manifest_path(archive_dir)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return {lane: str(payload.get(lane, "")).strip() for lane in LANES}


def legacy_current_dir(archive_dir: str | Path) -> Path:
    current = archive_path(archive_dir) / "current"
    if current.is_symlink():
        return current.resolve()
    if current.is_dir():
        return current
    raise FileNotFoundError("Archive current runtime is not configured.")


def _resolve_lane_source_dir(archive_root: Path, lane: str, head_id: str) -> Path:
    if not head_id:
        raise FileNotFoundError(f"Missing current head for lane={lane}")
    top_level = archive_root / head_id
    if top_level.is_dir():
        return top_level
    raise FileNotFoundError(f"Lane head not found for {lane}: {head_id}")


def resolve_runtime_dir(archive_dir: str | Path) -> Path:
    if has_lane_manifest(archive_dir):
        return ensure_materialized_runtime(archive_dir)
    return legacy_current_dir(archive_dir)


def _is_protected_runtime_path(rel_path: Path) -> bool:
    if rel_path.name in PROTECTED_RUNTIME_FILES:
        return True
    return any(part in PROTECTED_RUNTIME_DIRS for part in rel_path.parts)


def _iter_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if path.is_file():
            yield path


def _sync_filtered(source_root: Path, target_root: Path, *, lane: str | None = None) -> None:
    source_files: dict[str, Path] = {}
    for path in _iter_files(source_root):
        rel = path.relative_to(source_root)
        if _is_protected_runtime_path(rel):
            continue
        if lane and not lane_paths.path_owned_by_lane(rel, lane):
            continue
        source_files[rel.as_posix()] = path

    target_files: dict[str, Path] = {}
    for path in _iter_files(target_root):
        rel = path.relative_to(target_root)
        if _is_protected_runtime_path(rel):
            continue
        if lane and not lane_paths.path_owned_by_lane(rel, lane):
            continue
        target_files[rel.as_posix()] = path

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


def ensure_materialized_runtime(archive_dir: str | Path) -> Path:
    archive_root = archive_path(archive_dir)
    manifest = load_current_manifest(archive_root)
    if manifest is None:
        return legacy_current_dir(archive_root)

    runtime_dir = materialized_runtime_dir(archive_root)
    runtime_dir.mkdir(parents=True, exist_ok=True)

    legacy_dir = None
    current_link = archive_root / "current"
    if current_link.exists() and not current_link.samefile(runtime_dir):
        try:
            legacy_dir = legacy_current_dir(archive_root)
        except FileNotFoundError:
            legacy_dir = None

    if legacy_dir:
        for dirname in sorted(PROTECTED_RUNTIME_DIRS):
            source_dir = legacy_dir / dirname
            target_dir = runtime_dir / dirname
            if source_dir.exists() and not target_dir.exists():
                shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)

    core_id = manifest.get("core", "")
    if not core_id:
        raise FileNotFoundError("current.json is missing core head.")
    core_dir = _resolve_lane_source_dir(archive_root, "core", core_id)
    _sync_filtered(core_dir, runtime_dir)

    for lane in lane_paths.WORKFLOW_LANES:
        lane_id = manifest.get(lane, "")
        if not lane_id:
            continue
        lane_dir = _resolve_lane_source_dir(archive_root, lane, lane_id)
        _sync_filtered(lane_dir, runtime_dir, lane=lane)

    return runtime_dir


def write_current_manifest(archive_dir: str | Path, payload: dict[str, str]) -> Path:
    path = current_manifest_path(archive_dir)
    path.write_text(json.dumps({lane: payload.get(lane, "") for lane in LANES}, indent=2) + "\n")
    return path


def _lineage_path(archive_root: Path) -> Path:
    return archive_root / "lineage.jsonl"


def _load_latest_lineage(archive_root: Path) -> dict[str, dict]:
    latest: dict[str, dict] = {}
    path = _lineage_path(archive_root)
    if not path.exists():
        return latest
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and payload.get("id"):
            latest[str(payload["id"])] = payload
    return latest


def _append_lineage_entries(archive_root: Path, entries: list[dict]) -> None:
    path = _lineage_path(archive_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        for entry in entries:
            handle.write(json.dumps(entry) + "\n")


def initialize_current_heads(archive_dir: str | Path) -> dict[str, str]:
    archive_root = archive_path(archive_dir)
    existing = load_current_manifest(archive_root)
    if existing is not None:
        return existing

    legacy_dir = legacy_current_dir(archive_root)
    legacy_id = legacy_dir.name
    latest = _load_latest_lineage(archive_root)
    template_entry = dict(latest.get(legacy_id) or {})
    timestamp = template_entry.get("promoted_at") or template_entry.get("timestamp") or ""

    manifest: dict[str, str] = {lane: "" for lane in LANES}
    for lane in LANES:
        manifest[lane] = legacy_id

    lineage_updates: list[dict] = []
    if template_entry:
        core_entry = dict(template_entry)
        core_entry["lane"] = "core"
        if timestamp:
            core_entry["promoted_at"] = timestamp
        lineage_updates.append(core_entry)

    if lineage_updates:
        _append_lineage_entries(archive_root, lineage_updates)
    write_current_manifest(archive_root, manifest)
    return manifest


def set_current_head(archive_dir: str | Path, lane: str, variant_id: str) -> dict[str, str]:
    lane = lane.strip().lower()
    manifest = initialize_current_heads(archive_dir)
    manifest[lane] = variant_id
    write_current_manifest(archive_dir, manifest)
    return manifest


def main() -> None:
    archive_dir = os.environ.get("ARCHIVE_DIR")
    if not archive_dir:
        raise SystemExit("ARCHIVE_DIR is required")
    print(ensure_materialized_runtime(archive_dir))


if __name__ == "__main__":
    main()
