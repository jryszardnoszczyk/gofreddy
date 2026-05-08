#!/usr/bin/env bash
# Daily 06:35 LinkedIn keyword pull. Iterates linkedin_keywords from
# x_engine/sources_linkedin.yaml; cost-cap --max-cu 50 per call so daily
# total is bounded.
#
# Per master plan v13 §3.4 + §7.3. Wired by
# com.jryszardnoszczyk.linkedin-pull-search.plist.
#
# Requires: APIFY_TOKEN in env (loaded from .env via x_engine.cli's
# load_dotenv at xeng startup).
set -euo pipefail
cd "$(dirname "$0")/.."

LOGDIR="x_engine/logs"
mkdir -p "$LOGDIR"
LOG="$LOGDIR/linkedin-search-$(date +%Y-%m-%d).log"

echo -e "\n========== linkedin-search started $(date -u +%FT%TZ) ==========" >> "$LOG"
exec uv run xeng pull-linkedin-all-search --max-cu 50 2>&1 | tee -a "$LOG"
