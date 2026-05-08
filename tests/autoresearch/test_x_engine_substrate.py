"""x_engine substrate tests — angle_id + session_dir env-bridge.

Validates the fix landed 2026-05-08 evening for the v007-curated x_engine
lane: ``configure_env`` must propagate ``AUTORESEARCH_CONTEXT`` →
``X_ENGINE_ANGLE_ID`` and ``AUTORESEARCH_SESSION_DIR`` →
``X_ENGINE_SESSION_DIR`` so the agent prompt can read them.

Pre-fix symptom: agent ignored fixture context, called ``xeng angle-list``,
and picked the latest angle regardless of the fixture's intended angle.

Loader note: x_engine.py uses relative imports (``from .eval_cache import …``)
so it must be loaded as a member of a package, not a free-standing module.
The fixture wires a synthetic ``v007_workflows`` package whose
``__path__`` points at the lane workflows directory; submodule
``v007_workflows.x_engine`` then resolves the relative imports against it.
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
PKG_NAME = "_test_v007_workflows"


@pytest.fixture
def x_engine_module(monkeypatch: pytest.MonkeyPatch):
    # Synthetic parent package so ``from .eval_cache import …`` resolves.
    pkg = types.ModuleType(PKG_NAME)
    pkg.__path__ = [str(LANE_WORKFLOWS)]
    sys.modules[PKG_NAME] = pkg

    spec = importlib.util.spec_from_file_location(
        f"{PKG_NAME}.x_engine",
        LANE_WORKFLOWS / "x_engine.py",
        submodule_search_locations=None,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"{PKG_NAME}.x_engine"] = module
    spec.loader.exec_module(module)

    yield module

    sys.modules.pop(f"{PKG_NAME}.x_engine", None)
    sys.modules.pop(f"{PKG_NAME}.eval_cache", None)
    sys.modules.pop(f"{PKG_NAME}.specs", None)
    sys.modules.pop(PKG_NAME, None)


def test_configure_env_propagates_angle_id_when_context_set(
    x_engine_module, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("AUTORESEARCH_CONTEXT", "121")
    monkeypatch.delenv("X_ENGINE_ANGLE_ID", raising=False)

    x_engine_module.configure_env("jr")

    assert os.environ.get("X_ENGINE_ANGLE_ID") == "121"


def test_configure_env_strips_whitespace_in_angle_id(
    x_engine_module, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("AUTORESEARCH_CONTEXT", "  120  ")
    monkeypatch.delenv("X_ENGINE_ANGLE_ID", raising=False)

    x_engine_module.configure_env("jr")

    assert os.environ.get("X_ENGINE_ANGLE_ID") == "120"


def test_configure_env_noop_when_context_unset(
    x_engine_module, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.delenv("AUTORESEARCH_CONTEXT", raising=False)
    monkeypatch.delenv("X_ENGINE_ANGLE_ID", raising=False)

    x_engine_module.configure_env("jr")

    assert "X_ENGINE_ANGLE_ID" not in os.environ


def test_configure_env_noop_when_context_empty_string(
    x_engine_module, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("AUTORESEARCH_CONTEXT", "")
    monkeypatch.delenv("X_ENGINE_ANGLE_ID", raising=False)

    x_engine_module.configure_env("jr")

    assert "X_ENGINE_ANGLE_ID" not in os.environ


def test_configure_env_propagates_session_dir(
    x_engine_module, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    target = tmp_path / "sessions" / "x_engine" / "jr"
    monkeypatch.setenv("AUTORESEARCH_SESSION_DIR", str(target))
    monkeypatch.delenv("X_ENGINE_SESSION_DIR", raising=False)

    x_engine_module.configure_env("jr")

    assert os.environ.get("X_ENGINE_SESSION_DIR") == str(target)


def test_configure_env_propagates_both_angle_and_session_dir(
    x_engine_module, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    monkeypatch.setenv("AUTORESEARCH_CONTEXT", "125")
    monkeypatch.setenv("AUTORESEARCH_SESSION_DIR", str(tmp_path))
    monkeypatch.delenv("X_ENGINE_ANGLE_ID", raising=False)
    monkeypatch.delenv("X_ENGINE_SESSION_DIR", raising=False)

    x_engine_module.configure_env("jr")

    assert os.environ.get("X_ENGINE_ANGLE_ID") == "125"
    assert os.environ.get("X_ENGINE_SESSION_DIR") == str(tmp_path)


def test_configure_env_materializes_voice_md_into_current_runtime(
    x_engine_module, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """P0 #104 fix: when current_runtime exists but lacks voice.md,
    configure_env should copy it from the lane's v007-curated programs
    dir. Uses monkeypatch on _VARIANT_ROOT to point at a temp source."""
    # Synthetic v007-curated/programs/references/voice.md
    fake_variant = tmp_path / "v007-curated"
    fake_voice_src = fake_variant / "programs" / "references" / "voice.md"
    fake_voice_src.parent.mkdir(parents=True)
    fake_voice_src.write_text("# JR voice substrate\n")

    # Synthetic current_runtime peer
    fake_runtime = tmp_path / "current_runtime"
    fake_runtime.mkdir()
    runtime_voice = fake_runtime / "programs" / "references" / "voice.md"
    assert not runtime_voice.exists()

    # Patch lane module's _VARIANT_ROOT + _VOICE_SUBSTRATE to the fakes
    monkeypatch.setattr(x_engine_module, "_VARIANT_ROOT", fake_variant)
    monkeypatch.setattr(x_engine_module, "_VOICE_SUBSTRATE", fake_voice_src)

    x_engine_module.configure_env("jr")

    assert runtime_voice.exists()
    assert runtime_voice.read_text() == "# JR voice substrate\n"


def test_configure_env_skips_voice_md_copy_when_already_present(
    x_engine_module, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """If voice.md already exists in current_runtime, don't overwrite —
    the meta-agent or operator may have placed a different version."""
    fake_variant = tmp_path / "v007-curated"
    fake_voice_src = fake_variant / "programs" / "references" / "voice.md"
    fake_voice_src.parent.mkdir(parents=True)
    fake_voice_src.write_text("# JR voice substrate (canonical)\n")

    fake_runtime = tmp_path / "current_runtime"
    runtime_voice = fake_runtime / "programs" / "references" / "voice.md"
    runtime_voice.parent.mkdir(parents=True)
    runtime_voice.write_text("# Mid-session edit (do not overwrite)\n")

    monkeypatch.setattr(x_engine_module, "_VARIANT_ROOT", fake_variant)
    monkeypatch.setattr(x_engine_module, "_VOICE_SUBSTRATE", fake_voice_src)

    x_engine_module.configure_env("jr")

    assert runtime_voice.read_text() == "# Mid-session edit (do not overwrite)\n"


def test_configure_env_silent_when_current_runtime_missing(
    x_engine_module, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """If current_runtime doesn't exist (fresh checkout, no
    materialization yet), configure_env shouldn't crash — just skip."""
    fake_variant = tmp_path / "v007-curated"
    fake_voice_src = fake_variant / "programs" / "references" / "voice.md"
    fake_voice_src.parent.mkdir(parents=True)
    fake_voice_src.write_text("# voice\n")

    # No current_runtime dir created.
    monkeypatch.setattr(x_engine_module, "_VARIANT_ROOT", fake_variant)
    monkeypatch.setattr(x_engine_module, "_VOICE_SUBSTRATE", fake_voice_src)

    # Should not raise
    x_engine_module.configure_env("jr")

    assert not (tmp_path / "current_runtime").exists()
