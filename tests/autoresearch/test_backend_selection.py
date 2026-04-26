"""Backend selection coverage for harness/backend.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add autoresearch dir to path (mirrors harness/backend.py's own bootstrap).
# Insert at index 0 *after* removing any pre-existing entry so we beat the
# repo-root entry that pytest prepends (otherwise `import harness` resolves
# to the unrelated repo-root harness/ package).
AUTORESEARCH_DIR = str(Path(__file__).resolve().parents[2] / "autoresearch")
if AUTORESEARCH_DIR in sys.path:
    sys.path.remove(AUTORESEARCH_DIR)
sys.path.insert(0, AUTORESEARCH_DIR)

# Drop any stale `harness` module cached against the wrong package so the
# fresh import below resolves against autoresearch/harness/.
for _mod in [m for m in list(sys.modules) if m == "harness" or m.startswith("harness.")]:
    if not getattr(sys.modules[_mod], "__file__", "").startswith(AUTORESEARCH_DIR):
        del sys.modules[_mod]

from harness import backend as harness_backend  # noqa: E402


def test_session_backend_accepts_opencode_via_autoresearch_session_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AUTORESEARCH_SESSION_BACKEND", "opencode")
    monkeypatch.delenv("EVAL_BACKEND_OVERRIDE", raising=False)
    monkeypatch.setattr(harness_backend.shutil, "which", lambda name: f"/usr/local/bin/{name}")
    assert harness_backend.session_backend() == "opencode"


def test_session_backend_accepts_opencode_via_eval_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EVAL_BACKEND_OVERRIDE", "opencode")
    monkeypatch.delenv("AUTORESEARCH_SESSION_BACKEND", raising=False)
    monkeypatch.setattr(harness_backend.shutil, "which", lambda name: f"/usr/local/bin/{name}")
    assert harness_backend.session_backend() == "opencode"
