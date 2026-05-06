"""Thin shim to ``autoresearch/agent_retry.py``.

L3 wants the same backoff + transient-classifier as the autoresearch evolve
loop, but ``src/audit`` shouldn't import from ``autoresearch/`` directly when
that module is not on sys.path (the autoresearch tree is sometimes invoked
from its own directory). This shim attempts the import and falls back to a
local minimal implementation that mirrors the same backoff schedule.

If autoresearch is reachable, behavior is identical. If not, the local
fallback gives 3 attempts with delays (2s, 8s, 30s) between attempts and
classifies any non-zero return code as transient — caller bears the cost
of one extra retry vs. the smarter classifier.
"""
from __future__ import annotations

import os
import time

try:  # pragma: no cover — exercised in production runs
    from autoresearch import agent_retry as _ar  # type: ignore[import-not-found]
    _HAVE_AUTORESEARCH = True
except Exception:  # noqa: BLE001 — anything import-side falls through
    _ar = None  # type: ignore[assignment]
    _HAVE_AUTORESEARCH = False

_FALLBACK_MAX_ATTEMPTS = max(1, int(os.environ.get("OPENCODE_MAX_RETRIES", "3")))
_FALLBACK_BACKOFF_DELAYS = (2.0, 8.0, 30.0)


def max_attempts() -> int:
    if _HAVE_AUTORESEARCH:
        return _ar.max_attempts()
    return _FALLBACK_MAX_ATTEMPTS


def backoff_delay(attempt: int) -> float:
    if _HAVE_AUTORESEARCH:
        return _ar.backoff_delay(attempt)
    if attempt < 1:
        return 0.0
    idx = min(attempt - 1, len(_FALLBACK_BACKOFF_DELAYS) - 1)
    return _FALLBACK_BACKOFF_DELAYS[idx]


def sleep_for_retry(attempt: int) -> None:
    if _HAVE_AUTORESEARCH:
        _ar.sleep_for_retry(attempt)
        return
    time.sleep(backoff_delay(attempt))


def is_transient_failure(
    backend: str,
    returncode: int,
    stdout: bytes | str = b"",
    stderr: bytes | str = b"",
) -> bool:
    if _HAVE_AUTORESEARCH:
        return _ar.is_transient_failure(backend, returncode, stdout, stderr)
    # Local fallback — be lenient, retry any nonzero on the assumption that
    # the autoresearch classifier would have tried as well.
    return returncode != 0
