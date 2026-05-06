"""One-off: bootstrap state.db from cached /tmp/x-recon/user_*.json files.

Used during dev to test the pipeline without burning twitterapi.io credits.
Production runs use pipeline/pull.py (which hits the live API).
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

# Ensure we can import x_engine when run as a script
sys.path.insert(0, str(Path(__file__).parent.parent))

from x_engine.pipeline.db import init_db
from x_engine.pipeline.pull import upsert_tweets


def main() -> int:
    init_db()
    cache_dir = Path("/tmp/x-recon")
    files = sorted(cache_dir.glob("user_*.json"))
    if not files:
        print(f"No cache at {cache_dir}", file=sys.stderr)
        return 1
    total = 0
    for f in files:
        username = f.stem.replace("user_", "")
        try:
            data = json.loads(f.read_text())
        except json.JSONDecodeError:
            continue
        tweets = (data.get("data", {}) or {}).get("tweets") or data.get("tweets") or []
        # Filter out RTs
        clean = [t for t in tweets if not (t.get("text") or "").startswith("RT @")]
        n = upsert_tweets(clean, username)
        total += n
        print(f"  @{username}: {len(clean)} clean, {n} new")
    print(f"\nTotal inserted: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
