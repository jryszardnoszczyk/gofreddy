"""autoresearch_v2/tools/inspect.py — read-only inspector for v2 substrate.

Reimplements the `freddy autoresearch <cmd>` inspect surface against
`autoresearch_v2/lanes/<lane>/results.tsv` + git, replacing v1's
`autoresearch/archive_cli.py` (which read 5 separate JSON indices).

Subcommands (preserved from v1's shape, JSON output by default):

    frontier              # top composite per lane (1 row per lane)
    topk <lane> --k N     # top N composites for a lane
    show <commit>         # git show + matching TSV row
    diff <a> <b> [--lane] # git diff a..b -- lanes/<lane>.md
    regressions <lane>    # flag chronological composite drops > threshold
    traces <commit>       # list per-attempt session deliverable paths
    failures              # tail of alerts.jsonl filtered by severity=high

The CLI is callable directly OR registered into the freddy Typer subapp (U13).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

VALID_LANES = (
    "geo",
    "competitive",
    "monitoring",
    "storyboard",
    "marketing_audit",
    "x_engine",
    "linkedin_engine",
)
TSV_COLUMNS = (
    "timestamp",
    "commit",
    "composite",
    "wall_time_s",
    "status",
    "description",
    "asi_json",
)


def _repo_root() -> Path:
    override = os.environ.get("AUTORESEARCH_V2_ROOT")
    if override:
        return Path(override).resolve()
    return Path(__file__).resolve().parent.parent.parent


def _tsv_path(lane: str) -> Path:
    return _repo_root() / "autoresearch_v2" / "lanes" / lane / "results.tsv"


def _alerts_path() -> Path:
    return _repo_root() / "autoresearch_v2" / "alerts.jsonl"


def _attempts_dir(lane: str) -> Path:
    return _repo_root() / "autoresearch_v2" / "lanes" / lane / "attempts"


def read_tsv(lane: str) -> list[dict]:
    """Return all rows from a lane's results.tsv (chronological order)."""
    path = _tsv_path(lane)
    if not path.is_file():
        return []
    rows: list[dict] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        return []
    header = lines[0].split("\t")
    for line in lines[1:]:
        if not line.strip():
            continue
        cells = line.split("\t")
        cells = cells + [""] * (len(header) - len(cells))
        row = dict(zip(header, cells, strict=False))
        row["composite_float"] = _to_float(row.get("composite", ""))
        rows.append(row)
    return rows


def _to_float(s: str) -> float | None:
    s = (s or "").strip()
    if not s:
        return None
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def cmd_frontier(args) -> int:
    out = []
    for lane in VALID_LANES:
        rows = [r for r in read_tsv(lane) if r["status"] == "keep" and r["composite_float"] is not None]
        if not rows:
            out.append({"lane": lane, "rows": 0, "top": None})
            continue
        top = max(rows, key=lambda r: r["composite_float"])
        out.append({
            "lane": lane,
            "rows": len(rows),
            "top": {
                "commit": top["commit"],
                "composite": top["composite_float"],
                "timestamp": top["timestamp"],
                "description": top["description"],
            },
        })
    print(json.dumps(out, indent=2))
    return 0


def cmd_topk(args) -> int:
    lane = args.lane
    if lane not in VALID_LANES:
        sys.stderr.write(f"inspect topk: unknown lane {lane!r}\n")
        return 2
    rows = read_tsv(lane)
    if not rows:
        print("(no rows)")
        return 0
    keep_rows = [r for r in rows if r["status"] == "keep" and r["composite_float"] is not None]
    sorted_rows = sorted(keep_rows, key=lambda r: r["composite_float"], reverse=True)[: args.k]
    out = [
        {
            "commit": r["commit"],
            "composite": r["composite_float"],
            "timestamp": r["timestamp"],
            "wall_time_s": r["wall_time_s"],
            "description": r["description"],
        }
        for r in sorted_rows
    ]
    print(json.dumps(out, indent=2))
    return 0


def cmd_show(args) -> int:
    commit = args.commit
    matching: list[dict] = []
    for lane in VALID_LANES:
        for row in read_tsv(lane):
            if row.get("commit", "").startswith(commit) or commit.startswith(row.get("commit", "")):
                matching.append({"lane": lane, **row})

    show_proc = subprocess.run(
        ["git", "show", "--stat", "--format=fuller", commit],
        cwd=_repo_root(),
        capture_output=True,
        text=True,
        check=False,
    )
    git_summary = show_proc.stdout or show_proc.stderr or ""

    out = {
        "commit": commit,
        "tsv_rows": matching,
        "git_show": git_summary.strip().splitlines()[:30],  # cap to 30 lines so output stays terse
    }
    print(json.dumps(out, indent=2))
    return 0 if matching or show_proc.returncode == 0 else 2


def cmd_diff(args) -> int:
    paths: list[str] = []
    if args.lane:
        paths = ["--", f"autoresearch_v2/lanes/{args.lane}.md"]
    proc = subprocess.run(
        ["git", "diff", f"{args.left}..{args.right}", *paths],
        cwd=_repo_root(),
        capture_output=True,
        text=True,
        check=False,
    )
    sys.stdout.write(proc.stdout)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
    return proc.returncode


def cmd_regressions(args) -> int:
    lane = args.lane
    if lane not in VALID_LANES:
        sys.stderr.write(f"inspect regressions: unknown lane {lane!r}\n")
        return 2
    rows = [r for r in read_tsv(lane) if r["status"] == "keep" and r["composite_float"] is not None]
    if len(rows) < 3:
        print("(need >=3 keep rows for trend)")
        return 0
    threshold = args.threshold
    regressions = []
    prev: dict | None = None
    for row in rows:
        if prev is not None and prev["composite_float"] > 0:
            drop_pct = (prev["composite_float"] - row["composite_float"]) / prev["composite_float"]
            if drop_pct >= threshold:
                regressions.append({
                    "from_commit": prev["commit"],
                    "from_composite": prev["composite_float"],
                    "to_commit": row["commit"],
                    "to_composite": row["composite_float"],
                    "drop_pct": round(drop_pct * 100, 2),
                    "timestamp": row["timestamp"],
                })
        prev = row
    print(json.dumps({"lane": lane, "threshold_pct": threshold * 100, "regressions": regressions}, indent=2))
    return 0


def cmd_traces(args) -> int:
    commit = args.commit
    found: list[str] = []
    root = _repo_root() / "autoresearch_v2" / "lanes"
    if root.is_dir():
        for lane_dir in root.iterdir():
            attempts = lane_dir / "attempts"
            if not attempts.is_dir():
                continue
            for sub in attempts.iterdir():
                if sub.is_dir() and sub.name.startswith(commit):
                    sessions = sub / "sessions"
                    if sessions.is_dir():
                        found.extend(str(p.relative_to(_repo_root())) for p in sessions.glob("*"))
                    else:
                        found.append(str(sub.relative_to(_repo_root())))
    print(json.dumps({"commit": commit, "paths": found}, indent=2))
    return 0


def cmd_failures(args) -> int:
    path = _alerts_path()
    if not path.is_file():
        print(json.dumps([], indent=2))
        return 0
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("severity") == args.severity:
            rows.append(row)
    rows = rows[-args.tail :]
    print(json.dumps(rows, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="freddy-autoresearch-inspect",
        description="Inspect autoresearch_v2 state (read-only).",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("frontier", help="Top composite per lane")

    pt = sub.add_parser("topk", help="Top N composites for a lane")
    pt.add_argument("lane")
    pt.add_argument("--k", type=int, default=5)

    ps = sub.add_parser("show", help="git show + matching TSV row(s) for a commit")
    ps.add_argument("commit")

    pd = sub.add_parser("diff", help="git diff between two commits, optionally scoped to a lane")
    pd.add_argument("left")
    pd.add_argument("right")
    pd.add_argument("--lane", default=None, choices=VALID_LANES)

    pr = sub.add_parser("regressions", help="Flag chronological composite drops")
    pr.add_argument("lane")
    pr.add_argument("--threshold", type=float, default=0.20,
                    help="Fractional drop that counts as regression (default 0.20 = 20%%)")

    ptr = sub.add_parser("traces", help="List per-attempt session deliverable paths")
    ptr.add_argument("commit")

    pf = sub.add_parser("failures", help="Tail of alerts.jsonl filtered by severity")
    pf.add_argument("--severity", default="high", choices=["low", "medium", "high"])
    pf.add_argument("--tail", type=int, default=20)

    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    dispatch = {
        "frontier": cmd_frontier,
        "topk": cmd_topk,
        "show": cmd_show,
        "diff": cmd_diff,
        "regressions": cmd_regressions,
        "traces": cmd_traces,
        "failures": cmd_failures,
    }
    return dispatch[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
