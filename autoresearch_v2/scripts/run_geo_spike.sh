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

# Iters 2..N: meta-agent edits lanes/geo.md, runs sniff + holdout, logs result.
# Each invocation feeds claude the driver prompt + the lane meta-context +
# explicit instruction to do ONE cycle (read results.tsv, pick parent, mutate,
# run experiment, log). 30-min timeout per cycle.
META_AGENT_BACKEND="${EVAL_BACKEND_OVERRIDE:-claude}"
META_AGENT_MODEL="${AUTORESEARCH_META_AGENT_MODEL:-sonnet}"

for i in $(seq 2 "$ITERS"); do
    iter_start=$(date -u +%s)
    echo "[$(date -u +%H:%M:%S)] iter ${i}/${ITERS}: meta-agent cycle (backend=${META_AGENT_BACKEND}, model=${META_AGENT_MODEL})"

    PROMPT="$(cat <<EOF
$(cat autoresearch_v2/autoresearch.md)

---

# YOUR CURRENT TASK

You are firing iteration ${i}/${ITERS} of the U10 geo spike. Do ONE complete
cycle of the loop in autoresearch.md above, then EXIT. Do not loop forever
in this single invocation — the surrounding shell loop will fire you again
for iter $((i+1)).

Working lane: ${LANE}
Pre-read these files in order:
  1. autoresearch_v2/lanes/${LANE}-context.md  (read-only meta-context)
  2. autoresearch_v2/lanes/${LANE}/results.tsv (recent attempts ledger)
  3. autoresearch_v2/lanes/${LANE}.md          (the session prompt you mutate)

Then mutate ${LANE}.md, call:
  python3 autoresearch_v2/tools/run_experiment.py --domain ${LANE} --client mayoclinic --context https://www.mayoclinic.org --max-iter 5 --timeout 600
to sniff one fixture (cheap). If sniff exit_code==0 and deliverable_present==true:
  python3 autoresearch_v2/tools/score_holdout.py --lane ${LANE}
Then:
  python3 autoresearch_v2/tools/log_experiment.py --lane ${LANE} --status <keep|discard|crash|checks_failed> --composite <holdout-composite> --wall-time-seconds <total> --description "<one-line>" --asi-json '<json blob with rationale>'

After log_experiment, call:
  python3 autoresearch_v2/tools/alert_check.py --lane ${LANE}

Then exit. Do NOT continue past one cycle.
EOF
)"

    if [[ "$DRY_RUN" -eq 1 ]]; then
        echo "  [dry-run] would invoke ${META_AGENT_BACKEND} with ${#PROMPT}-char prompt"
        continue
    fi

    case "$META_AGENT_BACKEND" in
        claude)
            timeout 1800 claude -p "$PROMPT" \
                --output-format text \
                --model "$META_AGENT_MODEL" \
                --dangerously-skip-permissions \
                --session-id "u10-spike-iter${i}-$(date -u +%s)" \
                2>&1 | tee -a "$SPIKE_LOG" || echo "  (meta-agent exited non-zero — continuing to next iter)"
            ;;
        codex)
            echo "$PROMPT" | timeout 1800 codex exec \
                --model "$META_AGENT_MODEL" \
                --sandbox workspace-write \
                --color never \
                --ephemeral \
                -c 'approval_policy="never"' \
                2>&1 | tee -a "$SPIKE_LOG" || echo "  (meta-agent exited non-zero — continuing to next iter)"
            ;;
        opencode)
            timeout 1800 opencode run \
                --dangerously-skip-permissions \
                -m "$META_AGENT_MODEL" \
                --format json \
                "$PROMPT" \
                2>&1 | tee -a "$SPIKE_LOG" || echo "  (meta-agent exited non-zero — continuing to next iter)"
            ;;
        *)
            echo "FATAL: unknown META_AGENT_BACKEND=$META_AGENT_BACKEND (claude|codex|opencode)" >&2
            exit 2
            ;;
    esac

    iter_elapsed=$(( $(date -u +%s) - iter_start ))
    echo "[$(date -u +%H:%M:%S)] iter ${i} done in ${iter_elapsed}s"
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
