#!/usr/bin/env python3
"""Operator script — freeze the marketing_audit lane's manifest.

JR runs this **after** authoring + reviewing the MA-1..MA-8 rubric
prompts + 8 judge prompts + Stage 1b/1c/2/3/4 stage prompts (master
plan §6.4 + human-prereqs §2). The script computes whole-file SHA256
hashes for every prompt under the lane's manifest scope and writes
them to ``marketing_audit_manifest.json`` at repo root.

After freeze, ``custom_validate`` (wired in
``autoresearch/lane_registry.LANES["marketing_audit"]``) re-verifies
the manifest on every variant scoring; drift fails the variant.

Whole-file SHA256 freeze is the v1 strategy per master plan §6.6.
The ``[STABLE]`` / ``[EVOLVABLE]`` section-marker pattern is deferred
to v2 — v1 freezes whole files.

Usage::

    python -m autoresearch.scripts.regen_marketing_audit_manifest

Idempotent: re-running with the same prompt files produces the same
manifest. Operator workflow: edit prompts → regen → verify drift via
``custom_validate`` → commit both prompts + manifest in one commit.

L1 status: this script ships now so the operator workflow is wired.
The manifest_paths list below is empty in L1 — the prompt files
don't exist yet (they're authored in Phase 1's parallel content
track per master plan §7.2). Running the script today writes an
empty ``{}`` manifest; running it post-content-authoring writes the
real freeze. The script's behavior + path is stable; only the input
files change.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Repo root is one level above this file's autoresearch/scripts/ package.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from autoresearch.lane_registry import compute_manifest


# ─── Manifest scope ──────────────────────────────────────────────────────
#
# Master plan §6.6 covers:
#   - All 8 MA-1..MA-8 rubric prompts
#       programs/marketing_audit/prompts/rubrics/MA-*.md
#   - 8 judge prompts
#       programs/marketing_audit/prompts/judges/MA-*-judge.md
#   - Stage prompts
#       programs/marketing_audit/prompts/stage_*.md
#
# In L1, none of these files exist on disk yet — Phase 1 parallel
# content authoring lands them. The lookup below uses glob patterns
# so the freeze captures whatever set is present at the time the
# operator runs the script (after JR review).
_MANIFEST_GLOBS: tuple[str, ...] = (
    "programs/marketing_audit/prompts/rubrics/MA-*.md",
    "programs/marketing_audit/prompts/judges/MA-*-judge.md",
    "programs/marketing_audit/prompts/stage_*.md",
)

_MANIFEST_OUT = _REPO_ROOT / "marketing_audit_manifest.json"


def collect_manifest_paths(repo_root: Path) -> list[Path]:
    """Return all on-disk paths matching the lane's manifest globs.

    Sorted for deterministic ordering — important so two operators
    on different machines produce bit-identical manifests for the
    same content.
    """
    found: list[Path] = []
    for pattern in _MANIFEST_GLOBS:
        found.extend(repo_root.glob(pattern))
    return sorted(set(found))


def regen(repo_root: Path, out_path: Path) -> int:
    """Compute the manifest and write it to ``out_path``. Returns the
    count of files hashed. Idempotent."""
    paths = collect_manifest_paths(repo_root)
    manifest = compute_manifest(paths, repo_root) if paths else {}
    out_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return len(manifest)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=_REPO_ROOT,
        help="Repo root (default: %(default)s).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=_MANIFEST_OUT,
        help="Manifest output path (default: %(default)s).",
    )
    args = parser.parse_args()

    count = regen(args.repo_root, args.out)
    if count == 0:
        print(
            "no marketing_audit prompt files found — wrote empty "
            f"manifest to {args.out} (run again after Phase 1 content "
            "authoring lands the rubric/judge/stage prompts).",
            file=sys.stderr,
        )
    else:
        print(f"froze {count} marketing_audit prompt file(s) in {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
