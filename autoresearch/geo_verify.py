#!/usr/bin/env python3
"""autoresearch/geo_verify.py — Post-implementation verification for GEO sessions.

Re-runs visibility queries on completed sessions and compares against baselines.

Usage: python3 geo_verify.py <session_dir>
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def load_env() -> None:
    """Load ALL key-value pairs from the repo .env file into os.environ.

    Mirrors the bash init_env() function from geo-verify.sh:16-46.
    Does NOT use evolve_ops.load_repo_env_defaults() — that function filters
    to a 9-key allowlist and would drop FREDDY_API_URL which geo-verify needs.
    """
    env_file: Path | None = None
    parent_env = SCRIPT_DIR.parent / ".env"
    local_env = SCRIPT_DIR / ".env"

    if parent_env.is_file():
        env_file = parent_env
    elif local_env.is_file():
        env_file = local_env

    if env_file is not None:
        for raw in env_file.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip("'\"")
            os.environ[key] = value

    # Remove ANTHROPIC_API_KEY — geo-verify should not expose it to freddy
    os.environ.pop("ANTHROPIC_API_KEY", None)

    # Rewrite localhost → 127.0.0.1 for FREDDY_API_URL
    api_url = os.environ.get("FREDDY_API_URL", "")
    if api_url.startswith("http://localhost:"):
        os.environ["FREDDY_API_URL"] = api_url.replace(
            "http://localhost:", "http://127.0.0.1:", 1
        )
    elif api_url == "http://localhost":
        os.environ["FREDDY_API_URL"] = "http://127.0.0.1"


def extract_queries(session_dir: Path) -> list[str]:
    """Extract verification queries from session directory.

    Prefers verification-schedule.json if it exists, otherwise extracts
    from results.jsonl competitive entries.
    """
    schedule_file = session_dir / "verification-schedule.json"
    if schedule_file.is_file():
        data = json.loads(schedule_file.read_text())
        return data.get("queries", [])

    # Fall back to results.jsonl
    results_file = session_dir / "results.jsonl"
    if not results_file.is_file():
        return []

    queries: set[str] = set()
    for line in results_file.read_text().splitlines():
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
            if entry.get("type") == "competitive":
                for q in entry.get("queries", []):
                    queries.add(q)
        except json.JSONDecodeError:
            pass

    return sorted(queries)


def run_visibility_checks(queries: list[str]) -> list[tuple[str, str]]:
    """Run freddy visibility for each query with rate limiting.

    Returns list of (query, result_json_string) tuples.
    """
    results: list[tuple[str, str]] = []
    for i, query in enumerate(queries):
        if not query:
            continue
        print(f"Checking: {query}")

        try:
            proc = subprocess.run(
                ["freddy", "visibility", query],
                capture_output=True,
                text=True,
            )
            result = proc.stdout if proc.returncode == 0 else '{"error": "query failed"}'
        except (OSError, subprocess.SubprocessError):
            result = '{"error": "query failed"}'

        results.append((query, result))

        # Rate limit protection — skip sleep after the last query
        if i < len(queries) - 1:
            time.sleep(3)

    return results


def write_report(
    session_dir: Path,
    results: list[tuple[str, str]],
) -> Path:
    """Write markdown verification report to session_dir/verification-report.md."""
    report_file = session_dir / "verification-report.md"
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    lines: list[str] = [
        "# GEO Verification Report",
        "",
        f"Date: {now}",
        f"Session: {session_dir}",
        "",
        "## Query Results",
        "",
    ]

    for query, result in results:
        lines.append(f"### {query}")
        lines.append("")
        lines.append("```json")
        lines.append(result)
        lines.append("```")
        lines.append("")

    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(
        "Verification complete. Compare results above with baseline "
        "in competitors/visibility.json."
    )
    lines.append("")

    report_file.write_text("\n".join(lines))
    return report_file


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Post-implementation verification for GEO sessions."
    )
    parser.add_argument(
        "session_dir",
        type=str,
        help="Path to the session directory to verify",
    )
    args = parser.parse_args()

    session_dir = Path(args.session_dir)
    if not session_dir.is_dir():
        print(f"ERROR: Session directory not found: {session_dir}", file=sys.stderr)
        raise SystemExit(1)

    # Load environment
    load_env()

    print("=== GEO Verification ===")
    print(f"Session: {session_dir}")

    # Extract queries
    queries = extract_queries(session_dir)
    if not queries:
        print("No competitive queries found to verify.")
        raise SystemExit(0)

    schedule_file = session_dir / "verification-schedule.json"
    if not schedule_file.is_file():
        print("No verification-schedule.json found. Extracting queries from results.jsonl...")

    print(f"Queries to verify: {len(queries)}")
    print()

    # Run visibility checks and write report
    results = run_visibility_checks(queries)
    report_file = write_report(session_dir, results)

    print()
    print(f"Verification report written to: {report_file}")


if __name__ == "__main__":
    main()
