#!/usr/bin/env bash
# GEO verification — backward-compat shim. Real logic is in geo_verify.py.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/geo_verify.py" "$@"
