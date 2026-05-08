#!/usr/bin/env bash
# Install the launchd schedules for x_engine + linkedin_engine pull cadence.
# Idempotent: safe to re-run. Per master plan v13 §7.3 (D9 X cron revival +
# §3.4 LinkedIn pull cadence wiring).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Each entry: <plist-label>            <human-readable schedule note>
PLISTS=(
    "com.jryszardnoszczyk.x-engine|daily 06:30 — X pull + draft pipeline (D9 revival)"
    "com.jryszardnoszczyk.linkedin-pull-search|daily 06:35 — LinkedIn keyword pull (cost-cap --max-cu 50)"
    "com.jryszardnoszczyk.linkedin-pull-user|weekly Sun 07:00 — LinkedIn per-creator pull (cost-cap --max-cu 200)"
    "com.jryszardnoszczyk.evolve-x-engine|daily 02:00 — autoresearch evolution loop (x_engine lane)"
    "com.jryszardnoszczyk.evolve-linkedin-engine|daily 04:00 — autoresearch evolution loop (linkedin_engine lane)"
)

install_one() {
    local label="$1"
    local source="$SCRIPT_DIR/$label.plist"
    local target="$HOME/Library/LaunchAgents/$label.plist"

    if [ ! -f "$source" ]; then
        echo "  WARN: plist not found at $source — skipping" >&2
        return 0
    fi
    launchctl unload "$target" 2>/dev/null || true
    ln -sf "$source" "$target"
    launchctl load "$target"
    echo "  Installed: $target → $source"
}

echo "Installing x_engine + linkedin_engine LaunchAgents..."
for entry in "${PLISTS[@]}"; do
    label="${entry%%|*}"
    note="${entry##*|}"
    echo ""
    echo "  $label  ($note)"
    install_one "$label"
done

echo ""
echo "All schedules installed."
echo ""
echo "Next steps:"
echo "  - Logs:       x_engine/logs/{run,linkedin-search,linkedin-user}.log"
echo "  - Status:     launchctl list | grep com.jryszardnoszczyk"
echo "  - Disable:    launchctl unload \$HOME/Library/LaunchAgents/<label>.plist"
echo "  - Run NOW:    launchctl start <label>"
echo ""
echo "REQUIRED env (load via .env at gofreddy root):"
echo "  TWITTERAPI_IO_KEY  — for x_engine"
echo "  APIFY_TOKEN        — for linkedin-pull-{search,user}"
echo "  BRIGHTDATA_TOKEN   — only if LINKEDIN_USE_BRIGHTDATA=1 (R5 fallback)"
