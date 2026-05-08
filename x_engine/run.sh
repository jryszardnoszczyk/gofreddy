#!/usr/bin/env bash
# Compatibility stub for the legacy v1 daily 06:30 cron
# (com.jryszardnoszczyk.x-engine.plist). The v1 X compose/draft/topic_pick
# pipeline was dropped in the L2 §3.1 cull; daily X production now flows
# through the autoresearch evolution lane (com.jryszardnoszczyk.evolve-x-engine
# at 02:00) and the LinkedIn pull cadence (linkedin-pull-search at 06:35).
#
# This stub exists so JR's existing launchctl-loaded plist doesn't fire-and-fail
# post-merge. Exits 0 with a log line. JR retires this stub by:
#   launchctl unload ~/Library/LaunchAgents/com.jryszardnoszczyk.x-engine.plist
#   rm ~/Library/LaunchAgents/com.jryszardnoszczyk.x-engine.plist
# once the new evolve-x-engine cron is verified.
set -euo pipefail
cd "$(dirname "$0")/.."

LOGDIR="x_engine/logs"
mkdir -p "$LOGDIR"
LOG="$LOGDIR/run-$(date +%Y-%m-%d).log"

echo "" >> "$LOG"
echo "========== legacy run.sh stub fired at $(date -u +%FT%TZ) ==========" >> "$LOG"
echo "v1 X pipeline (compose/draft/topic_pick) dropped in L2 §3.1 cull." >> "$LOG"
echo "Daily X production now via evolve-x-engine.plist (02:00)." >> "$LOG"
echo "Retire this cron with: launchctl unload \$HOME/Library/LaunchAgents/com.jryszardnoszczyk.x-engine.plist" >> "$LOG"
exit 0
