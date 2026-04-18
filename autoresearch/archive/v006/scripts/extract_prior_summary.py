#!/usr/bin/env python3
"""Extract prior brief summary for next session's versioning.

Reads brief.md and extracts key metrics to prior_brief_summary.json.
The next session reads this for real "Changes vs Prior" deltas.

Usage:
    python3 scripts/extract_prior_summary.py <session_dir> <client>
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def extract(session_dir: str, client: str) -> None:
    brief_path = Path(session_dir) / "brief.md"
    if not brief_path.exists():
        return

    brief = brief_path.read_text()
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "client": client,
        "word_count": len(brief.split()),
        "sections": [m.group(1) for m in re.finditer(r"^## (.+)", brief, re.MULTILINE)],
    }

    # Extract SOV percentages
    sov_matches = re.findall(r"(\w[\w\s]+?):\s*~?(\d+(?:\.\d+)?)\s*%", brief)
    if sov_matches:
        summary["sov_snapshot"] = {name.strip(): float(pct) for name, pct in sov_matches[:10]}

    # Extract recommendation count
    recs = re.findall(r"^\d+\.", brief, re.MULTILINE)
    summary["recommendation_count"] = len(recs)

    output_path = Path(session_dir) / "prior_brief_summary.json"
    tmp = output_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(summary, indent=2) + "\n")
    tmp.rename(output_path)
    print(f"Written: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <session_dir> <client>", file=sys.stderr)
        sys.exit(1)
    extract(sys.argv[1], sys.argv[2])
