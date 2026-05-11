"""autoresearch_v2/tools/log_experiment.py — record an experiment outcome.

Append a row to `autoresearch_v2/lanes/<lane>/results.tsv` and either git-commit
(`keep`) or git-reset (`discard|crash|checks_failed`). Replaces v1's
`lineage.jsonl` + 5 redundant indices + `evolve_ops.promote_atomic`.

The TSV is the single source of truth per lane. It is UNTRACKED by git (see
`autoresearch_v2/.gitignore`); `git reset --hard` doesn't touch it because
reset only operates on tracked files.

Status semantics:
- `keep`: working tree must be dirty. `git add -A && git commit -m "evolve(<lane>): <desc>"`.
  TSV row records the NEW commit short-sha.
- `discard | crash | checks_failed`: TSV row records the PRE-RESET HEAD short-sha
  (same as the parent sha we reset back to). Then `git reset --hard HEAD` reverts
  the lane prose edits. Multiple discards from the same parent share the same
  `commit` column value; `description` + `asi_json` differentiate them.

Usage:
    log_experiment --lane geo --status keep --composite 4.77 \\
        --wall-time-seconds 1234 --description "added X heuristic" \\
        --asi-json '{"selection_rationale":"top-1 parent v007"}'

    log_experiment --lane geo --status discard --description "X regressed" \\
        --asi-json '{"error":"composite dropped 7.8 -> 4.2"}'
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

TSV_COLUMNS = (
    "timestamp",
    "commit",
    "composite",
    "wall_time_s",
    "status",
    "description",
    "asi_json",
)
VALID_STATUSES = frozenset({"keep", "discard", "crash", "checks_failed"})


def _repo_root() -> Path:
    """Repo root. Overridable via `AUTORESEARCH_V2_ROOT` env var for tests."""
    override = os.environ.get("AUTORESEARCH_V2_ROOT")
    if override:
        return Path(override).resolve()
    return Path(__file__).resolve().parent.parent.parent


def _run(cmd, *, check: bool = True, capture: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=_repo_root(),
        check=check,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
        text=True,
    )


def _short_sha(ref: str = "HEAD") -> str:
    return _run(["git", "rev-parse", "--short", ref]).stdout.strip()


def _working_tree_has_changes() -> bool:
    return bool(_run(["git", "status", "--porcelain"]).stdout.strip())


def _tsv_path(lane: str) -> Path:
    return _repo_root() / "autoresearch_v2" / "lanes" / lane / "results.tsv"


def _ensure_tsv_header(path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        fh.write("\t".join(TSV_COLUMNS) + "\n")


def _tsv_escape(value) -> str:
    if value is None:
        return ""
    s = str(value)
    return s.replace("\t", " ").replace("\n", "\\n").replace("\r", "")


def _append_row(path: Path, row: dict) -> None:
    _ensure_tsv_header(path)
    with path.open("a", encoding="utf-8") as fh:
        fh.write("\t".join(_tsv_escape(row[c]) for c in TSV_COLUMNS) + "\n")


def log_experiment(
    *,
    lane: str,
    status: str,
    composite: float | None,
    wall_time_s: float | None,
    description: str,
    asi_json,
    dry_run: bool = False,
) -> dict:
    if status not in VALID_STATUSES:
        raise ValueError(f"status must be one of {sorted(VALID_STATUSES)}, got {status!r}")
    if not lane or "/" in lane or lane.startswith("."):
        raise ValueError(f"invalid lane name {lane!r}")

    asi_blob = asi_json if isinstance(asi_json, str) else json.dumps(asi_json or {}, separators=(",", ":"))

    if status == "keep":
        if not _working_tree_has_changes():
            raise RuntimeError("status=keep but working tree is clean; nothing to commit")
        if not dry_run:
            _run(["git", "add", "-A"])
            _run(["git", "commit", "-m", f"evolve({lane}): {description}"])
        commit_sha = _short_sha()
    else:
        commit_sha = _short_sha()
        if not dry_run:
            _run(["git", "reset", "--hard", "HEAD"])

    row = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "commit": commit_sha,
        "composite": "" if composite is None else f"{composite:.4f}",
        "wall_time_s": "" if wall_time_s is None else f"{wall_time_s:.1f}",
        "status": status,
        "description": description,
        "asi_json": asi_blob,
    }
    if not dry_run:
        _append_row(_tsv_path(lane), row)
    return row


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        description="Record an experiment outcome: git commit/reset + append results.tsv row.",
    )
    p.add_argument("--lane", required=True, help="Lane name (e.g. geo, competitive, monitoring)")
    p.add_argument("--status", required=True, choices=sorted(VALID_STATUSES))
    p.add_argument("--composite", type=float, default=None,
                   help="Composite score for this experiment (omit for crash)")
    p.add_argument("--wall-time-seconds", dest="wall_time_s", type=float, default=None)
    p.add_argument("--description", required=True, help="One-line description of the attempt")
    p.add_argument(
        "--asi-json",
        default="{}",
        help='Free-form JSON blob (rationale, error, etc.). Use "-" to read from stdin.',
    )
    p.add_argument("--dry-run", action="store_true",
                   help="Print the row that would be written; don't commit/reset/write")
    args = p.parse_args(argv)

    asi_json = args.asi_json
    if asi_json == "-":
        asi_json = sys.stdin.read()

    try:
        row = log_experiment(
            lane=args.lane,
            status=args.status,
            composite=args.composite,
            wall_time_s=args.wall_time_s,
            description=args.description,
            asi_json=asi_json,
            dry_run=args.dry_run,
        )
    except (ValueError, RuntimeError) as e:
        sys.stderr.write(f"log_experiment: error: {e}\n")
        return 2

    print(json.dumps(row, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
