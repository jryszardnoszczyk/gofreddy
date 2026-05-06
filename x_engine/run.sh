#!/usr/bin/env bash
# x_engine daily run. Calls compose.py from gofreddy root.
# Logs to x_engine/logs/run-YYYY-MM-DD.log, also tee'd to stdout.
set -euo pipefail
cd "$(dirname "$0")/.."

LOGDIR="x_engine/logs"
mkdir -p "$LOGDIR"
LOG="$LOGDIR/run-$(date +%Y-%m-%d).log"

# Append-mode log so re-runs in the same day all land in one file.
echo -e "\n========== run started $(date -u +%FT%TZ) ==========" >> "$LOG"
exec uv run python -m x_engine.pipeline.compose "$@" 2>&1 | tee -a "$LOG"
