# Multi-provider support for autoresearch (OpenCode third backend)

**Status:** Design — awaiting JR review before writing-plans
**Date:** 2026-04-26
**Author:** Claude (under JR's direction)
**Branch context:** `plan/audit-engine-fusion-v1`

## Summary

Extend the autoresearch pipeline (harness session loop + evolve meta-agent loop + autoresearch judge calls) to support OpenRouter and open-source models alongside Anthropic and OpenAI, by adding **OpenCode** as a third agentic-CLI backend in `autoresearch/harness/backend.py` and migrating one in-process JSON judge call (`agent_calls.py`) to support an OpenAI-compatible `base_url` override.

The design preserves the existing CLI-shaped harness architecture (worktree-isolated subprocess agents, file-redirected stdout, graceful-stop / resume), reuses validated patterns rather than introducing new orchestration layers, and is bounded to ~100 lines of code change across 8 files.

**Audit engine is explicitly out of scope** — it is governed by a separate plan at `docs/plans/2026-04-24-005-feat-audit-engine-fusion-plan.md` and may pick its own model layer at implementation time.

## Background and motivation

### Current state (verified 2026-04-26)

Autoresearch invokes models through three patterns today:

| Layer | Pattern | Provider | Files |
|---|---|---|---|
| Agentic CLI sessions (harness fixer/verifier, evolve meta-agent) | Subprocess: `claude -p` or `codex exec`, file-redirected stdout | Anthropic OR OpenAI (env-switchable) | `autoresearch/harness/agent.py:38-65,99-124`, `autoresearch/harness/backend.py:22-49`, `autoresearch/evolve.py:500-539` |
| In-process JSON judge — parent selection | AsyncOpenAI SDK, `response_format=json_object` | OpenAI (`gpt-5.4` hardcoded default) | `autoresearch/agent_calls.py:23,31,124-159,162-183` |
| CLI-subprocess JSON judge — alert agent | Subprocess: `claude -p --output-format json`, capture_output | Anthropic | `autoresearch/compute_metrics.py:224-253` |

Two providers are wired in (Anthropic via Claude Code CLI, OpenAI via Codex CLI + OpenAI SDK). A third provider — open-source models via OpenRouter — is not currently supported.

### Goal

Enable open-source and OpenRouter-hosted models across **both** the agentic CLI loop and the JSON judge calls, without:
- Rewriting the harness's subprocess-shaped agent layer (would lose graceful-stop / resume, OAuth spawn stagger, FREDDY_API_URL injection, the verifier's 6 probes — all shipped fixes that live in the spawning layer)
- Introducing an orchestration framework (LangChain, LangGraph) or a model-routing library (LiteLLM) that competes with the harness's existing orchestration responsibilities
- Adding operational complexity (proxies, sidecar servers, non-trivial config files)

### Why OpenCode

OpenCode (`opencode.ai`, v1.14.25 verified 2026-04-26 — repo currently at `github.com/anomalyco/opencode` after a brand transition from SST) is the only off-the-shelf agentic CLI that:
- Speaks 75+ providers natively including Anthropic, OpenAI, OpenRouter, Ollama, Groq, DeepSeek, Together, Bedrock — covers every multi-provider use case
- Accepts `provider/model` strings on `--model`, mapping cleanly to multi-provider routing
- Has a non-interactive `opencode run` mode designed for automation (per official docs: "for scripting, automation, CI/CD")
- Emits richer telemetry than Claude Code CLI: per-step cost in USD, per-step token + cache breakdown, full tool input/output — a meaningful telemetry **upgrade** for `harness/telemetry.py`
- Tool surface (`read`, `apply_patch` / `edit`, `bash`, `glob`, `grep`, `write`) maps onto the harness fixer's existing needs

### Why no LiteLLM

OpenRouter is OpenAI-compatible by design (`https://openrouter.ai/api/v1`). The existing `AsyncOpenAI` client in `agent_calls.py:138` already accepts a custom `base_url`. Multi-provider for the in-process JSON judge call is a 5-line env-var-driven `base_url` swap, not a new library. Layer B-cold (alert agent) is already CLI-subprocess-shaped and migrates to `opencode run` directly, reusing the Layer A infrastructure. There is no remaining call site that requires a routing library.

### Why no fallback CLI

Goose was validated as a working alternative in spike testing but is demoted to "skip" rather than "backup": maintaining two third-backends doubles the testing matrix and the harness's CLI-shape adapter logic, which is exactly the complexity LiteLLM was avoiding. If OpenCode hits an unexpected production failure, the backend selector in `harness/backend.py:22-49` is already env-var-driven; switching to Goose at that point is a configuration change, not an architectural one. We design for one backend and gain operational simplicity now.

## Spike evidence (verified 2026-04-26)

Two spikes were run against synthetic fixture `/tmp/agentic-cli-spike/target.py` with prompt requiring `Read + Edit + Bash` tool use, executed via `subprocess.Popen` with file-redirected stdout (matching `autoresearch/harness/agent.py:108-117`):

**Spike: Goose 1.32.0** — PASS in 9s. `GOOSE_PROVIDER=openai GOOSE_MODEL=gpt-5.4 goose run --no-session --max-turns 8 -t "$PROMPT"`. File edit landed via `shell` tool (Python heredoc). Output is human-readable text with `▸` tool delimiters. **Note:** `--output-format stream-json` claimed by external research is **not present in goose 1.32.0** — only text mode. This eliminates Goose for telemetry-rich use.

**Spike: OpenCode 1.14.25** — PASS in 13s. `opencode run --dangerously-skip-permissions -m openai/gpt-5.4 --format json --dir /tmp/agentic-cli-spike "$PROMPT"`. File edit landed via `apply_patch` tool. Output is JSONL with structured event schema (see Appendix A). Per-step cost USD, token breakdown including cache hits, full tool input/output all present. Subprocess.Popen with file-redirected stdout did **not** trigger known issue #11891 (which is `readline()`-specific, not file-redirect). Total cost across 4 steps: $0.037 with `gpt-5.4` for ~9.9k tokens (most of which were cached on subsequent steps); an order of magnitude cheaper for the same workload with `openrouter/deepseek/deepseek-v3` per OpenRouter list pricing.

**Spike: claude-code-router (ccr)** — SKIPPED. ccr requires either an OpenRouter API key or a local Ollama install, neither present at spike time. Decision to skip ccr is independent of the missing key: ccr's value proposition (zero harness changes) is undercut by its known prompt-caching break (issue #1217: Claude Code injects `cc_version` headers that mutate every turn, breaking cache prefix match for non-Anthropic backends), 901 open issues, and a 7-week-old most-recent push at investigation time. The harness's long system prompts depend on prompt caching, making ccr's caching break a material harness regression.

## Design

### Layer A — Agentic CLI sessions

The agentic CLI is invoked through **two parallel command builders**, not one:

- `autoresearch/harness/agent.py:38` `_agent_command()` — used by `run_agent_session()` and `spawn_agent_process()` for harness fixer/verifier subprocess agents
- `autoresearch/evolve.py:500` `_build_meta_command()` — used by `run_meta_agent()` for the evolve generation orchestrator

**Both need an `opencode` branch.** They are driven by **three independent env-var schemes** (verified 2026-04-26):

- `AUTORESEARCH_SESSION_BACKEND` — controls `harness/agent.py` (fixer/verifier subprocesses)
- `META_BACKEND` — controls `evolve.py:load_config` line 253 (the meta-agent orchestrator that drives generations)
- `EVOLUTION_EVAL_BACKEND` — controls `evaluate_variant.py:_require_eval_target` line 186 (the per-variant eval subprocess spawned by the meta-agent)

This three-way duplication exists in current main and is **not unified** by this spec — unification would be a separate refactor.

**Touch points:** `autoresearch/harness/backend.py` (3 functions), `autoresearch/harness/agent.py` (1 function), `autoresearch/evolve.py` (`load_config` `META_BACKEND` validator at lines 253-261 + `_build_meta_command` at lines 500-521), `autoresearch/evaluate_variant.py` (the `EVOLUTION_EVAL_BACKEND` validator at lines 186-193), `autoresearch/README.md` (setup docs at lines 93-95).

**Change to `harness/backend.py`:**

`session_backend()` at line 22 currently allows `{"claude", "codex"}`. Extend to `{"claude", "codex", "opencode"}` — add `shutil.which("opencode")` to the binary-availability fallback chain at lines 31-37.

`default_session_model()` at line 40 currently returns `SESSION_MODEL` for Claude, `"gpt-5.4"` for Codex. Add a third branch: for `opencode`, default to a configurable env var (proposal: `AUTORESEARCH_OPENCODE_DEFAULT_MODEL`, falling back to `"openrouter/deepseek/deepseek-v3"` for cost-effective OSS-model experimentation, but operator can override).

**Change to `harness/agent.py`:**

`_agent_command()` at line 38 has two branches today (claude / codex). Add a third:

```python
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
```

The `subprocess.Popen` call site at line 108-117 needs no change — the existing `cwd=str(SCRIPT_DIR)`, `stdin=subprocess.DEVNULL`, `stdout=log_file`, `stderr=err_file`, `env=_unbuffered_env()` configuration works identically for OpenCode (verified by spike).

**Change to `evolve.py`:**

`load_config()` at lines 253-261 validates `META_BACKEND ∈ {claude, codex}` and rejects others with `ERROR: Unsupported meta backend '<name>'`. Extend the allowed-set tuple to `("claude", "codex", "opencode")`. Note: this is the env var `META_BACKEND` (or the `--backend` CLI arg), **not** `EVOLUTION_EVAL_BACKEND` which lives in `evaluate_variant.py` and controls a different subprocess.

`_build_meta_command()` at lines 500-521 has parallel claude / codex branches gated on `config.meta_backend`. Add a third branch:

```python
if config.meta_backend == "opencode":
    return [
        "opencode", "run",
        "--dangerously-skip-permissions",
        "-m", config.meta_model,
        "--format", "json",
        "--dir", str(workdir),
    ]
```

Note: meta-agent reads its prompt from stdin (see `run_meta_agent` line 541-549), but `opencode run` takes the prompt as a positional argument. Implementation should buffer stdin, then append it as the trailing argv element. Alternatively, write the prompt to a temp file and pass via `<(cat prompt_file)` — but argv-passing is simpler and matches the verified spike pattern.

`configure_eval_target_env()` at lines 350-389 propagates `EVOLUTION_EVAL_BACKEND` to the env passed to the eval subprocess. **No change needed here** — this function does not validate the backend value itself; that validation happens in `evaluate_variant.py`.

**Change to `evaluate_variant.py`:**

The `EVOLUTION_EVAL_BACKEND` validator at lines 186-193 currently raises `RuntimeError("EVOLUTION_EVAL_BACKEND is required and must be one of: claude, codex.")`. Extend to `{claude, codex, opencode}` and update the error-message text to match.

**Change to `autoresearch/README.md`:**

Lines 93-95 document the existing `EVOLUTION_EVAL_BACKEND=codex` / `EVOLUTION_EVAL_MODEL=gpt-5.4` setup. Add a sibling example showing the OpenCode-via-OpenRouter setup (`EVOLUTION_EVAL_BACKEND=opencode`, `EVOLUTION_EVAL_MODEL=openrouter/deepseek/deepseek-v3`) and a one-line note about OpenCode's auth living in `~/.local/share/opencode/auth.json`.

**Tool allowlist note:** OpenCode does **not** accept a `--allowedTools` flag equivalent to Claude Code's. Tool scoping is configured in `opencode.json` per-project under `permission.bash` / `permission.edit` etc. For the harness's `--dangerously-skip-permissions` use case (autonomous fixers in worktree-isolated sessions), the flag is sufficient and no `opencode.json` is needed. If finer-grained allowlisting becomes required later, the design path is to materialize an `opencode.json` per-worktree alongside the session prompt — a follow-up, not a v1 requirement.

### Layer B-hot — In-process JSON judge (parent selection)

**Touch points:** `autoresearch/agent_calls.py` (one function: `_call_openai_json` at line 124).

`_call_openai_json` constructs an `AsyncOpenAI` client at line 138 using only `api_key`. Extend to read two optional env vars:

- `AUTORESEARCH_PARENT_BASE_URL` — when set, passes `base_url=` to the AsyncOpenAI constructor. OpenRouter's value: `"https://openrouter.ai/api/v1"`.
- `AUTORESEARCH_PARENT_API_KEY` — when set, takes precedence over `OPENAI_API_KEY` for this client only. Lets the operator route this one judge call to OpenRouter without disturbing other OpenAI usage in the codebase.

Default behavior (no env vars set) is unchanged — direct OpenAI with `OPENAI_API_KEY`.

The `model` parameter at line 127 already accepts arbitrary strings; operator passes `"openrouter/anthropic/claude-opus-4.7"` or `"deepseek/deepseek-v3"` etc. depending on the routed `base_url`.

`response_format={"type": "json_object"}` at line 145 is supported by OpenRouter's OpenAI-compatible endpoint for any underlying model that supports JSON mode (most modern models do; OpenRouter passes through structured-output capability).

**Code sketch:**

```python
client = AsyncOpenAI(
    api_key=os.environ.get("AUTORESEARCH_PARENT_API_KEY") or key,
    base_url=os.environ.get("AUTORESEARCH_PARENT_BASE_URL"),  # None → default OpenAI
)
```

~5 lines, two env vars, no new dependency.

### Layer B-cold — CLI-subprocess JSON judge (alert agent)

**Touch points:** `autoresearch/compute_metrics.py` (one function: `_run_claude_json` at line 224).

Currently spawns `claude -p prompt --output-format json --session-id <uuid> --model X --dangerously-skip-permissions` and parses Claude's `{"result": "..."}` JSON envelope.

Migrate to `opencode run --dangerously-skip-permissions -m provider/model --format json prompt`. The OpenCode JSONL output requires a different parser (see Appendix A): walk the events, find the final `text` event with `metadata.openai.phase == "final_answer"` (or for non-OpenAI providers, the last `text` event before the final `step_finish` with `reason: "stop"`).

**Rename:** `_run_claude_json` → `_run_alert_agent_json` (the function is no longer Claude-specific).

**Backend selector reuse:** Use the same `session_backend()` selection mechanism as the harness — alert agent inherits the operator's chosen backend. New env var: `AUTORESEARCH_ALERT_BACKEND` overrides per-call (defaults to `session_backend()`'s output).

**Default model behavior:** `AUTORESEARCH_ALERT_MODEL` (existing) defaults to `"sonnet"`, which is correct for the claude backend but not meaningful for opencode. When `AUTORESEARCH_ALERT_BACKEND=opencode`, the operator must set `AUTORESEARCH_ALERT_MODEL` explicitly to a `provider/model` string (e.g., `anthropic/claude-haiku-4.5`, `openrouter/deepseek/deepseek-v3-chat`). Implementation enforces this with a fail-loud RuntimeError if the combination is unset, matching the existing strict-validation pattern in evolve.py for `EVOLUTION_EVAL_*` vars.

### Telemetry — new `harness/opencode_jsonl.py` parser utility

OpenCode's JSONL `step_finish` events emit per-step `cost` (float, USD) and `tokens` ({total, input, output, reasoning, cache: {write, read}}).

**Note on file placement:** an earlier version of this spec proposed extending `harness/telemetry.py`, but `harness/telemetry.py` is in fact the freddy session-tracking module (functions: `tracking_start`, `tracking_end`, `push_iteration`, `compute_inner_keep_rate`, `push_phase_event`) — it does not currently parse model output. Adding a JSONL parser there would mix concerns. **Implementation places the parser in a new sibling file `autoresearch/harness/opencode_jsonl.py`** with a single `parse_session(log_path: Path) -> SessionSummary` entry point. Existing CLI-output parsers live with their consumers (e.g., the inline parser in `compute_metrics._run_alert_agent_json`).

**SessionSummary shape:**
```python
@dataclass(frozen=True)
class SessionSummary:
    total_cost: float = 0.0          # sum of step_finish.part.cost across events
    total_cache_reads: int = 0       # sum of step_finish.part.tokens.cache.read
    final_answer: str | None = None  # last text event with phase=final_answer, or last text before terminal step_finish
```

Malformed JSONL lines are skipped (not fatal). Empty file returns a zero-valued summary.

**v1 consumer:** none yet; the helper is added in anticipation of a session-cost aggregator. The alert-agent path (`compute_metrics._run_alert_agent_json`) parses OpenCode JSONL inline — duplicating the logic in ~25 lines — because it operates on subprocess.run captured stdout (a string), not a file path. If a third consumer materializes, refactor `parse_session` to accept either a path or a string.

### Configuration — env vars only

No `providers.yaml`, no new config files. Following the existing pattern in `harness/backend.py:22-49`:

| Env var | Purpose | Default | Affects |
|---|---|---|---|
| `AUTORESEARCH_SESSION_BACKEND` | Pick harness agentic CLI: `claude` / `codex` / `opencode` | (auto: `codex` if available else `claude`) | Layer A — harness |
| `AUTORESEARCH_SESSION_MODEL` | Model for harness agentic CLI | per-backend default | Layer A — harness |
| `AUTORESEARCH_OPENCODE_DEFAULT_MODEL` | OpenCode's harness model when backend=opencode and `AUTORESEARCH_SESSION_MODEL` unset | `openrouter/deepseek/deepseek-v3` | Layer A — harness |
| `EVAL_BACKEND_OVERRIDE` | Forces harness backend (existing) | unset | Layer A — harness |
| `EVAL_MODEL_OVERRIDE` | Forces harness model (existing) | unset | Layer A — harness |
| `META_BACKEND` (existing — extended) | Pick evolve meta-agent CLI: `claude` / `codex` / `opencode` | (auto: `codex` if available else `claude`) | Layer A — evolve meta |
| `EVOLUTION_EVAL_BACKEND` (existing — extended) | Pick per-variant eval subprocess CLI: `claude` / `codex` / `opencode` | required (no auto) | Layer A — eval subprocess |
| `EVOLUTION_EVAL_MODEL` (existing) | Model for per-variant eval | required | Layer A — eval subprocess |
| `EVOLUTION_EVAL_REASONING_EFFORT` (existing) | Reasoning effort for per-variant eval | `high` | Layer A — eval subprocess |
| `AUTORESEARCH_PARENT_BASE_URL` | Custom OpenAI-compatible endpoint for parent selection | unset (= OpenAI direct) | Layer B-hot |
| `AUTORESEARCH_PARENT_API_KEY` | Override key for parent selection only | unset (= `OPENAI_API_KEY`) | Layer B-hot |
| `AUTORESEARCH_ALERT_BACKEND` | Backend for alert agent | (= `session_backend()`) | Layer B-cold |
| `AUTORESEARCH_ALERT_MODEL` (existing) | Model for alert agent | `sonnet` | Layer B-cold |

`OPENROUTER_API_KEY` should be added to `.env` if Layer B-hot routes to OpenRouter; OpenCode's own auth (Layer A + B-cold) is managed via OpenCode's internal credential store, not `.env`.

## Implementation sketch (file-by-file)

| File | Function(s) | Approx LoC | Change |
|---|---|---|---|
| `autoresearch/harness/backend.py` | `session_backend`, `default_session_model` | ~10 | Add `"opencode"` to allowed-set; add `shutil.which("opencode")` fallback; add per-backend default-model branch |
| `autoresearch/harness/agent.py` | `_agent_command` | ~12 | Third elif branch building the OpenCode command list |
| `autoresearch/harness/opencode_jsonl.py` (NEW) | OpenCode JSONL parser utility | ~50 | New `parse_session(log_path) -> SessionSummary` helper; skips malformed lines; tested in `tests/autoresearch/test_opencode_jsonl.py` |
| `autoresearch/evolve.py` | `load_config` `META_BACKEND` validator (lines 253-261) + `_build_meta_command` (lines 500-521) | ~20 | Extend `META_BACKEND` allowed-tuple to include opencode; add third elif branch in `_build_meta_command` (with stdin-to-argv adapter for opencode) |
| `autoresearch/evaluate_variant.py` | `EVOLUTION_EVAL_BACKEND` validator (lines 186-193) | ~5 | Extend allowed-set; update error-message text |
| `autoresearch/agent_calls.py` | `_call_openai_json` | ~5 | Read `AUTORESEARCH_PARENT_BASE_URL`, `AUTORESEARCH_PARENT_API_KEY`; pass to `AsyncOpenAI()` |
| `autoresearch/compute_metrics.py` | `_run_claude_json` → `_run_alert_agent_json` | ~25 | Branch on `AUTORESEARCH_ALERT_BACKEND`; for opencode, build different command + parse JSONL |
| `autoresearch/README.md` | env-var setup section (lines 93-95) | ~5 | Add OpenCode-via-OpenRouter setup example + auth note |
| Tests | several | ~70 | Backend=opencode branch coverage in `test_agent.py`; `EVOLUTION_EVAL_BACKEND=opencode` coverage in evolve / evaluate_variant tests; env-var coverage in `test_select_parent.py`; telemetry parser branch coverage in `test_telemetry.py` |

**Total production-code change:** ~100-105 lines across 8 files. **Plus ~70 lines of tests.**

## Setup prerequisites (operator-side)

1. **Install OpenCode CLI.** `curl -fsSL https://opencode.ai/install | bash` — installs to `~/.opencode/bin/opencode`. Add to PATH.
2. **Configure OpenCode credentials.** `opencode auth login` interactively, or place pre-existing `auth.json` at `~/.local/share/opencode/auth.json`. If multiple OpenCode installs exist on the operator's machine (e.g., a prior install at `~/.config/opencode/` plus a fresh install at `~/.opencode/bin/`), pick one canonical PATH location to avoid confusion about which credential store is in use.
3. **(Optional, only if Layer B-hot routes to OpenRouter)** Add `OPENROUTER_API_KEY` to `.env`. Set `AUTORESEARCH_PARENT_BASE_URL=https://openrouter.ai/api/v1` and `AUTORESEARCH_PARENT_API_KEY=$OPENROUTER_API_KEY` to enable.
4. **(Smoke test)** `AUTORESEARCH_SESSION_BACKEND=opencode AUTORESEARCH_SESSION_MODEL=openrouter/deepseek/deepseek-v3 python -m autoresearch.harness.agent ...` against a known-easy finding.

## Open risks and mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| OpenCode `--format json` output schema changes between releases (776 releases to date, schema documented by community not officially) | Medium | Pin OpenCode version in CI / `package.json`; add a telemetry parser regression test against a recorded JSONL fixture |
| OpenCode tool surface differs from Claude Code (uses `apply_patch` not `Edit`) | Low | Verifier's 6 probes inspect file state, not tool names — verified spike passes regardless of tool used |
| OpenCode subprocess.Popen + `--format json` hang issue #11891 reappears under specific stdin/stdout configurations | Low (refuted in spike for our pattern) | Existing pattern uses file-redirected stdout, not `readline()` consumption — issue #11891 is the latter. If detected, fall back to non-JSON `opencode run` and parse text output |
| OpenRouter quota/rate-limiting on OSS models causes session failure | Medium | Operator sets per-call timeouts; harness's existing `subprocess.TimeoutExpired` path at agent.py:119-121 catches and exits cleanly |
| Brand-split between sst/opencode and anomalyco/opencode causes confusion about which install is canonical | Low | Spec uses `opencode.ai/install` URL; pin npm package or brew tap in operator setup docs |
| Migrating `_run_claude_json` to opencode loses Claude-specific behavior (e.g., session-id resume) | Low | `_run_claude_json` doesn't use session resume today (`--session-id` is a fresh UUID per call at line 234) — no behavior to preserve |

## Out of scope

- **Audit engine** (`docs/plans/2026-04-24-005-feat-audit-engine-fusion-plan.md`). The audit engine commits to `claude_agent_sdk` for in-process async lens-agent fanout with per-role `max_budget_usd`. That plan picks its own model layer at implementation time and may use different conventions than this spec.
- **Replacing Claude Code or Codex backends.** Both remain first-class. OpenCode is purely additive.
- **LiteLLM, LangChain, LangGraph, OpenAI Agents SDK, or any orchestration framework.** OpenCode + the existing harness orchestration layer cover all current needs.
- **Custom tool implementations.** OpenCode's bundled tool set (`read`, `edit`/`apply_patch`, `bash`, `glob`, `grep`, `write`) covers the harness fixer's needs. No need to author MCP servers or custom tools in v1.
- **Streaming evaluator / mid-session interception.** Out of scope; if the audit engine ever needs this it goes through `claude_agent_sdk` per its own plan.
- **Provider routing for the audit engine's lens agents.** Handled by the audit engine plan.

---

## Appendix A — OpenCode JSONL event schema (verified 2026-04-26)

Each line is one JSON object. Top-level fields: `type` (one of `step_start`, `text`, `tool_use`, `step_finish`), `timestamp` (ms), `sessionID`, `part` (event-specific payload).

**`step_start`** — beginning of a model-call step. Payload: `{id, messageID, sessionID, type:"step-start"}`.

**`text`** — assistant text output. Payload: `{id, messageID, sessionID, type:"text", text:"...", time:{start, end}, metadata:{openai:{itemId, phase}}}`. `phase` is `"commentary"` for narrating thoughts, `"final_answer"` for the final response.

**`tool_use`** — tool invocation. Payload: `{type:"tool", tool:"<name>", callID, state:{status:"completed", input:{...}, output:"...", metadata:{...}}, time:{start, end}}`. Tool names observed: `read`, `apply_patch`, `bash`, `write`, `edit`, `glob`, `grep`. Tool-specific input/output shapes documented per-tool in `opencode.ai/docs`.

**`step_finish`** — end of a step. Payload: `{id, reason:"tool-calls"|"stop"|..., messageID, sessionID, type:"step-finish", tokens:{total, input, output, reasoning, cache:{write, read}}, cost: <float USD>}`. Final step has `reason:"stop"`.

**Telemetry parsing pattern:**
- Total cost: sum of all `step_finish.part.cost` events
- Total cache reads: sum of all `step_finish.part.tokens.cache.read`
- Final answer: last `text` event before the terminal `step_finish` with `reason:"stop"`
- Tool-call audit: filter `tool_use` events for verifier-visible tool names

## Appendix B — Spike artifacts

Workspace: `/tmp/agentic-cli-spike/`
- `target.py` — fixture file edited by spike runs
- `prompt.txt` — synthetic prompt forcing Read + Edit + Bash
- `goose.stdout.log`, `goose.stderr.log` — Goose spike output
- `opencode.stdout.log`, `opencode.stderr.log` — OpenCode spike output

These are scratch artifacts for the spec evidence; not committed to the repo.
