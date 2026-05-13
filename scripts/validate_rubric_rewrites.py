#!/usr/bin/env python3
"""Empirical validation of the 2026-05-13 rubric rewrites.

Re-scores a sample of archived post-fix artifacts under the new rubrics
(RUBRIC_VERSION 1fb3a9cb8b98) and compares per-criterion σ against the
old cached scores (which are still in .last_eval_cache.json files).

Prerequisites:
  - Session judge service running on port 7100 (or EVOLUTION_JUDGE_URL set)
  - SESSION_INVOKE_TOKEN exported (from .env)
  - freddy CLI on PATH

Usage:
  .venv/bin/python scripts/validate_rubric_rewrites.py [--lanes monitoring,competitive,storyboard,x_engine,geo] [--per-lane 5]

Output: per-lane σ delta table + raw new scores in /tmp/rubric_validation_<ts>.json
"""
from __future__ import annotations
import argparse
import json
import statistics
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# Project paths
REPO = Path("/Users/jryszardnoszczyk/Documents/GitHub/gofreddy")
ARCHIVE = REPO / "autoresearch" / "archive"
FIX_DATE_TS = datetime(2026, 5, 11, 0, 0, 0).timestamp()

# Rewritten criteria (the 13 + X-9 we shipped)
REWRITTEN = {
    "monitoring": ["MON-1", "MON-3", "MON-4", "MON-5", "MON-6"],
    "competitive": ["CI-1", "CI-5", "CI-6", "CI-7"],
    "storyboard": ["SB-1", "SB-2", "SB-3", "SB-5"],
    "x_engine": ["X-9"],  # new criterion; no old baseline
    "geo": [],  # control lane — no rewrites
}

EXCLUDE_PATH_FRAGMENTS = ("meta_workspace", "archived_sessions")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--lanes", default="monitoring,competitive,storyboard,x_engine,geo",
                   help="Comma-separated lane list")
    p.add_argument("--per-lane", type=int, default=5,
                   help="Number of post-fix artifacts to re-score per lane")
    p.add_argument("--dry-run", action="store_true",
                   help="Find artifacts + show plan but don't call judge")
    return p.parse_args()


def find_post_fix_artifacts(lane: str, n: int) -> list[tuple[Path, str, dict]]:
    """Find up to n .last_eval_cache.json files for `lane` with mtime > fix date.

    Returns: list of (cache_path, session_key, parsed_cache_entry).
    """
    results = []
    seen_keys = set()
    for cache_path in ARCHIVE.rglob(".last_eval_cache.json"):
        if any(frag in str(cache_path) for frag in EXCLUDE_PATH_FRAGMENTS):
            continue
        if cache_path.stat().st_mtime < FIX_DATE_TS:
            continue
        try:
            data = json.loads(cache_path.read_text())
        except Exception:
            continue
        for key, entry in data.items():
            if not key.startswith(f"{lane}:"):
                continue
            if key in seen_keys:
                continue
            seen_keys.add(key)
            try:
                payload = json.loads(entry.get("stdout", "{}"))
            except Exception:
                continue
            if not payload.get("results"):
                continue
            results.append((cache_path, key, payload))
            if len(results) >= n:
                return results
    return results


def extract_old_scores(payload: dict) -> dict[str, float]:
    """Return {criterion_id: score} from a cached judge response."""
    out = {}
    for r in payload.get("results", []):
        if not isinstance(r, dict):
            continue
        cid = r.get("criterion")
        s = r.get("score")
        if cid is not None and s is not None:
            out[cid] = float(s)
    return out


def find_artifact_for_session_key(cache_path: Path, session_key: str) -> Path | None:
    """Resolve session_key (e.g. 'monitoring:full:sessions/monitoring/Shopify/digest.md')
    to an absolute artifact path."""
    parts = session_key.split(":", 2)
    if len(parts) < 3:
        return None
    rel = parts[2]  # e.g. sessions/monitoring/Shopify/digest.md
    # Walk up from cache_path until we find the variant root containing `sessions/`
    cur = cache_path.parent
    while cur != cur.parent:
        candidate = cur / rel
        if candidate.exists():
            return candidate
        cur = cur.parent
    return None


def call_judge(artifact_text: str, source_text: str, criteria: list[dict]) -> dict | None:
    """Invoke freddy evaluate critique with a per-criterion batch payload.

    Returns the parsed response (with per_criterion results) or None on error.
    """
    payload = {"criteria": []}
    for c in criteria:
        payload["criteria"].append({
            "criterion_id": c["id"],
            "rubric_prompt": c["prompt"],
            "output_text": artifact_text,
            "source_text": source_text,
        })
    try:
        proc = subprocess.run(
            ["freddy", "evaluate", "critique", "-"],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=300,
        )
    except Exception as exc:
        print(f"  judge call failed: {exc}", file=sys.stderr)
        return None
    if proc.returncode != 0:
        print(f"  judge exit {proc.returncode}: {(proc.stderr or proc.stdout)[:200]}", file=sys.stderr)
        return None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None


def main():
    args = parse_args()
    lanes = [l.strip() for l in args.lanes.split(",") if l.strip()]

    # Load rubrics with new prose
    sys.path.insert(0, str(REPO))
    from src.evaluation.rubrics import RUBRICS, RUBRIC_VERSION  # noqa
    print(f"Rubrics loaded — RUBRIC_VERSION={RUBRIC_VERSION}\n")

    # Sample artifacts
    sample = {}
    for lane in lanes:
        found = find_post_fix_artifacts(lane, args.per_lane)
        print(f"  {lane}: found {len(found)} post-fix artifacts")
        sample[lane] = found

    if args.dry_run:
        print("\nDry run — exiting before judge calls.")
        for lane, items in sample.items():
            print(f"\n{lane}:")
            for cp, key, _ in items:
                print(f"  {key[:90]}")
        return

    # Per-lane: re-score under new rubric, compare to old
    all_results = {}
    for lane in lanes:
        rewritten = REWRITTEN.get(lane, [])
        # Compose criterion list = ALL criteria for the lane (so judge produces full result)
        lane_criteria = sorted([cid for cid, t in RUBRICS.items() if t.lane == lane])
        print(f"\n=== {lane.upper()} — {len(lane_criteria)} criteria, {len(sample[lane])} artifacts ===")
        critlist = [{"id": cid, "prompt": RUBRICS[cid].prompt} for cid in lane_criteria]

        new_scores_per_crit = defaultdict(list)
        old_scores_per_crit = defaultdict(list)

        for idx, (cache_path, key, old_payload) in enumerate(sample[lane], 1):
            artifact_path = find_artifact_for_session_key(cache_path, key)
            if not artifact_path:
                print(f"  [{idx}] could not resolve artifact for {key[:60]}")
                continue
            try:
                artifact_text = artifact_path.read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                print(f"  [{idx}] read failed: {exc}")
                continue

            t0 = time.monotonic()
            new_payload = call_judge(artifact_text, "(see archived source data)", critlist)
            dt = time.monotonic() - t0
            if not new_payload:
                print(f"  [{idx}] judge call failed for {key[:60]}")
                continue

            new_scores = extract_old_scores(new_payload)  # same shape
            old_scores = extract_old_scores(old_payload)
            print(f"  [{idx}] {key[:70]} | new judge call {dt:.1f}s | n_results={len(new_scores)}")

            for cid in lane_criteria:
                if cid in new_scores:
                    new_scores_per_crit[cid].append(new_scores[cid])
                if cid in old_scores:
                    old_scores_per_crit[cid].append(old_scores[cid])

        # Print comparison
        print(f"\n  {'criterion':<10} {'n':>4} {'old σ':>7} {'new σ':>7} {'Δσ':>7} {'old μ':>7} {'new μ':>7}  verdict")
        for cid in lane_criteria:
            old_s = old_scores_per_crit.get(cid, [])
            new_s = new_scores_per_crit.get(cid, [])
            if not new_s:
                continue
            old_std = statistics.stdev(old_s) if len(old_s) > 1 else 0.0
            new_std = statistics.stdev(new_s) if len(new_s) > 1 else 0.0
            old_mean = statistics.mean(old_s) if old_s else float("nan")
            new_mean = statistics.mean(new_s) if new_s else float("nan")
            delta_std = new_std - old_std
            is_rewritten = cid in rewritten
            verdict = ""
            if is_rewritten:
                if delta_std > 0.05:
                    verdict = "WIDENED ✓"
                elif delta_std < -0.05:
                    verdict = "NARROWED (check)"
                else:
                    verdict = "FLAT (retune)"
            else:
                verdict = "(control)"
            marker = "*" if is_rewritten else " "
            print(f"  {marker}{cid:<9} {len(new_s):>4} {old_std:>7.3f} {new_std:>7.3f} {delta_std:>+7.3f} "
                  f"{old_mean:>7.3f} {new_mean:>7.3f}  {verdict}")

        all_results[lane] = {
            "rewritten_criteria": rewritten,
            "new_scores_per_crit": dict(new_scores_per_crit),
            "old_scores_per_crit": dict(old_scores_per_crit),
        }

    # Persist
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path = Path(f"/tmp/rubric_validation_{ts}.json")
    out_path.write_text(json.dumps(all_results, indent=2))
    print(f"\nRaw results: {out_path}")


if __name__ == "__main__":
    main()
