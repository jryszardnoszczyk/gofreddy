#!/usr/bin/env bash
# Evolution loop — backward-compat shim. Real logic is in evolve.py.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/evolve.py" "$@"
