#!/usr/bin/env bash
# Claude Code PostToolUse hook → POSTs each tool call as a canonical event
# to the local portal ingestion endpoint. Installed by operators who want
# their Claude Code work captured in the gofreddy client portal.
#
# Install (operator side, one-time):
#   1. cp scripts/claude-code-hooks/portal-telemetry.sh ~/.claude/hooks/
#   2. chmod +x ~/.claude/hooks/portal-telemetry.sh
#   3. Add to ~/.claude/settings.json:
#        {
#          "hooks": {
#            "PostToolUse": [
#              { "command": "~/.claude/hooks/portal-telemetry.sh" }
#            ]
#          }
#        }
#   4. Export env vars in your shell rc:
#        export GOFREDDY_INGEST_TOKEN="<shared-secret-from-server>"
#        export GOFREDDY_INGEST_URL="http://127.0.0.1:8000/v1/portal/_ingest"
#   5. (Optional, per-shell) export GOFREDDY_CLIENT_ID="klinika-melitus"
#      before opening Claude Code in that client's worktree.
#
# Failure mode: silent. Hook MUST NOT block Claude Code's tool-call loop.
# Failed ingest is logged at ~/.claude/hooks/portal-telemetry.log for the
# operator to inspect later. Any non-zero curl exit drops the event on the
# floor and proceeds.
#
# Schema: per docs/brainstorms/2026-05-13-client-portal-telemetry-design.md
# and autoresearch/events.py CANONICAL_FIELDS. Fields populated from Claude
# Code's hook env vars + stdin JSON payload.

set -uo pipefail

LOG="${HOME}/.claude/hooks/portal-telemetry.log"
mkdir -p "$(dirname "$LOG")" 2>/dev/null || true

# Claude Code's modern hook protocol delivers context via a JSON payload on
# stdin with shape:
#   {"session_id": "...", "tool_name": "...", "tool_input": {...},
#    "tool_response": {...}, "transcript_path": "..."}
# We parse it with python (always available) to avoid a jq dependency.
# Falls back to env vars (older Claude Code versions) when stdin is empty.
HOOK_JSON="$(cat 2>/dev/null || true)"
if [[ -n "$HOOK_JSON" ]]; then
  read -r SESSION_ID TOOL_NAME < <(python3 -c '
import json, sys
try:
    d = json.loads(sys.stdin.read())
except Exception:
    print("unknown unknown")
    sys.exit(0)
print((d.get("session_id") or "unknown"), (d.get("tool_name") or "unknown"))
' <<<"$HOOK_JSON")
  TOOL_INPUT="$(python3 -c '
import json, sys
try:
    d = json.loads(sys.stdin.read())
except Exception:
    print("{}")
    sys.exit(0)
ti = d.get("tool_input") or {}
print(json.dumps(ti) if isinstance(ti, (dict, list)) else "{}")
' <<<"$HOOK_JSON")"
else
  SESSION_ID="${CLAUDE_SESSION_ID:-unknown}"
  TOOL_NAME="${CLAUDE_TOOL_NAME:-unknown}"
  TOOL_INPUT="${CLAUDE_TOOL_INPUT:-{}}"
fi
CLIENT_ID="${GOFREDDY_CLIENT_ID:-}"

URL="${GOFREDDY_INGEST_URL:-http://127.0.0.1:8000/v1/portal/_ingest}"
TOKEN="${GOFREDDY_INGEST_TOKEN:-}"

if [[ -z "$TOKEN" ]]; then
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) skipped: GOFREDDY_INGEST_TOKEN unset" >>"$LOG"
  exit 0
fi

# Build the canonical event payload. client_id is included only if non-empty
# (the server treats absent client_id as operator-internal).
if [[ -n "$CLIENT_ID" ]]; then
  CLIENT_FIELD=",\"client_id\":\"$CLIENT_ID\""
else
  CLIENT_FIELD=""
fi

PAYLOAD=$(cat <<JSON
{
  "kind": "tool_call",
  "source": "claude_code",
  "session_id": "$SESSION_ID",
  "actor": "agent",
  "action": "$TOOL_NAME",
  "args": $TOOL_INPUT,
  "status": "complete"$CLIENT_FIELD
}
JSON
)

# Fire and forget (max 2s timeout to avoid blocking the tool loop).
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  --max-time 2 \
  -X POST "$URL" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" 2>>"$LOG" || echo "000")

if [[ "$HTTP_STATUS" != "200" ]]; then
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) http=$HTTP_STATUS tool=$TOOL_NAME session=$SESSION_ID" >>"$LOG"
fi

exit 0
