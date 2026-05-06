#!/usr/bin/env python3
"""Validate results.jsonl entries against expected schema.

Called by the archive runner to catch malformed entries early.

Usage:
    python3 lib_validate_results.py <results_path>
    # Validates last entry, prints JSON: {"valid": bool, "message": str}
"""

import json
import sys
from pathlib import Path

REQUIRED_FIELDS: dict[str, list[str]] = {
    "gather": ["type", "iteration", "status", "competitors"],
    "analyze": ["type", "iteration", "status", "competitor", "quality_score"],
    "synthesize": ["type", "iteration", "status"],
    "verify": ["type", "iteration", "status", "quality_score"],
}

VALID_STATUSES: dict[str, set[str]] = {
    "gather": {"done", "blocked", "partial"},
    "analyze": {"kept", "discarded", "blocked", "failed"},
    "synthesize": {"done", "blocked"},
    "verify": {"pass", "rework", "complete", "blocked"},
}


def validate_last_entry(results_path: str) -> tuple[bool, str]:
    """Validate the last entry in results.jsonl.

    Returns (valid, message).
    """
    path = Path(results_path)
    if not path.exists():
        return False, "results.jsonl not found"

    lines = path.read_text().strip().split("\n")
    if not lines or not lines[-1].strip():
        return False, "results.jsonl is empty"

    last_line = lines[-1].strip()
    try:
        entry = json.loads(last_line)
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}"

    if not isinstance(entry, dict):
        return False, "Entry is not a JSON object"

    entry_type = entry.get("type", "")
    if not entry_type:
        return False, "Missing 'type' field"

    if entry_type not in REQUIRED_FIELDS:
        return False, f"Unknown type: {entry_type}"

    # Check required fields
    missing = [f for f in REQUIRED_FIELDS[entry_type] if f not in entry]
    if missing:
        return False, f"Missing fields for {entry_type}: {', '.join(missing)}"

    # Check status validity
    status = entry.get("status", "")
    valid_statuses = VALID_STATUSES.get(entry_type, set())
    if valid_statuses and status not in valid_statuses:
        return False, f"Invalid status '{status}' for {entry_type}. Expected: {', '.join(sorted(valid_statuses))}"

    # Type-specific validations
    if entry_type == "analyze":
        if not entry.get("competitor"):
            return False, "analyze entry missing competitor name"

    if entry_type == "gather":
        competitors = entry.get("competitors", 0)
        if not isinstance(competitors, int) or competitors < 0:
            return False, f"Invalid competitors count: {competitors}"

    return True, "ok"


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <results_path>", file=sys.stderr)
        sys.exit(1)

    valid, message = validate_last_entry(sys.argv[1])
    result = {"valid": valid, "message": message}
    print(json.dumps(result))
    sys.exit(0 if valid else 1)
