#!/usr/bin/env bash
# Daily 02:00 evolution loop on the x_engine lane.
#
# Per master plan v13 §4.2 adjacent + §6 + §7.4. Wired by
# com.jryszardnoszczyk.evolve-x-engine.plist.
#
# Defaults: 1 iteration × 3 candidates per cycle. Bump via env if the
# search lane wants wider exploration; default keeps cost in line with
# the other 4 lanes' single-iteration daily cycle.
set -euo pipefail
cd "$(dirname "$0")/.."

LOGDIR="x_engine/logs"
mkdir -p "$LOGDIR"
LOG="$LOGDIR/evolve-x-engine-$(date +%Y-%m-%d).log"

ITERATIONS="${EVOLVE_X_ITERATIONS:-1}"
CANDIDATES="${EVOLVE_X_CANDIDATES:-3}"

echo -e "\n========== evolve-x-engine started $(date -u +%FT%TZ) ==========" >> "$LOG"
exec uv run python -m autoresearch.evolve run \
    --lane x_engine \
    --iterations "$ITERATIONS" \
    --candidates "$CANDIDATES" 2>&1 | tee -a "$LOG"
