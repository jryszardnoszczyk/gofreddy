#!/usr/bin/env bash
# scripts/evolve-with-report.sh — run autoresearch/evolve.sh and emit a
# 1-line summary on completion (composite, pass-rate-delta, promoted Y/N).
#
# Why: overnight evolution runs are hours long. Tailing the log is fine
# while you're at the keyboard, but the operator wants a one-shot status
# they can check via ssh after the fact ("what happened with last night's
# run?") without parsing scores.json by hand.
#
# Usage:
#   scripts/evolve-with-report.sh run --lane geo --iterations 3 ...
#   tail /tmp/evolve-last.summary    # post-run digest
#
# Output destinations:
#   - stdout: same evolve.sh output (tee'd; not buffered)
#   - /tmp/evolve-last.summary: ONE line digest, atomic
#   - /tmp/evolve-last.exit: exit code (0 = clean, nonzero = failure)
#
# Reads:
#   - autoresearch/archive/v*/scores.json  (most recently mtime'd)
#   - autoresearch/archive/current.json    (to detect promotion)
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EVOLVE_SH="$REPO_ROOT/autoresearch/evolve.sh"
ARCHIVE="$REPO_ROOT/autoresearch/archive"
SUMMARY="${EVOLVE_REPORT_SUMMARY:-/tmp/evolve-last.summary}"
EXIT_FILE="${EVOLVE_REPORT_EXIT:-/tmp/evolve-last.exit}"
RUN_LOG="${EVOLVE_REPORT_LOG:-/tmp/evolve-last.log}"

if [ ! -x "$EVOLVE_SH" ]; then
  echo "evolve-with-report: $EVOLVE_SH not executable" >&2
  exit 64
fi

started_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
: > "$RUN_LOG"

# Capture exit code without losing stdout/stderr to the user.
set +e
"$EVOLVE_SH" "$@" 2>&1 | tee "$RUN_LOG"
status=${PIPESTATUS[0]}
set -e
finished_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

echo "$status" > "$EXIT_FILE"

# Build the summary in Python so we can read scores.json safely.
python3 - <<'PY' "$ARCHIVE" "$status" "$started_at" "$finished_at" "$SUMMARY"
import json
import os
import sys
from pathlib import Path

archive, status, started, finished, summary_path = sys.argv[1:6]
status_int = int(status)
archive_dir = Path(archive)

def _latest_variant():
    candidates = sorted(
        (p for p in archive_dir.glob("v*/scores.json") if p.is_file()),
        key=lambda p: p.stat().st_mtime,
    )
    return candidates[-1] if candidates else None

def _promoted_id():
    cur = archive_dir / "current.json"
    if not cur.is_file():
        return None
    try:
        data = json.loads(cur.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    head = data.get("head") if isinstance(data, dict) else None
    if isinstance(head, str):
        return head
    if isinstance(head, dict):
        for v in head.values():
            if isinstance(v, str):
                return v
    return None

latest = _latest_variant()
variant_id = latest.parent.name if latest else "?"
composite = "?"
pass_rate_delta = "?"
inner_pass_rate = "?"
outer_pass_rate = "?"
fixture_cohort = "?"
if latest is not None:
    try:
        s = json.loads(latest.read_text())
    except (OSError, json.JSONDecodeError):
        s = {}
    composite = s.get("composite", "?")
    inner = s.get("inner_metrics") or {}
    inner_pass_rate = inner.get("inner_pass_rate", "?")
    outer_pass_rate = inner.get("outer_pass_rate", "?")
    pass_rate_delta = inner.get("pass_rate_delta", "?")
    cohort = s.get("fixture_cohort") or {}
    if cohort:
        fixture_cohort = ",".join(
            f"{k}:{len(v)}" for k, v in cohort.items() if isinstance(v, list)
        )

promoted = _promoted_id()
promoted_match = "Y" if (promoted == variant_id and status_int == 0) else "N"
verdict = "PASS" if status_int == 0 else f"FAIL(exit={status_int})"

line = (
    f"[{finished}] verdict={verdict} variant={variant_id} "
    f"composite={composite} pass_rate_delta={pass_rate_delta} "
    f"inner={inner_pass_rate} outer={outer_pass_rate} "
    f"cohort={fixture_cohort} promoted={promoted_match} "
    f"promoted_head={promoted or 'none'} started={started}"
)
Path(summary_path).write_text(line + "\n")
print(line)
PY

exit "$status"
