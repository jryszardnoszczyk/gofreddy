# Multi-provider support via OpenCode — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add OpenCode as a third agentic-CLI backend across the autoresearch pipeline (harness fixer/verifier sessions + evolve meta-agent + per-variant eval subprocess + alert agent + parent-selection JSON judge), enabling OpenRouter and open-source models without rewriting the existing CLI-shaped subprocess architecture.

**Architecture:** Three subprocess agent invocations (harness, meta, eval) each driven by independent env-var-gated backend selectors. Each gets a parallel `opencode` branch in its command builder. The pure-LLM JSON judge gets a `base_url`/`api_key` env-var injection into the existing `AsyncOpenAI` client. The alert agent migrates from `claude -p` subprocess to a backend-switchable subprocess that supports both `claude -p` and `opencode run`. No new orchestration framework, no LiteLLM, no fallback CLI — OpenCode handles every multi-provider use case.

**Tech Stack:** Python 3.13, pytest, OpenAI SDK (`openai`), Pydantic, OpenCode CLI 1.14.25+ (external dependency), Claude Code CLI (existing), Codex CLI (existing).

**Spec:** `docs/superpowers/specs/2026-04-26-multi-provider-agentic-pipeline-design.md`

**Branch:** `plan/multi-provider-opencode-v1`

---

## File Structure

This plan modifies 8 existing files; no new files are created in production code (one new test file is created for telemetry coverage). Each file has one focused change.

| File | Responsibility | Why this file |
|---|---|---|
| `autoresearch/harness/backend.py` | Backend selection for harness sessions | Existing `session_backend()` and `default_session_model()` are the single source of truth for harness backend choice |
| `autoresearch/harness/agent.py` | Harness command-builder + subprocess spawning | Existing `_agent_command()` is the only place that produces the harness CLI argv |
| `autoresearch/evolve.py` | Meta-agent orchestrator backend + command-builder | Existing `load_config()` validates `META_BACKEND`; `_build_meta_command()` produces the meta-agent argv |
| `autoresearch/evaluate_variant.py` | Per-variant eval subprocess validator | Existing `_require_eval_target()` validates `EVOLUTION_EVAL_BACKEND` for the eval subprocess |
| `autoresearch/agent_calls.py` | In-process JSON judge calls (parent selection) | Existing `_call_openai_json()` is the only AsyncOpenAI call site |
| `autoresearch/compute_metrics.py` | Alert agent CLI subprocess | Existing `_run_claude_json()` is the only consumer; rename + branch is the cleanest migration |
| `autoresearch/harness/opencode_jsonl.py` (NEW) | OpenCode JSONL parser utility | Single-purpose helper consumed by `compute_metrics._run_alert_agent_json` and any future cost-capture consumer |
| `autoresearch/README.md` | Operator setup documentation | Existing setup docs at lines 93-95 cover `EVOLUTION_EVAL_BACKEND`; need a parallel example for OpenCode |

| Test file | Covers |
|---|---|
| `tests/autoresearch/test_select_parent.py` (existing — extended) | `agent_calls._call_openai_json` env-var routing |
| `tests/autoresearch/test_compute_metrics_alerts.py` (existing — extended) | Alert-agent backend switching + JSONL parsing |
| `tests/autoresearch/test_opencode_jsonl.py` (NEW) | OpenCode JSONL parser unit tests |
| `tests/autoresearch/test_backend_selection.py` (NEW) | `harness/backend.py` backend selection (currently no dedicated test file) |
| `tests/autoresearch/test_evolve_config.py` (NEW or existing — verify) | `evolve.load_config` META_BACKEND validation |

---

## Task 1: Extend `session_backend()` to allow `opencode`

**Files:**
- Modify: `autoresearch/harness/backend.py:22-37`
- Test: `tests/autoresearch/test_backend_selection.py` (create)

- [ ] **Step 1: Create test file with failing test for opencode acceptance**

Create `tests/autoresearch/test_backend_selection.py`:

```python
"""Backend selection coverage for harness/backend.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add autoresearch dir to path (mirrors harness/backend.py's own bootstrap)
AUTORESEARCH_DIR = Path(__file__).resolve().parents[2] / "autoresearch"
if str(AUTORESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(AUTORESEARCH_DIR))

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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/jryszardnoszczyk/Documents/GitHub/gofreddy && pytest tests/autoresearch/test_backend_selection.py -v`
Expected: FAIL — `session_backend()` returns `"claude"` (or `"codex"`) instead of `"opencode"` because the current allowed-set rejects `"opencode"`.

- [ ] **Step 3: Implement — extend allowed-sets in `session_backend()`**

Edit `autoresearch/harness/backend.py:22-37`. Replace the current function body:

```python
def session_backend() -> str:
    forced = os.environ.get("EVAL_BACKEND_OVERRIDE", "").strip().lower()
    if forced in {"claude", "codex", "opencode"}:
        preferred = forced
    else:
        backend = os.environ.get("AUTORESEARCH_SESSION_BACKEND", "").strip().lower()
        if backend in {"claude", "codex", "opencode"}:
            preferred = backend
        else:
            preferred = "codex" if shutil.which("codex") else "claude"

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
```

Note: opencode is **not** added to the auto-detection fallback at line 31 (`preferred = "codex" if shutil.which("codex") else "claude"`) — opencode must be explicitly chosen by env var. The auto-detect default stays codex/claude only.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/autoresearch/test_backend_selection.py -v`
Expected: PASS — both new tests green.

- [ ] **Step 5: Commit**

```bash
git add autoresearch/harness/backend.py tests/autoresearch/test_backend_selection.py
git commit -m "feat(harness): accept opencode in session_backend() allowed-set"
```

---

## Task 2: Extend `default_session_model()` for opencode

**Files:**
- Modify: `autoresearch/harness/backend.py:40-42`
- Test: `tests/autoresearch/test_backend_selection.py` (extend)

- [ ] **Step 1: Add failing test for opencode default model**

Append to `tests/autoresearch/test_backend_selection.py`:

```python
def test_default_session_model_opencode_uses_env_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AUTORESEARCH_OPENCODE_DEFAULT_MODEL", "openrouter/qwen/qwen3-coder")
    assert harness_backend.default_session_model("opencode") == "openrouter/qwen/qwen3-coder"


def test_default_session_model_opencode_falls_back_to_deepseek(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("AUTORESEARCH_OPENCODE_DEFAULT_MODEL", raising=False)
    assert harness_backend.default_session_model("opencode") == "openrouter/deepseek/deepseek-v3"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/autoresearch/test_backend_selection.py -v -k opencode_uses_env or opencode_falls_back`
Expected: FAIL — current `default_session_model()` returns `"gpt-5.4"` for any non-claude backend (the `else` branch).

- [ ] **Step 3: Implement — add opencode branch to `default_session_model()`**

Edit `autoresearch/harness/backend.py:40-42`. Replace:

```python
def default_session_model(backend: str | None = None) -> str:
    backend = backend or session_backend()
    if backend == "claude":
        return SESSION_MODEL
    if backend == "opencode":
        return os.environ.get(
            "AUTORESEARCH_OPENCODE_DEFAULT_MODEL",
            "openrouter/deepseek/deepseek-v3",
        )
    return "gpt-5.4"  # codex
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/autoresearch/test_backend_selection.py -v`
Expected: PASS — all 4 tests green (2 from Task 1 + 2 from Task 2).

- [ ] **Step 5: Commit**

```bash
git add autoresearch/harness/backend.py tests/autoresearch/test_backend_selection.py
git commit -m "feat(harness): default model for opencode backend"
```

---

## Task 3: Add opencode branch to `_agent_command()` in harness/agent.py

**Files:**
- Modify: `autoresearch/harness/agent.py:38-65`
- Test: `tests/autoresearch/test_backend_selection.py` (extend)

- [ ] **Step 1: Add failing test for opencode command shape**

Append to `tests/autoresearch/test_backend_selection.py`:

```python
def test_agent_command_opencode_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    """harness/agent.py _agent_command() returns opencode argv when backend=opencode."""
    monkeypatch.setenv("AUTORESEARCH_SESSION_BACKEND", "opencode")
    monkeypatch.setattr(harness_backend.shutil, "which", lambda name: f"/usr/local/bin/{name}")

    from harness import agent as harness_agent

    cmd = harness_agent._agent_command(
        model="openrouter/deepseek/deepseek-v3",
        max_turns=20,
        prompt_text="Fix finding F-test-1",
    )

    assert cmd[0] == "opencode"
    assert cmd[1] == "run"
    assert "--dangerously-skip-permissions" in cmd
    assert "-m" in cmd
    assert "openrouter/deepseek/deepseek-v3" in cmd
    assert "--format" in cmd
    assert "json" in cmd
    assert "--dir" in cmd
    assert cmd[-1] == "Fix finding F-test-1"


def test_agent_command_opencode_branch_no_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    """When prompt_text=None, command still well-formed (prompt fed via stdin elsewhere)."""
    monkeypatch.setenv("AUTORESEARCH_SESSION_BACKEND", "opencode")
    monkeypatch.setattr(harness_backend.shutil, "which", lambda name: f"/usr/local/bin/{name}")

    from harness import agent as harness_agent

    cmd = harness_agent._agent_command(
        model="anthropic/claude-opus-4.7",
        max_turns=20,
        prompt_text=None,
    )

    assert cmd[0] == "opencode"
    assert "anthropic/claude-opus-4.7" in cmd
    # No trailing positional prompt arg when prompt_text is None
    assert not cmd[-1].startswith("Fix")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/autoresearch/test_backend_selection.py::test_agent_command_opencode_branch -v`
Expected: FAIL — `_agent_command()` falls through to the codex branch (since opencode isn't matched), returning `["codex", "exec", ...]`.

- [ ] **Step 3: Implement — add opencode branch to `_agent_command()`**

Edit `autoresearch/harness/agent.py:38-65`. Insert a new branch **between** the claude branch (lines 40-48) and the codex fallthrough (line 49):

```python
def _agent_command(model: str, max_turns: int, prompt_text: str | None = None) -> list[str]:
    backend = session_backend()
    if backend == "claude":
        cmd = [
            "claude", "-p", "--model", model,
            "--allowedTools", "Bash,Read,Write,Edit,Glob,Grep",
            "--max-turns", str(max_turns),
        ]
        if prompt_text is not None:
            cmd.append(prompt_text)
        return cmd
    if backend == "opencode":
        cmd = [
            "opencode", "run",
            "--dangerously-skip-permissions",
            "-m", model,
            "--format", "json",
            "--dir", str(SCRIPT_DIR),
        ]
        if prompt_text is not None:
            cmd.append(prompt_text)
        return cmd
    cmd = [
        "codex", "exec",
        "--model", model,
        "--sandbox", codex_sandbox(),
        "--color", "never",
        "--ephemeral",
        "-c", f"approval_policy=\"{codex_approval_policy()}\"",
        "-c", f"model_reasoning_effort=\"{codex_reasoning_effort()}\"",
        "-c", f"web_search=\"{codex_web_search()}\"",
        "-c", "otel.exporter=\"none\"",
        "-c", "otel.trace_exporter=\"none\"",
        "-c", "otel.metrics_exporter=\"none\"",
        "-C", str(SCRIPT_DIR),
    ]
    if prompt_text is not None:
        cmd.append(prompt_text)
    return cmd
```

Note: opencode does **not** support a `--max-turns` flag; budgeting is done at the model layer. The `max_turns` parameter is intentionally unused for the opencode branch — this is documented design (per spec). If max-turn enforcement becomes critical for opencode runs later, follow up with a watchdog at the harness orchestration layer, not in `_agent_command()`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/autoresearch/test_backend_selection.py -v`
Expected: PASS — all tests including new opencode branch tests green.

- [ ] **Step 5: Commit**

```bash
git add autoresearch/harness/agent.py tests/autoresearch/test_backend_selection.py
git commit -m "feat(harness): opencode branch in _agent_command()"
```

---

## Task 4: Extend `META_BACKEND` validator in `evolve.py:load_config`

**Files:**
- Modify: `autoresearch/evolve.py:253-261`
- Test: `tests/autoresearch/test_evolve_config.py` (create)

- [ ] **Step 1: Inspect current validation**

Run: `sed -n '250,265p' autoresearch/evolve.py`
Confirm the lines look like:

```python
meta_backend = getattr(args, "backend", None) or os.environ.get("META_BACKEND", "")
if not meta_backend:
    if shutil.which("codex"):
        meta_backend = "codex"
    elif shutil.which("claude"):
        meta_backend = "claude"
meta_backend = meta_backend.lower()
if meta_backend not in ("claude", "codex"):
    print(f"ERROR: Unsupported meta backend '{meta_backend}'", file=sys.stderr)
```

- [ ] **Step 2: Decision — no isolated unit test for this task**

`load_config` mixes argument parsing, env-var reading, file I/O (suite manifest), and the META_BACKEND validation in one function spanning ~80 lines. Extracting the validator alone would require either: (a) a non-trivial refactor to expose a `_validate_meta_backend(name) -> str` helper, or (b) a heavyweight test fixture mocking argparse + dotenv + suite manifest reads.

Both have higher cost than the value of unit-testing a 4-line allowed-tuple change. **The implementation change is mechanical (one tuple literal extended); end-to-end coverage is provided by Task 11's smoke test which runs the full evolve invocation with `META_BACKEND=opencode`.**

If `load_config` is refactored later (separate work), add a unit test for the validator at that point. Track this as a known testing-debt item in `docs/superpowers/specs/...` follow-ups.

- [ ] **Step 3: Implement — extend allowed-tuple in `load_config`**

Edit `autoresearch/evolve.py:253-261`. Replace:

```python
    meta_backend = getattr(args, "backend", None) or os.environ.get("META_BACKEND", "")
    if not meta_backend:
        if shutil.which("codex"):
            meta_backend = "codex"
        elif shutil.which("claude"):
            meta_backend = "claude"
    meta_backend = meta_backend.lower()
    if meta_backend not in ("claude", "codex", "opencode"):
        print(f"ERROR: Unsupported meta backend '{meta_backend}' (must be claude, codex, or opencode)", file=sys.stderr)
        sys.exit(1)
    # Existing branch for claude-specific guard at line 267 stays unchanged.
```

(The `if meta_backend == "claude":` block at line 267 — about CLAUDE_PRINT_MODE — is unchanged. Verify by re-reading lines 265-280 after editing; it should still be claude-only.)

- [ ] **Step 4: Verify the change compiles**

Run: `cd /Users/jryszardnoszczyk/Documents/GitHub/gofreddy && python -c "import sys; sys.path.insert(0, 'autoresearch'); import evolve; print('evolve imports cleanly')"`
Expected: prints "evolve imports cleanly" with no `SyntaxError` or `NameError`.

- [ ] **Step 5: Commit**

```bash
git add autoresearch/evolve.py
git commit -m "feat(evolve): accept opencode in META_BACKEND validator"
```

---

## Task 5: Add opencode branches to all meta-backend dispatch sites in `evolve.py`

**Scope expansion (vs. the original T5 spec):** Plan-review of T4 caught two additional dispatch sites in evolve.py that the original T5 missed. Without opencode branches at these sites, T11's smoke test would fail at runtime with an opaque `ValueError: Unknown meta backend: 'opencode'`. T5 now covers all three remaining `meta_backend ==` dispatch sites in evolve.py:

1. **Line 267** — `meta_model` defaulter. Currently `if meta_backend == "claude": meta_model = "sonnet" else: meta_model = "gpt-5.4"`. The else branch silently mis-defaults opencode to `"gpt-5.4"`. Fix: add an explicit opencode branch defaulting to `"openrouter/deepseek/deepseek-v3"` (matches `default_session_model()` from T2 — symmetric across the harness/evolve dispatch surfaces).
2. **Lines 470-497** — `_build_meta_env(config, workdir)`. Currently raises `ValueError` for any backend except claude/codex. Add an opencode branch using **codex-style env handling** (`os.environ.copy()` minus `_CODEX_HOLDOUT_KEYS`) — claude's strict allowlist is impractical for opencode because it routes to many providers each with different env-var requirements (`OPENROUTER_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENCODE_*` config vars, etc.). The codex pattern was originally chosen for the same reason ("asymmetric trust model" per the docstring at line 470).
3. **Lines 500-521** — `_build_meta_command(config, workdir)`. Originally specified in T5. Add opencode branch building the same argv shape as `harness/agent.py:_agent_command()`.

**Files:**
- Modify: `autoresearch/evolve.py` lines 267, 470-497, 500-521
- Test: `tests/autoresearch/test_evolve_config.py` (create — file does not exist yet)

- [ ] **Step 1: Add failing test for opencode meta-command shape**

Append to `tests/autoresearch/test_evolve_config.py`:

```python
def test_build_meta_command_opencode_branch(tmp_path: Path) -> None:
    """_build_meta_command returns opencode argv when meta_backend=opencode."""
    config = evolve.EvolutionConfig(
        meta_backend="opencode",
        meta_model="openrouter/deepseek/deepseek-v3",
        max_turns=10,
        codex_sandbox="workspace-write",
        codex_approval_policy="never",
        codex_reasoning_effort="high",
        codex_web_search="disabled",
        # Other required fields default in the dataclass; if dataclass
        # signature changes, update this fixture.
    )

    cmd = evolve._build_meta_command(config, tmp_path)

    assert cmd[0] == "opencode"
    assert cmd[1] == "run"
    assert "--dangerously-skip-permissions" in cmd
    assert "openrouter/deepseek/deepseek-v3" in cmd
    assert "--format" in cmd
    assert "--dir" in cmd
    # workdir passed
    assert str(tmp_path) in cmd
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/autoresearch/test_evolve_config.py::test_build_meta_command_opencode_branch -v`
Expected: FAIL — `_build_meta_command` raises `ValueError: Unknown meta backend: 'opencode'` at line 521.

- [ ] **Step 3: Implement — add opencode branch to `_build_meta_command`**

Edit `autoresearch/evolve.py:500-521`. Replace the function body:

```python
def _build_meta_command(config: EvolutionConfig, workdir: Path) -> list[str]:
    """Build the command array for the meta agent subprocess."""
    if config.meta_backend == "claude":
        return [
            "claude", "-p",
            "--model", config.meta_model,
            "--allowedTools", "Bash,Read,Write,Edit,Glob,Grep",
            "--max-turns", str(config.max_turns),
        ]
    if config.meta_backend == "codex":
        return [
            "codex", "exec",
            "--model", config.meta_model,
            "--sandbox", config.codex_sandbox,
            "--color", "never",
            "-c", f'approval_policy="{config.codex_approval_policy}"',
            "-c", f'model_reasoning_effort="{config.codex_reasoning_effort}"',
            "-c", f'web_search="{config.codex_web_search}"',
            "-C", str(workdir),
            "-",
        ]
    if config.meta_backend == "opencode":
        return [
            "opencode", "run",
            "--dangerously-skip-permissions",
            "-m", config.meta_model,
            "--format", "json",
            "--dir", str(workdir),
        ]
    raise ValueError(f"Unknown meta backend: {config.meta_backend!r}")
```

**Stdin handling note for opencode:** `run_meta_agent` at line 541-549 opens `prompt_file` and passes it as `stdin=stdin_handle` to subprocess.Popen. OpenCode's `opencode run` reads its prompt from positional argv, NOT stdin — but it tolerates an unused stdin handle. **No code change needed at the run_meta_agent layer.** OpenCode will simply ignore the stdin pipe; the prompt must be passed via the harness layer that calls `_build_meta_command`. **Verify this assumption by running the integration smoke test in Task 11.** If OpenCode hangs reading stdin, fall back to: read the prompt file in `_build_meta_command` and append as the trailing argv element. Choose the simpler path empirically.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/autoresearch/test_evolve_config.py -v`
Expected: PASS — both META_BACKEND tests + the new _build_meta_command test green.

- [ ] **Step 5: Commit**

```bash
git add autoresearch/evolve.py tests/autoresearch/test_evolve_config.py
git commit -m "feat(evolve): opencode branch in _build_meta_command"
```

---

## Task 6: Extend `EVOLUTION_EVAL_BACKEND` validator in `evaluate_variant.py`

**Files:**
- Modify: `autoresearch/evaluate_variant.py:186-193`
- Test: existing test file or new — verify which exists

- [ ] **Step 1: Find or create the evaluate_variant test file**

Run: `ls tests/autoresearch/test_evaluate*.py`
If there's no test file targeting `_require_eval_target`, create `tests/autoresearch/test_evaluate_variant_target.py` with a test for the validator.

```python
"""EVOLUTION_EVAL_BACKEND validation coverage for evaluate_variant._require_eval_target."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

AUTORESEARCH_DIR = Path(__file__).resolve().parents[2] / "autoresearch"
if str(AUTORESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(AUTORESEARCH_DIR))

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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/autoresearch/test_evaluate_variant_target.py -v`
Expected: FAIL on the opencode test — current validator rejects opencode with `RuntimeError("EVOLUTION_EVAL_BACKEND is required and must be one of: claude, codex.")`.

- [ ] **Step 3: Implement — extend allowed-set in validator**

Edit `autoresearch/evaluate_variant.py:186-193`. Replace:

```python
    backend = env.get("EVOLUTION_EVAL_BACKEND", "").strip().lower()
    model = env.get("EVOLUTION_EVAL_MODEL", "").strip()
    if backend not in {"claude", "codex", "opencode"}:
        raise RuntimeError(
            "EVOLUTION_EVAL_BACKEND is required and must be one of: claude, codex, opencode."
        )
    if not model:
        raise RuntimeError("EVOLUTION_EVAL_MODEL is required.")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/autoresearch/test_evaluate_variant_target.py -v`
Expected: PASS — both tests green.

- [ ] **Step 5: Commit**

```bash
git add autoresearch/evaluate_variant.py tests/autoresearch/test_evaluate_variant_target.py
git commit -m "feat(evaluate_variant): accept opencode in EVOLUTION_EVAL_BACKEND validator"
```

---

## Task 7: Add `base_url` / `api_key` env-var routing to `agent_calls.py`

**Files:**
- Modify: `autoresearch/agent_calls.py:124-159`
- Test: `tests/autoresearch/test_select_parent.py` (extend)

- [ ] **Step 1: Add failing test for env-var routing**

Append to `tests/autoresearch/test_select_parent.py`:

```python
def test_call_openai_json_uses_parent_base_url_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """_call_openai_json passes AUTORESEARCH_PARENT_BASE_URL to AsyncOpenAI."""
    captured: dict = {}

    class FakeClient:
        def __init__(self, *, api_key: str, base_url: str | None = None) -> None:
            captured["api_key"] = api_key
            captured["base_url"] = base_url
            self.chat = self  # so .chat.completions.create works
            self.completions = self

        async def create(self, **kwargs):
            class _Choice:
                finish_reason = "stop"
                class message:
                    content = '{"parent_id": "v-1", "rationale": "ok", "confidence": "high"}'
            class _Resp:
                choices = [_Choice()]
            return _Resp()

        async def close(self) -> None:
            pass

    monkeypatch.setenv("AUTORESEARCH_PARENT_BASE_URL", "https://openrouter.ai/api/v1")
    monkeypatch.setenv("AUTORESEARCH_PARENT_API_KEY", "or-test-key")
    monkeypatch.setenv("OPENAI_API_KEY", "should-be-overridden")
    monkeypatch.setattr("agent_calls.AsyncOpenAI", FakeClient)

    import agent_calls
    asyncio.run(agent_calls._call_openai_json(prompt="x", model="openrouter/deepseek/deepseek-v3"))

    assert captured["base_url"] == "https://openrouter.ai/api/v1"
    assert captured["api_key"] == "or-test-key"


def test_call_openai_json_default_no_base_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When AUTORESEARCH_PARENT_BASE_URL unset, base_url is None (default OpenAI)."""
    captured: dict = {}

    class FakeClient:
        def __init__(self, *, api_key: str, base_url: str | None = None) -> None:
            captured["api_key"] = api_key
            captured["base_url"] = base_url
            self.chat = self
            self.completions = self

        async def create(self, **kwargs):
            class _Choice:
                finish_reason = "stop"
                class message:
                    content = '{"parent_id": "v-1", "rationale": "ok", "confidence": "high"}'
            class _Resp:
                choices = [_Choice()]
            return _Resp()

        async def close(self) -> None:
            pass

    monkeypatch.delenv("AUTORESEARCH_PARENT_BASE_URL", raising=False)
    monkeypatch.delenv("AUTORESEARCH_PARENT_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "default-key")
    monkeypatch.setattr("agent_calls.AsyncOpenAI", FakeClient)

    import agent_calls
    asyncio.run(agent_calls._call_openai_json(prompt="x", model="gpt-5.4"))

    assert captured["base_url"] is None
    assert captured["api_key"] == "default-key"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/autoresearch/test_select_parent.py::test_call_openai_json_uses_parent_base_url_env -v`
Expected: FAIL — current code instantiates `AsyncOpenAI(api_key=key)` with no `base_url` parameter.

- [ ] **Step 3: Implement — env-var routing**

Edit `autoresearch/agent_calls.py:124-159`. Replace the body of `_call_openai_json`:

```python
async def _call_openai_json(
    prompt: str,
    *,
    model: str = DEFAULT_MODEL,
    timeout: int = 30,
    api_key: str | None = None,
) -> str:
    """Low-level AsyncOpenAI call returning raw JSON text content.

    Caller is responsible for Pydantic validation.

    Multi-provider routing: when ``AUTORESEARCH_PARENT_BASE_URL`` is set,
    requests are routed to that endpoint (must be OpenAI-compatible — e.g.,
    OpenRouter at https://openrouter.ai/api/v1). When
    ``AUTORESEARCH_PARENT_API_KEY`` is set, it overrides ``OPENAI_API_KEY``
    for this client only.
    """
    explicit_key = api_key or os.environ.get("AUTORESEARCH_PARENT_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not explicit_key:
        raise RuntimeError(
            "OPENAI_API_KEY (or AUTORESEARCH_PARENT_API_KEY) is not set — cannot run autoresearch agent call"
        )
    base_url = os.environ.get("AUTORESEARCH_PARENT_BASE_URL") or None
    client = AsyncOpenAI(api_key=explicit_key, base_url=base_url)
    try:
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                response_format={"type": "json_object"},
            ),
            timeout=timeout,
        )
        choice = response.choices[0]
        if choice.finish_reason not in ("stop", "length"):
            raise RuntimeError(
                f"autoresearch agent call got bad finish_reason={choice.finish_reason}"
            )
        content = choice.message.content
        if not content:
            raise RuntimeError("autoresearch agent call returned empty content")
        return content
    finally:
        await client.close()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/autoresearch/test_select_parent.py -v`
Expected: PASS — new tests + existing tests all green.

- [ ] **Step 5: Commit**

```bash
git add autoresearch/agent_calls.py tests/autoresearch/test_select_parent.py
git commit -m "feat(agent_calls): route parent-selection via OPENAI_BASE_URL when set"
```

---

## Task 8: Create OpenCode JSONL parser utility

**Files:**
- Create: `autoresearch/harness/opencode_jsonl.py`
- Test: `tests/autoresearch/test_opencode_jsonl.py` (create)

- [ ] **Step 1: Create test file with failing tests**

Create `tests/autoresearch/test_opencode_jsonl.py`:

```python
"""Unit tests for the OpenCode JSONL parser."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

AUTORESEARCH_DIR = Path(__file__).resolve().parents[2] / "autoresearch"
if str(AUTORESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(AUTORESEARCH_DIR))

from harness import opencode_jsonl  # noqa: E402


SAMPLE_JSONL = """{"type":"step_start","timestamp":1,"sessionID":"s","part":{"type":"step-start"}}
{"type":"text","timestamp":2,"sessionID":"s","part":{"type":"text","text":"thinking out loud","metadata":{"openai":{"phase":"commentary"}}}}
{"type":"tool_use","timestamp":3,"sessionID":"s","part":{"type":"tool","tool":"read","state":{"status":"completed","input":{"filePath":"/x"},"output":"file contents"}}}
{"type":"step_finish","timestamp":4,"sessionID":"s","part":{"reason":"tool-calls","tokens":{"total":100,"input":80,"output":20,"reasoning":0,"cache":{"write":0,"read":0}},"cost":0.01}}
{"type":"text","timestamp":5,"sessionID":"s","part":{"type":"text","text":"Final answer is 42.","metadata":{"openai":{"phase":"final_answer"}}}}
{"type":"step_finish","timestamp":6,"sessionID":"s","part":{"reason":"stop","tokens":{"total":50,"input":10,"output":40,"reasoning":0,"cache":{"write":0,"read":80}},"cost":0.005}}
"""


def test_parse_total_cost_sums_all_step_finish_events(tmp_path: Path) -> None:
    log_path = tmp_path / "session.jsonl"
    log_path.write_text(SAMPLE_JSONL)

    summary = opencode_jsonl.parse_session(log_path)

    assert summary.total_cost == pytest.approx(0.015)


def test_parse_total_cache_reads_sums_all_step_finish_events(tmp_path: Path) -> None:
    log_path = tmp_path / "session.jsonl"
    log_path.write_text(SAMPLE_JSONL)

    summary = opencode_jsonl.parse_session(log_path)

    assert summary.total_cache_reads == 80


def test_parse_final_answer_returns_last_text_before_stop(tmp_path: Path) -> None:
    log_path = tmp_path / "session.jsonl"
    log_path.write_text(SAMPLE_JSONL)

    summary = opencode_jsonl.parse_session(log_path)

    assert summary.final_answer == "Final answer is 42."


def test_parse_returns_empty_summary_on_empty_file(tmp_path: Path) -> None:
    log_path = tmp_path / "empty.jsonl"
    log_path.write_text("")

    summary = opencode_jsonl.parse_session(log_path)

    assert summary.total_cost == 0.0
    assert summary.total_cache_reads == 0
    assert summary.final_answer is None


def test_parse_skips_malformed_lines(tmp_path: Path) -> None:
    """Malformed JSON lines should be skipped, not fatal."""
    log_path = tmp_path / "session.jsonl"
    log_path.write_text(
        SAMPLE_JSONL
        + "this is not json\n"
        + '{"type":"step_finish","part":{"reason":"stop","tokens":{"cache":{"read":0}},"cost":0.001}}\n'
    )

    summary = opencode_jsonl.parse_session(log_path)

    # Total cost = 0.01 + 0.005 + 0.001 (the second valid step_finish)
    assert summary.total_cost == pytest.approx(0.016)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/autoresearch/test_opencode_jsonl.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'harness.opencode_jsonl'`.

- [ ] **Step 3: Implement — create `opencode_jsonl.py`**

Create `autoresearch/harness/opencode_jsonl.py`:

```python
"""Parser for OpenCode's `--format json` JSONL output.

Each line of OpenCode's session log is a JSON object. We extract:
  - per-step USD cost (sum across step_finish events)
  - cache utilization (sum of cache.read across step_finish events)
  - final answer text (last `text` event with phase="final_answer", or last
    text before the terminal step_finish with reason="stop")

Spec: docs/superpowers/specs/2026-04-26-multi-provider-agentic-pipeline-design.md
Appendix A documents the event schema as verified 2026-04-26.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SessionSummary:
    """Aggregate result of parsing a single OpenCode JSONL session log."""

    total_cost: float = 0.0
    total_cache_reads: int = 0
    final_answer: str | None = None


def parse_session(log_path: Path) -> SessionSummary:
    """Parse an OpenCode JSONL log file. Malformed lines are skipped."""
    if not log_path.exists():
        return SessionSummary()

    total_cost = 0.0
    total_cache_reads = 0
    final_answer: str | None = None
    last_text: str | None = None

    with log_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            event_type = event.get("type")
            part = event.get("part") or {}

            if event_type == "step_finish":
                cost = part.get("cost")
                if isinstance(cost, (int, float)):
                    total_cost += float(cost)
                tokens = part.get("tokens") or {}
                cache = tokens.get("cache") or {}
                reads = cache.get("read")
                if isinstance(reads, int):
                    total_cache_reads += reads
                if part.get("reason") == "stop" and last_text is not None and final_answer is None:
                    final_answer = last_text

            elif event_type == "text":
                text = part.get("text")
                if isinstance(text, str):
                    last_text = text
                    metadata = part.get("metadata") or {}
                    openai_meta = metadata.get("openai") or {}
                    if openai_meta.get("phase") == "final_answer":
                        final_answer = text

    return SessionSummary(
        total_cost=total_cost,
        total_cache_reads=total_cache_reads,
        final_answer=final_answer,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/autoresearch/test_opencode_jsonl.py -v`
Expected: PASS — all 5 tests green.

- [ ] **Step 5: Commit**

```bash
git add autoresearch/harness/opencode_jsonl.py tests/autoresearch/test_opencode_jsonl.py
git commit -m "feat(harness): add opencode_jsonl parser utility"
```

---

## Task 9: Migrate `_run_claude_json` → `_run_alert_agent_json` with backend branch

**Files:**
- Modify: `autoresearch/compute_metrics.py:224-253` and `:322` (caller)
- Test: `tests/autoresearch/test_compute_metrics_alerts.py` (extend)

- [ ] **Step 1: Add failing test for opencode-backed alert agent**

Append to `tests/autoresearch/test_compute_metrics_alerts.py`:

```python
def test_alert_agent_uses_opencode_when_backend_env_set(
    sample_row: dict,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """When AUTORESEARCH_ALERT_BACKEND=opencode, alert agent calls opencode run."""
    monkeypatch.setattr(compute_metrics, "METRICS_DIR", tmp_path)
    monkeypatch.setattr(compute_metrics, "_GENERATIONS_LOG", tmp_path / "generations.jsonl")
    monkeypatch.setenv("AUTORESEARCH_ALERT_BACKEND", "opencode")
    monkeypatch.setenv("AUTORESEARCH_ALERT_MODEL", "openrouter/deepseek/deepseek-v3")

    captured_argv: list[str] = []

    def fake_run(cmd, capture_output, text, check, timeout):
        nonlocal captured_argv
        captured_argv = list(cmd)
        proc = mock.MagicMock()
        proc.returncode = 0
        # Synthesize an OpenCode JSONL with a final_answer "[]" (empty alerts)
        proc.stdout = (
            '{"type":"step_finish","part":{"reason":"stop","tokens":{"cache":{"read":0}},"cost":0.001}}\n'
            '{"type":"text","part":{"text":"[]","metadata":{"openai":{"phase":"final_answer"}}}}\n'
        )
        proc.stderr = ""
        return proc

    monkeypatch.setattr(compute_metrics.subprocess, "run", fake_run)

    result = compute_metrics._run_alert_agent_json(prompt="test", model="openrouter/deepseek/deepseek-v3", timeout=30)

    assert captured_argv[0] == "opencode"
    assert captured_argv[1] == "run"
    assert "--format" in captured_argv
    assert result == "[]"


def test_alert_agent_defaults_to_claude_when_backend_env_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When AUTORESEARCH_ALERT_BACKEND unset, alert agent uses claude (existing behavior)."""
    monkeypatch.delenv("AUTORESEARCH_ALERT_BACKEND", raising=False)

    captured_argv: list[str] = []

    def fake_run(cmd, capture_output, text, check, timeout):
        nonlocal captured_argv
        captured_argv = list(cmd)
        proc = mock.MagicMock()
        proc.returncode = 0
        proc.stdout = json.dumps({"result": "[]"})
        proc.stderr = ""
        return proc

    monkeypatch.setattr(compute_metrics.subprocess, "run", fake_run)

    result = compute_metrics._run_alert_agent_json(prompt="test", model="sonnet", timeout=30)

    assert captured_argv[0] == "claude"
    assert "-p" in captured_argv
    assert result == "[]"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/autoresearch/test_compute_metrics_alerts.py -v -k alert_agent`
Expected: FAIL — `_run_alert_agent_json` does not exist; `_run_claude_json` is the current name.

- [ ] **Step 3: Implement — rename + add backend branch**

Edit `autoresearch/compute_metrics.py:224-253`. Replace the function:

```python
def _run_alert_agent_json(prompt: str, *, model: str, timeout: int) -> str:
    """Invoke the alert agent CLI with JSON-mode output; return the assistant text.

    Backend selection (in order):
      1. AUTORESEARCH_ALERT_BACKEND env var: "claude" or "opencode"
      2. Fallback: "claude" (preserves prior default)

    For ``claude``: spawns ``claude -p prompt --output-format json …`` and
    extracts the ``result`` field of Claude CLI's JSON envelope.
    For ``opencode``: spawns ``opencode run … --format json prompt`` and
    extracts the final-answer ``text`` event from OpenCode's JSONL output
    via ``harness.opencode_jsonl.parse_session``-style parsing inline.
    """
    backend = os.environ.get("AUTORESEARCH_ALERT_BACKEND", "").strip().lower() or "claude"

    if backend == "opencode":
        cmd = [
            "opencode", "run",
            "--dangerously-skip-permissions",
            "-m", model,
            "--format", "json",
            prompt,
        ]
    elif backend == "claude":
        cmd = [
            "claude",
            "-p", prompt,
            "--output-format", "json",
            "--session-id", str(uuid.uuid4()),
            "--model", model,
            "--dangerously-skip-permissions",
        ]
    else:
        raise RuntimeError(
            f"AUTORESEARCH_ALERT_BACKEND={backend!r} not supported (must be claude or opencode)"
        )

    proc = subprocess.run(
        cmd, capture_output=True, text=True, check=False, timeout=timeout,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"{backend} CLI exited {proc.returncode}: {(proc.stderr or proc.stdout or '')[:400]}"
        )

    if backend == "opencode":
        # Parse OpenCode JSONL: walk lines, find last `text` event with
        # phase=final_answer (or final text before terminal step_finish).
        last_text: str | None = None
        final_answer: str | None = None
        for line in proc.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            etype = event.get("type")
            part = event.get("part") or {}
            if etype == "text":
                text = part.get("text")
                if isinstance(text, str):
                    last_text = text
                    meta = (part.get("metadata") or {}).get("openai") or {}
                    if meta.get("phase") == "final_answer":
                        final_answer = text
            elif etype == "step_finish" and part.get("reason") == "stop":
                if final_answer is None and last_text is not None:
                    final_answer = last_text
        return final_answer if final_answer is not None else proc.stdout

    # backend == "claude": parse the JSON envelope as before
    try:
        envelope = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return proc.stdout
    if isinstance(envelope, dict) and isinstance(envelope.get("result"), str):
        return envelope["result"]
    return proc.stdout
```

Update the caller at line 322. Replace:

```python
        raw = _run_alert_agent_json(prompt, model=_ALERT_AGENT_MODEL, timeout=_ALERT_AGENT_TIMEOUT)
```

(Same name, but now the function is the new one — verify with `grep -n _run_claude_json autoresearch/compute_metrics.py` returns 0 hits after the edit.)

**Note on duplication with `harness/opencode_jsonl.py`:** The inline parser here is intentionally not factored into the shared module. Reason: the alert-agent path already uses `subprocess.run` (capture_output=True) — the JSONL is already in-memory as a string, not a file. `harness.opencode_jsonl.parse_session` operates on file paths. Factoring would require either (a) changing the helper to accept strings, or (b) writing the captured output to a tmp file. Both add complexity for one consumer. If a third consumer appears, refactor; until then, accept the small duplication.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/autoresearch/test_compute_metrics_alerts.py -v`
Expected: PASS — both new tests + all existing alert tests green.

- [ ] **Step 5: Verify the rename completed cleanly**

Run: `grep -rn "_run_claude_json" autoresearch/ tests/ --include="*.py"`
Expected: 0 matches. (If any remain in tests, update them to `_run_alert_agent_json`.)

- [ ] **Step 6: Commit**

```bash
git add autoresearch/compute_metrics.py tests/autoresearch/test_compute_metrics_alerts.py
git commit -m "feat(compute_metrics): backend-switchable alert agent (claude or opencode)"
```

---

## Task 10: Update `autoresearch/README.md` setup docs

**Files:**
- Modify: `autoresearch/README.md:93-95`

- [ ] **Step 1: Inspect current setup section**

Run: `sed -n '85,110p' autoresearch/README.md`

- [ ] **Step 2: Add OpenCode setup example after the existing Codex example**

Edit `autoresearch/README.md`. Find the existing block:

```bash
export EVOLUTION_EVAL_BACKEND=codex
export EVOLUTION_EVAL_MODEL=gpt-5.4
export EVOLUTION_EVAL_REASONING_EFFORT=high
```

Append immediately after it:

````markdown

### OpenCode (multi-provider via OpenRouter / OSS models)

To run autoresearch evaluations with open-source models or OpenRouter-hosted Anthropic/OpenAI models, install OpenCode (`curl -fsSL https://opencode.ai/install | bash`) and configure credentials with `opencode auth login`. Then:

```bash
export META_BACKEND=opencode                                    # evolve meta-agent
export EVOLUTION_EVAL_BACKEND=opencode                          # per-variant eval subprocess
export EVOLUTION_EVAL_MODEL=openrouter/deepseek/deepseek-v3
export AUTORESEARCH_SESSION_BACKEND=opencode                    # harness fixer/verifier
export AUTORESEARCH_SESSION_MODEL=openrouter/deepseek/deepseek-v3
```

OpenCode handles its own authentication via `~/.local/share/opencode/auth.json` — no `OPENROUTER_API_KEY` is needed in `.env` for OpenCode-routed paths. If you also want the parent-selection JSON judge in `agent_calls.py` routed through OpenRouter (rather than OpenAI direct), set:

```bash
export AUTORESEARCH_PARENT_BASE_URL=https://openrouter.ai/api/v1
export AUTORESEARCH_PARENT_API_KEY=sk-or-...
```
````

- [ ] **Step 3: Verify the doc compiles in your renderer of choice (optional)**

Run: `glow autoresearch/README.md` or open in an editor that previews markdown. Confirm the new section sits after the existing Codex example and before the next major section.

- [ ] **Step 4: Commit**

```bash
git add autoresearch/README.md
git commit -m "docs(autoresearch): document OpenCode multi-provider setup"
```

---

## Task 11: Integration smoke test — end-to-end OpenCode harness session

**Files:**
- (No production code changes — test-only)
- Create: `tests/autoresearch/test_opencode_smoke.py`

- [ ] **Step 1: Confirm OpenCode is on PATH and authenticated**

Run: `opencode --version && opencode auth list`
Expected: prints version + a non-empty credential list (at least one provider configured, e.g., openrouter, anthropic, or openai).

If `opencode` is not on PATH, install per Task 10 setup notes. If `auth list` is empty, run `opencode auth login` and pick a provider you have keys for.

- [ ] **Step 2: Create the smoke test (skipif when opencode unavailable)**

Create `tests/autoresearch/test_opencode_smoke.py`:

```python
"""End-to-end smoke test: harness subprocess.Popen → opencode run completes a Read+Edit+Bash loop.

Skipped automatically when opencode is not on PATH or unauthenticated.
This is the same shape used by the harness's run_agent_session at
autoresearch/harness/agent.py:99-124.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

AUTORESEARCH_DIR = Path(__file__).resolve().parents[2] / "autoresearch"
if str(AUTORESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(AUTORESEARCH_DIR))


pytestmark = pytest.mark.skipif(
    shutil.which("opencode") is None,
    reason="opencode binary not on PATH",
)


def test_opencode_run_subprocess_completes_simple_tool_loop(tmp_path: Path) -> None:
    """Exercise the same Popen pattern harness/agent.py:108 uses against opencode.

    Pass criterion: file edit lands AND verification command exits 0.
    """
    # Workspace
    target = tmp_path / "spike-target.py"
    target.write_text('def hello():\n    return "world"\n')
    log = tmp_path / "session.jsonl"
    err = tmp_path / "session.err"

    prompt = (
        f"Edit the file {target}: add a single-line comment '# spike-marker' "
        "as the very first line of the file (before def hello). "
        f"After editing, verify with: head -1 {target}"
    )

    # Pick a model: prefer OPENCODE_SMOKE_MODEL env, else default. The default
    # MUST be one your opencode auth list has credentials for.
    model = os.environ.get("OPENCODE_SMOKE_MODEL", "openai/gpt-5.4")

    cmd = [
        "opencode", "run",
        "--dangerously-skip-permissions",
        "-m", model,
        "--format", "json",
        "--dir", str(tmp_path),
        prompt,
    ]

    with log.open("w") as log_fh, err.open("w") as err_fh:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=log_fh,
            stderr=err_fh,
            text=True,
            cwd=str(tmp_path),
        )
        exit_code = proc.wait(timeout=120)

    assert exit_code == 0, (
        f"opencode exited {exit_code}; stderr tail: {err.read_text()[-500:]}; "
        f"stdout tail: {log.read_text()[-500:]}"
    )
    assert "# spike-marker" in target.read_text(), (
        f"marker missing from target.py; stdout tail: {log.read_text()[-1000:]}"
    )
```

- [ ] **Step 3: Run the smoke test**

Run: `pytest tests/autoresearch/test_opencode_smoke.py -v`
Expected:
- If `opencode` is not on PATH: SKIPPED
- If `opencode` is on PATH and authenticated: PASS within ~30s
- If FAIL: inspect the test's stdout/stderr printout for diagnosis (auth issue, network, model name typo, etc.)

- [ ] **Step 4: Commit**

```bash
git add tests/autoresearch/test_opencode_smoke.py
git commit -m "test(harness): end-to-end opencode subprocess smoke test"
```

---

## Task 12: Final validation — full test suite + docs cross-check

**Files:**
- (No edits — verification only)

- [ ] **Step 1: Run full autoresearch test suite**

Run: `cd /Users/jryszardnoszczyk/Documents/GitHub/gofreddy && pytest tests/autoresearch/ -v`
Expected: ALL existing tests pass, plus the new tests added in Tasks 1-11. Any regression in existing tests indicates a hidden coupling — investigate before declaring done.

- [ ] **Step 2: Verify env-var documentation matches code**

Run:
```bash
echo "=== env vars referenced in README ==="
grep -oE "(META_BACKEND|EVOLUTION_EVAL_[A-Z_]+|AUTORESEARCH_[A-Z_]+|OPENROUTER_API_KEY|OPENAI_API_KEY)" autoresearch/README.md | sort -u
echo
echo "=== env vars referenced in code ==="
grep -roE 'os\.environ\.get\("(META_BACKEND|EVOLUTION_EVAL_[A-Z_]+|AUTORESEARCH_[A-Z_]+|OPENROUTER_API_KEY|OPENAI_API_KEY)"' autoresearch/ --include="*.py" | grep -oE '"[^"]+"' | sort -u
```

Expected: every env var referenced in code appears in README setup docs (or in the source-of-truth env-var table in the spec). If a var exists in code but is undocumented, add it.

- [ ] **Step 3: Manual sanity test of the multi-provider entry points (optional, not blocking)**

If you have OpenRouter creds wired up, run a single autoresearch session with `AUTORESEARCH_SESSION_BACKEND=opencode AUTORESEARCH_SESSION_MODEL=openrouter/deepseek/deepseek-v3`. This exercises Task 1-3 + Task 8 + Task 11 in concert. If the session completes and the harness verifier produces a verdict, the implementation is functionally complete.

- [ ] **Step 4: Final commit**

(If any small fixes were made during validation:)
```bash
git add -A
git commit -m "fix: address findings from final validation pass"
```

(Otherwise no commit needed.)

---

## Summary of changes

**Production code (~100 LoC):**
- `autoresearch/harness/backend.py` — extend allowed-set + opencode default model (Tasks 1-2)
- `autoresearch/harness/agent.py` — opencode branch in `_agent_command` (Task 3)
- `autoresearch/evolve.py` — `META_BACKEND` allowed-tuple + `_build_meta_command` opencode branch (Tasks 4-5)
- `autoresearch/evaluate_variant.py` — `EVOLUTION_EVAL_BACKEND` allowed-set (Task 6)
- `autoresearch/agent_calls.py` — `base_url` / `api_key` env-var routing (Task 7)
- `autoresearch/harness/opencode_jsonl.py` — JSONL parser utility (NEW, Task 8)
- `autoresearch/compute_metrics.py` — `_run_claude_json` → `_run_alert_agent_json` with backend branch (Task 9)
- `autoresearch/README.md` — OpenCode setup docs (Task 10)

**Tests (~200 LoC across new + existing files):**
- `tests/autoresearch/test_backend_selection.py` (NEW) — backend selection + agent command (Tasks 1-3)
- `tests/autoresearch/test_evolve_config.py` (NEW) — META_BACKEND validator + meta-command (Tasks 4-5)
- `tests/autoresearch/test_evaluate_variant_target.py` (NEW) — EVOLUTION_EVAL_BACKEND validator (Task 6)
- `tests/autoresearch/test_select_parent.py` (existing — extended) — base_url routing (Task 7)
- `tests/autoresearch/test_opencode_jsonl.py` (NEW) — JSONL parser (Task 8)
- `tests/autoresearch/test_compute_metrics_alerts.py` (existing — extended) — alert agent backend branch (Task 9)
- `tests/autoresearch/test_opencode_smoke.py` (NEW) — end-to-end harness smoke (Task 11)

**Operator setup:**
- Install OpenCode CLI
- Authenticate at least one provider (OpenRouter recommended for multi-provider)
- Set env vars per the new README section

**Out of scope (deferred):**
- Telemetry parser integration into `harness/telemetry.py` — `opencode_jsonl.py` is a standalone utility ready to be wired in when a consumer materializes (e.g., session-cost aggregation across runs)
- Audit engine (`docs/plans/2026-04-24-005-feat-audit-engine-fusion-plan.md`) — separate plan owns its model layer
- Unification of `AUTORESEARCH_SESSION_BACKEND` / `META_BACKEND` / `EVOLUTION_EVAL_BACKEND` into one config — a separate refactor, not multi-provider work
