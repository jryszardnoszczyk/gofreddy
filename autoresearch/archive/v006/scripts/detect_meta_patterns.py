#!/usr/bin/env python3
"""Cross-fixture + cross-lane meta-pattern detector — spec section A9.

Walks one or more session directories, runs extract_reasoning on each,
finds reasoning beats that recur across ≥2 fixtures with high text similarity,
and emits a JSON file of meta-patterns suitable for the Stage-2 Opus prompt.

Usage:
    detect_meta_patterns.py <session_dir> [<session_dir> ...] [-o out.json]
    detect_meta_patterns.py --all-lanes  # walks archive/v*/sessions/<lane>/*/

Heuristic: normalized-edit-distance similarity over the first 120 chars of
each beat. Beats with similarity ≥ 0.55 across 2+ fixtures are emitted.
For the v009 GEO + v010 COMPETITIVE + v006 MONITORING data, this catches:
  - "I'll read the persisted session state" (19/19 iterations · all lanes)
  - "rejected the artifact on structural labels" (3/3 GEO fixtures)
  - "prompt_builder allowlist violation" (≥3/4 lanes · architectural finding)
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR))
from extract_reasoning import extract_session  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parents[4]
ARCHIVE_ROOT = _REPO_ROOT / "autoresearch" / "archive"


def normalize(text: str, n: int = 120) -> str:
    """Lowercase, collapse whitespace, take first n chars for similarity."""
    text = re.sub(r"\s+", " ", text.lower().strip())
    return text[:n]


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def find_recent_session_dirs(lane_name: str | None = None) -> list[Path]:
    """Walk archive/v*/sessions/<lane>/*/ and return all session directories."""
    out = []
    if not ARCHIVE_ROOT.exists():
        return out
    for variant in sorted(ARCHIVE_ROOT.glob("v[0-9][0-9][0-9]")):
        sessions_root = variant / "sessions"
        if not sessions_root.exists():
            continue
        for lane in sessions_root.iterdir():
            if not lane.is_dir() or (lane_name and lane.name != lane_name):
                continue
            for session in lane.iterdir():
                if session.is_dir() and (session / "results.jsonl").exists():
                    out.append(session)
    return out


def collect_beats(session_dirs: list[Path]) -> list[dict]:
    """Run extract_reasoning on each session, return flat list of beats with provenance."""
    all_beats = []
    for sd in session_dirs:
        try:
            ex = extract_session(sd)
        except Exception:
            continue
        # provenance: lane + variant + slug
        try:
            slug = sd.name
            lane = sd.parent.name
            variant = sd.parent.parent.parent.name
        except (IndexError, AttributeError):
            continue
        for it in ex.get("iterations", []):
            for beat in it.get("reasoning_beats", []):
                all_beats.append({
                    "variant": variant,
                    "lane": lane,
                    "slug": slug,
                    "iteration": it["iteration"],
                    "phase": it.get("phase", "?"),
                    "kind": beat["kind"],
                    "text": beat["text"],
                })
    return all_beats


def cluster_similar(beats: list[dict], threshold: float = 0.55) -> list[list[int]]:
    """Greedy clustering by similarity. O(n^2). Returns list of cluster indices."""
    n = len(beats)
    cluster_of = [-1] * n
    clusters: list[list[int]] = []
    for i in range(n):
        if cluster_of[i] != -1:
            continue
        members = [i]
        cluster_of[i] = len(clusters)
        for j in range(i + 1, n):
            if cluster_of[j] != -1:
                continue
            if similarity(beats[i]["text"], beats[j]["text"]) >= threshold:
                cluster_of[j] = len(clusters)
                members.append(j)
        clusters.append(members)
    return clusters


def find_meta_patterns(session_dirs: list[Path], min_fixtures: int = 2,
                       min_lanes: int = 1) -> dict:
    beats = collect_beats(session_dirs)
    if not beats:
        return {"meta_patterns": [], "stats": {"sessions": 0, "beats": 0}}

    clusters = cluster_similar(beats)
    meta_patterns = []
    for cluster in clusters:
        if len(cluster) < 2:
            continue
        members = [beats[i] for i in cluster]
        # count distinct fixtures + lanes
        fixtures = {(m["variant"], m["lane"], m["slug"]) for m in members}
        lanes = {m["lane"] for m in members}
        if len(fixtures) < min_fixtures or len(lanes) < min_lanes:
            continue
        # representative text = shortest in cluster (often the canonical form)
        rep = min(members, key=lambda m: len(m["text"]))
        meta_patterns.append({
            "representative_text": rep["text"],
            "kind": rep["kind"],
            "occurrences": len(members),
            "distinct_fixtures": len(fixtures),
            "distinct_lanes": len(lanes),
            "lanes": sorted(lanes),
            "fixtures": [f"{v}/{ln}/{s}" for v, ln, s in sorted(fixtures)],
            "iterations": sorted({(m["variant"], m["lane"], m["slug"], m["iteration"])
                                   for m in members}),
        })

    # Sort by leverage: cross-lane (lanes>1) first, then fixture count, then occurrences
    meta_patterns.sort(key=lambda m: (-m["distinct_lanes"], -m["distinct_fixtures"],
                                      -m["occurrences"]))

    return {
        "meta_patterns": meta_patterns,
        "stats": {
            "sessions": len(session_dirs),
            "beats": len(beats),
            "clusters_found": len(clusters),
            "meta_patterns_emitted": len(meta_patterns),
        },
    }


def main():
    p = argparse.ArgumentParser(description="Detect cross-fixture + cross-lane meta-patterns")
    p.add_argument("session_dirs", nargs="*", type=Path, help="Session directories to analyze")
    p.add_argument("--all-lanes", action="store_true", help="Walk archive/v*/sessions/* automatically")
    p.add_argument("-o", "--output", type=Path, default=None)
    p.add_argument("--min-fixtures", type=int, default=2)
    p.add_argument("--min-lanes", type=int, default=1)
    args = p.parse_args()

    if args.all_lanes:
        session_dirs = find_recent_session_dirs()
    else:
        session_dirs = [d.resolve() for d in args.session_dirs]

    if not session_dirs:
        print("No session directories provided", file=sys.stderr)
        sys.exit(1)

    result = find_meta_patterns(session_dirs, args.min_fixtures, args.min_lanes)
    js = json.dumps(result, indent=2)
    if args.output:
        # Atomic write per 2026-05-08 review: a partial-write (timeout, OOM,
        # disk full) used to leave meta_patterns.json truncated, breaking the
        # portal route with a 500 until the next clean run. .tmp + os.replace
        # makes the swap atomic on POSIX.
        import os as _os
        tmp = args.output.with_suffix(args.output.suffix + ".tmp")
        tmp.write_text(js)
        _os.replace(tmp, args.output)
        print(f"Wrote {args.output} ({len(js)} bytes · {result['stats']['meta_patterns_emitted']} patterns)", file=sys.stderr)
    else:
        print(js)


if __name__ == "__main__":
    main()
