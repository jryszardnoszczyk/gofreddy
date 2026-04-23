#!/usr/bin/env bash
# Plan B Phase 4 Step 4 — migration-check with lane-head pinning.
#
# Runs one full evolution iteration on the core lane against the freshly-
# migrated search-v1@1.1 manifest, then asserts the lane head did not move.
# If it did, the pre-flight score-against-cache step auto-promoted a
# candidate and the baseline Phase 5 depends on has shifted. Roll back.
#
# PREREQUISITES (operator must boot these before running):
#   - gofreddy backend running at FREDDY_API_URL
#   - supabase postgres up
#   - evolution-judge-service on :7200 + session-judge-service on :7100
#   - ~/.config/gofreddy/judges.env sourced (EVOLUTION_INVOKE_TOKEN,
#     EVOLUTION_JUDGE_URL, SESSION_* equivalents)
#   - .env sourced (provider keys for the session-judge path)
#
# Exit: 0 = head unchanged (OK to proceed to Phase 5); 1 = head moved +
# rollback attempted (if rollback also failed, manual intervention needed).
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
ARCHIVE_CURRENT="${REPO_ROOT}/autoresearch/archive/current.json"

if [[ ! -f "${ARCHIVE_CURRENT}" ]]; then
  echo "FATAL: ${ARCHIVE_CURRENT} not found. Is the autoresearch archive initialized?" >&2
  exit 1
fi

# Fail loudly if judge credentials or backend URL are missing — without them
# evolve.sh would score against mocked judges and silently produce garbage.
: "${EVOLUTION_JUDGE_URL:?EVOLUTION_JUDGE_URL not set; source ~/.config/gofreddy/judges.env}"
: "${EVOLUTION_INVOKE_TOKEN:?EVOLUTION_INVOKE_TOKEN not set; source ~/.config/gofreddy/judges.env}"
: "${FREDDY_API_URL:?FREDDY_API_URL not set; source .env}"

CORE_HEAD_BEFORE="$(python3 -c "import json; print(json.load(open('${ARCHIVE_CURRENT}'))['core'])")"
echo "core lane head BEFORE migration check: ${CORE_HEAD_BEFORE}" >&2

"${REPO_ROOT}/autoresearch/evolve.sh" run \
  --iterations 1 \
  --candidates-per-iteration 1 \
  --lane core

CORE_HEAD_AFTER="$(python3 -c "import json; print(json.load(open('${ARCHIVE_CURRENT}'))['core'])")"

if [[ "${CORE_HEAD_AFTER}" != "${CORE_HEAD_BEFORE}" ]]; then
  echo "ERROR: migration check auto-promoted ${CORE_HEAD_AFTER} over ${CORE_HEAD_BEFORE}" >&2
  echo "Rolling back: ./autoresearch/evolve.sh promote --undo --lane core" >&2
  "${REPO_ROOT}/autoresearch/evolve.sh" promote --undo --lane core

  CORE_HEAD_AFTER="$(python3 -c "import json; print(json.load(open('${ARCHIVE_CURRENT}'))['core'])")"
  if [[ "${CORE_HEAD_AFTER}" != "${CORE_HEAD_BEFORE}" ]]; then
    echo "FATAL: rollback failed. Manual intervention required." >&2
    exit 1
  fi
  echo "Rollback succeeded; head restored to ${CORE_HEAD_BEFORE}" >&2
  exit 1
fi

echo "OK: core lane head pinned at ${CORE_HEAD_AFTER}" >&2
exit 0
