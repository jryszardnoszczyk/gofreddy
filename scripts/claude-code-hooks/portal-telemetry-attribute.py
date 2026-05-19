#!/usr/bin/env python3
"""Resolve CC PostToolUse hook attribution per R5.1 / R5.2 / R5.3 / R5.5.

Pure resolver — no network calls. The bash hook (``portal-telemetry.sh``)
pipes its stdin JSON into this script and reads two newline-separated lines:

    <line 1>: resolved client_id (empty string == operator-internal)
    <line 2>: an ``attribution_conflict`` moment payload as JSON
              (empty string == no conflict)

The bash hook then performs the curl POSTs. This split keeps the resolver
pure-Python (unit-testable) and keeps the hook itself fire-and-forget.

R7 HOOK PATH cases handled (see brainstorm 2026-05-15 lines 271-276):

  (a) env=A, cwd=A          → client_id=A,        no conflict
  (b) env unset, cwd=A      → client_id=A,        no conflict
  (c) env=A, cwd=B          → operator-internal,  conflict (env_vs_cwd_disagree)
  (d) env=A, cwd unset      → client_id=A,        no conflict
  (e) env unset, cwd unset  → operator-internal,  no conflict
  (f) env=invalid-slug      → operator-internal,  conflict (slug_invalid)

R5.5 server-side ``clients`` table existence check happens at the
``/_ingest`` endpoint — this helper does pattern validation only.

This script is INSTALLED ALONGSIDE the bash hook in ``~/.claude/hooks/``
(``cp scripts/claude-code-hooks/portal-telemetry-attribute.py ~/.claude/hooks/``).
It MUST NOT import from ``src/`` or ``autoresearch/`` — the install target
has no gofreddy checkout. Standard library only.
"""
from __future__ import annotations

import json
import os
import re
import sys

# Anchored slug regex — kept in sync with src/portal/transcript_tailer.py
# (_SLUG_RE) and the portal route patterns. Centralizing here would force
# a cross-tree import; this is a single line and the drift surface is
# small enough that we duplicate it deliberately.
_SLUG_RE = re.compile(r"^[a-z0-9-]{1,64}$")


def _extract_cwd_slug(cwd: str | None) -> str | None:
    """Return the slug from a ``clients/<slug>/...`` segment in cwd, else None.

    The pattern check (``_SLUG_RE``) is applied by ``resolve_attribution``,
    NOT here — this returns the raw candidate so the caller can distinguish
    "no clients/ segment" (None) from "candidate present but invalid".
    """
    if not cwd:
        return None
    # Normalize: split on `/` after stripping any trailing slash. Path
    # parts are case-sensitive ("Clients/foo" doesn't match).
    parts = cwd.rstrip("/").split("/")
    for i, part in enumerate(parts):
        if part == "clients" and i + 1 < len(parts):
            return parts[i + 1]
    return None


def resolve_attribution(
    env_client_id: str | None,
    cwd: str | None,
) -> tuple[str | None, dict | None]:
    """Compute the (client_id, conflict_payload) pair.

    Args:
      env_client_id: ``GOFREDDY_CLIENT_ID`` from process env. Empty
        string is treated as unset.
      cwd: CC hook's stdin ``cwd`` (the working directory the user's CC
        session was launched from). May be ``None`` if older CC sends no
        cwd.

    Returns:
      ``(client_id, conflict_payload)`` where:
        * ``client_id``: resolved slug or ``None`` for operator-internal.
        * ``conflict_payload``: ``dict`` shaped as an ``/_ingest`` POST
          body for the ``attribution_conflict`` moment, or ``None`` if no
          conflict to emit.

    Failure modes covered:
      * env set + invalid slug (R5.5 client-side)  → conflict ``slug_invalid``
      * env set + cwd set + disagree   (R5.3)      → conflict ``env_vs_cwd_disagree``

    Cwd-only invalid-slug failure is NOT emitted here: if env is unset
    and cwd has a malformed ``clients/<bad>/`` segment, we fall through
    to operator-internal silently. The tailer's ``attribute_session``
    will catch it later and emit the conflict moment then — this hook
    doesn't have the DB connection to disambiguate slug_invalid from
    slug_unknown, and we don't want two emissions on the same session.
    """
    env_candidate = (env_client_id or "").strip() or None
    cwd_candidate = _extract_cwd_slug(cwd)

    # R5.5 client-side: env present but malformed pattern → REFUSE.
    if env_candidate is not None and not _SLUG_RE.match(env_candidate):
        return None, {
            "kind": "moment",
            "source": "claude_code",
            "metadata": {
                "moment_kind": "attribution_conflict",
                "title": "GOFREDDY_CLIENT_ID failed pattern validation",
                "reason": "slug_invalid",
                "env_client_id": env_candidate,
                "cwd": cwd or "",
            },
        }

    # Cwd candidate, if present, must also be pattern-valid to be considered.
    # Invalid-cwd is silently treated as no-cwd-candidate here (see docstring).
    if cwd_candidate is not None and not _SLUG_RE.match(cwd_candidate):
        cwd_candidate = None

    # R5.3: env AND cwd both set AND disagree → conflict.
    if (
        env_candidate is not None
        and cwd_candidate is not None
        and env_candidate != cwd_candidate
    ):
        return None, {
            "kind": "moment",
            "source": "claude_code",
            "metadata": {
                "moment_kind": "attribution_conflict",
                "title": "env-vs-cwd disagree",
                "reason": "env_vs_cwd_disagree",
                "env_client_id": env_candidate,
                "cwd_client_id": cwd_candidate,
                "cwd": cwd or "",
            },
        }

    # Happy paths:
    # (a) env=A, cwd=A → A     (b) env unset, cwd=A → A
    # (d) env=A, cwd unset → A (e) env unset, cwd unset → None
    if env_candidate is not None:
        return env_candidate, None
    if cwd_candidate is not None:
        return cwd_candidate, None
    return None, None


def main() -> int:
    """CLI entry — reads stdin JSON + env, prints two output lines.

    Exits 0 always (the bash hook is fire-and-forget; this resolver
    can't usefully fail). Parse errors fall through to operator-internal.
    """
    try:
        raw = sys.stdin.read()
        hook_payload = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, ValueError):
        hook_payload = {}

    env_client_id = os.environ.get("GOFREDDY_CLIENT_ID")
    cwd = hook_payload.get("cwd") if isinstance(hook_payload, dict) else None

    resolved_client_id, conflict_payload = resolve_attribution(
        env_client_id=env_client_id,
        cwd=cwd if isinstance(cwd, str) else None,
    )

    # Line 1: resolved client_id, or empty for operator-internal.
    print(resolved_client_id or "")
    # Line 2: conflict payload JSON, or empty.
    if conflict_payload is not None:
        # Ensure session_id is propagated if CC supplied one — gives the
        # operator-internal moment a join key against the later tool_call.
        sid = hook_payload.get("session_id") if isinstance(hook_payload, dict) else None
        if isinstance(sid, str) and sid:
            conflict_payload["session_id"] = sid
        print(json.dumps(conflict_payload, separators=(",", ":")))
    else:
        print("")

    return 0


if __name__ == "__main__":
    sys.exit(main())
