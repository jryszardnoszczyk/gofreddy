"""Orchestrator. The only thing run.sh calls.

Phases:
1. Pull (twitterapi.io + GitHub releases + RSS)
2. Rank (resonance scores)
3. Topic pick (LLM → vault/YYYY-MM-DD.md)
4. Draft (writer + critic + revise → drafts/YYYY-MM-DD.md)
"""
from __future__ import annotations

import argparse
import concurrent.futures
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

from .db import init_db
from .draft import (
    draft_for_angle,
    load_voice_block,
    pick_top_drafts_for_today,
    write_drafts_file,
)
from .llm import LLM
from .pull import run_pull
from .rank import update_scores
from .topic_pick import pick_angles, save_angles_to_db, write_vault_file

X_ENGINE_DIR = Path(__file__).parent.parent
SOURCES_PATH = X_ENGINE_DIR / "sources.yaml"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="x_engine daily compose")
    parser.add_argument("--skip-pull", action="store_true", help="skip phase 1 (use cached state.db)")
    parser.add_argument("--skip-draft", action="store_true", help="skip phase 4 (only build vault)")
    parser.add_argument(
        "--angles-count", type=int, default=None, help="override sources.yaml limits.angles_per_run"
    )
    parser.add_argument(
        "--max-cost-usd", type=float, default=2.5, help="hard cap on LLM spend per run"
    )
    parser.add_argument(
        "--final-drafts", type=int, default=None, help="override sources.yaml limits.final_drafts_count"
    )
    parser.add_argument(
        "--max-workers", type=int, default=5,
        help="parallel codex sessions during drafting; 5 is conservative for ChatGPT plan rate limits",
    )
    args = parser.parse_args(argv)

    # load env from gofreddy/.env (one level up from x_engine/)
    load_dotenv(X_ENGINE_DIR.parent / ".env")
    twitterapi_key = os.environ.get("TWITTERAPI_IO_KEY")
    if not args.skip_pull and not twitterapi_key:
        print("ERROR: TWITTERAPI_IO_KEY not set", file=sys.stderr)
        return 2

    init_db()

    import yaml
    sources = yaml.safe_load(SOURCES_PATH.read_text())
    limits = sources.get("limits", {})
    angles_count = args.angles_count or limits.get("angles_per_run", 7)
    final_drafts = args.final_drafts or limits.get("final_drafts_count", 5)
    min_likes = limits.get("min_likes_threshold", 20)
    freshness_hours = limits.get("freshness_hours", 36)
    ranked_top_n = limits.get("ranked_top_n", 50)

    t0 = time.time()
    total_cost = 0.0

    # === Phase 1: Pull ===
    if not args.skip_pull:
        print("\n=== Phase 1: Pull ===")
        counts = run_pull(SOURCES_PATH, twitterapi_key=twitterapi_key)
        print(f"  pulled: {counts}")
    else:
        print("\n=== Phase 1: SKIPPED (--skip-pull) ===")

    # === Phase 2: Rank ===
    print("\n=== Phase 2: Rank ===")
    n_scored = update_scores()
    print(f"  scored: {n_scored} tweets")

    # === Phase 3: Topic pick ===
    print(f"\n=== Phase 3: Topic pick ({angles_count} angles) ===")
    llm = LLM()
    angles, stats = pick_angles(
        llm,
        angles_count=angles_count,
        top_n=ranked_top_n,
        min_likes=min_likes,
        freshness_hours=freshness_hours,
    )
    total_cost += stats["cost_usd"]
    print(f"  picked: {len(angles)} angles, cost ${stats['cost_usd']:.4f}")
    if not angles:
        print("ERROR: no angles picked. Check evidence count + topic_picker prompt.")
        return 3

    angle_ids = save_angles_to_db(angles)
    for i, aid in enumerate(angle_ids):
        angles[i]["angle_id"] = aid

    vault_path = write_vault_file(angles)
    print(f"  vault: {vault_path}")

    if args.skip_draft:
        print("\n=== Phase 4: SKIPPED (--skip-draft) ===")
        return 0

    # === Phase 4: Draft (parallel per-angle codex sessions) ===
    print(f"\n=== Phase 4: Draft — {args.max_workers} parallel codex sessions ===")
    voice_block = load_voice_block()
    print(f"  voice_block: {len(voice_block)} chars")
    print(f"  spawning {len(angles)} angle drafters (writer + critic × 3 + revise) in parallel")

    def _run_one(idx: int, angle: dict) -> tuple[int, dict]:
        # Each thread gets its own LLM (codex subprocess is stateless anyway,
        # but this keeps the API symmetric with the prior path)
        thread_llm = LLM()
        return idx, draft_for_angle(thread_llm, angle, voice_block=voice_block)

    phase_start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_workers) as ex:
        futures = {ex.submit(_run_one, i, a): (i, a) for i, a in enumerate(angles, 1)}
        for fut in concurrent.futures.as_completed(futures):
            idx_in, angle = futures[fut]
            try:
                idx, result = fut.result()
                total_cost += result["cost_usd"]
                ship_count = sum(1 for r in result["results"] if r["critic"].get("ship"))
                print(
                    f"  [{idx}/{len(angles)}] {angle.get('headline','?')[:60]} → "
                    f"{ship_count}/{len(result['results'])} ship; cost ${result['cost_usd']:.4f}"
                )
            except Exception as e:
                print(f"  [{idx_in}/{len(angles)}] FAILED: {angle.get('headline','?')[:60]} | {e}")

            if total_cost > args.max_cost_usd:
                print(f"  [budget] hit ${args.max_cost_usd:.2f} cap; cancelling remaining")
                for f in futures:
                    f.cancel()
                break
    print(f"  phase 4 took {time.time() - phase_start:.0f}s")

    # === Output ===
    print(f"\n=== Compose drafts file ===")
    drafts = pick_top_drafts_for_today(limit=final_drafts)
    drafts_path = write_drafts_file(drafts)
    print(f"  drafts: {drafts_path}")
    print(f"  shipping: {len(drafts)} of target {final_drafts}")

    elapsed = time.time() - t0
    print(f"\n=== Done in {elapsed:.0f}s, total LLM cost ${total_cost:.4f} ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
