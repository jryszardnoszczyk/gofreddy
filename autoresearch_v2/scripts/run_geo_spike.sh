#!/usr/bin/env bash
#
# U10 GEO SPIKE — Plan B's hard gate.
#
# Runs the v2 evolution loop against geo for N iterations and reports
# whether the gate passes:
#   PASS:  ≥1 iter with search-v1 composite ≥ 7.0 AND holdout-v1 composite ≥ 4.5
#          AND total cost ≤ $30
#          AND zero substrate↔substrate seam bugs
#   FAIL:  search-v1 stays < 6.5 OR holdout stays < 4.0 across all iters
#          OR cost > $60 OR a seam bug fires
#
# This script is INFRASTRUCTURE — it doesn't decide for you. Read the
# tail output and the post-spike writeup at
# docs/research/2026-05-XX-spike-geo-results.md (you write that doc when
# you call PASS or FAIL).
#
# Usage:
#   bash autoresearch_v2/scripts/run_geo_spike.sh [--iters N] [--dry-run]
#
# Required env (script fails loud if any are unset):
#   EVOLUTION_INVOKE_TOKEN      Bearer for evolution-judge :7200
#   EVOLUTION_HOLDOUT_MANIFEST  ~/.config/gofreddy/holdouts/holdout-v1.json
#   EVOLUTION_JUDGE_URL         http://localhost:7200 (default if unset)
#   AUTORESEARCH_REPO_ROOT      Path to gofreddy repo root
#
# Stream A flags exported by this script (default-on as of 2026-05-11
# but exported here belt-and-suspenders):
#   AUTORESEARCH_EVAL_FIX_AXIS_COLLAPSE=on
#   AUTORESEARCH_EVAL_FIX_HOLDOUT=on
#   AUTORESEARCH_EVAL_FIX_FRAGILE_FIXTURES=on

set -euo pipefail

# --- arg parse ---------------------------------------------------------------

ITERS=10
DRY_RUN=0
while [[ $# -gt 0 ]]; do
    case "$1" in
        --iters)   ITERS="$2"; shift 2;;
        --dry-run) DRY_RUN=1; shift;;
        -h|--help)
            sed -n '2,30p' "$0"; exit 0;;
        *) echo "unknown arg: $1" >&2; exit 2;;
    esac
done

# --- prereq checks -----------------------------------------------------------

require_env() {
    local name="$1"
    if [[ -z "${!name:-}" ]]; then
        echo "FATAL: $name is unset. See script header." >&2
        exit 2
    fi
}
require_env EVOLUTION_INVOKE_TOKEN
require_env EVOLUTION_HOLDOUT_MANIFEST
require_env AUTORESEARCH_REPO_ROOT

cd "$AUTORESEARCH_REPO_ROOT"

# Stream A flags (default-on, exported defensively)
export AUTORESEARCH_EVAL_FIX_AXIS_COLLAPSE=on
export AUTORESEARCH_EVAL_FIX_HOLDOUT=on
export AUTORESEARCH_EVAL_FIX_FRAGILE_FIXTURES=on
export EVOLUTION_JUDGE_URL="${EVOLUTION_JUDGE_URL:-http://localhost:7200}"

# Critique-prompt integrity check first — halt if drifted
echo "[$(date -u +%H:%M:%S)] verifying critique-prompt integrity..."
if ! python3 autoresearch_v2/tools/verify_critique_integrity.py; then
    echo "FATAL: critique-prompt integrity check failed. Halt and surface to JR." >&2
    exit 2
fi

# --- spike loop --------------------------------------------------------------

START_TS=$(date -u +%s)
LANE=geo
SPIKE_LOG="autoresearch_v2/lanes/${LANE}/spike-$(date -u +%Y%m%d-%H%M%S).log"
mkdir -p "$(dirname "$SPIKE_LOG")"

echo "[$(date -u +%H:%M:%S)] starting U10 geo spike: ${ITERS} iters (dry_run=${DRY_RUN})"
echo "  log: $SPIKE_LOG"

# Baseline measurement first (iter 1) — score current head without any mutation
echo "[$(date -u +%H:%M:%S)] iter 1/${ITERS}: BASELINE (no mutation, just score)"
if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "  [dry-run] would call: python3 autoresearch_v2/tools/score_holdout.py --lane ${LANE}"
else
    python3 autoresearch_v2/tools/score_holdout.py --lane "${LANE}" 2>&1 | tee -a "$SPIKE_LOG" || {
        echo "FATAL: baseline holdout score failed. Halt." >&2
        exit 3
    }
fi

# Iters 2..N: meta-agent edits lanes/geo.md, runs sniff + holdout, logs result
for i in $(seq 2 "$ITERS"); do
    echo "[$(date -u +%H:%M:%S)] iter ${i}/${ITERS}: meta-agent cycle"
    if [[ "$DRY_RUN" -eq 1 ]]; then
        echo "  [dry-run] would invoke meta-agent against autoresearch_v2/autoresearch.md"
        continue
    fi
    # NOTE: the actual meta-agent invocation is the one piece the operator
    # decides. Default is claude with the v2 driver prompt; you can swap
    # to codex/opencode via EVAL_BACKEND_OVERRIDE. The agent reads
    # autoresearch_v2/autoresearch.md, picks a parent, edits lanes/geo.md,
    # calls run_experiment + score_holdout + log_experiment, and exits.
    #
    # Recommended single-iter invocation pattern (uncomment + customize):
    #   timeout 1800 claude -p "$(cat autoresearch_v2/autoresearch.md)" \
    #       --model sonnet --dangerously-skip-permissions \
    #       --session-id "spike-${i}-$(date -u +%s)"
    echo "  [implementation note] insert meta-agent invocation here per script comments."
    echo "  [implementation note] meta-agent should call autoresearch_v2/tools/* tools per autoresearch.md."
done

# --- post-spike summary ------------------------------------------------------

END_TS=$(date -u +%s)
ELAPSED=$((END_TS - START_TS))

echo ""
echo "================================================================"
echo "spike complete — ${ELAPSED}s elapsed"
echo "================================================================"
echo ""
echo "Now check the gate:"
echo "  1. python3 autoresearch_v2/tools/inspect.py topk geo --k 3"
echo "  2. python3 autoresearch_v2/tools/inspect.py failures"
echo "  3. cat autoresearch_v2/lanes/geo/holdout_results.tsv | tail -${ITERS}"
echo ""
echo "GATE — ALL must hold for PASS:"
echo "  [ ] ≥1 iter with search-v1 composite ≥ 7.0"
echo "  [ ] ≥1 iter with holdout-v1 composite ≥ 4.5"
echo "  [ ] zero substrate-seam bugs (check failures + spike log for ModuleNotFoundError,"
echo "      JudgeUnreachable exhaustion, chmod 0444 perm leak, lock collision)"
echo "  [ ] total iteration cost ≤ \$30"
echo ""
echo "If PASS: write docs/research/2026-05-XX-spike-geo-results.md with composite"
echo "table, cost, runtime, any anomalies. Proceed to U11/U12."
echo ""
echo "If FAIL: write the same writeup with the failure mode. v1 stays untouched"
echo "(R5 invariant). Rollback: rm -rf autoresearch_v2/ (or git revert U1-U9)."
