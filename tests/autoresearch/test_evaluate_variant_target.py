"""EVOLUTION_EVAL_BACKEND validation coverage for evaluate_variant._require_eval_target."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Path-bootstrap mirrors test_backend_selection.py / test_evolve_config.py
# (same harness/ shadow workaround)
_repo_root = Path(__file__).resolve().parents[2]
_autoresearch_dir = _repo_root / "autoresearch"
if str(_autoresearch_dir) in sys.path:
    sys.path.remove(str(_autoresearch_dir))
sys.path.insert(0, str(_autoresearch_dir))
for _mod in [m for m in list(sys.modules) if m == "harness" or m.startswith("harness.")]:
    file_attr = getattr(sys.modules[_mod], "__file__", None) or ""
    if not file_attr.startswith(str(_autoresearch_dir)):
        del sys.modules[_mod]

import evaluate_variant  # noqa: E402


def test_require_eval_target_accepts_opencode_backend() -> None:
    env = {
        "EVOLUTION_EVAL_BACKEND": "opencode",
        "EVOLUTION_EVAL_MODEL": "openrouter/deepseek/deepseek-v3",
    }
    target = evaluate_variant._require_eval_target(env, suite_manifest={})
    assert target.backend == "opencode"
    assert target.model == "openrouter/deepseek/deepseek-v3"


def test_require_eval_target_rejects_unknown_backend() -> None:
    env = {
        "EVOLUTION_EVAL_BACKEND": "frobnicator",
        "EVOLUTION_EVAL_MODEL": "x",
    }
    with pytest.raises(RuntimeError, match="EVOLUTION_EVAL_BACKEND"):
        evaluate_variant._require_eval_target(env, suite_manifest={})
