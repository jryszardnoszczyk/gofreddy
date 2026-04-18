"""Backend selection -- which agent CLI and model to use for sessions."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

HARNESS_DIR = Path(__file__).resolve().parent
AUTORESEARCH_DIR = HARNESS_DIR.parent
if str(AUTORESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(AUTORESEARCH_DIR))

import harness  # noqa: F401,E402  # ensure package-level path setup runs

from runtime import config as runtime_config  # type: ignore  # noqa: E402

SESSION_MODEL = runtime_config.SESSION_MODEL


def session_backend() -> str:
    forced = os.environ.get("EVAL_BACKEND_OVERRIDE", "").strip().lower()
    if forced in {"claude", "codex"}:
        preferred = forced
    else:
        backend = os.environ.get("AUTORESEARCH_SESSION_BACKEND", "").strip().lower()
        if backend in {"claude", "codex"}:
            preferred = backend
        else:
            preferred = "codex" if shutil.which("codex") else "claude"

    if preferred == "codex" and not shutil.which("codex") and shutil.which("claude"):
        return "claude"
    if preferred == "claude" and not shutil.which("claude") and shutil.which("codex"):
        return "codex"
    return preferred


def default_session_model(backend: str | None = None) -> str:
    backend = backend or session_backend()
    return SESSION_MODEL if backend == "claude" else "gpt-5.4"


def session_model() -> str:
    return os.environ.get(
        "EVAL_MODEL_OVERRIDE",
        os.environ.get("AUTORESEARCH_SESSION_MODEL", default_session_model()),
    )


def codex_reasoning_effort() -> str:
    return os.environ.get("AUTORESEARCH_SESSION_REASONING_EFFORT", "high")


def codex_sandbox() -> str:
    sandbox = os.environ.get("AUTORESEARCH_SESSION_SANDBOX", "danger-full-access").strip().lower()
    return "workspace-write" if sandbox == "seatbelt" else sandbox


def codex_approval_policy() -> str:
    return os.environ.get("AUTORESEARCH_SESSION_APPROVAL_POLICY", "never")


def codex_web_search() -> str:
    return os.environ.get("AUTORESEARCH_SESSION_WEB_SEARCH", "disabled")
