#!/usr/bin/env python3
"""One-shot backfill: write `critique_manifest.json` (grace mode) into
every existing variant under `autoresearch/archive/v*/`.

Why grace
---------
R-#13 introduces the SHA256 manifest gate at Layer 1. Variants that
already exist on disk pre-date the gate and have no clone-time
manifest. Without backfill, every existing variant would fail L1 the
next time it's evaluated, which would freeze the loop. The grace
manifest lets L1 pass them through while still recording today's hashes
for forensic reference.

Explicit policy
---------------
This backfill does NOT attempt to detect retroactive tampering. If a
variant on disk was already malicious before R-#13 landed, the grace
sentinel says "we acknowledge we can't verify this one." All FRESH
clones written after R-#13 by `evolve.py` carry a strict (no-grace)
manifest, so the gate is fully active for everything new. Out of scope
for this script: cryptographic backdating defenses.

Usage
-----
Run from the repo root::

    python3 -m autoresearch.scripts.rebuild_manifests

The script is intentionally idempotent: re-running it on a variant that
already has a manifest preserves the existing file (whether grace or
strict) unless ``--force-grace`` is passed.

This script is a one-shot operation. Do NOT call it from normal test
or eval pathways — it has no place in the steady-state pipeline.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Repo root is one level above this file's `autoresearch/` package.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from autoresearch.critique_manifest import compute_expected_hashes


def _build_grace_manifest() -> dict[str, object]:
    payload: dict[str, object] = {"grace": True}
    payload.update(compute_expected_hashes())
    return payload


def backfill(archive_dir: Path, force_grace: bool = False) -> int:
    """Walk variant dirs under *archive_dir* and write a grace manifest
    into each that lacks one (or all of them, if *force_grace*).

    Returns the count of variants written.
    """
    if not archive_dir.is_dir():
        print(f"archive dir not found: {archive_dir}", file=sys.stderr)
        return 0

    written = 0
    payload = _build_grace_manifest()
    encoded = json.dumps(payload, indent=2, sort_keys=True)

    for entry in sorted(archive_dir.iterdir()):
        if not entry.is_dir():
            continue
        # Variant dirs are named like `v001`, `v042`, etc.
        if not (entry.name.startswith("v") and entry.name[1:].isdigit()):
            continue
        manifest_path = entry / "critique_manifest.json"
        if manifest_path.exists() and not force_grace:
            print(f"skip (manifest present): {entry.name}")
            continue
        manifest_path.write_text(encoded, encoding="utf-8")
        written += 1
        print(f"wrote grace manifest: {entry.name}")

    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--archive-dir",
        type=Path,
        default=_REPO_ROOT / "autoresearch" / "archive",
        help="Path to the autoresearch archive root (default: %(default)s).",
    )
    parser.add_argument(
        "--force-grace",
        action="store_true",
        help="Overwrite existing critique_manifest.json files with a grace "
        "manifest. Use with care — this discards strict manifests.",
    )
    args = parser.parse_args()
    written = backfill(args.archive_dir, force_grace=args.force_grace)
    print(f"backfill complete: {written} variant(s) updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
