"""Pure-stdlib mtime cache helper for workflow eval-result reuse.

Phase 5 (Unit 11 sub-task 4): The mtime cache check was repeated inline in
competitive, monitoring (twice), and storyboard. Extracted here so the
workflow modules can import it via a relative `from .eval_cache import ...`
path that works regardless of how `autoresearch.archive.v001` is loaded
(top-level `sys.path` insertion vs full package import).

Lives inside `workflows/` (not `runtime/`) so the import is package-local
and avoids the workflows → runtime → workflows circular dependency that
the original placement triggered.
"""

from __future__ import annotations

import json
from pathlib import Path


def read_cached_eval_if_fresh(artifact_path: Path, eval_path: Path) -> dict | None:
    """Return the cached eval dict if `eval_path` is newer than `artifact_path`.

    The eval is considered fresh when both files exist, the eval mtime is at
    least the artifact mtime, the eval JSON parses, and the parsed payload is
    a dict containing a `decision` key. Returns `None` in every other case so
    callers fall through to re-running the evaluator.

    `geo` workflow does not call this — it always re-evaluates.
    """
    if not (eval_path.exists() and artifact_path.exists()):
        return None
    try:
        if eval_path.stat().st_mtime >= artifact_path.stat().st_mtime:
            cached = json.loads(eval_path.read_text(encoding="utf-8", errors="replace"))
            if isinstance(cached, dict) and "decision" in cached:
                return cached
    except (OSError, json.JSONDecodeError):
        pass
    return None
