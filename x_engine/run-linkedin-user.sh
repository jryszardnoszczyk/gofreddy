#!/usr/bin/env bash
# Weekly Sunday 07:00 LinkedIn per-creator pull. Iterates linkedin_users
# from x_engine/sources_linkedin.yaml; cost-cap --max-cu 200 per call.
#
# Per master plan v13 §3.4 + §7.3. Wired by
# com.jryszardnoszczyk.linkedin-pull-user.plist.
#
# Requires: APIFY_TOKEN in env (loaded from .env via x_engine.cli's
# load_dotenv at xeng startup).
set -euo pipefail
cd "$(dirname "$0")/.."

LOGDIR="x_engine/logs"
mkdir -p "$LOGDIR"
LOG="$LOGDIR/linkedin-user-$(date +%Y-%m-%d).log"

echo -e "\n========== linkedin-user started $(date -u +%FT%TZ) ==========" >> "$LOG"
exec uv run xeng pull-linkedin-all-users --max-cu 200 2>&1 | tee -a "$LOG"
