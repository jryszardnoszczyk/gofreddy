#!/usr/bin/env bash
# Install the daily 06:30 launchd schedule for x_engine.
# Idempotent: safe to re-run.
set -euo pipefail

PLIST_NAME="com.jryszardnoszczyk.x-engine"
SOURCE="$(cd "$(dirname "$0")" && pwd)/$PLIST_NAME.plist"
TARGET="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"

if [ ! -f "$SOURCE" ]; then
    echo "ERROR: plist not found at $SOURCE" >&2
    exit 1
fi

# Unload prior version if loaded
launchctl unload "$TARGET" 2>/dev/null || true

# Symlink (so edits to the plist in repo propagate without re-install)
ln -sf "$SOURCE" "$TARGET"

# Load
launchctl load "$TARGET"

echo "Installed: $TARGET → $SOURCE"
echo ""
echo "Next steps:"
echo "  - Daily run scheduled at 06:30 local time"
echo "  - Logs: x_engine/logs/run-YYYY-MM-DD.log"
echo "  - Manual run any time:  ./x_engine/run.sh"
echo "  - Status:                launchctl list | grep $PLIST_NAME"
echo "  - Disable:               launchctl unload $TARGET"
echo "  - Run NOW:               launchctl start $PLIST_NAME"
