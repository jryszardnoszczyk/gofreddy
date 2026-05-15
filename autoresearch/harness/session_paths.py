"""Per-fixture session directory resolution (task #97).

x_engine + linkedin fixtures share client="jr"; without context-aware
nesting they overwrote each other's results.jsonl. Other lanes have
unique-per-fixture clients and keep the legacy 2-level path.
"""
from __future__ import annotations

import re
from pathlib import Path

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
    """``base/sessions/<domain>/<client>[/<context>]`` — context appended only
    for lanes in LANES_NEEDING_CONTEXT_ISOLATION when non-empty."""
    base = Path(base)
    leaf = (context or "").strip()
    if leaf and domain in LANES_NEEDING_CONTEXT_ISOLATION:
        safe = re.sub(r"[^A-Za-z0-9_-]", "_", leaf)[:64]
        return base / "sessions" / domain / client / safe
    return base / "sessions" / domain / client


def find_variant_root(session_dir: Path) -> Path:
    """Walk up to the variant root (parent of ``sessions/``), depth-agnostic.
    Lets callers avoid hardcoded ``parents[N]`` arithmetic when session_dir
    shape varies by lane."""
    session_dir = Path(session_dir)
    for parent in session_dir.parents:
        if parent.name == "sessions":
            return parent.parent
    raise ValueError(f"no 'sessions/' ancestor under {session_dir}")
