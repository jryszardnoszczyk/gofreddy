"""Tier A safety primitives — read-only / capability-restricted agent sessions.

These primitives back the audit pipeline's scoped Claude SDK sessions, where
the destructive capability is *positively* absent from the agent's toolbelt
rather than blocked by post-hoc checks. No production consumer exists yet;
the audit plan's Stage 5 ``scoped_tools.py`` will wrap these with concrete
allowed-tool lists (e.g. ``build_demo_flow_toolbelt`` for Playwright
observation, ``build_welcome_email_toolbelt`` for IMAP-read inboxes).

Tests for this module live with the audit plan's implementation, not here.
"""
from __future__ import annotations

import sys
from typing import Mapping, Sequence


def build_scoped_toolbelt(
    name: str, allowed_tools: Sequence[str]
) -> Mapping[str, object]:
    """Return a Claude SDK ``ClaudeAgentOptions``-shaped dict for a read-only session.

    The returned mapping carries three reinforcing controls so the safety story
    rests on independent layers, not on "the prompt happened not to ask for it":

    1. ``permission_mode="default"`` — every tool use prompts unless explicitly
       pre-allowed. The Stage 5 audit pipeline pairs this with a CLI-level
       per-action confirm (see :func:`per_action_confirm`).
    2. ``disallowed_tools=[...general-purpose builtins...]`` — deny-lists the
       SDK builtins (``Bash``, ``WebFetch``, ``WebSearch``, ``Write``, ``Edit``,
       ``Task``) even before the prompt-deny stage.
    3. ``allowed_tools=[...allowed_tools...]`` — positive allow-list of the
       caller-supplied scoped MCP tools (e.g. ``mcp__playwright_obs__page_goto``).

    The caller is expected to merge in ``mcp_servers={...}`` with the matching
    scoped MCP server definition. ``name`` is recorded as ``session_name`` for
    log attribution. No SDK import happens here so this primitive stays
    importable in environments without the Claude Agent SDK installed.
    """
    if not allowed_tools:
        raise ValueError(
            "allowed_tools must be non-empty — a scoped session with zero "
            "allowed tools cannot do anything useful and almost always means "
            "the caller forgot to pass the MCP tool list."
        )
    return {
        "session_name": name,
        "permission_mode": "default",
        "disallowed_tools": [
            "Bash", "WebFetch", "WebSearch", "Write", "Edit", "Task",
        ],
        "allowed_tools": list(allowed_tools),
    }


def per_action_confirm(prompt: str, *, stream=None) -> bool:
    """Block on a TTY prompt; return True only if the operator types ``y``/``yes``.

    Used at the moment an audit-pipeline agent identifies an irrecoverable
    operation (form submission, signup completion). Confirmation is not
    pre-approved by any opt-in flag — the flag gates whether the primitive
    can run at all; this gates the specific destructive action.

    In a non-interactive context (CI / scheduler) ``stdin`` is not a TTY and
    this returns False without blocking — the caller's primitive must surface
    the no-confirm result to the audit log so the missing data is visible.
    Pass ``stream`` (defaults to ``sys.stdin``) only for tests.
    """
    if stream is None:
        stream = sys.stdin
    if not getattr(stream, "isatty", lambda: False)():
        return False
    try:
        sys.stdout.write(f"{prompt} [y/N] ")
        sys.stdout.flush()
        answer = stream.readline().strip().lower()
    except (EOFError, KeyboardInterrupt):
        return False
    return answer in {"y", "yes"}
