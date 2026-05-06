#!/usr/bin/env bash
# x_engine daily run. Calls compose.py from gofreddy root.
set -euo pipefail
cd "$(dirname "$0")/.."
exec uv run python -m x_engine.pipeline.compose "$@"
