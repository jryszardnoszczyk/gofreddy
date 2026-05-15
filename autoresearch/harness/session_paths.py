"""Per-fixture session directory resolution (task #97).

Pre-fix (2026-05-15), every fixture wrote to ``sessions/<domain>/<client>/``.
That collides when multiple fixtures share a client — which is exactly what
x_engine + linkedin_engine do (all 4 fixtures use ``client="jr"`` and
distinguish themselves only by ``context`` = angle_id 121/122/123/124).

Symptom: parallel x_engine fixtures raced on the shared session_dir,
overwriting each other's results.jsonl, drafts/, .last_eval_cache.json,
report.md. Verified in archive/v007-curated/sessions/x_engine/jr/ —
results.jsonl had 1 line referencing only angle 123; the other 3
fixtures' results were clobbered. The MAX_PARALLEL_AGENTS=1 workaround
masked the crash but tripled wall time.

Fix: lane-conditional path nesting. Lanes whose fixtures share a client
get a 3-level path (`sessions/<lane>/<client>/<context>/`); lanes whose
client uniquely identifies a fixture (geo, competitive, monitoring,
storyboard, marketing_audit) keep the 2-level path unchanged. This
preserves backwards compatibility with all existing archive directories
and avoids touching ``parents[N]`` arithmetic across the codebase for
unaffected lanes.

DOWNSTREAM READERS: glob-based walkers (``harness/telemetry.py``,
``evolve_ops.py:_collect_report_artifacts``) need ``rglob`` (depth-agnostic)
or explicit handling of both shapes. ``parents[N]`` lookups in lane-specific
session_eval files (e.g. ``session_eval_x_engine.py:voice_path``) need to
walk up by lane shape, not a fixed depth.
"""
from __future__ import annotations

import re
from pathlib import Path

# Lanes that share a single ``client`` value across multiple fixtures and
# therefore require ``context`` (the angle_id) in the session_dir path to
# isolate per-fixture state. Other lanes have unique-per-fixture clients
# (e.g. monitoring/Shopify, geo/nubank) so the 2-level legacy path is fine.
LANES_NEEDING_CONTEXT_ISOLATION: frozenset[str] = frozenset({
    "x_engine",
    "linkedin_engine",
})


def session_dir_for(
    base: Path,
    domain: str,
    client: str,
    context: str | None = None,
) -> Path:
    """Canonical session directory for a fixture.

    Returns ``base/sessions/<domain>/<client>/<context>`` for
    x_engine + linkedin_engine when context is non-empty; legacy
    ``base/sessions/<domain>/<client>`` for every other lane (and for
    x_engine/linkedin when context is empty, e.g. cold-start invocations).

    Context is sanitized to filesystem-safe chars and capped at 64 to
    defend against pathological angle_ids — angle IDs are alphanumeric
    today, but the helper guards against future schema drift.
    """
    base = Path(base)
    leaf = (context or "").strip()
    if leaf and domain in LANES_NEEDING_CONTEXT_ISOLATION:
        safe = re.sub(r"[^A-Za-z0-9_-]", "_", leaf)[:64]
        return base / "sessions" / domain / client / safe
    return base / "sessions" / domain / client


def find_variant_root(session_dir: Path) -> Path:
    """Return the variant root above a session_dir, regardless of shape.

    Walks up looking for ``sessions/`` so callers don't hardcode
    ``parents[2]`` (legacy 2-level) vs ``parents[3]`` (new 3-level).
    Used by ``session_eval_x_engine.py`` to find ``voice.md`` and any
    other lane-eval that resolves variant-relative paths.

    Raises ``ValueError`` if no ``sessions/`` ancestor is found — the
    caller is in an unexpected location and should surface loudly rather
    than silently using an arbitrary parent.
    """
    session_dir = Path(session_dir)
    for parent in session_dir.parents:
        if parent.name == "sessions":
            return parent.parent
    raise ValueError(
        f"find_variant_root: no 'sessions/' ancestor found under {session_dir}"
    )
