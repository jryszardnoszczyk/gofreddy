#!/bin/bash
# Driver loop for marketing_audit fresh-strategy single-phase pipeline.
#
# marketing_audit completes ONE phase per subprocess (phase0 → findability →
# narrative → acquisition → experience → competitive → monitoring → AI Visibility
# → state-of-business → martech → proposal → final report). The agent persists
# state to files between phases. This driver re-invokes run.py until session.md
# reads "## Status: COMPLETE" or "## Status: BLOCKED", with a hard ceiling on
# iterations to avoid infinite spin.
#
# Usage:
#   bash autoresearch/archive/v006/scripts/run_marketing_audit_to_complete.sh \
#       <client> <context> [max_iter_per_phase] [phase_timeout_seconds]
#
# Example:
#   bash autoresearch/archive/v006/scripts/run_marketing_audit_to_complete.sh \
#       Stripe https://stripe.com
#
# Override the outer iteration cap with MAX_ITERS=N (default 12 — covers the
# 8-phase pipeline plus headroom for retries).
#
# Exits 0 on terminal status (COMPLETE/BLOCKED) reached, non-zero on:
#   - run.py error exit
#   - hitting MAX_ITERS without reaching terminal status
#   - missing session.md after iter 1 (run.py never started a session)
set -euo pipefail

CLIENT="${1:?usage: $0 <client> <context> [max_iter_per_phase] [phase_timeout_seconds]}"
CONTEXT="${2:?context (URL/identifier) required}"
PER_PHASE_MAX_ITER="${3:-50}"
PER_PHASE_TIMEOUT="${4:-3000}"
MAX_ITERS="${MAX_ITERS:-12}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
SESSION_DIR="${REPO_ROOT}/autoresearch/archive/v006/sessions/marketing_audit/${CLIENT}"
SESSION_MD="${SESSION_DIR}/session.md"
RUN_PY="${REPO_ROOT}/autoresearch/archive/v006/run.py"

echo "[marketing_audit driver] client=${CLIENT} context=${CONTEXT}"
echo "[marketing_audit driver] session_md=${SESSION_MD}"
echo "[marketing_audit driver] max_outer_iters=${MAX_ITERS}"

for i in $(seq 1 "$MAX_ITERS"); do
  echo "[$(date '+%H:%M:%S')] === driver iter ${i}/${MAX_ITERS} ==="
  set +e
  # CRITICAL: --resume flag preserves session state between driver iters.
  # Without it, --strategy fresh sets AUTORESEARCH_FRESH=true → init_session
  # archives the prior phase output (phase0/, findability/, narrative/, ...)
  # before each invocation. The agent then sees an empty session_dir and
  # restarts from phase 0, redoing all completed phases. This was the
  # original (now-fixed) bug surfaced by the Stripe driver run on
  # 2026-05-08 evening: 7 phases accumulated through iter 3 then iter 4
  # archived everything. --resume keeps AUTORESEARCH_FRESH unset so
  # session_dir state persists; agent reads prior phases and continues
  # at the next phase. On iter 1 with empty session_dir, --resume is
  # a no-op; the agent does phase 0 fresh.
  python3 "$RUN_PY" \
    --domain marketing_audit --strategy fresh --resume --no-confirm \
    "$CLIENT" "$CONTEXT" "$PER_PHASE_MAX_ITER" "$PER_PHASE_TIMEOUT"
  rc=$?
  set -e

  if [ $rc -ne 0 ]; then
    echo "[marketing_audit driver] run.py exited rc=${rc} on iter ${i}; halting"
    exit "$rc"
  fi

  if [ ! -f "$SESSION_MD" ]; then
    echo "[marketing_audit driver] session.md missing after iter ${i}; halting"
    exit 2
  fi

  if grep -qE "^## Status: (COMPLETE|BLOCKED)" "$SESSION_MD"; then
    status_line=$(grep -E "^## Status:" "$SESSION_MD" | head -1)
    echo "[$(date '+%H:%M:%S')] [marketing_audit driver] terminal: ${status_line} (iter ${i})"
    exit 0
  fi

  current_status=$(grep -E "^## Status:" "$SESSION_MD" | head -1 || echo "## Status: <none>")
  echo "[$(date '+%H:%M:%S')] [marketing_audit driver] still running: ${current_status}"
done

echo "[marketing_audit driver] hit MAX_ITERS=${MAX_ITERS} without terminal status; halting"
exit 3
