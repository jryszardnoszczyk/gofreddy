"""Per-step model split (2026-05-13).

Validates that the inner fixture-session backend/model is resolved
independently from the meta-agent backend/model, with the priority chain:

  LaneSpec override > CLI flag > EVOLUTION_INNER_* env > EVOLUTION_EVAL_* env

CRITIQUE_BACKEND env-var dispatch in judges/session/agents/* is covered
in tests/judges/test_critique_review_backend_dispatch.py — putting it here
fails because autoresearch/judges/__init__.py shadows the top-level
judges/ package once autoresearch/ is on sys.path.

Memory ref: project-evolution-redesign-implementation-checklist-2026-05-13.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Path-bootstrap mirrors test_evaluate_variant_target.py.
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
import evolve  # noqa: E402


# --------------------------------------------------------------------------- #
# Step 1.1 + 1.3: LaneSpec override + _resolve_inner_target priority chain
# --------------------------------------------------------------------------- #


def test_geo_lane_inner_override_beats_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """geo's LaneSpec inner_backend=claude/inner_model=sonnet must beat
    EVOLUTION_INNER_* env vars set to codex (the cyber-filter regression
    case we're guarding against)."""
    monkeypatch.setenv("EVOLUTION_INNER_BACKEND", "codex")
    monkeypatch.setenv("EVOLUTION_INNER_MODEL", "gpt-5.5")
    monkeypatch.delenv("EVOLUTION_INNER_REASONING_EFFORT", raising=False)
    monkeypatch.delenv("EVOLUTION_EVAL_REASONING_EFFORT", raising=False)
    backend, model, _ = evolve._resolve_inner_target(
        lane="geo", cli_backend=None, cli_model=None,
    )
    assert backend == "claude"
    assert model == "sonnet"


def test_non_geo_lane_falls_through_to_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Lanes without a LaneSpec override (e.g. monitoring) must honor the
    EVOLUTION_INNER_* env. Use monitoring not competitive — the latter has
    its own claude/sonnet override since the codex cyber filter rejects
    competitive-intel prompts (added 2026-05-13 mid-Phase-3)."""
    monkeypatch.setenv("EVOLUTION_INNER_BACKEND", "codex")
    monkeypatch.setenv("EVOLUTION_INNER_MODEL", "gpt-5.5")
    backend, model, _ = evolve._resolve_inner_target(
        lane="monitoring", cli_backend=None, cli_model=None,
    )
    assert backend == "codex"
    assert model == "gpt-5.5"


def test_cli_flag_beats_env_when_no_lane_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EVOLUTION_INNER_BACKEND", "codex")
    monkeypatch.setenv("EVOLUTION_INNER_MODEL", "gpt-5.5")
    backend, model, _ = evolve._resolve_inner_target(
        lane="monitoring", cli_backend="claude", cli_model="opus",
    )
    assert backend == "claude"
    assert model == "opus"


def test_back_compat_eval_env_when_inner_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pre-2026-05-13 launches set only EVOLUTION_EVAL_*. Those must still
    drive the inner target on lanes WITHOUT a LaneSpec override so old
    launch scripts keep working. Use monitoring (no override) — competitive
    + geo now have lane-locked claude/sonnet inner."""
    monkeypatch.delenv("EVOLUTION_INNER_BACKEND", raising=False)
    monkeypatch.delenv("EVOLUTION_INNER_MODEL", raising=False)
    monkeypatch.setenv("EVOLUTION_EVAL_BACKEND", "claude")
    monkeypatch.setenv("EVOLUTION_EVAL_MODEL", "opus")
    backend, model, _ = evolve._resolve_inner_target(
        lane="monitoring", cli_backend=None, cli_model=None,
    )
    assert backend == "claude"
    assert model == "opus"


def test_competitive_lane_override_beats_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """competitive's LaneSpec override (claude/sonnet) MUST beat env vars
    set to codex — confirms we dodge the codex cyber filter that hit Phase 3
    epic/figma/canva fixtures regardless of operator launch flags."""
    monkeypatch.setenv("EVOLUTION_INNER_BACKEND", "codex")
    monkeypatch.setenv("EVOLUTION_INNER_MODEL", "gpt-5.5")
    backend, model, _ = evolve._resolve_inner_target(
        lane="competitive", cli_backend=None, cli_model=None,
    )
    assert backend == "claude"
    assert model == "sonnet"


# --------------------------------------------------------------------------- #
# Step 1.3 (continued): _require_eval_target reads INNER_* before EVAL_*
# --------------------------------------------------------------------------- #


def test_require_eval_target_prefers_inner_over_eval() -> None:
    env = {
        "EVOLUTION_INNER_BACKEND": "codex",
        "EVOLUTION_INNER_MODEL": "gpt-5.5",
        "EVOLUTION_EVAL_BACKEND": "claude",
        "EVOLUTION_EVAL_MODEL": "opus",
    }
    target = evaluate_variant._require_eval_target(env, suite_manifest={})
    assert target.backend == "codex"
    assert target.model == "gpt-5.5"


def test_require_eval_target_skips_suite_check_when_split() -> None:
    """When INNER and EVAL diverge, the suite-manifest cross-check (which
    pins the EVAL pair against the manifest's eval_target) must skip —
    otherwise diverged operators get false 'manifest mismatch' rejects."""
    env = {
        "EVOLUTION_INNER_BACKEND": "codex",
        "EVOLUTION_INNER_MODEL": "gpt-5.5",
        "EVOLUTION_EVAL_BACKEND": "claude",
        "EVOLUTION_EVAL_MODEL": "opus",
    }
    suite = {"eval_target": {"backend": "claude", "model": "opus"}}
    # Should NOT raise — INNER differs from EVAL → manifest check skipped.
    target = evaluate_variant._require_eval_target(env, suite_manifest=suite)
    assert target.backend == "codex"


# Critique/review backend dispatch tests live in
# tests/judges/test_critique_review_backend_dispatch.py
# (see module docstring for sys.path-shadowing rationale).
