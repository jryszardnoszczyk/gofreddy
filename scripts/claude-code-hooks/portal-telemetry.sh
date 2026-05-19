#!/usr/bin/env bash
# Claude Code PostToolUse hook → POSTs each tool call as a canonical event
# to the local portal ingestion endpoint. Installed by operators who want
# their Claude Code work captured in the gofreddy client portal.
#
# Install (operator side, one-time):
#   1. cp scripts/claude-code-hooks/portal-telemetry.sh ~/.claude/hooks/
#      cp scripts/claude-code-hooks/portal-telemetry-attribute.py ~/.claude/hooks/
#   2. chmod +x ~/.claude/hooks/portal-telemetry.sh
#      chmod +x ~/.claude/hooks/portal-telemetry-attribute.py
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
#      Equivalent: launch CC from inside a `clients/<slug>/...` working
#      directory and the hook auto-attributes via cwd (R5.2).
#
# Attribution (R5.1–R5.5):
#   * env GOFREDDY_CLIENT_ID is primary; if unset, cwd `clients/<slug>/`
#     segment is used.
#   * If both are set and disagree, the hook emits an operator-internal
#     `attribution_conflict` moment and writes the tool_call without
#     client_id (fail closed — R5.3).
#   * If env contains an invalid slug, same fail-closed treatment with
#     reason=`slug_invalid`.
#   * Server-side, /_ingest validates the slug against the `clients` DB
#     table (R5.5). A 400 here lands in the log but doesn't block CC.
#
# Failure mode: silent. Hook MUST NOT block Claude Code's tool-call loop.
# Failed ingest is logged at ~/.claude/hooks/portal-telemetry.log for the
# operator to inspect later. Any non-zero curl exit drops the event on the
# floor and proceeds.
#
# Schema: per docs/brainstorms/2026-05-13-client-portal-telemetry-design.md
# and autoresearch/events.py CANONICAL_FIELDS. Fields populated from Claude
# Code's hook stdin JSON payload (modern protocol).

set -uo pipefail

LOG="${HOME}/.claude/hooks/portal-telemetry.log"
mkdir -p "$(dirname "$LOG")" 2>/dev/null || true

# Co-located attribution helper. Resolves env-vs-cwd per R5/R7. Lives
# next to this hook (same install dir). If absent, attribution falls
# back to env-only (legacy behavior) so old installs keep working.
ATTRIBUTE_HELPER="$(dirname "$0")/portal-telemetry-attribute.py"

# Claude Code's modern hook protocol delivers context via a JSON payload on
# stdin with shape:
#   {"session_id": "...", "tool_name": "...", "tool_input": {...},
#    "tool_response": {...}, "transcript_path": "...", "cwd": "..."}
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

URL="${GOFREDDY_INGEST_URL:-http://127.0.0.1:8000/v1/portal/_ingest}"
TOKEN="${GOFREDDY_INGEST_TOKEN:-}"

if [[ -z "$TOKEN" ]]; then
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) skipped: GOFREDDY_INGEST_TOKEN unset" >>"$LOG"
  exit 0
fi

# --- Attribution resolution (R5.1/R5.2/R5.3/R5.5 client-side) ---
# Helper reads HOOK_JSON on stdin + GOFREDDY_CLIENT_ID from env, prints
# two lines: <resolved_client_id_or_empty> and <conflict_payload_json_or_empty>.
RESOLVED_CLIENT_ID=""
CONFLICT_PAYLOAD_JSON=""
if [[ -x "$ATTRIBUTE_HELPER" ]] && [[ -n "$HOOK_JSON" ]]; then
  ATTR_OUT="$(printf '%s' "$HOOK_JSON" | python3 "$ATTRIBUTE_HELPER" 2>>"$LOG" || true)"
  RESOLVED_CLIENT_ID="$(printf '%s\n' "$ATTR_OUT" | sed -n '1p')"
  CONFLICT_PAYLOAD_JSON="$(printf '%s\n' "$ATTR_OUT" | sed -n '2p')"
else
  # Legacy fallback: env-only, no validation. Server-side /_ingest
  # still enforces R5.5 slug-table check.
  RESOLVED_CLIENT_ID="${GOFREDDY_CLIENT_ID:-}"
fi

# --- Conflict moment POST (operator-internal; fires FIRST so the
#     subsequent tool_call has temporal ordering w/ its explanation). ---
if [[ -n "$CONFLICT_PAYLOAD_JSON" ]]; then
  CONFLICT_HTTP=$(curl -s -o /dev/null -w "%{http_code}" \
    --max-time 2 \
    -X POST "$URL" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$CONFLICT_PAYLOAD_JSON" 2>>"$LOG" || echo "000")
  if [[ "$CONFLICT_HTTP" != "200" ]]; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) conflict-post http=$CONFLICT_HTTP session=$SESSION_ID" >>"$LOG"
  fi
fi

# --- Normal tool_call event ---
# client_id is included only when non-empty (server treats absent
# client_id as operator-internal).
if [[ -n "$RESOLVED_CLIENT_ID" ]]; then
  CLIENT_FIELD=",\"client_id\":\"$RESOLVED_CLIENT_ID\""
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
