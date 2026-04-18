#!/bin/bash
# Auto-restart wrapper for the gofreddy backend.
# Use during multi-hour autoresearch evolution runs to survive uvicorn crashes.
# Ported from freddy/scripts/run_backend.sh; gofreddy exposes `app` directly
# (not a factory) so the uvicorn invocation drops `--factory`.
set -euo pipefail
echo "[run_backend] Starting backend on :8000 — Ctrl+C to stop" >&2
while true; do
    uv run uvicorn src.api.main:app --host 127.0.0.1 --port 8000 || true
    echo "[run_backend] Backend exited at $(date), restarting in 2s..." >&2
    sleep 2
done
