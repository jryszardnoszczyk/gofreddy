# Fixture Infrastructure Implementation Plan (Plan A of 2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the qualitative-first fixture authoring and validation infrastructure — CLI tooling (`freddy fixture <cmd>`), cache layer with staleness detection, judge-based calibration harness, versioning, and pool-separation conventions — and delete the superseded legacy code it replaces.

**Architecture:** New `freddy fixture` command group exposes `validate` / `list` / `envs` / `staleness` / `refresh` / `dry-run` / `discriminate` subcommands. Fixtures gain a required semver `version` field. Cache lives at `~/.local/share/gofreddy/fixture-cache/<pool>/<fixture_id>/v<version>/` with a per-fixture `CacheManifest` tracking fetch metadata and retention. Cache-artifact filenames include a short sha1 hash of the primary call-argument so multiple args can coexist under one fixture. Cache-first reads are wired for geo (`freddy scrape`) and monitoring (`freddy monitor mentions/sentiment/sov`) only; opt-in via `FREDDY_FIXTURE_*` env vars. Holdout pools hard-fail on cache miss to prevent identity leakage. Manual refresh is the only cache-update path — never automatic.

**Tech Stack:** Python 3.11+, existing Typer-based `freddy` CLI, existing `autoresearch` harness. No new runtime dependencies.

**Companion plan:** `2026-04-21-003-feat-fixture-program-execution-plan.md` (Plan B) uses this infrastructure to author holdout-v1 + expand search-v1 + run the overfit canary + enable autonomous promotion. Plan B's Phase 1 (taxonomy matrix) can be drafted in parallel with Plan A; Plan B Phases 2+ require Plan A Phase 7 (dry-run) to have landed.

**Out of scope (separate initiatives, not postponed parts of this plan):** MAD confidence scoring, `lane_checks.sh` correctness gates, lane scheduling rework, IRT benchmark-health dashboard, full MT-Bench-style judge-calibration harness. These are different features covered by separate initiatives; nothing in this plan is weakened or delayed by their absence. (Cross-family judge and per-fixture win-rate, originally listed as out-of-scope, are NOW included in Plan B Phase 6 Steps 3b/3c.)

---

## File Structure

**New files:**
- `cli/freddy/fixture/__init__.py` — module init
- `cli/freddy/fixture/schema.py` — `FixtureSpec`, `SuiteManifest`, validators
- `cli/freddy/fixture/cache.py` — cache manifest format + staleness + arg-hashed filenames
- `cli/freddy/fixture/cache_integration.py` — helpers read by the four cache-first-wired freddy commands
- `cli/freddy/fixture/refresh.py` — manual refresh orchestration
- `cli/freddy/fixture/dryrun.py` — judge-based calibration + rank-sum discriminability
- `cli/freddy/commands/fixture.py` — command group registering subcommands
- `autoresearch/eval_suites/SCHEMA.md` — authoritative schema documentation
- `tests/freddy/__init__.py` (empty; Phase 2)
- `tests/freddy/conftest.py` — sys.path shim so `cli.freddy.*` and `autoresearch.*` import (Phase 2)
- `tests/freddy/fixture/test_schema.py`
- `tests/freddy/fixture/test_cli_integration.py`
- `tests/freddy/fixture/test_validate.py`
- `tests/freddy/fixture/test_list_envs.py`
- `tests/freddy/fixture/test_cache.py`
- `tests/freddy/fixture/test_staleness.py`
- `tests/freddy/fixture/test_refresh.py`
- `tests/freddy/fixture/test_dryrun.py`
- `tests/freddy/fixture/test_discriminate.py`
- `tests/freddy/fixture/test_cache_integration.py`
- `tests/autoresearch/test_evaluate_single_fixture.py` — exercises the new `evaluate_single_fixture` entry point

**Modified files:**
- `autoresearch/evaluate_variant.py` — add `version` field support + tighten loader (Phase 1); add `--single-fixture` / `--seeds` / `--json-output` flags + `evaluate_single_fixture` entry point (Phase 7); remove canary gate and one-time `_finalized/` migration (Phase 11)
- `autoresearch/evolve.py` — remove `_DEPRECATED_COMMANDS` dict + `_check_deprecated_commands` helper and its call site (Phase 11)
- `autoresearch/eval_suites/search-v1.json` — add suite `version` + per-fixture `version` fields (Phase 1)
- `cli/freddy/main.py` — register new `fixture` command group via `app.add_typer(fixture.app, name="fixture")` (Phase 2)
- `cli/freddy/commands/monitor.py`, `scrape.py` — cache-first read path (Phase 8). Competitive / visibility / search-ads / search-content are intentionally NOT wired.
- `autoresearch/README.md` — add "Fixture authoring" section (Phase 9); drop references to retired artifacts (Phase 11)

**Deleted files:**
- `autoresearch/archive_cli.py`
- `autoresearch/geo_verify.py`
- `autoresearch/geo-verify.sh`

---

## Phase 0: Branch Setup and Baseline

**Files:** none changed; verification only

- [ ] **Step 1: Create feature branch**

Run: `git checkout -b feat/fixture-infrastructure`

- [ ] **Step 2: Verify test suite is green**

Run: `pytest tests/autoresearch/ -x -q` — expect all pass.

- [ ] **Step 3: Snapshot baseline checksums**

Run: `sha256sum autoresearch/evaluate_variant.py autoresearch/evolve.py autoresearch/eval_suites/search-v1.json > /tmp/fixture-infra-baseline-sha.txt` — expect 3 checksums in file.

- [ ] **Step 4: Verify scipy availability**

Run: `python -c "import scipy.stats; print(scipy.stats.__name__)"` — expect `scipy.stats` (no ImportError). scipy is already present (used by `src/generation/music_service.py`; pinned in `requirements.txt`). If missing, add `scipy>=1.17` to `pyproject.toml`/requirements and re-run.

- [ ] **Step 5: Produce Phase 0 inventory artifact (cost + stdout shape)**

Run each wired command (`freddy monitor mentions`, `freddy monitor sentiment`, `freddy monitor sov`, `freddy scrape`, `freddy visibility`, `freddy search-ads`, `freddy search-content`) against a realistic input and record its output shape + cost-emission path. Commit the findings as `docs/plans/phase-0-inventory.json`:

```json
{
  "generated_at": "2026-04-XX...",
  "commands": {
    "freddy monitor mentions": {
      "stdout_shape": "dict",
      "top_level_keys_sample": ["items", "_meta"],
      "cost_emission_path": "_meta.cost_usd",
      "shape_flags": ["format"],
      "json_flag_required": false
    },
    "freddy scrape": {
      "stdout_shape": "dict",
      "cost_emission_path": "absent",
      "shape_flags": [],
      "json_flag_required": false
    }
  }
}
```

`cost_emission_path` values: `_meta.cost_usd` | `cost_usd` (top-level) | `absent`.
`shape_flags` values: list of CLI flag names that alter payload shape (drives Phase 4 `SHAPE_FLAGS_REGISTRY`).
`json_flag_required: true` means the command emits non-JSON by default and a `--json` flag must be passed.

**Phase 6 `_run_source_fetch` + Phase 4 `SHAPE_FLAGS_REGISTRY` both read this artifact** rather than hardcoded assumptions. This replaces the prior scratchpad + "pick one path before starting Phase 6" hand-wave — now every downstream phase has a typed contract to assert against.

Acceptance: `phase-0-inventory.json` exists, committed, and contains one entry per wired command. If any command emits neither `_meta.cost_usd` nor top-level `cost_usd`, declare `"cost_emission_path": "absent"` — Phase 6's cost-extraction helper will then not warn on zero for that command.

- [ ] **Step 6: Commit initial state**

```bash
git commit --allow-empty -m "chore: start fixture infrastructure branch

Baseline captured in /tmp/fixture-infra-baseline-sha.txt"
```

---

## Phase 0c: Judge Service Isolation (Load-Bearing Prerequisite)

**Purpose:** Physically isolate judge code, prompts, credentials, and verdict history from autoresearch worker agents (meta-agent + variant session subprocesses). Enforces the anti-gaming / anti-pollution guarantee that the dual-judge architecture was designed to provide.

**Threat model:**

| Process | Role | Can read judge code? | Has CLI auth? | Can read prior verdicts? | Can mutate judge prompts? |
|---|---|---|---|---|---|
| Meta-agent subprocess | UNTRUSTED (proposes variants) | NO | NO | NO | NO |
| Variant session subprocess | UNTRUSTED (runs a variant's work) | NO | NO | NO | NO |
| Evolution orchestrator | TRUSTED (runs evolve.sh) | NO | NO | via redacted summaries | **session only** (via admin API) |
| Session-judge-service host | OWNS session/ code | YES | YES (claude/codex) | YES | YES |
| Evolution-judge-service host | OWNS evolution/ code | YES | YES (claude/codex) | YES | PR-gated only |
| Human engineer via PR | TRUSTED (dev time) | YES (via PR review) | NO | YES (via logs) | YES (both) |

**Architectural asymmetry — why two services:**

Session judges live *inside* the evolution loop: they're part of the thing being refined. Their prompts can evolve via a trusted orchestrator tuning loop based on observed outcomes. Evolution judges live *outside/meta*: they're the reference point that must stay stable during iteration, otherwise cross-cycle scoring comparisons become meaningless. Freezing evolution judges is load-bearing; making session judges tunable prevents the rubric from becoming the system's learning ceiling.

This asymmetry maps to two runtime services with different mutation policies. Meta-agent cannot reach either service's code, prompts, or credentials — the HTTP API is the only exposed surface.

### Files

- Create: `judges/session/` — review, critique + prompt files (runs on session-judge-service host)
- Create: `judges/evolution/` — `variant_scorer`, 3 decision agents (`promotion_agent`, `rollback_agent`, `canary_agent`), 1 unified `system_health_agent` + prompt files (runs on evolution-judge-service host)
- Create: `judges/server.py` — FastAPI server shared by both services (role-locked per deployment)
- Create: `judges/invoke_cli.py` — `claude` / `codex` CLI wrappers (replaces httpx+API-key path)
- Create: `judges/deploy/` — deploy manifests per service (GitHub Actions / Dockerfile / local-daemon options A/B/C)
- Create: `.github/workflows/deploy-session-judge.yml`
- Create: `.github/workflows/deploy-evolution-judge.yml`
- Modify: `cli/freddy/commands/evaluate.py` → thin HTTP client to session-judge-service (drops `EVALUATE_PROMPT`, drops httpx+API-key path)
- Modify: `autoresearch/evaluate_variant.py::_score_session` → calls evolution-judge-service via HTTP (not `freddy evaluate variant` subprocess)
- Modify: `cli/freddy/main.py` → add lint-time check that `autoresearch/` and `cli/` never import from `judges/`
- Create: `tests/judges/` — FastAPI TestClient-based integration tests
- **Remove from autoresearch-side runtime:** `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` env vars. Credentials live only on judge-service hosts.

### Directory structure

**Agent count rationale:** The 4 main domain judges (GEO / Competitive / Monitoring / Storyboard × 8-criteria rubric per domain, primary + secondary families) do all the heavy variant-quality evaluation. Auxiliary agents are a thin meta layer:

- **3 separate decision agents** for high-stakes autonomous actions: promotion, rollback, canary. Each gets its own focused prompt + dedicated file because the input shapes and decision surfaces differ and each drives an autonomous action.
- **1 unified system-health agent** for advisory/meta concerns (saturation, content drift, discriminability, fixture quality, calibration drift, noise escalation). One file + one prompt with role dispatch — each invocation is a fresh CLI call with role-specific framing, so no cross-concern context leak across calls. Qualitative signal is preserved (simple thresholds miss reasoning drift and material-vs-cosmetic distinctions); ceremony is minimized (one file vs six).

```
judges/
├── session/                              # deployed to session-judge-service host only
│   ├── agents/
│   │   ├── review_agent.py               # adversarial reviewer
│   │   └── critique_agent.py             # session-time critique
│   └── prompts/
│       ├── review.md
│       └── critique.md
├── evolution/                            # deployed to evolution-judge-service host only
│   ├── agents/
│   │   ├── variant_scorer.py             # per-fixture scoring (primary + secondary via codex + claude CLIs)
│   │   ├── promotion_agent.py            # autonomous: promote | reject (reads scores across fixtures)
│   │   ├── rollback_agent.py             # autonomous: rollback | hold (reads head-score trajectory)
│   │   ├── canary_agent.py               # autonomous one-shot: go | fail | revise (reads canary checkpoints)
│   │   └── system_health_agent.py        # advisory, role-dispatched (see roles below)
│   └── prompts/
│       ├── scorer.md
│       ├── promotion.md
│       ├── rollback.md
│       ├── canary.md
│       └── system_health.md              # single prompt file; role-sectioned
├── server.py                             # FastAPI — deployed to both, scoped to local dir at runtime
├── invoke_cli.py                         # claude / codex CLI wrappers
├── deploy/
│   ├── session-judge.Dockerfile
│   ├── evolution-judge.Dockerfile
│   └── local-daemon.sh
└── tests/                                # judge-side integration tests
```

**`system_health_agent.py` role dispatch:**

| Role | Input | Verdict values |
|---|---|---|
| `saturation` | per-fixture beat-rate history | `rotate_now` / `rotate_soon` / `fine` |
| `content_drift` | old + new content previews, fixture metadata | `material` / `cosmetic` / `unknown` |
| `discriminability` | two variants' score distributions + Wilcoxon p + Cliff's delta | `separable` / `not_separable` / `insufficient_data` |
| `fixture_quality` | dry-run per-seed scores + MAD + median + cost | `healthy` / `saturated` / `degenerate` / `unstable` / `cost_excess` |
| `calibration_drift` | baseline + current scores+reasoning from ONE family (called once per family for cross-family check) | `stable` / `magnitude_drift` / `variance_drift` / `reasoning_drift` / `mixed` |
| `noise_escalation` | observed IQR + current seed count + trajectory | `sufficient` / `bump_seeds` / `bump_iterations` |

All 6 roles are batchable where N items of the same role are available (e.g., 30 fixtures' saturation histories in one call, 16 fixtures' discriminability pairs in one call). Batch prompts include explicit stateless framing ("evaluate each item independently; peer-ranked not sequential"). Max batch size 20; larger splits into multiple calls. Parse-failure fallback to per-item calls with `kind="judge_batch_fallback"` event logged.

### HTTP API contracts

**Session-judge-service** (port 7100; bearer-token authenticated):

| Endpoint | Auth | Purpose |
|---|---|---|
| `POST /invoke/review` | `SESSION_INVOKE_TOKEN` | Adversarial review; returns `{decision, confidence, weaknesses[], rationale}` |
| `POST /invoke/critique` | `SESSION_INVOKE_TOKEN` | Trusted critique; returns structured critique JSON |
| `POST /admin/tune-prompt/{judge_name}` | `SESSION_ADMIN_TOKEN` | Orchestrator-only; updates prompt file with audit-logged diff |

**Evolution-judge-service** (port 7200; bearer-token authenticated):

| Endpoint | Auth | Purpose |
|---|---|---|
| `POST /invoke/score` | `EVOLUTION_INVOKE_TOKEN` | Score one session artifact set; returns per-fixture scores + aggregates (primary + secondary) |
| `POST /invoke/decide/promotion` | `EVOLUTION_INVOKE_TOKEN` | Autonomous promote | reject |
| `POST /invoke/decide/rollback` | `EVOLUTION_INVOKE_TOKEN` | Autonomous rollback | hold |
| `POST /invoke/decide/canary` | `EVOLUTION_INVOKE_TOKEN` | Autonomous go | fail | revise |
| `POST /invoke/system_health/{role}` | `EVOLUTION_INVOKE_TOKEN` | Advisory; role ∈ {saturation, content_drift, discriminability, fixture_quality, calibration_drift, noise_escalation}; batchable via `{items: [...]}` request body |

No mutation API on evolution-judge-service. Prompt changes ship via PR-gated deploy only — the `deploy-evolution-judge.yml` workflow is the only write path. This is how we preserve cross-cycle scoring stability.

**Token storage:**
- `SESSION_INVOKE_TOKEN`: on autoresearch host; readable by variant subprocesses (they need to call session judges); rotates monthly
- `SESSION_ADMIN_TOKEN`: on autoresearch host only, in a path readable by the trusted orchestrator, NOT inheritable by variant subprocesses (env-scrubbed on subprocess spawn)
- `EVOLUTION_INVOKE_TOKEN`: on autoresearch host; readable by trusted orchestrator (needed for scoring + decisions); env-scrubbed on meta-agent / variant subprocess spawn so only trusted code calls evolution-judge

### `claude` + `codex` CLI invocation (replaces httpx+API-key)

All judge-side model calls go through the CLI tools, which authenticate via subscription rather than API keys. No provider credentials live as env vars on any host.

```python
# judges/invoke_cli.py — runs on judge-service hosts only

import asyncio, json, subprocess
from pathlib import Path


CLAUDE_POOL_SIZE = 3  # concurrent claude CLI invocations per service
CODEX_POOL_SIZE = 3   # concurrent codex CLI invocations per service

_claude_sem = asyncio.Semaphore(CLAUDE_POOL_SIZE)
_codex_sem = asyncio.Semaphore(CODEX_POOL_SIZE)


async def invoke_claude(prompt: str, *, model: str = "claude-opus-4-7", timeout: int = 300) -> str:
    async with _claude_sem:
        proc = await asyncio.create_subprocess_exec(
            "claude", "--model", model, "--print", prompt,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            raise RuntimeError(f"claude CLI timeout after {timeout}s")
        if proc.returncode != 0:
            raise RuntimeError(f"claude CLI exit {proc.returncode}: {stderr.decode()[:500]}")
        return stdout.decode()


async def invoke_codex(prompt: str, *, model: str = "gpt-5.4", timeout: int = 300) -> str:
    async with _codex_sem:
        proc = await asyncio.create_subprocess_exec(
            "codex", "exec", "--model", model, prompt,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            raise RuntimeError(f"codex CLI timeout after {timeout}s")
        if proc.returncode != 0:
            raise RuntimeError(f"codex CLI exit {proc.returncode}: {stderr.decode()[:500]}")
        return stdout.decode()
```

**Rate-limit policy:** subscription tiers throttle concurrent requests tighter than API. Pool-of-3 per CLI per service (6 total across both services when both are on separate hosts) is the starting conservative default; bump if observation shows underutilization without throttling. Requests above the pool size queue; the service returns HTTP 503 with `Retry-After` if the queue grows past 30s deep.

**No API-key fallback.** The plan drops httpx + `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` entirely. If the CLI subscription tools are down, the judge-service returns 503 and the evolution loop pauses until they recover. This is deliberate: having a credential-based fallback path means the credential has to live somewhere, and somewhere is gameable. Availability vs. isolation — we picked isolation.

### Service implementation sketch

```python
# judges/server.py — deployed to both session and evolution hosts with JUDGE_MODE env var

from fastapi import FastAPI, HTTPException, Header
from pathlib import Path
import json, os, hashlib

MODE = os.environ["JUDGE_MODE"]  # "session" | "evolution"
INVOKE_TOKEN = os.environ["INVOKE_TOKEN"]
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")  # only set on session-judge-service
EVENTS_LOG = Path("/var/lib/gofreddy-judges/events.jsonl")  # judge-side audit log

app = FastAPI()


def _require_token(authorization: str | None, required: str) -> None:
    if not authorization or authorization != f"Bearer {required}":
        raise HTTPException(401, "invalid token")


def _log(kind: str, payload: dict, verdict: dict) -> None:
    EVENTS_LOG.parent.mkdir(parents=True, exist_ok=True)
    payload_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]
    with EVENTS_LOG.open("a") as f:
        f.write(json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "kind": kind, "mode": MODE,
            "payload_hash": payload_hash,
            "verdict": verdict,  # full reasoning trace stays on this side
        }) + "\n")
        f.flush(); os.fsync(f.fileno())


@app.post("/invoke/critique")
async def invoke_critique(payload: dict, authorization: str | None = Header(None)):
    _require_token(authorization, INVOKE_TOKEN)
    if MODE != "session":
        raise HTTPException(404, "session endpoint on wrong service")
    from judges.session.critique import critique_session
    verdict = await critique_session(payload)
    _log("critique", payload, verdict)
    return verdict  # caller receives verdict only; reasoning-trace body may be truncated for caller
```

Each handler imports from the local `judges/session/` or `judges/evolution/` dir at request time. The FastAPI process itself has no ability to read the OTHER service's directory (it isn't deployed there). Crossing a service boundary requires HTTP.

### Deployment boundary enforcement

**CI lint rule** in `.github/workflows/ci.yml`:
```bash
# Fails the build if autoresearch or cli imports from judges/
if rg -l "^from judges|^import judges" autoresearch/ cli/ src/; then
    echo "FAIL: autoresearch/cli/src must not import from judges/"
    exit 1
fi
```

**Deploy pipelines:**
- `deploy-session-judge.yml`: `rsync judges/session/ judges/server.py judges/invoke_cli.py judges/prompts/session/` → session-judge-host; sets `JUDGE_MODE=session`, `INVOKE_TOKEN=<secret>`, `ADMIN_TOKEN=<secret>`
- `deploy-evolution-judge.yml`: `rsync judges/evolution/ judges/server.py judges/invoke_cli.py judges/prompts/evolution/` → evolution-judge-host; sets `JUDGE_MODE=evolution`, `INVOKE_TOKEN=<secret>`; NO admin token
- `deploy-autoresearch.yml`: `rsync --exclude='judges/' .` → autoresearch-host; the judges/ directory literally does not exist on that filesystem

**Local-dev fallback (Option C):** run both judge-services as local daemons under a separate OS user (`judge-service`), bound to 127.0.0.1:7100 / 7200. Autoresearch runs as the normal user; filesystem ACLs (`chmod 700` on `~/.local/share/gofreddy-judges/`) deny read access from the autoresearch user. This is dev-only — documented in commit messages when used for production runs.

### Autoresearch-side HTTP clients

```python
# cli/freddy/commands/evaluate.py — now a thin HTTP client (drops EVALUATE_PROMPT and all model-call logic)

import httpx, json, os, typer

app = typer.Typer(help="Evaluate content quality (thin HTTP clients to judge services).")

SESSION_JUDGE_URL = os.environ.get("SESSION_JUDGE_URL", "http://localhost:7100")
SESSION_INVOKE_TOKEN = os.environ.get("SESSION_INVOKE_TOKEN", "")
EVOLUTION_JUDGE_URL = os.environ.get("EVOLUTION_JUDGE_URL", "http://localhost:7200")
EVOLUTION_INVOKE_TOKEN = os.environ.get("EVOLUTION_INVOKE_TOKEN", "")


@app.command("review")
def review(session_dir: str) -> None:
    payload = {"session_dir": session_dir}  # judge-service loads artifacts itself
    r = httpx.post(f"{SESSION_JUDGE_URL}/invoke/review", json=payload,
                   headers={"Authorization": f"Bearer {SESSION_INVOKE_TOKEN}"}, timeout=300)
    r.raise_for_status()
    typer.echo(r.text)


@app.command("critique")
def critique(request_file: str) -> None:
    payload = json.loads(open(request_file).read())
    r = httpx.post(f"{SESSION_JUDGE_URL}/invoke/critique", json=payload,
                   headers={"Authorization": f"Bearer {SESSION_INVOKE_TOKEN}"}, timeout=300)
    r.raise_for_status()
    typer.echo(r.text)


@app.command("variant")
def variant(domain: str, session_dir: str, campaign_id: str, variant_id: str) -> None:
    payload = {"domain": domain, "session_dir": session_dir,
               "campaign_id": campaign_id, "variant_id": variant_id}
    r = httpx.post(f"{EVOLUTION_JUDGE_URL}/invoke/score", json=payload,
                   headers={"Authorization": f"Bearer {EVOLUTION_INVOKE_TOKEN}"}, timeout=400)
    r.raise_for_status()
    typer.echo(r.text)
```

**Session-artifact transfer — pick one per deployment:**

| Mode | How artifacts reach judge-service | When to use |
|---|---|---|
| **Shared volume** | Autoresearch + judge-service mount the same NFS / bind-mount / shared Docker volume. Autoresearch writes `~/.local/share/gofreddy/archive/<variant_id>/<session_id>/`; judge-service reads that path directly. Autoresearch POSTs only `{"session_dir": "<variant>/<session>"}` as a reference. | Local-dev (Option C) or single-host container setup (Option B with shared volume). Fast, zero network transfer, but requires filesystem coupling. |
| **Multipart upload** | Autoresearch tars the session dir (`tar cJ session/`), POSTs as `multipart/form-data` to `/invoke/score`. Judge-service extracts to ephemeral tmp dir, scores, deletes. | Remote judge-service (Option A GitHub Actions, or separate host). No filesystem coupling; payload is self-contained. Slower for large sessions. |
| **S3 / object-store reference** | Autoresearch uploads session tarball to S3 bucket; POSTs `{"artifact_url": "s3://..."}`. Judge-service pulls, scores, deletes. | Production with geographically-separated services. Requires S3 credentials on both sides (limited blast radius: read-only on judge-service, write-only on autoresearch). |

**Default for Plan A implementation:** shared-volume (Mode 1) for local-dev, multipart-upload (Mode 2) for GitHub-Actions deployment. S3 mode (Mode 3) deferred unless geographically-distributed operation becomes required.

The `POST /invoke/score` request schema accepts EITHER form:
```json
{
  "mode": "shared_volume" | "multipart" | "artifact_url",
  "session_ref": "<relative path>" | null,  // mode=shared_volume
  "artifact_url": "s3://..." | null,        // mode=artifact_url
  "fixture": {...}, "domain": "...", "lane": "...", "seeds": 10
}
```
For multipart uploads the session tarball is the first part of the multipart body; `mode` is in the JSON part.

Judge-service cleans up extracted artifacts after scoring completes (success or failure). Autoresearch keeps its own session-dir copy for lineage archival.

### Updated `autoresearch/judges/quality_judge.py` and `promotion_judge.py`

These become thin HTTP clients (reduces each from ~100 plan-described lines to ~30):

```python
# autoresearch/judges/promotion_judge.py

import httpx, json, os
from dataclasses import dataclass, field

EVOLUTION_JUDGE_URL = os.environ.get("EVOLUTION_JUDGE_URL", "http://localhost:7200")
EVOLUTION_INVOKE_TOKEN = os.environ.get("EVOLUTION_INVOKE_TOKEN", "")


@dataclass(frozen=True)
class PromotionVerdict:
    decision: str
    reasoning: str
    confidence: float
    concerns: list[str] = field(default_factory=list)


def call_promotion_judge(payload: dict) -> PromotionVerdict:
    # role ∈ {"promotion", "rollback", "canary"} — routes to the 3 dedicated
    # decision agents on the judge service.
    role = payload.get("role", "promotion")
    assert role in {"promotion", "rollback", "canary"}, f"invalid decision role: {role}"
    r = httpx.post(
        f"{EVOLUTION_JUDGE_URL}/invoke/decide/{role}", json=payload,
        headers={"Authorization": f"Bearer {EVOLUTION_INVOKE_TOKEN}"}, timeout=300,
    )
    r.raise_for_status()
    data = r.json()
    return PromotionVerdict(
        decision=str(data["decision"]),
        reasoning=str(data.get("reasoning", "")),
        confidence=float(data.get("confidence", 0.5)),
        concerns=list(data.get("concerns", [])),
    )


# autoresearch/judges/quality_judge.py — advisory/system-health client

def call_quality_judge(payload: dict) -> QualityVerdict:
    # role ∈ {"saturation", "content_drift", "discriminability",
    #         "fixture_quality", "calibration_drift", "noise_escalation"}.
    # All routes to the single unified system_health_agent on the judge service.
    role = payload.get("role")
    assert role in {
        "saturation", "content_drift", "discriminability",
        "fixture_quality", "calibration_drift", "noise_escalation",
    }, f"invalid system_health role: {role}"
    r = httpx.post(
        f"{EVOLUTION_JUDGE_URL}/invoke/system_health/{role}", json=payload,
        headers={"Authorization": f"Bearer {EVOLUTION_INVOKE_TOKEN}"}, timeout=300,
    )
    r.raise_for_status()
    return QualityVerdict(**r.json())
```

All prompt templates (`QUALITY_JUDGE_PROMPT`, `PROMOTION_JUDGE_PROMPT`) specced in Plan B Phase 0b **move out of autoresearch-side code** and into `judges/evolution/prompts/`. Autoresearch-side Python files never contain prompt text. `promotion_judge.py` fans out across 3 dedicated decision endpoints; `quality_judge.py` fans out across the 6 roles of the single unified `system_health_agent`.

### Meta-agent / variant subprocess environment scrubbing

When autoresearch spawns subprocesses that run untrusted code, strip all judge-admin-level credentials:

```python
# autoresearch/evaluate_variant.py::_score_env — add scrub
def _score_env() -> dict[str, str]:
    env = os.environ.copy()
    # Scrub admin-level tokens that must never reach untrusted subprocesses.
    # Leave SESSION_INVOKE_TOKEN (variants need to call critique/review);
    # drop SESSION_ADMIN_TOKEN and EVOLUTION_INVOKE_TOKEN.
    for key in ("SESSION_ADMIN_TOKEN", "EVOLUTION_INVOKE_TOKEN",
                "OPENAI_API_KEY", "ANTHROPIC_API_KEY",
                "CLAUDE_API_KEY", "CODEX_API_KEY"):
        env.pop(key, None)
    repo_root = _repo_root()
    cli_path = str(repo_root / "cli")
    # ... existing PYTHONPATH setup ...
    return env
```

Variant subprocesses (via `_run_fixture_session`) get `SESSION_INVOKE_TOKEN` (they need to call session judges) but NOT `EVOLUTION_INVOKE_TOKEN` or any admin token. Meta-agent subprocess (spawned by `evolve.py`'s meta-agent dispatch) gets NEITHER invoke token — it doesn't call judges directly, it only writes variant files that subsequent scoring steps process.

### Orchestrator session-judge tuning loop (reserved slot)

The trusted evolution orchestrator (`evolve.py`, running under the user's full shell) holds `SESSION_ADMIN_TOKEN` in a path not inherited by subprocesses. The tuning loop — a separate feature to build out later — would:

1. Periodically read evolution outcomes (from `events.jsonl` on autoresearch side, which has decisions but no reasoning)
2. Observe correlation between session-judge verdicts and downstream promotion outcomes
3. Propose a session-judge prompt diff
4. POST to `session-judge://admin/tune-prompt/{judge_name}` with the diff + reason
5. Session-judge-service validates the diff, applies to prompt file, logs to audit

This loop is NOT in scope for this plan — it's the architectural slot that makes session judges evolvable. Evolution judges never gain this capability by design.

### Tests

- `tests/judges/test_session_judge_server.py` — FastAPI TestClient; mock `invoke_claude`/`invoke_codex`; verify endpoints return verdicts, reject bad tokens, log to events
- `tests/judges/test_evolution_judge_server.py` — same pattern; assert admin endpoints return 404 (not present on evolution service)
- `tests/judges/test_invoke_cli.py` — mocks `asyncio.create_subprocess_exec`; verify pool-of-3 semaphore + timeout + error propagation
- `tests/autoresearch/test_evaluate_client.py` — verify `cli/freddy/commands/evaluate.py` is HTTP-only (no httpx with api.openai.com/anthropic URLs; grep-based test)
- `tests/autoresearch/test_env_scrub.py` — verify `_score_env()` strips admin tokens + API keys

### Commit

```bash
git add judges/ cli/freddy/commands/evaluate.py autoresearch/evaluate_variant.py \
        autoresearch/judges/ tests/judges/ tests/autoresearch/test_env_scrub.py \
        .github/workflows/deploy-session-judge.yml \
        .github/workflows/deploy-evolution-judge.yml
git commit -m "feat(judges): physical isolation — two judge services, claude/codex CLI auth, no API keys on autoresearch host"
```

---

## Phase 1: Fixture Schema + Version Field

**Purpose:** Introduce per-fixture and per-suite semver `version` fields. Everything downstream (cache keys, refresh tracking, promotion logs) depends on this.

**Files:**
- Create: `cli/freddy/fixture/__init__.py`
- Create: `cli/freddy/fixture/schema.py`
- Create: `tests/freddy/fixture/__init__.py`
- Create: `tests/freddy/fixture/test_schema.py`
- Modify: `autoresearch/evaluate_variant.py` (Fixture dataclass, `_fixture_from_payload`)
- Modify: `autoresearch/eval_suites/search-v1.json`

- [ ] **Step 1: Write failing tests for FixtureSpec**

Create `tests/freddy/fixture/__init__.py` empty, and `tests/freddy/fixture/test_schema.py`:

```python
import pytest
from cli.freddy.fixture.schema import (
    FixtureSpec, FixtureValidationError, parse_fixture_spec,
    SuiteManifest, parse_suite_manifest,
)


def test_fixture_spec_requires_version():
    with pytest.raises(FixtureValidationError, match="version"):
        parse_fixture_spec({
            "fixture_id": "geo-test",
            "client": "test",
            "context": "https://example.com",
        })


def test_fixture_spec_accepts_semver_version():
    spec = parse_fixture_spec({
        "fixture_id": "geo-test",
        "client": "test",
        "context": "https://example.com",
        "version": "1.0",
    })
    assert spec.fixture_id == "geo-test"
    assert spec.version == "1.0"


def test_fixture_spec_rejects_non_semver_version():
    with pytest.raises(FixtureValidationError, match="semver"):
        parse_fixture_spec({
            "fixture_id": "geo-test",
            "client": "test",
            "context": "https://example.com",
            "version": "v1",
        })


def test_suite_manifest_requires_version():
    with pytest.raises(FixtureValidationError, match="version"):
        parse_suite_manifest({
            "suite_id": "test-v1",
            "domains": {"geo": [{
                "fixture_id": "x", "client": "y", "context": "z", "version": "1.0"
            }]},
        })


def test_suite_manifest_parses_with_version():
    manifest = parse_suite_manifest({
        "suite_id": "test-v1",
        "version": "1.0",
        "domains": {"geo": [{
            "fixture_id": "x", "client": "y", "context": "z", "version": "1.0"
        }]},
    })
    assert manifest.suite_id == "test-v1"
    assert manifest.version == "1.0"
    assert len(manifest.fixtures["geo"]) == 1
```

- [ ] **Step 2: Implement schema module**

Create `cli/freddy/fixture/__init__.py` empty, and `cli/freddy/fixture/schema.py`:

```python
"""Fixture schema (structural + type validation); qualitative checks live in dryrun.py."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Mapping


class FixtureValidationError(ValueError):
    """Raised when a fixture payload fails structural validation."""


_SEMVER_RE = re.compile(r"^\d+\.\d+(\.\d+)?$")


@dataclass(frozen=True)
class FixtureSpec:
    fixture_id: str
    client: str
    context: str
    version: str
    max_iter: int = 3
    timeout: int = 300
    anchor: bool = False
    env: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class SuiteManifest:
    suite_id: str
    version: str
    fixtures: Mapping[str, tuple[FixtureSpec, ...]]


def parse_fixture_spec(payload: Mapping[str, Any]) -> FixtureSpec:
    for required in ("fixture_id", "client", "context", "version"):
        value = payload.get(required)
        if not isinstance(value, str) or not value.strip():
            raise FixtureValidationError(
                f"fixture spec missing required string field: {required!r}"
            )
    version = str(payload["version"]).strip()
    if not _SEMVER_RE.match(version):
        raise FixtureValidationError(
            f"fixture version {version!r} must be semver (e.g. '1.0', '1.2.3')"
        )
    env_raw = payload.get("env", {})
    if not isinstance(env_raw, dict):
        raise FixtureValidationError("fixture 'env' must be a dict")
    return FixtureSpec(
        fixture_id=str(payload["fixture_id"]).strip(),
        client=str(payload["client"]).strip(),
        context=str(payload["context"]).strip(),
        version=version,
        max_iter=int(payload.get("max_iter", 3)),
        timeout=int(payload.get("timeout", 300)),
        anchor=bool(payload.get("anchor", False)),
        env={str(k): str(v) for k, v in env_raw.items()},
    )


def parse_suite_manifest(payload: Mapping[str, Any]) -> SuiteManifest:
    suite_id = payload.get("suite_id")
    if not isinstance(suite_id, str) or not suite_id.strip():
        raise FixtureValidationError("suite_id is required and must be a string")
    suite_version = payload.get("version")
    if not isinstance(suite_version, str) or not _SEMVER_RE.match(suite_version):
        raise FixtureValidationError(
            f"suite {suite_id!r} version {suite_version!r} must be semver"
        )
    domains_payload = payload.get("domains")
    if not isinstance(domains_payload, dict):
        raise FixtureValidationError("suite 'domains' must be a dict")
    fixtures: dict[str, tuple[FixtureSpec, ...]] = {}
    for domain, items in domains_payload.items():
        if not isinstance(items, list):
            raise FixtureValidationError(f"domain {domain!r} must be a list")
        fixtures[domain] = tuple(parse_fixture_spec(item) for item in items)
    return SuiteManifest(
        suite_id=suite_id.strip(),
        version=suite_version.strip(),
        fixtures=fixtures,
    )


def assert_pool_matches(pool: str, manifest: SuiteManifest) -> None:
    """Raise ValueError if --pool does not match manifest.suite_id.

    Shared guard used by refresh/refresh_all/dry-run/discriminate — all of
    which must reject cross-pool cache contamination before any cache I/O.
    """
    if pool != manifest.suite_id:
        raise ValueError(
            f"--pool {pool!r} does not match manifest.suite_id "
            f"{manifest.suite_id!r}. Pool and suite_id must agree to prevent "
            f"cross-pool cache contamination."
        )
```

Run: `pytest tests/freddy/fixture/test_schema.py -v` — expect all 5 tests PASS.

- [ ] **Step 3: Backfill version in search-v1.json + add required-field loader**

Do the backfill and the required-field enforcement in a single edit pass so there's no intermediate state where a missing-version fixture silently passes validation.

1. Modify `autoresearch/eval_suites/search-v1.json`:
   - Add `"version": "1.0"` at manifest top level (after `"description"`)
   - Add `"version": "1.0"` to each of the 23 fixture entries
2. Modify `autoresearch/evaluate_variant.py`'s `Fixture` dataclass: add `version: str` as a **required** field (no default). Place after `anchor: bool = False` (required-before-optional rule honored since `anchor` has a default — either add `version: str` before `anchor` or mark `version` with a sentinel and validate at construction; in practice, pick the field order that satisfies dataclass ordering rules).
3. Modify `_fixture_from_payload` to read + validate `version`:

```python
version = payload.get("version")
if not isinstance(version, str) or not version.strip():
    raise ValueError(
        f"fixture {payload.get('fixture_id')!r} missing required 'version' field"
    )
```

Run: `python -c "import json; json.load(open('autoresearch/eval_suites/search-v1.json'))"` (valid JSON).
Run: `pytest tests/autoresearch/ -x -q` — all pass (every fixture now carries `version`).

**Why one step, not two:** the earlier two-step "add permissive default, then remove it" pattern had a silent-failure window: if Step 6 was skipped (subagent interrupted, commit batched wrong), any missing-version fixture slipped past validation while `pytest -x -q` stayed green. Collapsing eliminates that window.

- [ ] **Step 4: Commit**

```bash
git add cli/freddy/fixture/ tests/freddy/fixture/ autoresearch/evaluate_variant.py autoresearch/eval_suites/search-v1.json
git commit -m "feat(fixture): add FixtureSpec schema with required version field (backfills version=1.0 on 23 search-v1 fixtures)"
```

---

## Phase 2: Fixture CLI Command Group Skeleton

**Files:**
- Create: `cli/freddy/commands/fixture.py`
- Modify: main CLI registration file
- Create: `tests/freddy/__init__.py`
- Create: `tests/freddy/conftest.py`
- Create: `tests/freddy/fixture/test_cli_integration.py`

- [ ] **Step 0: Ensure tests/freddy/ is importable + add shared fixture helpers (local imports avoid Phase 4 coupling)**

The `seed_cache` factory below imports `CacheManifest`, `DataSourceRecord`, `cache_path_for`, `write_cache_manifest` from `cli.freddy.fixture.cache` — a module that doesn't exist until Phase 4. **Fix:** do the imports inside the fixture-function body (local imports), so `conftest.py` collection succeeds at Phase 2 time and only fixture-use at Phase 4+ time requires the module.

Create `tests/freddy/__init__.py` (empty) and `tests/freddy/conftest.py` with the shared sys.path shim so test modules can import `cli.freddy.*` and `autoresearch.*`:

```python
"""Shared pytest config for tests/freddy/*.

Inserts the repo root into sys.path so `from cli.freddy.fixture.schema
import ...` resolves to the in-repo module rather than an installed
package, and adds `cli/` so `from freddy import main` also works if used.
"""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
for p in (_REPO_ROOT, _REPO_ROOT / "cli"):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)
```

Also create `tests/freddy/fixture/__init__.py` (empty) and `tests/freddy/fixture/conftest.py` exporting factory fixtures reused across test modules in this phase and later phases:

```python
"""Shared fixtures for freddy fixture test modules.

Note: imports from `cli.freddy.fixture.cache` are deferred to fixture
function bodies (not at module level). This lets conftest collection
succeed at Phase 2 time; fixture invocation triggers import at Phase 4+
when the module actually exists.
"""
from __future__ import annotations
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest


@pytest.fixture
def manifest_file(tmp_path):
    """Factory: write a minimal suite manifest and return the path (as str)."""
    def _make(suite_id="search-v1", version="1.0", domain="geo", fixtures=None):
        fixtures = fixtures or [{
            "fixture_id": f"{domain}-a", "client": "acme",
            "context": "https://acme.com", "version": "1.0",
        }]
        payload = {"suite_id": suite_id, "version": version,
                   "domains": {domain: fixtures}}
        path = tmp_path / "m.json"
        path.write_text(json.dumps(payload))
        return str(path)
    return _make


@pytest.fixture
def fetch_payload():
    """Factory: returns a _run_source_fetch return list (one dict per shape variant)."""
    def _make(shape_variants=None, **overrides):
        shape_variants = shape_variants if shape_variants is not None else [None]
        records = []
        for shape in shape_variants:
            base = {
                "source": "xpoz", "data_type": "mentions", "arg": "https://acme.com",
                "shape_flags": shape,
                "retention_days": 30,
                "cached_artifact": "xpoz_mentions__deadbeefcafe.json",
                "record_count": 100, "cost_usd": 0.10,
            }
            base.update(overrides)
            records.append(base)
        return records
    return _make


@pytest.fixture
def seed_cache(tmp_path):
    """Factory: seed a cache dir with a CacheManifest. Returns the cache root."""
    from cli.freddy.fixture.cache import (
        CacheManifest, DataSourceRecord, cache_path_for, write_cache_manifest,
    )
    def _make(pool, fixture_id, version="1.0", source="xpoz",
              data_type="mentions", arg="https://acme.com", age_days=0.0):
        cache_root = tmp_path / "cache"
        cache_dir = cache_path_for(cache_root, pool, fixture_id, version)
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / f"{source}_{data_type}__deadbeefcafe.json").write_text("{}")
        fetched_at = datetime.now(timezone.utc) - timedelta(days=age_days)
        write_cache_manifest(cache_dir, CacheManifest(
            fixture_id=fixture_id, fixture_version=version, pool=pool,
            fetched_at=fetched_at, fetched_by="seed",
            data_sources=[DataSourceRecord(
                source=source, data_type=data_type, arg=arg,
                retention_days=30,
                cached_artifact=f"{source}_{data_type}__deadbeefcafe.json",
                record_count=100, cost_usd=0.10,
            )],
        ))
        return cache_root
    return _make
```

Verify collection: `pytest tests/freddy/fixture/test_schema.py -v --collect-only` — expect tests collect without `ModuleNotFoundError`.

- [ ] **Step 1: Inspect existing command registration**

Run: `grep -n "add_typer\|app.command" cli/freddy/main.py`
Record the pattern used by existing groups (`monitor`, `competitive`, etc.) so `fixture` follows it. Expected pattern: each command-group module defines `app = typer.Typer(...)` at top-level and `main.py` registers it via `app.add_typer(<module>.app, name="<group-name>")`.

- [ ] **Step 2: Write failing integration test**

Create `tests/freddy/fixture/test_cli_integration.py`:

```python
import subprocess


def test_fixture_command_group_registered():
    result = subprocess.run(
        ["freddy", "fixture", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "fixture" in result.stdout.lower()
```

- [ ] **Step 3: Create fixture command group**

Create `cli/freddy/commands/fixture.py`:

```python
"""freddy fixture — fixture authoring and calibration CLI.

Subcommands added by subsequent phases:
  - fixture validate / list / envs  (Phase 3)
  - fixture staleness               (Phase 5)
  - fixture refresh                 (Phase 6)
  - fixture dry-run                 (Phase 7)
  - fixture discriminate            (Phase 10)
"""
from __future__ import annotations

import typer


app = typer.Typer(
    name="fixture",
    help="Author, validate, calibrate, and refresh fixtures for search and holdout suites.",
    no_args_is_help=True,
    invoke_without_command=True,  # Prevents Typer from collapsing a single-subcommand app;
                                   # lets us land Phase 2 with 0 real subcommands and add them in Phase 3.
)
```

- [ ] **Step 4: Register in main CLI**

Modify `cli/freddy/main.py` to add `fixture` alongside the other `app.add_typer(...)` calls. Add to the imports at the top (next to `monitor, query_monitor, save, scrape, ...`):

```python
from .commands import (
    audit, auth, auto_draft, client, competitive, detect, digest, evaluate, fixture,
    iteration, monitor, query_monitor, save, scrape, search_ads, search_content,
    search_mentions, seo, session, setup, sitemap, transcript, trends, visibility,
)
```

Then, alongside the existing `app.add_typer(...)` block (after `app.add_typer(seo.app, name="seo")`), add:

```python
app.add_typer(fixture.app, name="fixture")
```

- [ ] **Step 5: Verify pass**

Run: `pytest tests/freddy/fixture/test_cli_integration.py -v` — expect PASS.
Run: `freddy fixture --help` — expect the help text configured on the Typer app.

- [ ] **Step 6: Commit**

```bash
git add cli/freddy/commands/fixture.py cli/freddy/main.py tests/freddy/fixture/test_cli_integration.py
git commit -m "feat(fixture): scaffold freddy fixture command group"
```

---

## Phase 3: `validate` + `inspect` (Mechanical Layer)

**Purpose:** Cheap, fast validation and introspection. No LLM calls. Used during authoring to catch schema errors before burning judge tokens.

**CLI consolidation:** `list` and `envs` are flags on a single `freddy fixture inspect <manifest>` command (`--domain X` filters; `--envs` shows env-var references, optionally `--missing`). Merging eliminates two command registrations + two help-string entries. The test code below uses `["list", ...]` / `["envs", ...]` for brevity — replace with `["inspect", ..., "--envs"]` at implementation time.

**Files:**
- Modify: `cli/freddy/commands/fixture.py`
- Create: `tests/freddy/fixture/test_validate.py`
- Create: `tests/freddy/fixture/test_list_envs.py`

- [ ] **Step 1: Write failing test for validate**

Create `tests/freddy/fixture/test_validate.py`:

```python
import json
from typer.testing import CliRunner
from cli.freddy.commands.fixture import app as fixture_app


def _write(tmp_path, payload):
    p = tmp_path / "manifest.json"
    p.write_text(json.dumps(payload))
    return str(p)


def test_validate_accepts_well_formed_manifest(manifest_file):
    runner = CliRunner()
    result = runner.invoke(fixture_app, ["validate", manifest_file()])
    assert result.exit_code == 0, result.output
    assert "1 fixture" in result.output


def test_validate_rejects_missing_suite_version(tmp_path):
    path = _write(tmp_path, {
        "suite_id": "test-v1",
        "domains": {"geo": [{"fixture_id": "x", "client": "y",
                             "context": "z", "version": "1.0"}]},
    })
    runner = CliRunner()
    result = runner.invoke(fixture_app, ["validate", path])
    assert result.exit_code != 0
    # Typer's default error stream goes to stderr; CliRunner mixes them into .output.
    assert "version" in result.output.lower()


def test_validate_rejects_duplicate_fixture_ids(manifest_file):
    path = manifest_file(fixtures=[
        {"fixture_id": "dup", "client": "a", "context": "b", "version": "1.0"},
        {"fixture_id": "dup", "client": "c", "context": "d", "version": "1.0"},
    ])
    runner = CliRunner()
    result = runner.invoke(fixture_app, ["validate", path])
    assert result.exit_code != 0
    assert "duplicate" in result.output.lower()
```

- [ ] **Step 2: Implement validate**

Append to `cli/freddy/commands/fixture.py`:

```python
import json
from pathlib import Path

from cli.freddy.fixture.schema import (
    FixtureValidationError,
    parse_suite_manifest,
)


def _fail(message: str) -> None:
    """Emit an error message to stderr and exit with code 1."""
    typer.echo(f"error: {message}", err=True)
    raise typer.Exit(1)


def _load_manifest_payload(manifest_path: str) -> dict:
    """Read + JSON-parse a manifest, exiting cleanly on malformed JSON."""
    try:
        return json.loads(Path(manifest_path).read_text())
    except json.JSONDecodeError as exc:
        _fail(f"manifest at {manifest_path!r} is not valid JSON: {exc}")


@app.command("validate")
def validate_cmd(
    manifest_path: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
) -> None:
    """Validate a fixture manifest's schema and structural invariants."""
    payload = _load_manifest_payload(str(manifest_path))
    try:
        manifest = parse_suite_manifest(payload)
    except FixtureValidationError as exc:
        _fail(str(exc))

    seen: set[str] = set()
    for domain, fixtures in manifest.fixtures.items():
        for fixture in fixtures:
            if fixture.fixture_id in seen:
                _fail(
                    f"duplicate fixture_id {fixture.fixture_id!r} in domain {domain!r}"
                )
            seen.add(fixture.fixture_id)

    total = sum(len(f) for f in manifest.fixtures.values())
    typer.echo(
        f"✓ {manifest.suite_id}@{manifest.version}: {total} fixture(s) across "
        f"{len(manifest.fixtures)} domain(s)"
    )
```

Run: `pytest tests/freddy/fixture/test_validate.py -v` — expect all 3 PASS.

- [ ] **Step 3: Add list + envs tests**

Create `tests/freddy/fixture/test_list_envs.py`:

```python
import json
from typer.testing import CliRunner
from cli.freddy.commands.fixture import app as fixture_app


def _manifest(tmp_path):
    payload = {
        "suite_id": "t-v1", "version": "1.0",
        "domains": {
            "geo": [{"fixture_id": "geo-a", "client": "x",
                     "context": "https://a.com", "version": "1.0", "anchor": True}],
            "monitoring": [{"fixture_id": "mon-a", "client": "b",
                            "context": "${SHOP_CONTEXT}", "version": "1.0",
                            "env": {"AUTORESEARCH_WEEK_RELATIVE": "most_recent_complete"}}],
        },
    }
    p = tmp_path / "m.json"
    p.write_text(json.dumps(payload))
    return str(p)


def test_list_prints_all_fixtures(tmp_path):
    runner = CliRunner()
    result = runner.invoke(fixture_app, ["list", _manifest(tmp_path)])
    assert result.exit_code == 0, result.output
    assert "geo-a" in result.output
    assert "mon-a" in result.output


def test_list_filters_by_domain(tmp_path):
    runner = CliRunner()
    result = runner.invoke(fixture_app, ["list", _manifest(tmp_path), "--domain", "geo"])
    assert result.exit_code == 0
    assert "geo-a" in result.output
    assert "mon-a" not in result.output


def test_envs_lists_all_referenced_vars(tmp_path):
    runner = CliRunner()
    result = runner.invoke(fixture_app, ["envs", _manifest(tmp_path)])
    assert result.exit_code == 0
    assert "SHOP_CONTEXT" in result.output
```

- [ ] **Step 4: Verify failure, implement, verify pass**

Append to `cli/freddy/commands/fixture.py`:

```python
import re

_ENV_REF_RE = re.compile(r"\$\{([A-Z0-9_]+)\}")


@app.command("list")
def list_cmd(
    manifest_path: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    domain: str | None = typer.Option(None, "--domain", help="Filter to a specific domain."),
) -> None:
    """List fixtures in a manifest, optionally filtered by domain."""
    payload = _load_manifest_payload(str(manifest_path))
    manifest = parse_suite_manifest(payload)
    typer.echo(f"{'Fixture':<40} {'Domain':<14} {'Ver':<6} {'Anchor':<7}")
    for dom, fixtures in manifest.fixtures.items():
        if domain and dom != domain:
            continue
        for f in fixtures:
            typer.echo(f"{f.fixture_id:<40} {dom:<14} {f.version:<6} "
                       f"{'yes' if f.anchor else 'no':<7}")


@app.command("envs")
def envs_cmd(
    manifest_path: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    missing: bool = typer.Option(False, "--missing", help="Only show env vars NOT currently set."),
) -> None:
    """List all env var references across a manifest's fixtures."""
    import os
    payload = _load_manifest_payload(str(manifest_path))
    manifest = parse_suite_manifest(payload)
    refs: set[str] = set()
    for fixtures in manifest.fixtures.values():
        for f in fixtures:
            for value in (f.context, *f.env.values()):
                refs.update(_ENV_REF_RE.findall(value))
    for var in sorted(refs):
        set_status = var in os.environ
        if missing and set_status:
            continue
        marker = "✓" if set_status else "✗"
        typer.echo(f"{marker} {var}")
```

Run: `pytest tests/freddy/fixture/test_list_envs.py -v` — expect all PASS.

- [ ] **Step 5: Commit**

```bash
git add cli/freddy/commands/fixture.py tests/freddy/fixture/test_validate.py tests/freddy/fixture/test_list_envs.py
git commit -m "feat(fixture): add validate, list, envs subcommands (mechanical, no LLM calls)"
```

---

## Phase 4: Cache Layer Data Model

**Purpose:** Define `CacheManifest`, filesystem conventions, and roundtrip I/O.

**Files:**
- Create: `cli/freddy/fixture/cache.py`
- Create: `tests/freddy/fixture/test_cache.py`

- [ ] **Step 1: Write failing roundtrip test**

Create `tests/freddy/fixture/test_cache.py`:

```python
from datetime import datetime, timezone

from cli.freddy.fixture.cache import (
    CacheManifest, DataSourceRecord,
    cache_path_for, load_cache_manifest, write_cache_manifest,
)


def test_cache_path_conventions(tmp_path):
    path = cache_path_for(tmp_path / "cache", "holdout-v1", "monitoring-shopify", "1.0")
    assert path == tmp_path / "cache" / "holdout-v1" / "monitoring-shopify" / "v1.0"


def test_cache_manifest_roundtrip(tmp_path):
    path = cache_path_for(tmp_path / "cache", "search-v1", "monitoring-shopify", "1.0")
    path.mkdir(parents=True)
    manifest = CacheManifest(
        fixture_id="monitoring-shopify",
        fixture_version="1.0",
        pool="search-v1",
        fetched_at=datetime(2026, 4, 1, 12, 0, tzinfo=timezone.utc),
        fetched_by="tester",
        data_sources=[
            DataSourceRecord(
                source="xpoz", data_type="mentions", arg="mon-uuid-123",
                retention_days=30,
                cached_artifact="xpoz_mentions__a1b2c3d4e5f6.json",
                record_count=1200, cost_usd=0.50,
            ),
        ],
        total_fetch_cost_usd=0.50,
        fetch_duration_seconds=45,
    )
    write_cache_manifest(path, manifest)
    loaded = load_cache_manifest(path)
    assert loaded == manifest
```

- [ ] **Step 2: Implement cache module**

Create `cli/freddy/fixture/cache.py`:

```python
"""Fixture data cache — layout, manifest format, I/O primitives, staleness.

Authoritative conventions (referenced by SCHEMA.md and the plan):

  Cache root:  ~/.local/share/gofreddy/fixture-cache/<pool>/<fixture_id>/v<version>/
  Contents:    manifest.json + one artifact per (source, data_type, arg, shape_flags) tuple.
  Filename:    <source>_<data_type>__<arg_hash>.json
  arg_hash:    sha1("|".join([arg, *sorted(shape_flags.items())])).hexdigest()[:12]

  Shape flags are output-shape-affecting CLI flags that alter the payload a
  session receives (e.g. `freddy monitor mentions --format summary` returns an
  aggregated dict where `--format full` returns a list). Including them in the
  hash prevents a summary-shaped session from reading a full-shaped cache
  entry (silently wrong data — the collision bug flagged by Plan A review).
  Hashing distinct (source, data_type, arg) triples lets one (source,
  data_type) pair hold multiple entries under one dir (e.g., three different
  URLs scraped by `freddy scrape` coexist).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_CACHE_ROOT = Path("~/.local/share/gofreddy/fixture-cache").expanduser()
MANIFEST_FILENAME = "manifest.json"


def arg_hash(arg: str, shape_flags: dict[str, str] | None = None) -> str:
    """Stable short hash of a call's (arg + output-shape flags), used in cache filenames.

    shape_flags is a mapping of flag-name -> flag-value for any CLI flags that
    change the payload shape. Keys are sorted for determinism across callers.
    When shape_flags is None or empty, the hash is identical to the previous
    arg-only scheme (backward-compatible for geo-scrape, visibility, etc.
    which have no shape flags).
    """
    key = arg
    if shape_flags:
        key += "|" + "|".join(f"{k}={shape_flags[k]}" for k in sorted(shape_flags))
    return hashlib.sha1(key.encode()).hexdigest()[:12]


# SHAPE_FLAGS_REGISTRY (B2): loaded from shape_flags.json at module import.
# Maps `freddy <command>` → list of CLI flag names that alter output shape
# (and therefore must participate in the cache key). Single source of truth
# for shape-aware caching; new commands / new flags register in the JSON only.
_SHAPE_FLAGS_REGISTRY: dict[str, list[str]] | None = None


def _load_shape_flags_registry() -> dict[str, list[str]]:
    global _SHAPE_FLAGS_REGISTRY
    if _SHAPE_FLAGS_REGISTRY is None:
        config_path = Path(__file__).resolve().parent / "shape_flags.json"
        _SHAPE_FLAGS_REGISTRY = json.loads(config_path.read_text())
    return _SHAPE_FLAGS_REGISTRY


def shape_flags_for_command(command_str: str) -> list[str]:
    """Return ordered list of shape-affecting flag names for a given command.

    command_str is the full command like 'freddy monitor mentions'. Returns
    empty list if the command is not registered (treated as no shape flags).
    """
    return list(_load_shape_flags_registry().get(command_str, []))


def artifact_filename(source: str, data_type: str, arg: str, shape_flags: dict[str, str] | None = None) -> str:
    return f"{source}_{data_type}__{arg_hash(arg, shape_flags)}.json"


@dataclass(frozen=True)
class DataSourceRecord:
    source: str
    data_type: str
    arg: str  # raw positional argument that produced this cache entry
    retention_days: int
    cached_artifact: str
    record_count: int = 0
    cost_usd: float = 0.0


@dataclass(frozen=True)
class CacheManifest:
    fixture_id: str
    fixture_version: str
    pool: str
    fetched_at: datetime
    fetched_by: str
    # total_fetch_cost_usd and fetch_duration_seconds are NOT stored —
    # derivable from data_sources / refresh report. No cache_schema_version —
    # the file itself IS v1; add it if/when we actually introduce v2.
    # List, not dict: one (source, data_type) may have multiple entries
    # keyed by distinct arg values. Store as a list and look up linearly.
    data_sources: list[DataSourceRecord]


def cache_path_for(root: Path, pool: str, fixture_id: str, fixture_version: str) -> Path:
    return root / pool / fixture_id / f"v{fixture_version}"


def _dt_to_iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def _iso_to_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def write_cache_manifest(cache_dir: Path, manifest: CacheManifest) -> None:
    payload: dict[str, Any] = asdict(manifest)
    payload["fetched_at"] = _dt_to_iso(manifest.fetched_at)
    payload["data_sources"] = [asdict(src) for src in manifest.data_sources]
    (cache_dir / MANIFEST_FILENAME).write_text(
        json.dumps(payload, indent=2, sort_keys=True)
    )


def load_cache_manifest(cache_dir: Path) -> CacheManifest:
    payload = json.loads((cache_dir / MANIFEST_FILENAME).read_text())
    sources = [DataSourceRecord(**src) for src in payload.pop("data_sources")]
    payload["fetched_at"] = _iso_to_dt(payload["fetched_at"])
    return CacheManifest(**payload, data_sources=sources)
```

Run: `pytest tests/freddy/fixture/test_cache.py -v` — expect PASS.

- [ ] **Step 3: Commit**

```bash
git add cli/freddy/fixture/cache.py tests/freddy/fixture/test_cache.py
git commit -m "feat(fixture): add cache layer data model (CacheManifest + IO)"
```

---

## Phase 5: Staleness Detection + `freddy fixture cache`

**Purpose:** Compute per-fixture freshness tier and expose it via CLI. Enables the manual-refresh-on-flag workflow.

**CLI consolidation:** The staleness view lives under `freddy fixture cache [--pool X] [--tier fresh|aging|stale]`. The former `staleness` command is now `fixture cache` — same output, more intuitive command name for "show me the cache state". Tests below still invoke `["staleness", ...]` — rename at implementation.

**Files:**
- Modify: `cli/freddy/fixture/cache.py` (add `staleness_status`)
- Modify: `cli/freddy/commands/fixture.py` (add command)
- Create: `tests/freddy/fixture/test_staleness.py`

- [ ] **Step 1: Write failing staleness tests**

Create `tests/freddy/fixture/test_staleness.py`:

```python
from datetime import datetime, timedelta, timezone

import pytest

from cli.freddy.fixture.cache import (
    CacheManifest, DataSourceRecord, staleness_status,
)


def _manifest(days_ago: int, retention_days: int = 30) -> CacheManifest:
    return CacheManifest(
        fixture_id="x", fixture_version="1.0", pool="search-v1",
        fetched_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
        fetched_by="t",
        data_sources=[DataSourceRecord(
            source="xpoz", data_type="mentions", arg="abc",
            retention_days=retention_days,
            cached_artifact="xpoz_mentions__deadbeef0001.json",
        )],
    )


@pytest.mark.parametrize("age_days,expected", [
    (0, "fresh"), (10, "fresh"), (14, "fresh"),
    (15, "aging"), (25, "aging"),
    (30, "stale"), (45, "stale"),
])
def test_staleness_tiers_for_30d_retention(age_days, expected):
    assert staleness_status(_manifest(age_days, 30)) == expected


def test_staleness_uses_shortest_retention():
    manifest = CacheManifest(
        fixture_id="x", fixture_version="1.0", pool="search-v1",
        fetched_at=datetime.now(timezone.utc) - timedelta(days=20),
        fetched_by="t",
        data_sources=[
            DataSourceRecord(
                "freddy-scrape", "page", "https://x.com", 180,
                "freddy-scrape_page__aaaa00000001.json",
            ),
            DataSourceRecord(
                "xpoz", "mentions", "mon-uuid", 30,
                "xpoz_mentions__bbbb00000001.json",
            ),
        ],
    )
    assert staleness_status(manifest) == "aging"
```

- [ ] **Step 2: Implement staleness_status**

Append to `cli/freddy/fixture/cache.py`:

```python
from typing import Literal

Staleness = Literal["fresh", "aging", "stale"]


def staleness_status(manifest: CacheManifest, *, now: datetime | None = None) -> Staleness:
    """Return the cache's staleness tier.

    Based on the shortest retention window across data sources:
    - fresh: age < 50% of shortest retention
    - aging: 50% <= age < 100% (refresh soon before records age out)
    - stale: age >= 100%
    """
    current = now or datetime.now(timezone.utc)
    age = current - manifest.fetched_at
    if not manifest.data_sources:
        return "fresh"
    shortest = min(src.retention_days for src in manifest.data_sources)
    ratio = age.total_seconds() / (shortest * 86400)
    if ratio < 0.5:
        return "fresh"
    if ratio < 1.0:
        return "aging"
    return "stale"
```

Run: `pytest tests/freddy/fixture/test_staleness.py -v` — expect all PASS.

- [ ] **Step 3: Add CLI test + implementation**

Append to `tests/freddy/fixture/test_staleness.py`:

```python
from typer.testing import CliRunner
from cli.freddy.commands.fixture import app as fixture_app


def test_staleness_cli_lists_fixtures(seed_cache):
    seed_cache("search-v1", "mon-a", age_days=5)
    root = seed_cache("search-v1", "mon-b", age_days=35)
    runner = CliRunner()
    result = runner.invoke(fixture_app, ["staleness", "--cache-root", str(root)])
    assert result.exit_code == 0
    assert "mon-a" in result.output and "fresh" in result.output
    assert "mon-b" in result.output and "stale" in result.output
```

Append to `cli/freddy/commands/fixture.py`:

```python
from cli.freddy.fixture.cache import (
    DEFAULT_CACHE_ROOT, load_cache_manifest, staleness_status,
)


@app.command("staleness")
def staleness_cmd(
    cache_root: Path = typer.Option(Path(str(DEFAULT_CACHE_ROOT)), "--cache-root", file_okay=False),
    pool: str | None = typer.Option(None, "--pool", help="Filter to a specific pool."),
    stale_only: bool = typer.Option(False, "--stale-only"),
    aging_or_worse: bool = typer.Option(False, "--aging-or-worse"),
) -> None:
    """List cached fixtures with staleness tier."""
    root = Path(cache_root)
    if not root.exists():
        typer.echo("cache root does not exist; nothing to report")
        return
    rows = []
    for pool_dir in sorted(root.iterdir()):
        if pool and pool_dir.name != pool:
            continue
        if not pool_dir.is_dir():
            continue
        for fixture_dir in sorted(pool_dir.iterdir()):
            for version_dir in sorted(fixture_dir.iterdir()):
                try:
                    manifest = load_cache_manifest(version_dir)
                except Exception:
                    continue
                status = staleness_status(manifest)
                if stale_only and status != "stale":
                    continue
                if aging_or_worse and status == "fresh":
                    continue
                rows.append((pool_dir.name, manifest.fixture_id,
                             manifest.fixture_version, status))
    typer.echo(f"{'Pool':<16} {'Fixture':<40} {'Ver':<6} {'Status':<8}")
    for row in rows:
        typer.echo(f"{row[0]:<16} {row[1]:<40} {row[2]:<6} {row[3]:<8}")
```

Run: `pytest tests/freddy/fixture/test_staleness.py -v` — expect all PASS.

- [ ] **Step 4: Commit**

```bash
git add cli/freddy/fixture/cache.py cli/freddy/commands/fixture.py tests/freddy/fixture/test_staleness.py
git commit -m "feat(fixture): add staleness detection + 'freddy fixture staleness' (three-tier fresh/aging/stale by shortest retention)"
```

---

## Phase 6: `freddy fixture refresh`

**Purpose:** Operator-triggered manual refresh. Archives prior cache. Supports `--dry-run` for cost estimation and `--all-stale` / `--all-aging` batch modes.

**Files:**
- Create: `cli/freddy/fixture/refresh.py`
- Create: `cli/freddy/fixture/sources.json` (B1 — source descriptors per domain, single source of truth)
- Create: `cli/freddy/fixture/shape_flags.json` (B2 — SHAPE_FLAGS_REGISTRY: command → set of output-shape-affecting flags)
- Create: `cli/freddy/fixture/pool_policies.json` (B3 — POOL_POLICIES: pool → miss-semantics, default-deny)
- Modify: `cli/freddy/commands/fixture.py`
- Create: `tests/freddy/fixture/test_refresh.py`

**sources.json** structure (B1 + B4 consolidated):

```json
{
  "retention_defaults": {
    "monitoring": {"_default": 30},
    "geo": {"page": 180, "visibility": 90},
    "competitive": {"_default": 90},
    "storyboard": {"_default": 365}
  },
  "domains": {
    "monitoring": [
      {"source": "xpoz", "data_type": "mentions", "retention_days": "_default",
       "command": ["freddy", "monitor", "mentions"], "args_from": ["context"]},
      {"source": "xpoz", "data_type": "sentiment", "retention_days": "_default",
       "command": ["freddy", "monitor", "sentiment"], "args_from": ["context"]},
      {"source": "xpoz", "data_type": "sov", "retention_days": "_default",
       "command": ["freddy", "monitor", "sov"], "args_from": ["context"]}
    ],
    "geo": [
      {"source": "freddy-scrape", "data_type": "page", "retention_days": "page",
       "command": ["freddy", "scrape"], "args_from": ["context"]},
      {"source": "freddy-visibility", "data_type": "visibility", "retention_days": "visibility",
       "command": ["freddy", "visibility"], "args_from": ["context"]}
    ],
    "competitive": [
      {"source": "foreplay", "data_type": "ads", "retention_days": "_default",
       "command": ["freddy", "search-ads"], "args_from": ["context"]}
    ],
    "storyboard": [
      {"source": "ic", "data_type": "creator_videos", "retention_days": "_default",
       "command": ["freddy", "search-content"], "args_from": ["context"]}
    ]
  }
}
```

**Shape flags registry** — now empty. Monitor's `--format summary` pre-fetching was dropped (YAGNI: variants may never request non-default shape during a session, and pre-fetching doubles monitoring refresh cost). If a holdout session requests a non-default shape at runtime, cache miss → live-fetch (search pool) or hard-fail (holdout pool) with clear diagnostic. Add shape-variant support when a session actually requires it.

**pool_policies.json** (B3):
```json
{
  "search-v1": {"on_miss": "live_fetch"},
  "holdout-v1": {"on_miss": "hard_fail"},
  "_default": {"on_miss": "hard_fail"}
}
```
`try_read_cache` consults this registry instead of `pool.startswith("holdout")`. Unknown pool → hits `_default` → hard-fail. A future pool rename (`adversarial-v1`, `blind-v1`) fails closed by default; operator explicitly allowlists `live_fetch` if that's intended.

- [ ] **Step 1: Write failing test stubbing subprocess calls**

Create `tests/freddy/fixture/test_refresh.py`. Note: the monitoring-domain fixtures here override the default `manifest_file` fixture shape via keyword args:

```python
from unittest.mock import patch

from typer.testing import CliRunner

from cli.freddy.fixture.cache import cache_path_for, load_cache_manifest
from cli.freddy.commands.fixture import app as fixture_app


_MON_FIXTURES = [{
    "fixture_id": "mon-a", "client": "acme",
    "context": "https://acme.com", "version": "1.0",
    "env": {"AUTORESEARCH_WEEK_RELATIVE": "most_recent_complete"},
}]


def test_refresh_dry_run_prints_plan_no_write(manifest_file, tmp_path):
    runner = CliRunner()
    result = runner.invoke(fixture_app, [
        "refresh", "mon-a",
        "--manifest", manifest_file(domain="monitoring", fixtures=_MON_FIXTURES),
        "--pool", "search-v1",
        "--cache-root", str(tmp_path / "cache"),
        "--dry-run",
    ])
    assert result.exit_code == 0, result.output
    assert "would fetch" in result.output.lower() or "plan" in result.output.lower()
    assert not (tmp_path / "cache").exists()


def test_refresh_rejects_pool_manifest_mismatch(manifest_file, tmp_path):
    """--pool must equal manifest.suite_id (cross-pool contamination guard)."""
    runner = CliRunner()
    result = runner.invoke(fixture_app, [
        "refresh", "mon-a",
        "--manifest", manifest_file(domain="monitoring", fixtures=_MON_FIXTURES),
        "--pool", "holdout-v1",  # mismatched against suite_id "search-v1"
        "--cache-root", str(tmp_path / "cache"),
        "--dry-run",
    ])
    assert result.exit_code == 1
    assert "does not match" in result.output.lower()
    assert "suite_id" in result.output.lower()


@patch("cli.freddy.fixture.refresh._run_source_fetch")
def test_refresh_writes_cache_manifest(mock_fetch, manifest_file, fetch_payload, tmp_path):
    mock_fetch.return_value = fetch_payload(record_count=1200, cost_usd=0.5)
    runner = CliRunner()
    result = runner.invoke(fixture_app, [
        "refresh", "mon-a",
        "--manifest", manifest_file(domain="monitoring", fixtures=_MON_FIXTURES),
        "--pool", "search-v1",
        "--cache-root", str(tmp_path / "cache"),
    ])
    assert result.exit_code == 0, result.output
    cache_dir = cache_path_for(tmp_path / "cache", "search-v1", "mon-a", "1.0")
    assert cache_dir.exists()
    manifest = load_cache_manifest(cache_dir)
    assert manifest.fixture_id == "mon-a"
    assert len(manifest.data_sources) >= 1


@patch("cli.freddy.fixture.refresh._run_source_fetch")
def test_refresh_archives_prior_cache(mock_fetch, manifest_file, fetch_payload, tmp_path):
    mock_fetch.return_value = fetch_payload(cost_usd=0.1)
    mpath = manifest_file(domain="monitoring", fixtures=_MON_FIXTURES)
    runner = CliRunner()
    runner.invoke(fixture_app, [
        "refresh", "mon-a", "--manifest", mpath,
        "--pool", "search-v1", "--cache-root", str(tmp_path / "cache"),
    ])
    result = runner.invoke(fixture_app, [
        "refresh", "mon-a", "--manifest", mpath,
        "--pool", "search-v1", "--cache-root", str(tmp_path / "cache"),
        "--force",
    ])
    assert result.exit_code == 0
    pool_dir = tmp_path / "cache" / "search-v1" / "mon-a"
    archived = [d for d in pool_dir.iterdir() if "archive-" in d.name]
    assert len(archived) == 1
```

- [ ] **Step 2: Implement refresh module**

Create `cli/freddy/fixture/refresh.py`:

```python
"""Manual fixture cache refresh orchestration.

Operator-triggered only. Never auto-refetches — that would defeat the
staleness-flag-and-manual-refresh contract.
"""
from __future__ import annotations

import getpass
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cli.freddy.fixture.cache import (
    CacheManifest, DataSourceRecord,
    cache_path_for, load_cache_manifest, write_cache_manifest, staleness_status,
)
from cli.freddy.fixture.schema import FixtureSpec, parse_suite_manifest


@dataclass
class RefreshResult:
    fixture_id: str
    report_lines: list[str]
    cache_dir: Path | None
    cost_usd: float


# `_retention_for` inlined at call sites — it's a one-liner:
#   fixture.env.get("RETENTION_DAYS", default).isdigit() ? int(...) : default
# `_resolve_arg` similarly inlined: `fixture.context if name=="context" else fixture.env.get(name, "")`
# `_find_fixture` removed — refresh_fixture parses the manifest once at entry
# and passes the parsed object through. `_find_one_fixture` stays (single authoritative).


# Loaded from cli/freddy/fixture/sources.json at module import. Single source
# of truth for (source, data_type, command, retention_days, shape_variants)
# per domain. Adding a domain = edit the JSON file, no code change.
_SOURCES_CONFIG: dict[str, Any] | None = None


def _load_sources_config() -> dict[str, Any]:
    global _SOURCES_CONFIG
    if _SOURCES_CONFIG is None:
        config_path = Path(__file__).resolve().parent / "sources.json"
        _SOURCES_CONFIG = json.loads(config_path.read_text())
    return _SOURCES_CONFIG


def _determine_sources(fixture: FixtureSpec, domain: str) -> list[dict[str, Any]]:
    """Return ordered source-fetch descriptors for this fixture (by domain).

    Descriptors come from sources.json. Session-time *read* policy is
    pool-dependent (see Phase 8 + POOL_POLICIES): search pool reads only
    geo-scrape + monitoring caches; holdout pool reads all 4 domains
    cache-first with hard-fail on miss (credential isolation — see Plan B
    Phase 2 Step 9f).
    """
    config = _load_sources_config()
    domain_descriptors = config.get("domains", {}).get(domain)
    if domain_descriptors is None:
        raise ValueError(
            f"no source descriptors registered for domain {domain!r} "
            f"in cli/freddy/fixture/sources.json. Add the domain block before refreshing."
        )

    out: list[dict[str, Any]] = []
    for desc in domain_descriptors:
        resolved = dict(desc)
        # retention_days may be a sentinel like "_default" referring to
        # RETENTION_DEFAULTS[domain][data_type]; resolve via _retention_for.
        if isinstance(resolved.get("retention_days"), str):
            default_key = resolved["retention_days"]
            default_val = int(config["retention_defaults"][domain][default_key])
            resolved["retention_days"] = _retention_for(fixture, default_val)
        elif isinstance(resolved.get("retention_days"), int):
            resolved["retention_days"] = _retention_for(fixture, resolved["retention_days"])
        out.append(resolved)
    return out


def _resolve_arg(fixture: FixtureSpec, arg_name: str) -> str:
    """Resolve one `args_from` entry to its literal value on this fixture."""
    if arg_name == "context":
        return fixture.context
    return fixture.env.get(arg_name, "")


def _run_source_fetch(
    source_desc: dict[str, Any],
    fixture_id: str,
    fixture: FixtureSpec,
    cache_dir: Path,
    arg: str,
) -> list[dict[str, Any]]:
    """Execute the freddy CLI call for one (source, data_type, arg) triple.

    If `source_desc['shape_variants']` is present (e.g. monitor commands with
    `--format full|summary`), the command is invoked once per shape variant
    and each gets its own cache artifact (filename includes arg_hash of
    arg+shape_flags). Without shape_variants, a single artifact is written.

    Returns a list of dicts compatible with DataSourceRecord() — one per
    shape variant.
    """
    import os
    import subprocess

    from cli.freddy.fixture.cache import artifact_filename

    # Scrub inherited FREDDY_FIXTURE_* to prevent recursive cache reads.
    parent_env = {k: v for k, v in os.environ.items() if not k.startswith("FREDDY_FIXTURE_")}
    env = {
        **parent_env,
        "FREDDY_FIXTURE_ID": fixture_id,
        "FREDDY_FIXTURE_VERSION": fixture.version,
    }

    shape_variants = source_desc.get("shape_variants") or [None]
    records: list[dict[str, Any]] = []
    for shape_flags in shape_variants:
        flag_args: list[str] = []
        if shape_flags:
            for k, v in sorted(shape_flags.items()):
                flag_args.extend([f"--{k}", str(v)])
        cmd = [*source_desc["command"], arg, *flag_args] if arg else [*source_desc["command"], *flag_args]
        out_path = cache_dir / artifact_filename(
            source_desc["source"], source_desc["data_type"], arg, shape_flags,
        )
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=fixture.timeout, env=env,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"fetch failed for {source_desc['source']}/{source_desc['data_type']} "
                f"shape={shape_flags} (arg={arg[:60]}): {result.stderr[:500]}"
            )
        out_path.write_text(result.stdout)
        try:
            data = json.loads(result.stdout)
            record_count = len(data) if isinstance(data, list) else 1
        except json.JSONDecodeError:
            raise RuntimeError(
                f"fetch for {source_desc['source']} returned non-JSON output"
            )
        # Cost extraction per the Phase 0 inventory artifact (see phase-0-inventory.json).
        # The artifact declares per-command `cost_emission_path` (e.g. "_meta.cost_usd",
        # top-level "cost_usd", or "absent"). Any shape that diverges from the declared
        # path is a loud failure — silent $0 accumulation corrupts cost dashboards.
        cost_usd = _extract_cost_usd(source_desc["command"], data)
        if cost_usd == 0.0 and _command_declares_cost(source_desc["command"]):
            sys.stderr.write(
                f"⚠️  cost_usd=0 from {source_desc['source']}/{source_desc['data_type']} "
                f"but Phase 0 inventory declares cost emission for this command. "
                f"Investigate response shape drift before trusting the cache manifest.\n"
            )
        records.append({
            "source": source_desc["source"],
            "data_type": source_desc["data_type"],
            "arg": arg,
            "shape_flags": shape_flags,
            "retention_days": source_desc["retention_days"],
            "cached_artifact": out_path.name,
            "record_count": record_count,
            "cost_usd": cost_usd,
        })
    return records


def _find_fixture(manifest_path: Path, fixture_id: str) -> tuple[FixtureSpec, str]:
    payload = json.loads(manifest_path.read_text())
    manifest = parse_suite_manifest(payload)
    for domain, fixtures in manifest.fixtures.items():
        for f in fixtures:
            if f.fixture_id == fixture_id:
                return f, domain
    raise KeyError(f"fixture {fixture_id!r} not found in {manifest_path}")


def refresh_fixture(
    *, manifest_path: Path, pool: str, fixture_id: str,
    cache_root: Path, dry_run: bool = False, force: bool = False,
) -> RefreshResult:
    payload = json.loads(Path(manifest_path).read_text())
    parsed_manifest = parse_suite_manifest(payload)
    assert_pool_matches(pool, parsed_manifest)

    fixture, domain = _find_fixture(Path(manifest_path), fixture_id)
    cache_dir = cache_path_for(cache_root, pool, fixture.fixture_id, fixture.version)

    sources = _determine_sources(fixture, domain)
    lines: list[str] = [
        f"Refreshing {fixture_id}@{fixture.version} ({pool}, domain={domain})"
    ]

    if dry_run:
        lines.append("Sources that would be fetched:")
        for src in sources:
            for arg_name in src["args_from"]:
                arg_val = _resolve_arg(fixture, arg_name)
                lines.append(
                    f"  - {src['source']}/{src['data_type']} "
                    f"(arg={arg_name}={repr(arg_val)[:40]}, "
                    f"retention {src['retention_days']}d)"
                )
        lines.append("(dry-run; no fetches performed)")
        return RefreshResult(fixture_id=fixture_id, report_lines=lines,
                             cache_dir=None, cost_usd=0.0)

    # Freshness gate unless --force
    if cache_dir.exists() and not force:
        manifest = load_cache_manifest(cache_dir)
        if staleness_status(manifest) == "fresh":
            lines.append(
                "cache is fresh; pass --force to refresh anyway"
            )
            return RefreshResult(fixture_id=fixture_id, report_lines=lines,
                                 cache_dir=cache_dir, cost_usd=0.0)

    # Archive existing cache
    if cache_dir.exists():
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        archive = cache_dir.parent / f"{cache_dir.name}.archive-{ts}"
        cache_dir.rename(archive)
        lines.append(f"archived prior cache to {archive.name}")

    cache_dir.mkdir(parents=True)
    start = time.time()
    records: list[DataSourceRecord] = []
    total_cost = 0.0
    for src in sources:
        for arg_name in src["args_from"]:
            arg_val = _resolve_arg(fixture, arg_name)
            payloads = _run_source_fetch(
                src, fixture.fixture_id, fixture, cache_dir, arg_val,
            )
            for payload in payloads:
                # DataSourceRecord does not carry shape_flags on the record itself
                # (it's encoded in cached_artifact's filename hash); strip it.
                payload_for_record = {k: v for k, v in payload.items() if k != "shape_flags"}
                records.append(DataSourceRecord(**payload_for_record))
                total_cost += payload.get("cost_usd", 0.0)
                shape_label = f" shape={payload['shape_flags']}" if payload.get("shape_flags") else ""
                lines.append(
                    f"  ✓ {payload['source']}/{payload['data_type']}"
                    f"{shape_label} (arg={arg_name}) {payload['record_count']} records  "
                    f"${payload['cost_usd']:.2f}"
                )

    duration = int(time.time() - start)
    manifest = CacheManifest(
        fixture_id=fixture.fixture_id,
        fixture_version=fixture.version,
        pool=pool,
        fetched_at=datetime.now(timezone.utc),
        fetched_by=getpass.getuser(),
        data_sources=records,
        total_fetch_cost_usd=total_cost,
        fetch_duration_seconds=duration,
    )
    write_cache_manifest(cache_dir, manifest)
    lines.append(f"  Total: {sum(r.record_count for r in records)} records, "
                 f"${total_cost:.2f}, {duration}s")
    lines.append(f"Cache written: {cache_dir}")
    return RefreshResult(fixture_id=fixture_id, report_lines=lines,
                         cache_dir=cache_dir, cost_usd=total_cost)
```

- [ ] **Step 3: Wire refresh command**

Append to `cli/freddy/commands/fixture.py`:

```python
from cli.freddy.fixture.refresh import refresh_fixture


@app.command("refresh")
def refresh_cmd(
    fixture_id: str = typer.Argument(..., help="Fixture id to refresh."),
    manifest_path: Path = typer.Option(..., "--manifest", exists=True, readable=True),
    pool: str = typer.Option(..., "--pool", help="Pool name, e.g. 'search-v1'."),
    cache_root: Path = typer.Option(Path(str(DEFAULT_CACHE_ROOT)), "--cache-root", file_okay=False),
    dry_run: bool = typer.Option(False, "--dry-run"),
    force: bool = typer.Option(False, "--force", help="Refresh even if cache is fresh."),
) -> None:
    """Manually refresh cached data for a fixture."""
    result = refresh_fixture(
        manifest_path=Path(manifest_path), pool=pool, fixture_id=fixture_id,
        cache_root=Path(cache_root), dry_run=dry_run, force=force,
    )
    for line in result.report_lines:
        typer.echo(line)
```

Run: `pytest tests/freddy/fixture/test_refresh.py -v` — expect all PASS.

- [ ] **Step 4: Add batch modes**

Append to `tests/freddy/fixture/test_refresh.py` (uses the shared `seed_cache`, `manifest_file`, `fetch_payload` fixtures):

```python
_BATCH_FIXTURES = [
    {"fixture_id": f"mon-{name}", "client": name[0], "context": name[0],
     "version": "1.0",
     "env": {"AUTORESEARCH_WEEK_RELATIVE": "most_recent_complete"}}
    for name in ("fresh", "aging", "stale")
]


@patch("cli.freddy.fixture.refresh._run_source_fetch")
def test_refresh_all_stale_only_refreshes_stale(
    mock_fetch, manifest_file, fetch_payload, seed_cache,
):
    mock_fetch.return_value = fetch_payload(record_count=10, cost_usd=0.0)
    mpath = manifest_file(domain="monitoring", fixtures=_BATCH_FIXTURES)
    seed_cache("search-v1", "mon-fresh", age_days=5)
    seed_cache("search-v1", "mon-aging", age_days=20)
    cache_root = seed_cache("search-v1", "mon-stale", age_days=35)

    runner = CliRunner()
    result = runner.invoke(fixture_app, [
        "refresh", "--all-stale", "--manifest", mpath, "--pool", "search-v1",
        "--cache-root", str(cache_root),
    ])
    assert result.exit_code == 0, result.output
    assert "mon-stale" in result.output
    assert "mon-fresh" not in result.output or "skipped" in result.output.lower()
    # Monitoring has 3 source descriptors (mentions/sentiment/sov) → 1 stale
    # fixture × 3 descriptors == 3 fetch calls.
    assert mock_fetch.call_count == 3


@patch("cli.freddy.fixture.refresh._run_source_fetch")
def test_refresh_all_aging_covers_aging_and_stale(
    mock_fetch, manifest_file, fetch_payload, seed_cache,
):
    mock_fetch.return_value = fetch_payload(record_count=5, cost_usd=0.0)
    # Seed the same three tiers as above; aging + stale → 2 fixtures ×
    # 3 descriptors == 6 fetch calls. Assert mock_fetch.call_count == 6.
```

Implement the batch modes in `cli/freddy/fixture/refresh.py`:

```python
def refresh_all(
    *, manifest_path: Path, pool: str, cache_root: Path,
    tier_filter: str,  # "stale" or "aging-or-worse"
    dry_run: bool = False,
) -> list[RefreshResult]:
    payload = json.loads(manifest_path.read_text())
    manifest = parse_suite_manifest(payload)
    assert_pool_matches(pool, manifest)
    results: list[RefreshResult] = []
    for fixtures in manifest.fixtures.values():
        for fixture in fixtures:
            cache_dir = cache_path_for(cache_root, pool, fixture.fixture_id,
                                        fixture.version)
            if not cache_dir.exists():
                continue  # Nothing to refresh; no baseline cache exists
            try:
                cm = load_cache_manifest(cache_dir)
            except Exception:
                continue
            status = staleness_status(cm)
            if tier_filter == "stale" and status != "stale":
                continue
            if tier_filter == "aging-or-worse" and status == "fresh":
                continue
            results.append(refresh_fixture(
                manifest_path=manifest_path, pool=pool,
                fixture_id=fixture.fixture_id, cache_root=cache_root,
                dry_run=dry_run, force=True,
            ))
    return results
```

Update the CLI command in `cli/freddy/commands/fixture.py` to make `fixture_id` optional when `--all-stale` or `--all-aging` is set. Replace the `refresh_cmd` definition added earlier with this extended version:

```python
@app.command("refresh")
def refresh_cmd(
    fixture_id: str | None = typer.Argument(None, help="Fixture id (omit with --all-stale/--all-aging)."),
    manifest_path: Path = typer.Option(..., "--manifest", exists=True, readable=True),
    pool: str = typer.Option(..., "--pool", help="Pool name, e.g. 'search-v1'."),
    cache_root: Path = typer.Option(Path(str(DEFAULT_CACHE_ROOT)), "--cache-root", file_okay=False),
    dry_run: bool = typer.Option(False, "--dry-run"),
    force: bool = typer.Option(False, "--force", help="Refresh even if cache is fresh."),
    all_stale: bool = typer.Option(False, "--all-stale", help="Batch-refresh every stale fixture."),
    all_aging: bool = typer.Option(False, "--all-aging", help="Batch-refresh every aging-or-worse fixture."),
) -> None:
    """Manually refresh cached data for a fixture (or batch)."""
    from cli.freddy.fixture.refresh import refresh_fixture, refresh_all
    if all_stale or all_aging:
        if fixture_id:
            _fail(
                "do not combine a specific fixture_id with --all-stale/--all-aging"
            )
        tier = "stale" if all_stale else "aging-or-worse"
        results = refresh_all(
            manifest_path=Path(manifest_path), pool=pool,
            cache_root=Path(cache_root), tier_filter=tier, dry_run=dry_run,
        )
        for r in results:
            for line in r.report_lines:
                typer.echo(line)
        typer.echo(f"Refreshed {len(results)} fixture(s) matching tier={tier!r}")
        return
    if not fixture_id:
        _fail("fixture_id is required unless --all-stale or --all-aging is set")
    try:
        result = refresh_fixture(
            manifest_path=Path(manifest_path), pool=pool, fixture_id=fixture_id,
            cache_root=Path(cache_root), dry_run=dry_run, force=force,
        )
    except ValueError as exc:  # pool/suite_id mismatch
        _fail(str(exc))
    for line in result.report_lines:
        typer.echo(line)
```

Run: `pytest tests/freddy/fixture/test_refresh.py -v` — expect all batch-mode tests PASS.

- [ ] **Step 5: Commit**

```bash
git add cli/freddy/fixture/refresh.py cli/freddy/commands/fixture.py tests/freddy/fixture/test_refresh.py
git commit -m "feat(fixture): add 'freddy fixture refresh' (manual-trigger, archives prior cache, --dry-run / --force / --all-stale / --all-aging)"
```

---

## Phase 7: `freddy fixture dry-run` (Judge-Based Calibration)

**Purpose:** The qualitative validation gate. Replaces the mechanical canary gate. Produces judge-score distribution per fixture.

**Files:**
- Create: `cli/freddy/fixture/dryrun.py`
- Modify: `cli/freddy/commands/fixture.py`
- Modify: `autoresearch/evaluate_variant.py` (add `--single-fixture` mode)
- Create: `tests/freddy/fixture/test_dryrun.py`

- [ ] **Step 1: Define output contract**

Dry-run report shape:

```json
{
  "fixture_id": "geo-bmw-ev-de",
  "fixture_version": "1.0",
  "baseline_variant": "v006",
  "judge_seeds": 3,
  "per_seed_scores": [0.72, 0.68, 0.74],
  "median_score": 0.72,
  "mad": 0.03,
  "structural_passed": true,
  "warnings": [],
  "quality_verdict": {
    "verdict": "healthy",
    "reasoning": "Median 0.72 with MAD 0.03 is in the discriminating-middle zone; cost well under typical anchor budget.",
    "confidence": 0.80,
    "recommended_action": null
  },
  "cost_usd": 0.42,
  "duration_seconds": 180
}
```

**Quality verdict:** instead of hardcoded `saturated/degenerate/unstable/cost_gate` thresholds, the dry-run command emits the raw stats and delegates interpretation to the `quality-judge` agent (Plan B Phase 0b). The judge sees median, MAD, per_seed_scores, cost_usd, fixture metadata (domain, anchor/rotating, context) and returns a verdict in `{healthy, saturated, degenerate, unstable, cost_excess}` with prose reasoning. No magic numbers in dryrun.py.

**Seeds semantics:** `--seeds N` means N independent sessions (each with a distinct `AUTORESEARCH_SEED`), one judge call per session. Captures joint variant+judge variance. Canonical spec lives in SCHEMA.md (pinned by Plan B Phase 0 Step 3); determinism empirically verified by Plan B Phase 0 probe.

- [ ] **Step 2: Write tests with stubbed judge**

Create `tests/freddy/fixture/test_dryrun.py`. One parametrized test exercises all five flag paths (healthy, saturated, degenerate, unstable, cost_gate):

```python
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from cli.freddy.commands.fixture import app as fixture_app


@pytest.mark.parametrize("per_seed_scores,cost_usd,mock_verdict,expected_exit", [
    # (scores, cost, mocked-judge verdict, expected exit_code)
    ([0.50, 0.52, 0.48, 0.51, 0.49], 0.10, "healthy", 0),
    ([0.92, 0.91, 0.93, 0.90, 0.92], 0.10, "saturated", 1),
    ([0.05, 0.06, 0.04, 0.05, 0.07], 0.10, "degenerate", 1),
    ([0.50, 0.85, 0.15, 0.65, 0.35], 0.10, "unstable", 1),
    ([0.50, 0.52, 0.48, 0.51, 0.49], 2.50, "cost_excess", 1),
])
@patch("cli.freddy.fixture.dryrun.call_quality_judge")
@patch("cli.freddy.fixture.dryrun._run_single_fixture_eval")
def test_dryrun_delegates_to_quality_judge(
    mock_eval, mock_judge, per_seed_scores, cost_usd, mock_verdict, expected_exit,
    manifest_file, tmp_path,
):
    from autoresearch.judges.quality_judge import QualityVerdict
    mock_eval.return_value = {
        "per_seed_scores": per_seed_scores,
        "structural_passed": True,
        "cost_usd": cost_usd,
    }
    mock_judge.return_value = QualityVerdict(
        verdict=mock_verdict,
        reasoning=f"Mocked verdict: {mock_verdict}",
        confidence=0.85,
        recommended_action=None,
    )
    runner = CliRunner()
    result = runner.invoke(fixture_app, [
        "dry-run", "geo-a", "--manifest", manifest_file(),
        "--pool", "search-v1", "--baseline", "v006", "--seeds", "5",
        "--cache-root", str(tmp_path / "cache"),
    ])
    assert result.exit_code == expected_exit, result.output
    assert mock_verdict in result.output.lower()
    # Verify the payload passed to the judge contains the raw stats (no thresholding inside dryrun.py)
    judge_payload = mock_judge.call_args[0][0]
    assert judge_payload["role"] == "fixture_quality"
    assert judge_payload["stats"]["per_seed_scores"] == per_seed_scores
    assert judge_payload["stats"]["cost_usd"] == cost_usd
```

- [ ] **Step 3: Implement single-fixture eval mode in evaluate_variant.py**

Add a new entry-point function `evaluate_single_fixture` to `autoresearch/evaluate_variant.py`, placed next to the existing `evaluate_search` / `evaluate_holdout` entry points (around line ~1600, after those definitions). The function bypasses the full evaluation orchestration: no `_sample_fixtures`, no L1 canary validation, no `scores.json` write, no lineage append. It reuses the existing `_run_fixture_session` (line 510) and `_score_session` (line 564) helpers — the same ones `evaluate_search` / `evaluate_holdout` already call per fixture — and runs them N times with distinct seed env vars.

```python
def _find_one_fixture(suite_manifest: dict[str, Any], fixture_id: str) -> tuple[Fixture, str]:
    """Return (Fixture, domain) for the given fixture_id in a suite manifest."""
    for domain, fixtures in suite_manifest.get("domains", {}).items():
        for payload in fixtures:
            if payload.get("fixture_id") == fixture_id:
                return _fixture_from_payload(payload), domain
    raise KeyError(f"fixture {fixture_id!r} not found in suite manifest")


def evaluate_single_fixture(
    variant_dir: Path,
    archive_dir: Path,
    suite_manifest: dict[str, Any],
    fixture_id: str,
    seeds: int,
    lane: str,
) -> dict[str, Any]:
    """Run one fixture through a variant N times (independent sessions); bypass lineage/scores.json.

    Returns {fixture_id, fixture_version, per_seed_scores (len=seeds),
    structural_passed, cost_usd, warnings}. Seeds semantics in SCHEMA.md.
    """
    import os

    fixture_spec, domain = _find_one_fixture(suite_manifest, fixture_id)
    per_seed: list[float] = []
    total_cost = 0.0
    warnings: list[str] = []
    structural_passed = True

    for seed in range(seeds):
        # AUTORESEARCH_SEED is inherited by _run_fixture_session's subprocess.
        prior = os.environ.get("AUTORESEARCH_SEED")
        os.environ["AUTORESEARCH_SEED"] = str(seed)
        try:
            session_dir = _run_fixture_session(
                variant_dir=variant_dir,
                fixture=fixture_spec,
                domain=domain,
                archive_dir=archive_dir,
                lane=lane,
            )
            score_result = _score_session(
                session_dir=session_dir,
                fixture=fixture_spec,
                domain=domain,
                lane=lane,
            )
        finally:
            if prior is None:
                os.environ.pop("AUTORESEARCH_SEED", None)
            else:
                os.environ["AUTORESEARCH_SEED"] = prior

        per_seed.append(float(score_result.get("score", 0.0)))
        total_cost += float(score_result.get("cost_usd", 0.0) or 0.0)
        if not score_result.get("structural_passed", True):
            structural_passed = False
        warnings.extend(score_result.get("warnings", []) or [])

    return {
        "fixture_id": fixture_id,
        "fixture_version": fixture_spec.version,
        "per_seed_scores": per_seed,
        "structural_passed": structural_passed,
        "cost_usd": total_cost,
        "warnings": warnings,
    }
```

**Helper contract (under Phase 0c architecture):**
- `_run_fixture_session(variant_dir, fixture, domain, archive_dir, lane) -> Path` — returns the session output directory. Handles subprocess invocation, timeout, and error bubbling. Reads `AUTORESEARCH_SEED` from env if the variant's sampler honors it.
- `_score_session(session_dir, fixture, domain, lane) -> dict` — returns `{"score": float, "secondary_score": float, "structural_passed": bool, "warnings": list[str]}`. **POSTs to `${EVOLUTION_JUDGE_URL}/invoke/score`** (Phase 0c) with a session-dir reference; evolution-judge-service executes both primary (gpt-5.4 via `codex` CLI) and secondary (claude-opus-4-7 via `claude` CLI) scoring. Response includes both score sets.

Migration note: the existing `_score_session` currently subprocess-invokes `freddy evaluate variant`. Phase 0c refactors this into an HTTP call; both plans reference the new shape. If running in a dev environment before the judge-service is deployed, the `freddy evaluate` CLI thin-clients (also from Phase 0c) forward to the local judge-service daemon.

Wire new CLI flags in `autoresearch/evaluate_variant.py`'s argparse section (near the existing `evaluate_search` / `evaluate_holdout` flag handlers):

```python
parser.add_argument(
    "--single-fixture",
    help="Format: '<pool>:<fixture_id>'. Route to evaluate_single_fixture.",
)
parser.add_argument("--seeds", type=int, default=1)
parser.add_argument("--json-output", action="store_true")
parser.add_argument(
    "--manifest", type=Path,
    help="Suite manifest path (required with --single-fixture).",
)
parser.add_argument("--baseline-variant", default="v006")
```

Dispatch block (inside the existing `main()` switch):

```python
if args.single_fixture:
    pool, fixture_id = args.single_fixture.split(":", 1)
    suite_payload = json.loads(args.manifest.read_text())
    if pool != suite_payload.get("suite_id"):
        print(f"error: pool {pool!r} != manifest.suite_id {suite_payload.get('suite_id')!r}",
              file=sys.stderr)
        sys.exit(1)
    result = evaluate_single_fixture(
        variant_dir=Path("autoresearch/archive") / args.baseline_variant,
        archive_dir=Path("autoresearch/archive"),
        suite_manifest=suite_payload,
        fixture_id=fixture_id,
        seeds=args.seeds,
        lane=args.lane,
    )
    if args.json_output:
        print(json.dumps(result))
    return
```

Add `tests/autoresearch/test_evaluate_single_fixture.py` exercising the real function (minimal fixture + tiny artifact; patch `_run_fixture_session` and `_score_session` at their import sites for in-process runs). Assert: returned `per_seed_scores` has length == `seeds`; `cost_usd` present and numeric; no writes to `scores.json` / `lineage.ndjson` / `_finalized/`; `AUTORESEARCH_SEED` env var is set to a distinct string for each call (capture via a side-effect patch).

- [ ] **Step 4: Implement dryrun module**

Create `cli/freddy/fixture/dryrun.py`:

```python
"""Judge-based fixture calibration harness."""
from __future__ import annotations

import json
import statistics
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class DryRunReport:
    fixture_id: str
    fixture_version: str
    baseline_variant: str
    judge_seeds: int
    per_seed_scores: list[float]
    median_score: float
    mad: float
    structural_passed: bool
    warnings: list[str]
    quality_verdict: dict[str, Any]  # {verdict, reasoning, confidence, recommended_action}
    cost_usd: float
    duration_seconds: int

    def is_rejection(self) -> bool:
        return str(self.quality_verdict.get("verdict", "healthy")).lower() != "healthy"

    def format_human(self) -> str:
        v = self.quality_verdict
        lines = [
            f"Dry-run: {self.fixture_id}@{self.fixture_version} vs {self.baseline_variant}",
            f"  Seeds: {self.judge_seeds}   Scores: {self.per_seed_scores}",
            f"  Median: {self.median_score:.3f}   MAD: {self.mad:.3f}",
            f"  Structural: {'pass' if self.structural_passed else 'FAIL'}",
            f"  Verdict: {v.get('verdict')}  (confidence {v.get('confidence', 0):.2f})",
            f"  Reasoning: {v.get('reasoning', '')}",
            f"  Cost: ${self.cost_usd:.2f}   Duration: {self.duration_seconds}s",
        ]
        return "\n".join(lines)


def _run_single_fixture_eval(fixture_id: str, pool: str, manifest_path: Path,
                              baseline_variant: str, seeds: int) -> dict[str, Any]:
    """Invoke evaluate_variant.py in solo mode. Tests patch this directly."""
    cmd = [
        "python", "autoresearch/evaluate_variant.py",
        "--single-fixture", f"{pool}:{fixture_id}",
        "--baseline-variant", baseline_variant,
        "--seeds", str(seeds),
        "--manifest", str(manifest_path),
        "--json-output",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    if result.returncode != 0:
        raise RuntimeError(f"single-fixture eval failed: {result.stderr[:500]}")
    return json.loads(result.stdout)


def run_dry_run(
    *, manifest_path: Path, pool: str, fixture_id: str,
    baseline_variant: str | None, seeds: int, cache_root: Path,
) -> DryRunReport:
    baseline = baseline_variant or "v006"

    from cli.freddy.fixture.schema import parse_suite_manifest, assert_pool_matches
    payload = json.loads(manifest_path.read_text())
    manifest = parse_suite_manifest(payload)
    assert_pool_matches(pool, manifest)
    fixture_spec = next(
        (f for fixtures in manifest.fixtures.values() for f in fixtures
         if f.fixture_id == fixture_id),
        None,
    )
    if fixture_spec is None:
        raise KeyError(fixture_id)

    start = time.time()
    # Single subprocess call, N judge seeds inside it (no outer loop)
    raw = _run_single_fixture_eval(
        fixture_id, pool, manifest_path, baseline, seeds,
    )
    scores = [float(s) for s in raw["per_seed_scores"]]
    structural = bool(raw.get("structural_passed", True))
    total_cost = float(raw.get("cost_usd", 0.0))
    warnings: list[str] = list(raw.get("warnings", []))

    median = statistics.median(scores)
    mad = statistics.median(abs(s - median) for s in scores)

    # Delegate quality interpretation to the quality-judge agent.
    # No thresholds here; the judge sees raw stats + fixture metadata and decides.
    from autoresearch.judges.quality_judge import call_quality_judge
    verdict = call_quality_judge({
        "role": "fixture_quality",
        "fixture_id": fixture_id,
        "fixture_version": fixture_spec.version,
        "domain": next(
            (dom for dom, fxs in manifest.fixtures.items() if fixture_spec in fxs),
            None,
        ),
        "anchor": bool(getattr(fixture_spec, "anchor", False)),
        "baseline_variant": baseline,
        "stats": {
            "per_seed_scores": scores,
            "median": median,
            "mad": mad,
            "cost_usd": total_cost,
            "structural_passed": structural,
        },
    })

    report = DryRunReport(
        fixture_id=fixture_id, fixture_version=fixture_spec.version,
        baseline_variant=baseline, judge_seeds=seeds,
        per_seed_scores=scores, median_score=median, mad=mad,
        structural_passed=structural, warnings=warnings,
        quality_verdict={
            "verdict": verdict.verdict,
            "reasoning": verdict.reasoning,
            "confidence": verdict.confidence,
            "recommended_action": verdict.recommended_action,
        },
        cost_usd=total_cost, duration_seconds=int(time.time() - start),
    )
    return report
```

The `DryRunReport` dataclass's `flags: dict[str, bool]` field is replaced by `quality_verdict: dict[str, Any]`; update the dataclass definition accordingly (also drops `COST_GATE_USD` constant — now unused).

- [ ] **Step 5: Wire dry-run command**

Append to `cli/freddy/commands/fixture.py`:

```python
from cli.freddy.fixture.dryrun import run_dry_run


@app.command("dry-run")
def dryrun_cmd(
    fixture_id: str = typer.Argument(..., help="Fixture id to evaluate."),
    manifest_path: Path = typer.Option(..., "--manifest", exists=True, readable=True),
    pool: str = typer.Option(..., "--pool", help="Pool name, e.g. 'search-v1'."),
    baseline: str | None = typer.Option(None, "--baseline", help="Variant id (defaults to promoted head)."),
    seeds: int = typer.Option(3, "--seeds"),
    cache_root: Path = typer.Option(Path(str(DEFAULT_CACHE_ROOT)), "--cache-root", file_okay=False),
) -> None:
    """Run a fixture against a baseline variant and report judge score distribution."""
    try:
        report = run_dry_run(
            manifest_path=Path(manifest_path), pool=pool, fixture_id=fixture_id,
            baseline_variant=baseline, seeds=seeds, cache_root=Path(cache_root),
        )
    except ValueError as exc:  # pool/suite_id mismatch
        _fail(str(exc))
    typer.echo(report.format_human())
    if report.is_rejection():
        _fail(f"fixture not healthy: verdict={report.quality_verdict.get('verdict')}")
```

- [ ] **Step 6: Run tests, commit**

Run: `pytest tests/freddy/fixture/test_dryrun.py -v` — expect all PASS.

```bash
git add cli/freddy/fixture/dryrun.py cli/freddy/commands/fixture.py autoresearch/evaluate_variant.py tests/freddy/fixture/test_dryrun.py
git commit -m "feat(fixture): add 'freddy fixture dry-run' judge-based calibration (median+MAD, flags for saturated/degenerate/unstable/cost_gate)"
```

---

## Phase 8: Freddy CLI Cache-First Integration

**Purpose:** When a variant's session invokes `freddy monitor mentions` (etc.), freddy reads cached data instead of hitting providers live. Never auto-refetches — manual refresh contract preserved.

**Pool-dependent cache-read policy:** `try_read_cache` is wired into ALL session-invoked freddy commands, but its cache-miss behavior differs by pool:
- **search pool (`FREDDY_FIXTURE_POOL=search-v1`):** cache miss returns None → caller live-fetches (current behavior). Cache-first is effectively active for geo-scrape + monitoring (the commands where refresh actually writes cache); competitive + storyboard commands cache-miss and live-fetch unchanged.
- **holdout pool (`FREDDY_FIXTURE_POOL=holdout-*`):** cache miss **raises RuntimeError**, aborting the session. Required for credential isolation (see Plan B Phase 2 Step 9f — holdout sessions must never hit providers with holdout identity visible in request logs).

This means: for holdout fixtures, refresh must populate cache for ALL commands the variant session will invoke (scrape, visibility, mentions, sentiment, sov, search-ads, search-content). `_determine_sources` already writes those during refresh for all 4 domains. The Phase 8 wiring just adds cache-first branches to the three commands previously left live-fetch-only.

Wired commands (all 7 session-invoked; cache-first branch with pool-dependent miss semantics):
- `freddy monitor mentions` / `sentiment` / `sov` (monitoring domain)
- `freddy scrape`, `freddy visibility` (geo domain)
- `freddy search-ads` (competitive domain)
- `freddy search-content` (storyboard domain)

**Cache-key contract (SA-004):** cache hits require the session to call with the same primary argument that `freddy fixture refresh` wrote. Different args → different cache key (sha1(arg)[:12] suffix on the filename). Sessions that pass different output-shape-affecting flags (e.g. `--format summary` when the cache was written without it) will see a cache miss and live-fetch (search pool) or hard-fail (holdout pool). Document this in SCHEMA.md's cache-semantics section; output-shape flags should also participate in the arg_hash if added later.

**Files:**
- Modify: `cli/freddy/commands/monitor.py` (cache-first read: mentions, sentiment, sov)
- Modify: `cli/freddy/commands/scrape.py` (cache-first read)
- Modify: `cli/freddy/commands/visibility.py` (cache-first read)
- Modify: `cli/freddy/commands/search_ads.py` (cache-first read)
- Modify: `cli/freddy/commands/search_content.py` (cache-first read)
- Modify: `autoresearch/evaluate_variant.py` (inject `FREDDY_FIXTURE_*` env vars)
- Create: `cli/freddy/fixture/cache_integration.py`
- Create: `tests/freddy/fixture/test_cache_integration.py`

- [ ] **Step 1: Inventory session-invoked freddy commands**

Run: `grep -rn "freddy.*mentions\|freddy.*scrape" autoresearch/archive/current_runtime/ --include='*.py' --include='*.md'`
Record which commands sessions actually call. Target those for cache-first.

- [ ] **Step 2: Write cache-first test**

Create `tests/freddy/fixture/test_cache_integration.py`:

```python
import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from cli.freddy.fixture.cache import (
    CacheManifest, DataSourceRecord, artifact_filename,
    cache_path_for, write_cache_manifest,
)
from datetime import datetime, timezone


def _set_env(monkeypatch, cache_root, pool, fixture_id, version="1.0"):
    monkeypatch.setenv("FREDDY_FIXTURE_CACHE_DIR", str(cache_root))
    monkeypatch.setenv("FREDDY_FIXTURE_POOL", pool)
    monkeypatch.setenv("FREDDY_FIXTURE_ID", fixture_id)
    monkeypatch.setenv("FREDDY_FIXTURE_VERSION", version)


def test_monitor_mentions_returns_cached_data_when_env_set(seed_cache, monkeypatch):
    cache_root = seed_cache("search-v1", "mon-a", source="xpoz", data_type="mentions", arg="abc")
    _set_env(monkeypatch, cache_root, "search-v1", "mon-a")

    from cli.freddy.commands.monitor import app as monitor_app
    with patch("cli.freddy.commands.monitor.api_request") as mock_api:
        runner = CliRunner()
        result = runner.invoke(monitor_app, ["mentions", "abc"])
        assert "cached" in result.output.lower()
        mock_api.assert_not_called()


def test_monitor_mentions_cache_miss_on_different_arg(seed_cache, monkeypatch):
    cache_root = seed_cache("search-v1", "mon-a", source="xpoz", data_type="mentions", arg="abc")
    _set_env(monkeypatch, cache_root, "search-v1", "mon-a")

    from cli.freddy.commands.monitor import app as monitor_app
    with patch("cli.freddy.commands.monitor.api_request") as mock_api:
        mock_api.return_value = {"items": []}
        runner = CliRunner()
        runner.invoke(monitor_app, ["mentions", "xyz"])  # arg differs from cache
        assert mock_api.called


def test_holdout_pool_cache_miss_raises_not_fallback(tmp_path, monkeypatch):
    _set_env(monkeypatch, tmp_path / "empty", "holdout-v1", "mon-missing")

    from cli.freddy.fixture.cache_integration import try_read_cache
    with patch("cli.freddy.commands.monitor.api_request") as mock_api:
        with pytest.raises(RuntimeError, match="Holdout cache miss"):
            try_read_cache("xpoz", "mentions", "mon-missing")
        mock_api.assert_not_called()
```

- [ ] **Step 3: Implement cache-first helper**

Create `cli/freddy/fixture/cache_integration.py`:

```python
"""Helpers for freddy commands to read from fixture cache when env vars are set."""
from __future__ import annotations

import json
import os
from pathlib import Path

from cli.freddy.fixture.cache import (
    artifact_filename, cache_path_for, load_cache_manifest, staleness_status,
)


def fixture_cache_context() -> dict[str, str] | None:
    """Return fixture-cache context if env indicates cache-first mode, else None."""
    required = ("FREDDY_FIXTURE_CACHE_DIR", "FREDDY_FIXTURE_POOL",
                "FREDDY_FIXTURE_ID", "FREDDY_FIXTURE_VERSION")
    values = {k: os.environ.get(k, "").strip() for k in required}
    if not all(values.values()):
        return None
    return values


def try_read_cache(source: str, data_type: str, arg: str) -> dict | list | None:
    """Return cached data for the given (source, data_type, arg) triple.

    Cache miss semantics:
    - If ``FREDDY_FIXTURE_POOL`` starts with ``"holdout"``, raise
      ``RuntimeError`` on miss. A holdout session MUST NOT fall through to a
      live fetch, because the provider's outbound call would leak holdout
      identity to its logs.
    - Otherwise, return None (caller continues with live fetch).

    Prints a stderr warning if cache is stale; never auto-refetches.
    """
    import typer

    ctx = fixture_cache_context()
    if ctx is None:
        return None

    cache_dir = cache_path_for(
        Path(ctx["FREDDY_FIXTURE_CACHE_DIR"]),
        ctx["FREDDY_FIXTURE_POOL"],
        ctx["FREDDY_FIXTURE_ID"],
        ctx["FREDDY_FIXTURE_VERSION"],
    )
    # POOL_POLICIES (B3): consult pool_policies.json for miss-semantics.
    # Unknown pool → `_default` → hard_fail. Default-deny prevents a future
    # pool-naming convention change from silently downgrading isolation.
    _policies_path = Path(__file__).resolve().parent / "pool_policies.json"
    _policies = json.loads(_policies_path.read_text())
    _pool = ctx["FREDDY_FIXTURE_POOL"]
    _on_miss = _policies.get(_pool, _policies["_default"])["on_miss"]
    hard_fail_on_miss = _on_miss == "hard_fail"

    def _miss(reason: str) -> None:
        if hard_fail_on_miss:
            # Message says "Live-fetch would leak identity to provider logs" —
            # accurate for holdout pool and for any future pool configured as
            # hard_fail (the default-deny for unknown pools).
            raise RuntimeError(
                f"Holdout cache miss for {source}/{data_type} "
                f"(arg={arg[:60]}): {reason}. "
                f"Live-fetch would leak holdout identity to provider logs. "
                f"Run: freddy fixture refresh {ctx['FREDDY_FIXTURE_ID']} "
                f"--pool {ctx['FREDDY_FIXTURE_POOL']} "
                f"--manifest <your-manifest>"
            )

    if not cache_dir.exists():
        _miss("cache directory does not exist")
        return None

    try:
        manifest = load_cache_manifest(cache_dir)
    except Exception as exc:
        _miss(f"manifest unreadable: {exc}")
        return None

    expected_artifact = artifact_filename(source, data_type, arg, shape_flags)
    for src in manifest.data_sources:
        if (src.source == source
                and src.data_type == data_type
                and src.cached_artifact == expected_artifact):
            status = staleness_status(manifest)
            if status != "fresh":
                typer.echo(
                    f"⚠️  Fixture {ctx['FREDDY_FIXTURE_ID']} cache is {status.upper()}. "
                    f"Refresh: freddy fixture refresh {ctx['FREDDY_FIXTURE_ID']} "
                    f"--pool {ctx['FREDDY_FIXTURE_POOL']}",
                    err=True,
                )
            artifact_path = cache_dir / src.cached_artifact
            return json.loads(artifact_path.read_text())

    _miss("no matching (source, data_type, arg) entry in manifest")
    return None
```

- [ ] **Step 4: Wire into all 7 session-invoked commands**

Wire cache-first branches into all 7 commands a variant session may invoke. Pattern (example: `mentions`):

```python
from cli.freddy.fixture.cache_integration import try_read_cache

@app.command()
@handle_errors
def mentions(
    monitor_id: str = typer.Argument(..., help="Monitor UUID"),
    # ... existing options ...
) -> None:
    cached = try_read_cache("xpoz", "mentions", monitor_id)
    if cached is not None:
        typer.echo(json.dumps(cached))
        return
    # existing live-fetch code continues unchanged.
    # Note: for holdout pool, try_read_cache raises on miss; never reaches here.
```

Update `try_read_cache` signature to `try_read_cache(source, data_type, arg, shape_flags: dict[str, str] | None = None)` so shape flags thread into the cache-key hash (required for `--format summary` vs `--format full` to resolve to distinct entries).

Wire:
- `freddy monitor mentions` → `try_read_cache("xpoz", "mentions", monitor_id, shape_flags={"format": format_opt})`
- `freddy monitor sentiment` → `try_read_cache("xpoz", "sentiment", monitor_id, shape_flags={"format": format_opt})`
- `freddy monitor sov` → `try_read_cache("xpoz", "sov", monitor_id, shape_flags={"format": format_opt})`
- `freddy scrape` → `try_read_cache("freddy-scrape", "page", url)`
- `freddy visibility` → `try_read_cache("freddy-visibility", "visibility", context)`
- `freddy search-ads` → `try_read_cache("foreplay", "ads", context)`
- `freddy search-content` → `try_read_cache("ic", "creator_videos", context)`

Refresh writes the default-shape artifact; non-default session requests cache-miss → live-fetch (search) or hard-fail (holdout). Wiring all 7 (not just the 4 on search pool) is required for holdout credential isolation: an unwired command on the holdout pool would live-fetch with holdout creds.

Add a regression test `test_monitor_mentions_different_format_misses_cache`: seed default-shape cache, invoke with `--format summary`, assert live-fetch (cache miss).

- [ ] **Step 5: Inject env vars in evaluate_variant.py**

Modify `autoresearch/evaluate_variant.py` at the session-subprocess spawn. Add a `manifest: SuiteManifest` parameter to the spawn helper and thread it down from `evaluate_search()` / `evaluate_holdout()`. Extend the subprocess `env`:

```python
session_env = {
    **os.environ,
    "FREDDY_FIXTURE_CACHE_DIR": os.environ.get(
        "FREDDY_FIXTURE_CACHE_DIR",
        str(Path.home() / ".local/share/gofreddy/fixture-cache"),
    ),
    "FREDDY_FIXTURE_POOL": active_manifest.suite_id,  # e.g. "search-v1"
    "FREDDY_FIXTURE_ID": fixture.fixture_id,
    "FREDDY_FIXTURE_VERSION": fixture.version,
}
```

- [ ] **Step 6: Verify tests pass**

Run: `pytest tests/freddy/fixture/test_cache_integration.py -v` — expect PASS.

- [ ] **Step 7: Manual smoke test**

Manually run: pick one fixture, refresh it, run a session locally with `FREDDY_FIXTURE_*` vars set, confirm (via logs or stderr) that no provider calls were made.

- [ ] **Step 8: Commit**

```bash
git add cli/freddy/fixture/cache_integration.py \
        cli/freddy/commands/monitor.py cli/freddy/commands/scrape.py \
        autoresearch/evaluate_variant.py \
        tests/freddy/fixture/test_cache_integration.py
git commit -m "feat(fixture): cache-first read in freddy CLI when FREDDY_FIXTURE_* set (search pool: miss→live; holdout pool: miss→hard-fail)"
```

---

## Phase 9: Schema Documentation (SCHEMA.md)

**Purpose:** Authoritative schema doc (currently schema lives only in code — a gap from the audit).

**Files:**
- Create: `autoresearch/eval_suites/SCHEMA.md`

- [ ] **Step 1: Write SCHEMA.md as a pointer table**

Create `autoresearch/eval_suites/SCHEMA.md` as a short index, not a re-statement of facts that live elsewhere. Authoritative sources live in code + the real manifest example:

```markdown
# Fixture Schema

**Manifest shape & field contracts:** see `autoresearch/eval_suites/search-v1.json` (canonical example) and `cli/freddy/fixture/schema.py::parse_suite_manifest` (validator).

**Cache layout & arg-hash contract:** see `cli/freddy/fixture/cache.py` module docstring.

**Source descriptors & retention defaults:** see `cli/freddy/fixture/config.json`.

**Pool isolation policy:** see `config.json` `pool_policies` key. Unknown pool → hard-fail on miss (default-deny).

**Holdout manifests:** live out-of-repo at `~/.config/gofreddy/holdouts/` (`chmod 600`), loaded via `EVOLUTION_HOLDOUT_MANIFEST`. Example at `holdout-v1.json.example` includes `"is_redacted_example": true` sentinel — loaders refuse manifests with this field set.

**Seed semantics:** `--seeds N` = N independent sessions with distinct `AUTORESEARCH_SEED`. Verified by Plan B Phase 0 probe.

**Threat boundary caveat:** pool separation is behavioral (chmod + refresh wrapper + cache-first-or-fail), NOT cryptographic. Same-UID process can read the credentials file. See Plan B header "Accepted risks".
```

- [ ] **Step 2: Update autoresearch/README.md with new CLI section**

Open `autoresearch/README.md`. Add a section titled "Fixture authoring" near the top of the Evaluation or Notes area. Content:

```markdown
## Fixture authoring

See `autoresearch/eval_suites/SCHEMA.md` (pointer index) for schema + pool layout.

CLI (post-consolidation): `freddy fixture validate | inspect | cache | refresh | dry-run` (+ `author` / `migrate` from Plan B). `freddy fixture --help` is authoritative.
```

- [ ] **Step 3: Commit**

```bash
git add autoresearch/eval_suites/SCHEMA.md autoresearch/README.md
git commit -m "docs(fixture): add SCHEMA.md authoritative reference"
```

---

## Phase 10: Discriminability Gate

**CLI consolidation:** `discriminate` is implemented as a flag on `freddy fixture dry-run`: `--variants v_a,v_b` triggers the rank-sum discriminability check instead of a single-variant dry-run. Eliminates a separate command for what is structurally "dry-run with multiple variants." Tests invoke `["discriminate", ...]` — at implementation, the flag path is `["dry-run", ..., "--variants", "v_a,v_b"]`.

**Purpose:** BenchBuilder-style minimum-discriminability acceptance check. A fixture is useful only if it separates variants of meaningfully different capability; this command surfaces fixtures that don't.

**Approach:** Wilcoxon rank-sum test (`scipy.stats.ranksums`) + Cliff's delta effect-size check. Fixture is `separable` when at least one pair yields p<0.05 AND |Cliff's delta| >= 0.3. Minimum n=10 gives ~0.8 power for Cohen d~0.8 at alpha=0.05; n=5 is underpowered (requires complete distribution separation, flaps under judge noise).

**Files:**
- Modify: `cli/freddy/fixture/dryrun.py` (add discriminability check)
- Modify: `cli/freddy/commands/fixture.py` (add `discriminate` subcommand)
- Create: `tests/freddy/fixture/test_discriminate.py`

- [ ] **Step 1: Write failing tests**

Create `tests/freddy/fixture/test_discriminate.py` (uses the shared `manifest_file` fixture):

```python
from pathlib import Path
from unittest.mock import patch

import pytest
import typer
from typer.testing import CliRunner

from cli.freddy.commands.fixture import app as fixture_app
from cli.freddy.fixture.dryrun import run_discriminability_check


@patch("cli.freddy.fixture.dryrun._run_single_fixture_eval")
def test_discriminability_separable_when_distributions_differ(mock_eval, manifest_file):
    """Two variants with clearly-different scores -> separable=True."""
    def side_effect(fixture_id, pool, manifest_path, variant, seeds):
        if variant == "v_low":
            return {"per_seed_scores": [0.10, 0.12, 0.09, 0.11, 0.13]}
        return {"per_seed_scores": [0.82, 0.85, 0.80, 0.83, 0.86]}
    mock_eval.side_effect = side_effect

    report = run_discriminability_check(
        fixture_id="geo-a", pool="search-v1",
        manifest_path=Path(manifest_file()),
        variants=["v_low", "v_high"], seeds=5,
    )
    assert report.separable is True
    assert all(0.0 <= pr["pvalue"] <= 1.0 for pr in report.pair_results)


@patch("cli.freddy.fixture.dryrun._run_single_fixture_eval")
def test_discriminability_not_separable_when_overlap(mock_eval, manifest_file):
    """Two variants with overlapping scores -> separable=False."""
    def side_effect(fixture_id, pool, manifest_path, variant, seeds):
        if variant == "v_a":
            return {"per_seed_scores": [0.50, 0.52, 0.48, 0.51, 0.49]}
        return {"per_seed_scores": [0.51, 0.49, 0.52, 0.50, 0.48]}
    mock_eval.side_effect = side_effect

    report = run_discriminability_check(
        fixture_id="geo-a", pool="search-v1",
        manifest_path=Path(manifest_file()),
        variants=["v_a", "v_b"], seeds=5,
    )
    assert report.separable is False


def test_discriminability_rejects_seeds_below_floor(manifest_file):
    """--seeds 5 is below the noise floor and must be rejected (min is 10)."""
    with pytest.raises(typer.BadParameter, match=">= 10"):
        run_discriminability_check(
            fixture_id="geo-a", pool="search-v1",
            manifest_path=Path(manifest_file()),
            variants=["v_a", "v_b"], seeds=5,
        )


@patch("cli.freddy.fixture.dryrun._run_single_fixture_eval")
def test_discriminability_requires_cliffs_delta_not_just_pvalue(mock_eval, manifest_file):
    """Low p-value with tiny effect (|Cliff's delta| < 0.3) -> separable=False.

    Two distributions with 10 seeds each that barely differ: p can dip below
    0.05 by luck but the effect size exposes it as noise.
    """
    def side_effect(fixture_id, pool, manifest_path, variant, seeds):
        if variant == "v_a":
            return {"per_seed_scores": [0.50, 0.51, 0.49, 0.50, 0.52, 0.49, 0.51, 0.50, 0.51, 0.49]}
        return {"per_seed_scores": [0.51, 0.52, 0.50, 0.51, 0.53, 0.50, 0.52, 0.51, 0.52, 0.50]}
    mock_eval.side_effect = side_effect
    report = run_discriminability_check(
        fixture_id="geo-a", pool="search-v1",
        manifest_path=Path(manifest_file()),
        variants=["v_a", "v_b"], seeds=10,
    )
    # effect size is small; even if p<0.05, separable must be False
    assert all("cliffs_delta" in pr for pr in report.pair_results)
    assert report.separable is False


def test_discriminate_cli_rejects_pool_manifest_mismatch(manifest_file):
    runner = CliRunner()
    result = runner.invoke(fixture_app, [
        "discriminate", "geo-a",
        "--manifest", manifest_file(),
        "--pool", "holdout-v1",  # mismatched against suite_id "search-v1"
        "--variants", "v001,v006", "--seeds", "5",
    ])
    assert result.exit_code == 1
    assert "does not match" in result.output.lower()
```

- [ ] **Step 2: Implement discriminability check**

Append to `cli/freddy/fixture/dryrun.py`:

```python
from dataclasses import dataclass, field

import typer
from scipy.stats import ranksums


MIN_SEEDS = 10  # noise floor; below this the rank-sum test is underpowered
CLIFFS_DELTA_FLOOR = 0.3  # medium effect size threshold


@dataclass
class DiscriminabilityReport:
    fixture_id: str
    variant_scores: dict[str, list[float]]
    pair_results: list[dict]  # each: {"pair": (a, b), "pvalue": float, "stat": float, "cliffs_delta": float}
    separable: bool


def _cliffs_delta(a: list[float], b: list[float]) -> float:
    """Cliff's delta effect size in [-1, 1]; |>=0.3| = medium effect."""
    if not a or not b:
        return 0.0
    greater = sum(1 for x in a for y in b if x > y)
    lesser = sum(1 for x in a for y in b if x < y)
    return (greater - lesser) / (len(a) * len(b))


def run_discriminability_check(
    *, fixture_id: str, pool: str, manifest_path: Path,
    variants: list[str], seeds: int = MIN_SEEDS,
) -> DiscriminabilityReport:
    """Check whether a fixture separates variants of meaningfully different capability.

    For each variant, ``_run_single_fixture_eval`` is called once with
    ``seeds=N``; that call returns ``per_seed_scores`` (a list of N judge
    scores). Variant pairs are then compared via ``scipy.stats.ranksums``
    AND Cliff's delta. A pair is separable iff p<0.05 AND |Cliff's delta|>=0.3.
    The fixture is ``separable`` if at least one pair passes both gates.

    Requires seeds >= 10 (computed ~0.8 power for Cohen d~0.8 at alpha=0.05).
    """
    if seeds < MIN_SEEDS:
        raise typer.BadParameter(
            f"--seeds must be >= {MIN_SEEDS} for discriminability (noise floor; "
            f"n<{MIN_SEEDS} is underpowered for judge MAD>=0.10)"
        )
    if len(variants) < 2:
        raise typer.BadParameter("--variants requires at least two ids")

    # pool/suite_id consistency
    from cli.freddy.fixture.schema import parse_suite_manifest, assert_pool_matches
    payload = json.loads(Path(manifest_path).read_text())
    parsed = parse_suite_manifest(payload)
    assert_pool_matches(pool, parsed)

    variant_scores: dict[str, list[float]] = {}
    for variant in variants:
        result = _run_single_fixture_eval(
            fixture_id, pool, manifest_path, variant, seeds,
        )
        variant_scores[variant] = [float(s) for s in result["per_seed_scores"]]

    pair_results: list[dict] = []
    separable = False
    for i, v_a in enumerate(variants):
        for v_b in variants[i + 1:]:
            stat, pvalue = ranksums(variant_scores[v_a], variant_scores[v_b])
            delta = _cliffs_delta(variant_scores[v_a], variant_scores[v_b])
            pair_results.append({
                "pair": (v_a, v_b),
                "pvalue": float(pvalue),
                "stat": float(stat),
                "cliffs_delta": float(delta),
            })
            # Both gates must pass: statistical significance AND medium effect size
            if pvalue < 0.05 and abs(delta) >= CLIFFS_DELTA_FLOOR:
                separable = True

    return DiscriminabilityReport(
        fixture_id=fixture_id,
        variant_scores=variant_scores,
        pair_results=pair_results,
        separable=separable,
    )
```

- [ ] **Step 3: Wire CLI command**

Append to `cli/freddy/commands/fixture.py`:

```python
@app.command("discriminate")
def discriminate_cmd(
    fixture_id: str = typer.Argument(..., help="Fixture id."),
    manifest_path: Path = typer.Option(..., "--manifest", exists=True, readable=True),
    pool: str = typer.Option(..., "--pool", help="Pool name."),
    variants: str = typer.Option(..., "--variants", help="Comma-separated variant ids (min 2)."),
    seeds: int = typer.Option(10, "--seeds", min=10, help="Judge seeds per variant (>=10; noise floor)."),
) -> None:
    """Verify fixture separates variants of differing capability (rank-sum test)."""
    from dataclasses import asdict

    from cli.freddy.fixture.dryrun import run_discriminability_check
    try:
        report = run_discriminability_check(
            fixture_id=fixture_id, pool=pool,
            manifest_path=Path(manifest_path),
            variants=variants.split(","), seeds=seeds,
        )
    except ValueError as exc:  # pool/suite_id mismatch
        _fail(str(exc))
    typer.echo(json.dumps(asdict(report), indent=2, default=str))
    if not report.separable:
        _fail("fixture does not discriminate between variants (all p >= 0.05)")
```

- [ ] **Step 4: Verify tests pass, commit**

Run: `pytest tests/freddy/fixture/test_discriminate.py -v` — expect all PASS.

```bash
git add cli/freddy/fixture/dryrun.py cli/freddy/commands/fixture.py tests/freddy/fixture/test_discriminate.py
git commit -m "feat(fixture): add 'freddy fixture discriminate' (rank-sum gate, seeds>=5)"
```

---

## Phase 11: Legacy Code Deletion

**Purpose:** Remove superseded code. All replacements from Phases 1-10 are now working, so deletion is safe.

**Files to delete:**
- `autoresearch/archive_cli.py`
- `autoresearch/geo_verify.py`
- `autoresearch/geo-verify.sh`

**Files to modify:**
- `autoresearch/evolve.py` — remove `_DEPRECATED_COMMANDS` dict + `_check_deprecated_commands` helper (see Step 5 for exact anchors)
- `autoresearch/evaluate_variant.py` — remove canary gate (see Step 3 for exact anchors) and the one-time legacy-path migration inside `_private_result_path` (see Step 4 for exact anchors)
- `autoresearch/README.md` — drop references to retired artifacts


- [ ] **Step 1: Verify no live importers**

Run: `grep -rn "archive_cli\|geo_verify\|_DEPRECATED_COMMANDS\|_check_deprecated_commands" --include='*.py' --include='*.sh' --include='*.md' . | grep -v "^\./docs/plans/"` — expect only matches inside files being deleted or modified (no external callers).

- [ ] **Step 2: Delete files**

```bash
git rm autoresearch/archive_cli.py autoresearch/geo_verify.py autoresearch/geo-verify.sh
```

- [ ] **Step 3: Remove canary gate (agent-driven)**

The canary gate is the staged-eval Stage 1/Stage 2 split in `evaluate_variant.py::evaluate_search`. The surrounding function has drifted since this plan was drafted; exact-anchor edits are brittle in both directions (anchors mismatch → silent no-op; anchors partially match → orphaned variable references). Delegate the deletion to an agent with a clear goal + an objective completion check.

**Dispatch pattern:** use the subagent-driven executor (superpowers:subagent-driven-development). Brief:

```
Goal: remove the canary gate from autoresearch/evaluate_variant.py.

The canary gate is the Stage 1 / Stage 2 split introduced around Gap 17:
Stage 1 runs one "canary" fixture per affected domain; if aggregate
canary pass-rate < 0.5, the rest of the run aborts. Stage 2 runs the
remaining fixtures only when canary passed.

Remove the split entirely so all fixtures run in a single unsharded pass.
Preserve: `scored_fixtures`, `any_output`, `smoke_summary` (minus
`canary_aborted` key), lineage-row shape (minus `canary_aborted` reason
branch). Remove: `canary_aborted` variable, `canary_fixtures` list,
`canary_scores` dict, `canary_pass_rate` computation, the
`if canary_pass_rate < 0.5:` branch, the `if not canary_aborted:` Stage 2
guard, the `remaining = fixtures_by_domain[domain][1:]` slicing that
skips the canary.

Objective completion check (must pass before committing):
  rg -n "canary_(scores|aborted|fixtures|pass_rate)" autoresearch/evaluate_variant.py
must return zero matches. If it returns any match, iterate until clean.

Run the full autoresearch test suite after the edit:
  pytest tests/autoresearch/ -x -q
must pass. Any canary-specific tests that fail indicate either (a) the
test should be deleted as part of this removal, or (b) the edit dropped
a code path the test depended on beyond canary. Diagnose case-by-case.
```

The agent reads the current file, reasons about control flow, and applies consistent edits regardless of drift. Two-gate completion (grep returns clean + tests pass) is the same safety net the old exact-anchor approach relied on, without the anchor-fragility.

If the agent's edit produces diffs the reviewer considers surprising (e.g., removes more than expected, renames a variable), override — but with the goal + gates pinned, most churn stays local.

- [ ] **Step 4: Remove one-time legacy migration**

Open `autoresearch/evaluate_variant.py` and locate the `_private_result_path` function's `shortlist` branch. Use an exact-anchor Edit to replace:

```python
    if kind == "shortlist":
        safe_suite_id = str(id_key).replace("/", "_")
        canonical = root / "_finalized" / f"{lane}--{safe_suite_id}.json"
        if not canonical.exists():
            # One-time migration: rename legacy path (no lane prefix) to canonical
            legacy = root / "_finalized" / f"{safe_suite_id}.json"
            if legacy.exists():
                legacy.parent.mkdir(parents=True, exist_ok=True)
                legacy.rename(canonical)
        return canonical
```

with:

```python
    if kind == "shortlist":
        safe_suite_id = str(id_key).replace("/", "_")
        return root / "_finalized" / f"{lane}--{safe_suite_id}.json"
```

Also update the function's docstring to drop the sentence about legacy-path migration (search for `If a legacy path` and remove the two-sentence fragment covering the migration behavior).

- [ ] **Step 5: Remove deprecated commands block**

Open `autoresearch/evolve.py`. Use exact-anchor Edits:

1. Delete the `_DEPRECATED_COMMANDS` dict + `_check_deprecated_commands` helper together. Anchor on the block starting with the header comment:

   ```python
   # ---------------------------------------------------------------------------
   # Deprecated command handling
   # ---------------------------------------------------------------------------

   _DEPRECATED_COMMANDS: dict[str, str] = {
   ```

   and ending after the helper:

   ```python
   def _check_deprecated_commands() -> None:
       """Check sys.argv[1] for deprecated commands and exit(2) with a message."""
       if len(sys.argv) < 2:
           return
       cmd = sys.argv[1]
       if cmd in _DEPRECATED_COMMANDS:
           print(_DEPRECATED_COMMANDS[cmd], file=sys.stderr)
           sys.exit(2)
   ```

   Delete both the header-comment section and the dict + function. Leave the following `# ---- Argument parsing ----` header in place.

2. Remove the one remaining call site. Grep the file for `_check_deprecated_commands()` and delete that line (currently a single call inside the `main` / dispatch section).

3. Run `grep -rn "_check_deprecated_commands\|_DEPRECATED_COMMANDS" autoresearch/` and confirm no hits remain.

- [ ] **Step 6: Run full test suite**

Run: `pytest tests/autoresearch/ tests/freddy/ -x -q` — expect all pass.
Run: `freddy fixture validate autoresearch/eval_suites/search-v1.json` — expect PASS (23 fixtures validated).

- [ ] **Step 7: Update documentation references**

Grep `autoresearch/README.md` and `autoresearch/GAPS.md` for `archive_cli`, `geo_verify`, `geo-verify.sh`, `canary`. Update or remove matching lines.

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "chore: delete legacy code superseded by fixture infrastructure

Removes:
- autoresearch/archive_cli.py (inspection CLI never invoked)
- autoresearch/geo_verify.py + geo-verify.sh (replaced by in-variant evaluator)
- evolve.py _DEPRECATED_COMMANDS block (grace period complete)
- evaluate_variant.py canary gate (replaced by 'freddy fixture dry-run')
- evaluate_variant.py one-time legacy path migration (April 2026)"
```

---

## Acceptance Criteria (done = all hold)

Grouped by theme for clarity.

### 1. Schema & CLI surface

- `freddy fixture --help` lists: `validate`, `list`, `envs`, `staleness`, `refresh`, `dry-run`, `discriminate` (7 subcommands)
- `freddy fixture validate autoresearch/eval_suites/search-v1.json` passes on the migrated 23-fixture suite
- `autoresearch/eval_suites/SCHEMA.md` exists and documents: manifest shape, fixture-entry fields, semver policy, env-var reference syntax, cache semantics (arg-keyed hits, holdout hard-fail), per-fixture retention override, holdout-example sentinel

### 2. Cache layer

- `~/.local/share/gofreddy/fixture-cache/` exists with at least one refreshed fixture after exercising `freddy fixture refresh`
- Cache artifact filenames follow `<source>_<data_type>__<sha1(arg)[:12]>.json`
- `freddy fixture staleness` correctly tiers fixtures into fresh / aging / stale
- `freddy fixture refresh <any fixture> --dry-run` prints a plan without fetching
- `freddy fixture refresh <any fixture>` archives prior cache as `v<version>.archive-<ts>/` before rewriting

### 3. Calibration (dry-run + discriminability)

- `freddy fixture dry-run <any fixture> --seeds 5` returns a JSON report on stdout with median + MAD + flags
- `freddy fixture discriminate <fixture_id> --variants v_a,v_b --seeds 10` emits a report with a `separable` boolean, p-value, AND `cliffs_delta`; `--seeds 5` (below MIN_SEEDS=10) is rejected at parse time
- `tests/autoresearch/test_evaluate_single_fixture.py` passes — verifies `per_seed_scores` length and no lineage/scores.json writes

### 4. Integration (cache-first + legacy deletion)

- With `FREDDY_FIXTURE_*` env vars set, `POOL=search-v1`, and a populated cache, `freddy monitor mentions`, `freddy monitor sentiment`, `freddy monitor sov`, and `freddy scrape` serve from cache without any outbound provider call (verify via network mock or stderr logs). `freddy visibility`, `freddy search-ads`, `freddy search-content` live-fetch on search pool (cache returns None → live path; acceptable because search runs with search creds).
- With `FREDDY_FIXTURE_POOL=holdout-v1` and an empty cache, ALL 7 wired commands (`mentions`, `sentiment`, `sov`, `scrape`, `visibility`, `search-ads`, `search-content`) raise `RuntimeError` rather than falling through to live fetch — this is the holdout credential-isolation guarantee
- Three deletion-target files are gone: `archive_cli.py`, `geo_verify.py`, `geo-verify.sh`
- `rg -n "canary_(scores|aborted)" autoresearch/evaluate_variant.py` returns no matches
- `rg -n "_check_deprecated_commands|_DEPRECATED_COMMANDS" autoresearch/` returns no matches

### 5. Tests pass

- Full test suite (`pytest tests/autoresearch/ tests/freddy/ -x -q`) passes

---

## Execution Options

Subagent-driven execution recommended (see sub-skill directive at top). Inline via `superpowers:executing-plans` is the alternative.

**Next after Plan A lands:** execute Plan B (`2026-04-21-003-feat-fixture-program-execution-plan.md`) — authors fixtures, runs the overfit canary, enables autonomous promotion.
