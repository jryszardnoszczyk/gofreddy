#!/usr/bin/env python3
"""Inspect the public autoresearch archive state."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from archive_index import (
    entries_by_status,
    load_json,
    load_latest_lineage,
    ordered_latest_entries,
    public_entry_summary,
    refresh_archive_outputs,
)
from frontier import DOMAINS, composite_score, domain_score, entry_lane, has_search_metrics, objective_score


def _default_suite_manifest_path() -> Path:
    return SCRIPT_DIR / "eval_suites" / "search-v1.json"


def _refresh_if_needed(archive_dir: Path) -> None:
    manifest_path = _default_suite_manifest_path()
    suite_manifest = load_json(manifest_path) if manifest_path.exists() else None
    refresh_archive_outputs(archive_dir, suite_manifest=suite_manifest if isinstance(suite_manifest, dict) else None)


def _entry_for_variant(archive_dir: Path, variant_id: str) -> dict[str, Any]:
    """Look up the lineage entry for *variant_id* and return a public summary."""
    latest = load_latest_lineage(archive_dir)
    entry = latest.get(variant_id)
    if entry is None:
        raise SystemExit(f"Variant {variant_id} not found in lineage")
    return public_entry_summary(archive_dir, entry)


def cmd_frontier(archive_dir: Path, _args) -> None:
    _refresh_if_needed(archive_dir)
    payload = load_json(archive_dir / "frontier.json", default={})
    print(json.dumps(payload, indent=2))


def cmd_topk(archive_dir: Path, args) -> None:
    lane = str(args.lane or "").strip().lower()
    entries = sorted(
        [
            entry
            for entry in ordered_latest_entries(archive_dir)
            if has_search_metrics(entry) and (not lane or entry_lane(entry) == lane)
        ],
        key=lambda entry: objective_score(entry) if lane else (composite_score(entry) or 0.0),
        reverse=True,
    )[: args.k]
    payload = [
        {
            "id": entry.get("id"),
            "lane": entry_lane(entry),
            "composite": composite_score(entry),
            "objective_score": objective_score(entry),
            "scores": entry.get("scores"),
        }
        for entry in entries
    ]
    print(json.dumps(payload, indent=2))


def cmd_show(archive_dir: Path, args) -> None:
    _refresh_if_needed(archive_dir)
    print(json.dumps(_entry_for_variant(archive_dir, args.variant_id), indent=2))


def cmd_diff(archive_dir: Path, args) -> None:
    left = archive_dir / args.left
    right = archive_dir / args.right
    if not left.is_dir() or not right.is_dir():
        raise SystemExit("Both diff variants must exist in the archive.")
    result = subprocess.run(
        ["git", "diff", "--no-index", "--stat", str(left), str(right)],
        capture_output=True,
        text=True,
    )
    output = (result.stdout or result.stderr or "").strip()
    print(output)


def cmd_regressions(archive_dir: Path, args) -> None:
    lane = str(args.lane or "").strip().lower()
    entries = {
        entry["id"]: entry
        for entry in ordered_latest_entries(archive_dir)
        if has_search_metrics(entry) and (not lane or entry_lane(entry) == lane)
    }
    regressions: list[dict[str, Any]] = []
    for entry in entries.values():
        parent_id = entry.get("parent")
        if not parent_id or parent_id not in entries:
            continue
        parent = entries[parent_id]
        delta = {
            domain: round((domain_score(entry, domain) or 0.0) - (domain_score(parent, domain) or 0.0), 4)
            for domain in DOMAINS
        }
        worst_domain = min(delta, key=lambda domain: delta[domain])
        regressions.append(
            {
                "id": entry.get("id"),
                "lane": entry_lane(entry),
                "parent": parent_id,
                "worst_domain": worst_domain,
                "worst_delta": delta[worst_domain],
                "composite_delta": round((composite_score(entry) or 0.0) - (composite_score(parent) or 0.0), 4),
                "domain_deltas": delta,
            }
        )
    regressions.sort(key=lambda item: item["worst_delta"])
    print(json.dumps(regressions[: args.limit], indent=2))


def cmd_traces(archive_dir: Path, args) -> None:
    summary = _entry_for_variant(archive_dir, args.variant_id)
    artifacts = summary.get("artifacts") or {}
    print(json.dumps({"variant_id": args.variant_id, "traces": artifacts.get("traces", [])}, indent=2))


def cmd_failures(archive_dir: Path, _args) -> None:
    discarded = entries_by_status(archive_dir, "discarded")
    print(json.dumps(discarded, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect autoresearch archive state.")
    parser.add_argument("command", choices=("frontier", "topk", "show", "diff", "regressions", "traces", "failures"))
    parser.add_argument("arg1", nargs="?")
    parser.add_argument("arg2", nargs="?")
    parser.add_argument("--archive-dir", default=str(SCRIPT_DIR / "archive"))
    parser.add_argument("-k", type=int, default=5)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--lane", default=None)
    args = parser.parse_args()

    archive_dir = Path(args.archive_dir).resolve()
    if args.command == "frontier":
        cmd_frontier(archive_dir, args)
        return
    if args.command == "topk":
        cmd_topk(archive_dir, args)
        return
    if args.command == "show":
        if not args.arg1:
            raise SystemExit("show requires a variant id")
        cmd_show(archive_dir, argparse.Namespace(variant_id=args.arg1))
        return
    if args.command == "diff":
        if not args.arg1 or not args.arg2:
            raise SystemExit("diff requires two variant ids")
        cmd_diff(archive_dir, argparse.Namespace(left=args.arg1, right=args.arg2))
        return
    if args.command == "regressions":
        cmd_regressions(archive_dir, args)
        return
    if args.command == "traces":
        if not args.arg1:
            raise SystemExit("traces requires a variant id")
        cmd_traces(archive_dir, argparse.Namespace(variant_id=args.arg1))
        return
    if args.command == "failures":
        cmd_failures(archive_dir, args)
        return


if __name__ == "__main__":
    main()
