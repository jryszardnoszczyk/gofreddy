"""linkedin_engine substrate tests — angle_id + session_dir env-bridge.

Mirrors test_x_engine_substrate.py shape with LINKEDIN_ENGINE_ prefixes.
See that file's docstring for the synthetic-package loader rationale.
"""

from __future__ import annotations

import importlib.util
import os
import sys
import types
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
LANE_WORKFLOWS = REPO_ROOT / "autoresearch" / "archive" / "v007-curated" / "workflows"
PKG_NAME = "_test_v007_workflows_li"


@pytest.fixture(autouse=True)
def _set_voice_persona_ref(monkeypatch: pytest.MonkeyPatch):
    """U11 (commit c1dc44e) added `LINKEDIN_ENGINE_VOICE_PERSONA_REF`
    as a hard-required env var in configure_env() — the pre-U11 tests
    in this file were authored against the pre-U11 contract and need
    the env set or they raise RuntimeError on every configure_env call.

    This is NOT a pre-existing env-only failure (as a stale handoff
    classified it) — it's a CE-review-corrected test-fixture update
    making the regression invariant explicit. The substrate test that
    pins the U11 contract itself (RuntimeError on missing env) lives
    in test_linkedin_engine_voice_migration.py.
    """
    monkeypatch.setenv("LINKEDIN_ENGINE_VOICE_PERSONA_REF", "jr")
    yield


@pytest.fixture
def linkedin_engine_module(monkeypatch: pytest.MonkeyPatch):
    pkg = types.ModuleType(PKG_NAME)
    pkg.__path__ = [str(LANE_WORKFLOWS)]
    sys.modules[PKG_NAME] = pkg

    spec = importlib.util.spec_from_file_location(
        f"{PKG_NAME}.linkedin_engine",
        LANE_WORKFLOWS / "linkedin_engine.py",
        submodule_search_locations=None,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"{PKG_NAME}.linkedin_engine"] = module
    spec.loader.exec_module(module)

    yield module

    sys.modules.pop(f"{PKG_NAME}.linkedin_engine", None)
    sys.modules.pop(f"{PKG_NAME}.eval_cache", None)
    sys.modules.pop(f"{PKG_NAME}.specs", None)
    sys.modules.pop(PKG_NAME, None)


def test_configure_env_propagates_angle_id_when_context_set(
    linkedin_engine_module, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("AUTORESEARCH_CONTEXT", "121")
    monkeypatch.delenv("LINKEDIN_ENGINE_ANGLE_ID", raising=False)

    linkedin_engine_module.configure_env("jr")

    assert os.environ.get("LINKEDIN_ENGINE_ANGLE_ID") == "121"


def test_configure_env_strips_whitespace_in_angle_id(
    linkedin_engine_module, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("AUTORESEARCH_CONTEXT", "  120  ")
    monkeypatch.delenv("LINKEDIN_ENGINE_ANGLE_ID", raising=False)

    linkedin_engine_module.configure_env("jr")

    assert os.environ.get("LINKEDIN_ENGINE_ANGLE_ID") == "120"


def test_configure_env_noop_when_context_unset(
    linkedin_engine_module, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.delenv("AUTORESEARCH_CONTEXT", raising=False)
    monkeypatch.delenv("LINKEDIN_ENGINE_ANGLE_ID", raising=False)

    linkedin_engine_module.configure_env("jr")

    assert "LINKEDIN_ENGINE_ANGLE_ID" not in os.environ


def test_configure_env_propagates_session_dir(
    linkedin_engine_module, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    target = tmp_path / "sessions" / "linkedin_engine" / "jr"
    monkeypatch.setenv("AUTORESEARCH_SESSION_DIR", str(target))
    monkeypatch.delenv("LINKEDIN_ENGINE_SESSION_DIR", raising=False)

    linkedin_engine_module.configure_env("jr")

    assert os.environ.get("LINKEDIN_ENGINE_SESSION_DIR") == str(target)


def test_configure_env_propagates_both_angle_and_session_dir(
    linkedin_engine_module, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    monkeypatch.setenv("AUTORESEARCH_CONTEXT", "125")
    monkeypatch.setenv("AUTORESEARCH_SESSION_DIR", str(tmp_path))
    monkeypatch.delenv("LINKEDIN_ENGINE_ANGLE_ID", raising=False)
    monkeypatch.delenv("LINKEDIN_ENGINE_SESSION_DIR", raising=False)

    linkedin_engine_module.configure_env("jr")

    assert os.environ.get("LINKEDIN_ENGINE_ANGLE_ID") == "125"
    assert os.environ.get("LINKEDIN_ENGINE_SESSION_DIR") == str(tmp_path)
