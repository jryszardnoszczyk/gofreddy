#!/usr/bin/env python3
"""Audit fixer-written verdicts against actual git state on the staging branch.

Spot-checks internal consistency between what the fixers self-reported
(`run_dir/verdicts/<track>/<id>.yaml`) and what's actually on the staging
branch. Flags four classes of inconsistency:

  - **claimed-passed-but-missing** — verdict says `passed` but no
    `harness: fix <id>` commit exists on the staging branch.
  - **claimed-passed-but-reverted** — verdict says `passed` and the
    original commit landed, but a `Revert "harness: fix <id>"` is also
    present (someone manually reverted, or revert-phase ran on a stale
    failed verdict — see commit 54ade91).
  - **claimed-failed-but-not-reverted** — verdict says `failed` and
    the commit landed but was not reverted (reverter crashed, or the
    failed verdict was written after revert-phase).
  - **no-verdict-but-shipped** — a `harness: fix <id>` commit exists
    on the branch with no verdict YAML at all.

Usage:
    python scripts/harness_verdict_audit.py --run-dir harness/runs/run-<ts>

Exit code 0 when no inconsistencies, 1 otherwise (so this can later
gate CI on harness output sanity).
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

# Ensure repo root is importable when invoked as `python scripts/...`.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from harness.engine import Verdict  # noqa: E402


_FIX_COMMIT_RE = re.compile(r"^harness: fix (\S+?)@c\d+ —")
_REVERT_RE = re.compile(r'^Revert "harness: fix (\S+?)@c\d+')


def _branch_for_run_dir(run_dir: Path) -> str:
    """Mirror harness/run.py:_run_dir_for_branch in reverse."""
    name = run_dir.name  # "run-<ts>"
    if not name.startswith("run-"):
        raise SystemExit(f"unexpected run_dir layout: {run_dir} (expected name 'run-<ts>')")
    ts = name.removeprefix("run-")
    return f"harness/run-{ts}"


def _git_log_subjects(branch: str) -> list[str]:
    """Subjects of every commit on the branch since main, oldest first."""
    try:
        out = subprocess.check_output(
            ["git", "log", f"main..{branch}", "--format=%s"],
            text=True, stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as exc:
        raise SystemExit(
            f"could not read git log for {branch}: {exc.stderr.strip()}"
        ) from exc
    return [line for line in out.splitlines() if line.strip()]


def _index_branch_state(subjects: list[str]) -> tuple[set[str], set[str]]:
    """Return (set of fix-finding-ids landed, set of finding-ids reverted)."""
    landed: set[str] = set()
    reverted: set[str] = set()
    for s in subjects:
        if (m := _FIX_COMMIT_RE.match(s)):
            landed.add(m.group(1))
        elif (m := _REVERT_RE.match(s)):
            reverted.add(m.group(1))
    return landed, reverted


def _iter_verdict_paths(run_dir: Path):
    verdicts_dir = run_dir / "verdicts"
    if not verdicts_dir.is_dir():
        return
    for path in sorted(verdicts_dir.rglob("*.yaml")):
        if path.is_file():
            yield path


def audit(run_dir: Path) -> dict[str, list[tuple[str, str]]]:
    """Return inconsistencies grouped by category. Each entry is (finding_id, detail)."""
    branch = _branch_for_run_dir(run_dir)
    subjects = _git_log_subjects(branch)
    landed, reverted = _index_branch_state(subjects)

    inconsistencies: dict[str, list[tuple[str, str]]] = defaultdict(list)
    seen_ids: set[str] = set()

    for vp in _iter_verdict_paths(run_dir):
        finding_id = vp.stem  # "F-a-1"
        seen_ids.add(finding_id)
        verdict = Verdict.parse(vp)
        is_landed = finding_id in landed
        is_reverted = finding_id in reverted

        if verdict.verified:
            if not is_landed:
                inconsistencies["claimed-passed-but-missing"].append(
                    (finding_id, f"verdict 'passed' but no fix commit on {branch}"),
                )
            elif is_reverted:
                inconsistencies["claimed-passed-but-reverted"].append(
                    (finding_id,
                     f"verdict 'passed' but commit was reverted ({verdict.reason[:80]!r})"),
                )
        else:  # verdict 'failed'
            if is_landed and not is_reverted:
                inconsistencies["claimed-failed-but-not-reverted"].append(
                    (finding_id,
                     f"verdict 'failed' ({verdict.reason[:80]!r}) but commit not reverted"),
                )

    # Commits with no verdict YAML at all.
    for fid in landed:
        if fid not in seen_ids:
            inconsistencies["no-verdict-but-shipped"].append(
                (fid, "commit on branch with no verdict YAML"),
            )

    return inconsistencies


def _format_report(run_dir: Path, results: dict[str, list[tuple[str, str]]]) -> str:
    if not results:
        return f"verdict audit for {run_dir.name}: clean — no inconsistencies\n"
    lines = [f"verdict audit for {run_dir.name}: {sum(len(v) for v in results.values())} inconsistencies\n"]
    for category in (
        "claimed-passed-but-missing",
        "claimed-passed-but-reverted",
        "claimed-failed-but-not-reverted",
        "no-verdict-but-shipped",
    ):
        entries = results.get(category, [])
        if not entries:
            continue
        lines.append(f"\n## {category} ({len(entries)})")
        for fid, detail in entries:
            lines.append(f"  - {fid}: {detail}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="harness_verdict_audit",
        description=__doc__.split("\n\n")[0],
    )
    parser.add_argument(
        "--run-dir", required=True, type=Path,
        help="Path to a harness run dir (e.g., harness/runs/run-20260429-104632).",
    )
    args = parser.parse_args(argv)

    if not args.run_dir.is_dir():
        print(f"run-dir not found: {args.run_dir}", file=sys.stderr)
        return 2

    results = audit(args.run_dir)
    sys.stdout.write(_format_report(args.run_dir, results))
    return 1 if results else 0


if __name__ == "__main__":
    raise SystemExit(main())
