"""AUTORESEARCH_AUTO_RENDER env gate test.

Confirms that post_session._auto_render_enabled() reads the env var and
treats the standard skip-values as off. The full post_session_hooks
integration test lives in the substrate-validation runbook (it needs a
real run_script subprocess).
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
POST_SESSION_PATH = (
    REPO_ROOT
    / "autoresearch"
    / "archive"
    / "v006"
    / "runtime"
    / "post_session.py"
)


@pytest.fixture(scope="module")
def post_session_module():
    # The module imports `from workflows import get_workflow_spec` so we
    # need the v006 dir on sys.path during load.
    v006 = REPO_ROOT / "autoresearch" / "archive" / "v006"
    sys.path.insert(0, str(v006))
    spec = importlib.util.spec_from_file_location(
        "post_session_test_module", POST_SESSION_PATH
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["post_session_test_module"] = mod
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path.pop(0)
    return mod


@pytest.mark.parametrize("value", ["1", "true", "on", "yes", "anything-else"])
def test_auto_render_enabled_truthy(monkeypatch, post_session_module, value):
    monkeypatch.setenv("AUTORESEARCH_AUTO_RENDER", value)
    assert post_session_module._auto_render_enabled() is True


@pytest.mark.parametrize("value", ["0", "off", "skip", "false", "no",
                                    "FALSE", "OFF", "Skip"])
def test_auto_render_disabled_via_env(monkeypatch, post_session_module, value):
    monkeypatch.setenv("AUTORESEARCH_AUTO_RENDER", value)
    assert post_session_module._auto_render_enabled() is False


def test_auto_render_default_on(monkeypatch, post_session_module):
    monkeypatch.delenv("AUTORESEARCH_AUTO_RENDER", raising=False)
    assert post_session_module._auto_render_enabled() is True
