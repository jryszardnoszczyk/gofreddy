#!/usr/bin/env bash
# Daily 04:00 evolution loop on the linkedin_engine lane.
#
# Per master plan v13 §4.2 adjacent + §6 + §7.4. Wired by
# com.jryszardnoszczyk.evolve-linkedin-engine.plist. Staggered 2hr after
# evolve-x-engine to avoid claude/codex semaphore contention.
set -euo pipefail
cd "$(dirname "$0")/.."

LOGDIR="x_engine/logs"
mkdir -p "$LOGDIR"
LOG="$LOGDIR/evolve-linkedin-engine-$(date +%Y-%m-%d).log"

ITERATIONS="${EVOLVE_LI_ITERATIONS:-1}"
CANDIDATES="${EVOLVE_LI_CANDIDATES:-3}"

echo -e "\n========== evolve-linkedin-engine started $(date -u +%FT%TZ) ==========" >> "$LOG"
exec uv run python -m autoresearch.evolve run \
    --lane linkedin_engine \
    --iterations "$ITERATIONS" \
    --candidates "$CANDIDATES" 2>&1 | tee -a "$LOG"
