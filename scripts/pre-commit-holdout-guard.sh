#!/usr/bin/env bash
# Plan B Phase 2 Step 9f — pre-commit guard against HOLDOUT_*_API_KEY leakage.
#
# Refuses any commit that introduces a reference to a holdout credential
# env-var name OUTSIDE .github/workflows/holdout-refresh.yml. Proposer-visible
# files must never mention these names — either by accident (docs) or
# malicious insertion (a compromised variant prompt could learn the keys
# exist and search for them at runtime).
#
# Wire up:
#   ln -sf ../../scripts/pre-commit-holdout-guard.sh .git/hooks/pre-commit
#   chmod +x .git/hooks/pre-commit
set -euo pipefail

ALLOWED_FILE=".github/workflows/holdout-refresh.yml"
FORBIDDEN_PATTERN='HOLDOUT_(FREDDY|XPOZ|OPENAI)_API_KEY'

# Files staged for commit that are NOT the allowed workflow file.
mapfile -t offending < <(
  git diff --cached --name-only --diff-filter=ACMR \
    | grep -v "^${ALLOWED_FILE}\$" \
    | xargs -I{} -r git diff --cached --no-color -- {} \
    | grep -oE "${FORBIDDEN_PATTERN}" || true
)

if [[ ${#offending[@]} -gt 0 ]]; then
  echo "ERROR: pre-commit guard — HOLDOUT_*_API_KEY references found outside ${ALLOWED_FILE}:" >&2
  echo >&2
  git diff --cached --name-only --diff-filter=ACMR \
    | grep -v "^${ALLOWED_FILE}\$" \
    | xargs -I{} -r sh -c 'git diff --cached --no-color -- "$1" | grep -n -E "'"${FORBIDDEN_PATTERN}"'" | sed "s|^|$1:|"' _ {} >&2
  echo >&2
  echo "Holdout credential env-var names must ONLY appear in the refresh workflow." >&2
  echo "If this is a documentation reference, redact the actual name (use HOLDOUT_*_API_KEY placeholder)." >&2
  exit 1
fi

exit 0
