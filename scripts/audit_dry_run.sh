#!/usr/bin/env bash
# Marketing audit v1 — guided dry-run helper.
#
# Walks JR through the §7.7 acceptance run against a test prospect URL.
# Bails early if prerequisites aren't met. Each step prints the next
# expected action so JR can resume between gates without remembering
# the full sequence.
#
# Usage:
#   ./scripts/audit_dry_run.sh <slug> <domain>
#   ./scripts/audit_dry_run.sh test-1 example.com

set -euo pipefail

SLUG="${1:-}"
DOMAIN="${2:-}"

if [[ -z "$SLUG" || -z "$DOMAIN" ]]; then
  cat <<EOF
Usage: $0 <slug> <domain>
Example: $0 test-prospect-1 example.com

Prerequisites:
  • Provider keys set (see scripts/audit_provider_check.py --human)
  • Claude/Codex/OpenCode CLI on PATH
  • ANTHROPIC_API_KEY (or equivalent for chosen LLM)

This script does NOT auto-run all gates — JR makes a manual decision
between each (intake-confirm, mark-paid, publish). It prints the next
command after each successful step.
EOF
  exit 2
fi

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# Auto-load .env from worktree OR main-repo root so the freddy CLI +
# audit pipeline see provider keys regardless of where this script runs.
ENV_FILE=""
for ancestor in "$REPO_ROOT" "$REPO_ROOT/.." "$REPO_ROOT/../.." "$REPO_ROOT/../../.." "$REPO_ROOT/../../../.."; do
  if [[ -f "$ancestor/.env" ]]; then
    ENV_FILE="$ancestor/.env"
    break
  fi
done

if [[ -n "$ENV_FILE" ]]; then
  echo "Loading env from $ENV_FILE"
  set -o allexport
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +o allexport
fi

# ── Step 0: precheck ─────────────────────────────────────────────────
echo "═══ Step 0: provider precheck ═══"
if ! python scripts/audit_provider_check.py --human; then
  cat <<EOF

⚠  Some REQUIRED providers are missing. The audit will run but content
   will be heavily gap-flagged. Continue? [y/N]
EOF
  read -r reply
  [[ "$reply" == "y" || "$reply" == "Y" ]] || exit 1
fi

# ── Step 1: init ─────────────────────────────────────────────────────
echo
echo "═══ Step 1: freddy audit init $SLUG --domain $DOMAIN ═══"
freddy audit init "$SLUG" --domain "$DOMAIN"

# ── Step 2: first run → halts at intake gate ─────────────────────────
echo
echo "═══ Step 2: first run (Stages 0/1/1b/1c) — halts at intake gate ═══"
freddy audit run "$SLUG"

# Surface where the brief landed
WORKSPACE="${GOFREDDY_CLIENTS_DIR:-/data/clients}/$SLUG/audit"
if [[ ! -d "$WORKSPACE" ]]; then
  # Fall back: freddy CLI computes its own clients_dir
  WORKSPACE=$(find "$HOME"/clients ./clients -maxdepth 3 -name "audit" -type d 2>/dev/null | head -1)
fi
cat <<EOF

🛑 Halted at INTAKE GATE.
   Brief: $WORKSPACE/prediscovery/brief.md
   Gaps:  $WORKSPACE/prediscovery/gaps.jsonl

   Review and when satisfied, run:
     freddy audit confirm-brief $SLUG
     freddy audit mark-paid $SLUG --stripe-event-id manual
     freddy audit run $SLUG                  # produces deliverable
     freddy audit publish $SLUG --dry-run    # skips R2 upload
     freddy audit close-engagement $SLUG --converted N
EOF
