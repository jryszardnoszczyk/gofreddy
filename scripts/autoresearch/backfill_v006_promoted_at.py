#!/usr/bin/env python3
"""One-shot backfill: append a v006 lineage entry with promoted_at set.

Pre-fix the lineage had 49 entries but zero with non-null promoted_at —
v006 was promoted in production but mark_promoted was never called against
it. This breaks previous_promoted_variant + the phase4-migration-check
rollback path.

Idempotent: refuses to append if a v006 entry already has promoted_at set.
Run once after the Unit 2 predicate fix lands.

  python3 scripts/autoresearch/backfill_v006_promoted_at.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

LINEAGE = Path(__file__).resolve().parents[2] / "autoresearch" / "archive" / "lineage.jsonl"
PROMOTED_AT_SENTINEL = "2026-04-18T13:58:06+02:00"  # freddy import commit


def main() -> int:
    if not LINEAGE.exists():
        print(f"ERROR: lineage not found at {LINEAGE}", file=sys.stderr)
        return 1

    entries = [
        json.loads(line) for line in LINEAGE.read_text().splitlines() if line.strip()
    ]

    already_promoted = [
        e for e in entries
        if e.get("id") == "v006" and e.get("promoted_at")
    ]
    if already_promoted:
        print(
            f"v006 already has {len(already_promoted)} promoted_at entries — refusing to backfill again",
            file=sys.stderr,
        )
        return 0

    v006_entries = [e for e in entries if e.get("id") == "v006"]
    if not v006_entries:
        print("ERROR: no v006 entries in lineage", file=sys.stderr)
        return 1

    # Use the latest entry (last write wins under load_latest_lineage's
    # dedup-by-id) as the canonical row to copy.
    latest_v006 = v006_entries[-1]
    new_entry = dict(latest_v006)
    new_entry["promoted_at"] = PROMOTED_AT_SENTINEL

    with LINEAGE.open("a") as fh:
        fh.write(json.dumps(new_entry) + "\n")

    print(f"Appended v006 entry with promoted_at={PROMOTED_AT_SENTINEL}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
