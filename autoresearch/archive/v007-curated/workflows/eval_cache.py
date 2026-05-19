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
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .specs import RunSessionEvaluator


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


def evaluate_artifact_glob(
    domain: str,
    session_dir: Path,
    artifact_glob: str,
    output_prefix: str,
    mode: str,
    run_session_evaluator: "RunSessionEvaluator",
    *,
    use_cache: bool = True,
) -> list[dict[str, str | None]]:
    """Iterate artifacts matching ``artifact_glob`` under ``session_dir``,
    evaluate each (or read mtime-cached result), return per-artifact
    decisions.

    Ported from v006 + current_runtime — was missing from v007-curated's
    eval_cache.py despite storyboard.py importing it. The omission only
    surfaced when CE-review testing finding test-4 made tests load
    v007-curated directly instead of current_runtime; before that the
    operator-materialized current_runtime carried this function.

    `use_cache=False` matches geo's "always re-evaluate" semantics.
    Output paths are
    ``session_dir / "evals" / f"{output_prefix}-{artifact.stem}.json"``.
    """
    decisions: list[dict[str, str | None]] = []
    eval_dir = session_dir / "evals"
    for artifact in sorted(session_dir.glob(artifact_glob)):
        output_path = eval_dir / f"{output_prefix}-{artifact.stem}.json"
        cached = read_cached_eval_if_fresh(artifact, output_path) if use_cache else None
        if cached is not None:
            decisions.append({"artifact": artifact.name, "decision": cached["decision"]})
            continue
        data = run_session_evaluator(domain, artifact, session_dir, output_path, mode)
        decisions.append({
            "artifact": artifact.name,
            "decision": data.get("decision") if data else None,
        })
    return decisions
