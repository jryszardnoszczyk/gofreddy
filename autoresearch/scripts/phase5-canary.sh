#!/usr/bin/env bash
# Plan B Phase 5 Step 4 — overfit-canary checkpoint-scoring loop.
#
# Runs 10 evolution iterations (with 3 candidates each — 30 variants total)
# then scores each checkpoint iteration {2, 4, 6, 8, 10, 12, 14, 16, 18, 20}
# against BOTH a public fixture (search-v1) and a holdout anchor
# (holdout-v1). 10 seeds per checkpoint per surface → 200 evaluations total.
#
# Operator sets the fixture pair via env — the holdout fixture_id MUST NOT
# appear in-repo per the "no in-repo file names any holdout fixture_id"
# acceptance criterion.
#
# Output:
#   /tmp/canary-public-<iter>.jsonl   # per-seed public scores
#   /tmp/canary-holdout-<iter>.jsonl  # per-seed holdout scores
#
# After this runs, hand the two sets to the canary agent (Plan B Phase 5
# Step 6: call_promotion_judge with role="canary") to get GO | FAIL | REVISE.
#
# PREREQUISITES:
#   - Phase 4 migration-check passed (see phase4-migration-check.sh)
#   - Deliberately-overfit variant exists in the archive (Plan B Phase 5
#     Step 2.6 — operator hand-crafts a variant that scores ≥0.15 higher
#     on public than holdout before running this canary)
#   - Live stack: backend, supabase, judge services, provider creds
#
# BUDGET: days of wall-clock (20 iter × 3 candidates × ~N fixtures × variant
# session time). Do not run casually.
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
ARCHIVE_CURRENT="${REPO_ROOT}/autoresearch/archive/current.json"
HOLDOUT_MANIFEST="${HOME}/.config/gofreddy/holdouts/holdout-v1.json"

: "${EVOLUTION_JUDGE_URL:?EVOLUTION_JUDGE_URL not set; source ~/.config/gofreddy/judges.env}"
: "${EVOLUTION_INVOKE_TOKEN:?EVOLUTION_INVOKE_TOKEN not set; source ~/.config/gofreddy/judges.env}"
: "${FREDDY_API_URL:?FREDDY_API_URL not set; source .env}"

if [[ ! -f "${HOLDOUT_MANIFEST}" ]]; then
  echo "FATAL: holdout manifest not found at ${HOLDOUT_MANIFEST}" >&2
  echo "  (Phase 2 must land before running the canary.)" >&2
  exit 1
fi

# Run 20 evolution iterations producing the candidate-variant trajectory.
# This is the cohort the canary measures.
echo "Starting 20-iteration canary run (3 candidates per iter = 60 total)..." >&2
"${REPO_ROOT}/autoresearch/evolve.sh" run \
  --iterations 20 \
  --candidates-per-iteration 3 \
  --lane geo

# Score checkpoints after the run. Operator supplies the pair via env —
# the recommended default is a same-taxonomy-cell (domain × lang × geo ×
# vertical × adversarial) pair with different URLs so divergence measures
# generalization to the same intent on a fresh URL.
#
# Example:
#   export CANARY_PUBLIC_FIXTURE=search-v1:geo-bmw-ix-de
#   export CANARY_HOLDOUT_FIXTURE=holdout-v1:<your-geo-anchor-id>
: "${CANARY_PUBLIC_FIXTURE:?set CANARY_PUBLIC_FIXTURE=search-v1:<fixture_id>}"
: "${CANARY_HOLDOUT_FIXTURE:?set CANARY_HOLDOUT_FIXTURE=holdout-v1:<fixture_id> (fixture_id stays out of git)}"
PUBLIC_FIXTURE="${CANARY_PUBLIC_FIXTURE}"
HOLDOUT_FIXTURE="${CANARY_HOLDOUT_FIXTURE}"
for iter_num in 2 4 6 8 10 12 14 16 18 20; do
  head_id="$(python3 -c "import json; print(json.load(open('${ARCHIVE_CURRENT}'))['geo'])")"
  echo "checkpoint iter=${iter_num} head=${head_id}" >&2
  for seed in 1 2 3 4 5 6 7 8 9 10; do
    AUTORESEARCH_SEED="${seed}" python3 "${REPO_ROOT}/autoresearch/evaluate_variant.py" \
      --single-fixture "${PUBLIC_FIXTURE}" \
      --manifest "${REPO_ROOT}/autoresearch/eval_suites/search-v1.json" \
      --seeds 1 \
      --baseline-variant "${head_id}" \
      --json-output \
      >> "/tmp/canary-public-${iter_num}.jsonl"

    AUTORESEARCH_SEED="${seed}" python3 "${REPO_ROOT}/autoresearch/evaluate_variant.py" \
      --single-fixture "${HOLDOUT_FIXTURE}" \
      --manifest "${HOLDOUT_MANIFEST}" \
      --seeds 1 \
      --baseline-variant "${head_id}" \
      --json-output \
      >> "/tmp/canary-holdout-${iter_num}.jsonl"
  done
done

echo "Canary complete. 200 evaluations written to /tmp/canary-{public,holdout}-*.jsonl" >&2
echo "Next: invoke the canary agent with these trajectories (Plan B Phase 5 Step 6)." >&2
