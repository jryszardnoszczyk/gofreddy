"""Backend selection — which agent CLI and model to use for sessions.

Slim port of autoresearch/harness/backend.py (95 → 70 LOC). Dropped the
runtime/config.py import (v2 has no runtime/ module; SESSION_MODEL is
hardcoded here). Otherwise verbatim — handles #117 content-mod failover
(codex → claude/opencode) and JR's EVAL_BACKEND_OVERRIDE convention.
"""

from __future__ import annotations

import os
import platform
import shutil

# Hardcoded — v1 read this from runtime/config.py; v2 doesn't have that module.
# Operator overrides via AUTORESEARCH_SESSION_MODEL / EVAL_MODEL_OVERRIDE env vars.
SESSION_MODEL = "sonnet"

VALID_BACKENDS = frozenset({"claude", "codex", "opencode"})


def session_backend() -> str:
    forced = (os.environ.get("EVAL_BACKEND_OVERRIDE") or "").strip().lower()
    if forced in VALID_BACKENDS:
        preferred = forced
    else:
        backend = (os.environ.get("AUTORESEARCH_SESSION_BACKEND") or "").strip().lower()
        preferred = backend if backend in VALID_BACKENDS else (
            "codex" if shutil.which("codex") else "claude"
        )

    # Failover chain for missing CLIs (#117 content-mod class).
    if preferred == "codex" and not shutil.which("codex") and shutil.which("claude"):
        return "claude"
    if preferred == "claude" and not shutil.which("claude") and shutil.which("codex"):
        return "codex"
    if preferred == "opencode" and not shutil.which("opencode"):
        if shutil.which("codex"):
            return "codex"
        if shutil.which("claude"):
            return "claude"
    return preferred


def default_session_model(backend: str | None = None) -> str:
    backend = backend or session_backend()
    if backend == "claude":
        return SESSION_MODEL
    if backend == "opencode":
        return os.environ.get(
            "AUTORESEARCH_OPENCODE_DEFAULT_MODEL",
            "openrouter/deepseek/deepseek-v4-pro",
        )
    return "gpt-5.5"  # codex


def session_model() -> str:
    return os.environ.get(
        "EVAL_MODEL_OVERRIDE",
        os.environ.get("AUTORESEARCH_SESSION_MODEL", default_session_model()),
    )


def codex_reasoning_effort() -> str:
    return os.environ.get("AUTORESEARCH_SESSION_REASONING_EFFORT", "high")


def codex_sandbox() -> str:
    """Pick the codex sandbox mode.

    Default: Darwin → workspace-write (Seatbelt available); Linux →
    danger-full-access (bubblewrap may be missing; codex would silently
    downgrade workspace-write anyway). Legacy alias `seatbelt` →
    `workspace-write`.
    """
    default = "workspace-write" if platform.system() == "Darwin" else "danger-full-access"
    sandbox = (os.environ.get("AUTORESEARCH_SESSION_SANDBOX") or default).strip().lower()
    return "workspace-write" if sandbox == "seatbelt" else sandbox


def codex_approval_policy() -> str:
    return os.environ.get("AUTORESEARCH_SESSION_APPROVAL_POLICY", "never")


def codex_web_search() -> str:
    return os.environ.get("AUTORESEARCH_SESSION_WEB_SEARCH", "disabled")
