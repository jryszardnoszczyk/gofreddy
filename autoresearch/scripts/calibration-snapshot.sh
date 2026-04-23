#!/usr/bin/env bash
# Plan B Phase 4 Step 3b — MVP carve-out log-only replacement.
#
# The full bi-directional judge-calibration drift detection is DEFERRED
# per the MVP carve-out (see the "MVP carve-out" section of the Plan B
# doc). This tiny helper records per-variant per-fixture scores of a
# stable calibration variant set, appending one event per score into the
# unified events log. Follow-up `docs/plans/NNNN-judge-calibration-drift.md`
# will reason about this data.
#
# Intended cadence: monthly (operator cron). Idempotent — calibration
# events have timestamps so multiple runs produce duplicates rather than
# overwrites. Downstream analysis groups by variant + fixture and sorts
# by timestamp.
#
# Usage:
#   ./autoresearch/scripts/calibration-snapshot.sh
#
# Cost: 3 variants × 3 fixtures × 1 seed = 9 judge invocations.
# Approx. $0.10-$0.50 + 10-30 min wall-clock.
#
# PREREQUISITES: live stack (backend + judges + supabase + creds).
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
SEARCH_MANIFEST="${REPO_ROOT}/autoresearch/eval_suites/search-v1.json"

# Calibration variants: historically stable baselines. Update this list
# only when retiring a variant; never remove a variant that has
# accumulated historical snapshots unless the data is migrating to a
# replacement's history.
CALIBRATION_VARIANTS=("v001" "v006")
# v020 is on the deferred list — will be enabled when it lands.

# Calibration fixture subset: one per domain, none from anchor set
# (anchors drive decisions — we want independent signal).
CALIBRATION_FIXTURES=(
  "geo-moz-homepage"
  "competitive-figma"
  "storyboard-techreview"
)

: "${EVOLUTION_JUDGE_URL:?EVOLUTION_JUDGE_URL not set; source ~/.config/gofreddy/judges.env}"
: "${EVOLUTION_INVOKE_TOKEN:?EVOLUTION_INVOKE_TOKEN not set; source ~/.config/gofreddy/judges.env}"

for variant in "${CALIBRATION_VARIANTS[@]}"; do
  if [[ ! -d "${REPO_ROOT}/autoresearch/archive/${variant}" ]]; then
    echo "WARN: ${variant} not in archive; skipping" >&2
    continue
  fi
  for fixture in "${CALIBRATION_FIXTURES[@]}"; do
    echo "[$(date -u +%FT%TZ)] calibration: variant=${variant} fixture=${fixture}" >&2
    # Score and capture the JSON blob.
    result_json="$(python3 "${REPO_ROOT}/autoresearch/evaluate_variant.py" \
      --single-fixture "search-v1:${fixture}" \
      --manifest "${SEARCH_MANIFEST}" \
      --seeds 1 \
      --baseline-variant "${variant}" \
      --json-output 2>/dev/null || echo '{}')"

    # Log one calibration_score event per (variant, fixture) pair.
    python3 <<PY
import json
from autoresearch.events import log_event

payload = json.loads('''${result_json}''' or '{}')
log_event(
    kind="calibration_score",
    variant=${variant@Q},
    fixture=${fixture@Q},
    median_score=(sum(payload.get("per_seed_scores") or []) / max(1, len(payload.get("per_seed_scores") or []))),
    per_seed_scores=payload.get("per_seed_scores") or [],
    cost_usd=float(payload.get("cost_usd") or 0.0),
    duration_seconds=int(payload.get("duration_seconds") or 0),
    structural_passed=bool(payload.get("structural_passed", True)),
)
PY
  done
done

echo "Calibration snapshot complete. Query the log:" >&2
echo "  jq 'select(.kind == \"calibration_score\")' ~/.local/share/gofreddy/events.jsonl" >&2
