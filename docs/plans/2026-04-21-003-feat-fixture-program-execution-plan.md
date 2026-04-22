# Fixture Program Execution Plan (Plan B of 2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Use the infrastructure from Plan A to author `holdout-v1` (16 adversarial fixtures, out-of-repo), modestly expand `search-v1` (6-8 new fixtures filling coverage gaps), migrate existing search-v1 fixtures onto the new infrastructure, validate the whole design with an overfit-canary experiment, and enable autonomous promotion with a 6-gate dual-judge promotion rule.

**Architecture:** Content-heavy work driven by a shared taxonomy matrix (6-axis grid of domain × language × geography × vertical × adversarial-axis × stressed-rubric-criteria). Every fixture lands in exactly one cell and exactly one pool. Holdout lives outside the repo at `~/.config/gofreddy/holdouts/holdout-v1.json`; search expansion lands in-repo at `autoresearch/eval_suites/search-v1.json` (version-bumped to 1.1). Promotion gate requires: (1) holdout eligibility, (2) first-of-lane floor when no baseline, (3) public-delta > epsilon, (4) holdout-delta > epsilon, (5) per-fixture win-rate ≥60%, (6) cross-family secondary judge (Claude Opus 4.7) passes the same 3-delta tests.

**Tech Stack:** Plan A's `freddy fixture` CLI (`validate`, `list`, `envs`, `staleness`, `refresh`, `dry-run`, `discriminate`), Codex/gpt-5.4 judge via `freddy evaluate`, existing `evolve.sh`. No new runtime dependencies.

**Prerequisite:** **Plan A (`2026-04-21-002-feat-fixture-infrastructure-plan.md`) Phase 10 must land before Phase 2 Step 7 of this plan.** Phase 2 Step 7 uses `freddy fixture discriminate`, which is built in Plan A Phase 10 (discriminability gate). Earlier steps use commands from Plan A Phases 1–8, so Plan A Phases 1–8 are the minimum before starting Plan B Phase 2 Steps 0–6. Phase 1 of this plan (taxonomy matrix) is pure design work and can be drafted in parallel with Plan A from day one.

**Cross-plan guards (enforced in Plan A; listed here for operator awareness):**

1. Holdout cache-miss hard-fails in `try_read_cache` — see Plan A Phase 8. If that test is absent, do not run Plan B Phase 2 Step 4.
2. `--pool` must match `manifest.suite_id` on refresh/dry-run/staleness/discriminate — see Plan A.
3. Cache-first read policy is pool-dependent (Plan A Phase 8). For **search pool**: geo-scrape + monitoring are cache-first; competitive and storyboard live-fetch (acceptable — search sessions run with search-side creds). For **holdout pool**: ALL 7 session-invoked commands are cache-first with cache-miss hard-fail; this provides the holdout credential-isolation guarantee. Phase 4 Step 1 refreshes all domains for both pools; holdout sessions must hit cache for every command or abort.
4. Content-hash drift detection: `DataSourceRecord.content_sha1` is populated on refresh; `_run_source_fetch` compares against prior artifact bytes and calls `log_event(kind="content_drift", ...)` (see Phase 0a events log) when the pair diverges beyond threshold (Plan A amendment, referenced from Phase 4 Step 1 below).

**Accepted risks:**

- Monitoring content drift — see Phase 5 timing constraint.
- Compromised upstream fixture URL — URL content is hashed on refresh and compared on next refresh; >20% hash delta on an anchor fixture raises a warning (see Phase 4 Step 1).

**Mitigated (not accepted):**

- Provider-side telemetry and holdout credential exfiltration: holdout refresh runs on **process-boundary-isolated infrastructure** — a GitHub Action or dedicated VM (see Phase 2 Step 9f Options A/B) that the proposer process never accesses. The evolution machine only ever receives refreshed cache artifacts, never the credentials. Local-dev (Option C) retains a same-UID wrapper as a documented trust-boundary shortcut, usable only when the operator retains full visibility into every variant generated.

**Out of scope (separate initiatives, not postponed):** MAD confidence scoring, `lane_checks.sh` gates, lane scheduling rework, IRT benchmark-health dashboard, full MT-Bench-style judge-calibration harness (note: basic judge-drift detection against a fixed calibration anchor IS in scope — see Phase 4 Step 3b), pinned-history snapshot cache (blocked by 30-90 day provider retention; not deferrable — holdout-v2 bump waits on infrastructure that doesn't exist in any provider). Cross-family judge and per-fixture win-rate, previously out-of-scope, are NOW included here — see Phase 6 Steps 3b/3c.

---

## File Structure

**New files (in repo):**
- `docs/plans/fixture-taxonomy-matrix.md` — 6-axis matrix with all fixtures placed
- `autoresearch/eval_suites/TAXONOMY.md` — concise living index pointing at the matrix
- `autoresearch/eval_suites/holdout-v1.json.example` — redacted reference copy of holdout manifest (NOT loaded)
- `docs/plans/overfit-canary-results.md` — experiment log from Phase 5

**New files (in repo):**
- `.github/workflows/holdout-refresh.yml` — CI-side holdout refresh (Phase 2 Step 9f Option A)

**New files (out of repo, never committed):**
- `~/.config/gofreddy/holdouts/holdout-v1.json` — real holdout manifest (600 perms)
- `~/.local/share/gofreddy/fixture-cache/holdout-v1/...` — cache entries per holdout fixture
- `~/.local/share/gofreddy/fixture-cache/search-v1/...` — cache entries for all search fixtures (existing + expansion)
- `~/.local/share/gofreddy/holdout-runs/` — existing `EVOLUTION_PRIVATE_ARCHIVE_DIR`

**Modified files:**
- `autoresearch/eval_suites/search-v1.json` — append 6-8 new fixtures, bump manifest version to `1.1`
- `autoresearch/evolve_ops.py` — strengthen `is_promotable` to require holdout beat (Phase 6)
- `autoresearch/README.md` — document new 2-condition promotion rule
- `autoresearch/GAPS.md` — mark Gaps 2, 3, 18 as partially addressed

---

## Phase 0: Judge Determinism Probe (Load-Bearing Prerequisite)

**Purpose:** The scoring judge's nondeterminism is load-bearing — discriminability's rank-sum test and the promotion-judge agent's per-fixture reasoning both assume repeated scoring of the same (variant, fixture) pair produces distinct samples with nonzero variance. If the underlying scoring judge provider caches responses or is fully deterministic, MAD collapses to 0 and every downstream signal becomes meaningless. Validate empirically before relying on any noise-based signal.

**Blocking:** if this probe fails, Phases 2-6 cannot proceed as designed. Halt, revisit the seed mechanism, or switch to a judge backend that demonstrably produces distinct samples.

**Files:**
- Create: `tests/autoresearch/test_judge_determinism_probe.py`
- Create: `docs/plans/judge-determinism-probe.md` (record results)
- Modify: `autoresearch/eval_suites/SCHEMA.md` (pin "seed" semantics; written by Plan A Phase 9 — add amendment here)

- [ ] **Step 1: Probe script**

Create `tests/autoresearch/test_judge_determinism_probe.py`:

```python
"""Judge determinism probe (Plan B Phase 0).

Runs `evaluate_single_fixture` twice with seeds=5 on the same (variant,
fixture) pair and asserts nonzero MAD in at least one run AND nonzero
variance of MAD across the two runs. A MAD of 0 means the judge/provider
is returning cached or perfectly deterministic responses — every downstream
noise threshold in this plan is defeated.
"""
import json
import statistics
import subprocess
import sys
from pathlib import Path


def test_judge_produces_distinct_samples_at_fixed_input():
    """Invariant: joint variant+judge sampling produces nonzero MAD.

    MAD == 0 across 5 seeds means the judge is deterministic/cached; every
    downstream noise-based signal silently becomes invalid. This is a
    boolean invariant — no agent, no interpretation.
    """
    import json
    from pathlib import Path
    manifest_payload = json.loads(Path("autoresearch/eval_suites/search-v1.json").read_text())
    # First anchor geo fixture; first v*-prefixed archive dir. If the operator's
    # state differs (no anchors yet, empty archive), the probe halts — operator
    # picks a target manually.
    geo = [fx for fx in manifest_payload["domains"]["geo"] if fx.get("anchor")]
    assert geo, "no anchor geo fixture available — run probe manually"
    fixture_id = geo[0]["fixture_id"]
    variants = sorted(
        d.name for d in Path("autoresearch/archive").iterdir()
        if d.is_dir() and d.name.startswith("v")
    )
    assert variants, "no variants in autoresearch/archive"
    variant = variants[len(variants) // 2]

    def run_once() -> list[float]:
        result = subprocess.run([
            sys.executable, "autoresearch/evaluate_variant.py",
            "--single-fixture", f"search-v1:{fixture_id}",
            "--manifest", "autoresearch/eval_suites/search-v1.json",
            "--seeds", "5", "--baseline-variant", variant, "--json-output",
        ], capture_output=True, text=True, check=True)
        return list(json.loads(result.stdout.strip().splitlines()[-1])["per_seed_scores"])

    run_a, run_b = run_once(), run_once()

    def mad(xs: list[float]) -> float:
        med = statistics.median(xs)
        return statistics.median(abs(x - med) for x in xs)

    assert mad(run_a) > 0.0 or mad(run_b) > 0.0, f"both MAD=0 (run_a={run_a}, run_b={run_b})"
    assert run_a != run_b, f"identical runs — provider caching responses: {run_a}"
```

- [ ] **Step 2: Run probe + record result**

Run: `pytest tests/autoresearch/test_judge_determinism_probe.py -v`

**Expected:** PASS with observed MAD values recorded. Typical expectation: MAD in `[0.03, 0.20]` per run. If MAD=0 or runs identical: halt.

- [ ] **Step 3: Pin seed semantics in SCHEMA.md**

Plan A Phase 9 creates `autoresearch/eval_suites/SCHEMA.md`. Append (or file as an amendment to Plan A if SCHEMA.md is not yet written):

```markdown
## Seeds Semantics (Plan B Phase 0)

In this plan, `--seeds N` ALWAYS means "run the variant N independent times
with distinct `AUTORESEARCH_SEED` env vars, score each session once, report
N scores." This captures joint variant + judge variance.

This is NOT "score the same artifact N times." The previous spec
("judge N times on one artifact") was abandoned because `freddy evaluate
critique` takes no seed/nonce and provider response caching would collapse
MAD to zero — see Plan A Phase 7 Seeds semantics section.

**Load-bearing assumption verified at Phase 0 probe:** `MAD > 0` across
two 5-seed runs of the same (variant, fixture) pair. If a future judge
migration (different backend, different model, aggressive caching) makes
this no longer true, the noise-threshold machinery silently becomes
non-functional. Re-run the Phase 0 probe on every judge backend or model
migration.
```

- [ ] **Step 4: Commit**

```bash
git add tests/autoresearch/test_judge_determinism_probe.py docs/plans/judge-determinism-probe.md
git commit -m "test(autoresearch): Phase 0 judge determinism probe (blocks downstream noise gates)"
```

---

## Phase 0a: Unified Events Log

All autonomous-decision trails and signal streams (promotion decisions, rollback checks, judge drift, content drift, saturation cycles, judge raw calls, URL drift) land in ONE append-only log: `~/.local/share/gofreddy/events.jsonl`. Every line is `{timestamp, kind, ...data}`. Downstream tools filter with `jq 'select(.kind == "promotion_decision")'`.

**Canonical helper in `autoresearch/events.py`:**

```python
"""Unified event log for all autonomous-decision trails and signal streams."""
from __future__ import annotations
import json, os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EVENTS_LOG = Path.home() / ".local/share/gofreddy/events.jsonl"


def log_event(kind: str, **data: Any) -> None:
    """Append one JSONL event with durability. All gofreddy decisions/signals use this."""
    record = {"timestamp": datetime.now(timezone.utc).isoformat(), "kind": kind, **data}
    EVENTS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with EVENTS_LOG.open("a") as handle:
        handle.write(json.dumps(record) + "\n")
        handle.flush()
        try:
            os.fsync(handle.fileno())
        except OSError:
            pass
```

**Event kinds used in this plan:** `promotion_decision`, `regression_check`, `saturation_cycle`, `judge_drift`, `judge_raw`, `content_drift`. Each replaces a previously-separate JSONL file.

**Exception kept separate:** `~/.local/share/gofreddy/head-scores.jsonl` — the promotion-judge reads this log frequently during rollback checks; keeping it a narrow stream avoids jq-filtering a growing mixed log on every run. All other recurring per-event streams consolidate into `events.jsonl`.

---

## Phase 0b: Decision-Judge Agent Roles

**Purpose:** Replace hardcoded quality/promotion thresholds (dry-run flags, saturation, judge drift, URL drift, promotion gates, rollback triggers, canary GO/FAIL) with two AI agents that consume raw measurements and return reasoned decisions. Thresholded interpretations of noise are judgment calls; baking them as constants creates brittle autonomous behavior that can't adapt to regime changes. The statistical *measurements* (MAD, IQR, Wilcoxon, Mann-Kendall, per-fixture win-rate, trajectory diffs) stay programmatic — they're honest numbers. The *interpretation* is delegated.

**Two roles, two CLI commands:**

- `freddy evaluate quality-judge` — advisory decisions (fixture quality, saturation, calibration drift, URL drift, noise-escalation recommendations). Runs dozens of times per week. Low stakes (outputs advisory verdicts an operator or upstream automation consumes).
- `freddy evaluate promotion-judge` — autonomous decisions (promotion, rollback, canary GO/FAIL). Runs ~1-10 times/day. High stakes (drives autonomous lane-head changes).

**Backing models:**

- `quality-judge` uses `claude-opus-4-7` (Anthropic). No cross-family requirement — it's advisory.
- `promotion-judge` uses `claude-opus-4-7` deliberately from a DIFFERENT family than the primary scoring judge (`gpt-5.4`). Preserves the cross-family-judge property from the earlier design: a variant that games the gpt-5.4 scorer still has to pass a Claude-based promotion decision, reducing single-family gaming risk.

**Files:**
- Create: `cli/freddy/commands/evaluate.py` additions — `quality_judge_command`, `promotion_judge_command`
- Create: `autoresearch/judges/quality_judge.py` — prompt template + invocation helper
- Create: `autoresearch/judges/promotion_judge.py` — prompt template + invocation helper
- Create: `tests/autoresearch/test_judges.py` — mocked-response tests (no live API)

- [ ] **Step 1: Write failing tests (mocked agent responses)**

Create `tests/autoresearch/test_judges.py`:

```python
"""Judge-agent interface tests. Mock httpx.post; test wiring + payload + response parsing.

Under the Phase 0c HTTP-client architecture, tests mock the HTTP transport
(httpx.post), not an in-process model-invocation function. This tests the
CLIENT's contract: does it POST to the right URL with the right bearer
token, and does it parse the response correctly?
"""
import json
from unittest.mock import patch, MagicMock

import pytest

from autoresearch.judges.quality_judge import call_quality_judge, QualityVerdict
from autoresearch.judges.promotion_judge import call_promotion_judge, PromotionVerdict


def _mock_http_response(body: str, status_code: int = 200) -> MagicMock:
    """Build a minimal httpx.Response stand-in that raise_for_status() + .json() work on."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.raise_for_status = MagicMock()
    resp.json = MagicMock(return_value=json.loads(body))
    resp.text = body
    return resp


def test_quality_judge_returns_verdict_with_reasoning():
    payload = {
        "role": "fixture_quality",
        "fixture_id": "geo-bmw-ev-de",
        "stats": {"median": 0.92, "mad": 0.03, "cost_usd": 0.12, "per_seed_scores": [0.90, 0.92, 0.93, 0.91, 0.94]},
    }
    mock_response = json.dumps({
        "verdict": "saturated",
        "reasoning": "Median 0.92 is near ceiling; low MAD means consistent ceiling. Fixture is too easy.",
        "confidence": 0.85,
        "recommended_action": "rotate_out_next_cycle",
    })
    with patch("httpx.post", return_value=_mock_http_response(mock_response)):
        result = call_quality_judge(payload)
    assert isinstance(result, QualityVerdict)
    assert result.verdict == "saturated"
    assert "ceiling" in result.reasoning.lower()
    assert 0.0 <= result.confidence <= 1.0


def test_promotion_judge_promote_when_signals_coherent():
    payload = {
        "role": "promotion",
        "candidate_id": "v007", "baseline_id": "v006", "lane": "geo",
        "public_scores": {"candidate": 0.72, "baseline": 0.65},
        "holdout_scores": {"candidate": 0.62, "baseline": 0.55},
        "per_fixture": {  # {fixture_id: {"candidate": float, "baseline": float}}
            "geo-a": {"candidate": 0.75, "baseline": 0.60},
            "geo-b": {"candidate": 0.70, "baseline": 0.65},
            # ... N fixtures
        },
        "secondary_public_scores": {"candidate": 0.70, "baseline": 0.64},
        "secondary_holdout_scores": {"candidate": 0.61, "baseline": 0.54},
    }
    mock = json.dumps({
        "decision": "promote",
        "reasoning": "Public +0.07, holdout +0.07, both judges agree direction and magnitude, per-fixture wins dominate.",
        "confidence": 0.88,
        "concerns": [],
    })
    with patch("httpx.post", return_value=_mock_http_response(mock)):
        result = call_promotion_judge(payload)
    assert isinstance(result, PromotionVerdict)
    assert result.decision == "promote"


def test_promotion_judge_rejects_on_single_judge_disagreement():
    payload = {
        "role": "promotion", "candidate_id": "v008", "baseline_id": "v006", "lane": "geo",
        "public_scores": {"candidate": 0.70, "baseline": 0.60},
        "holdout_scores": {"candidate": 0.58, "baseline": 0.55},
        "per_fixture": {"geo-a": {"candidate": 0.95, "baseline": 0.50}, "geo-b": {"candidate": 0.55, "baseline": 0.55}},
        "secondary_public_scores": {"candidate": 0.60, "baseline": 0.60},  # secondary says no improvement
        "secondary_holdout_scores": {"candidate": 0.55, "baseline": 0.55},
    }
    mock = json.dumps({
        "decision": "reject",
        "reasoning": "Primary and secondary judges disagree; single-fixture dominance suggests gaming.",
        "confidence": 0.82,
        "concerns": ["cross_family_disagreement", "uneven_per_fixture_wins"],
    })
    with patch("httpx.post", return_value=_mock_http_response(mock)):
        result = call_promotion_judge(payload)
    assert result.decision == "reject"
    assert "cross_family_disagreement" in result.concerns


def test_promotion_judge_rollback_decision():
    payload = {
        "role": "rollback", "lane": "geo",
        "current_head": "v010", "prior_head": "v006",
        "head_scores_log": [  # recent head-scores.jsonl entries
            {"timestamp": "...", "head_id": "v006", "public_score": 0.65, "holdout_score": 0.55},
            {"timestamp": "...", "head_id": "v010", "public_score": 0.58, "holdout_score": 0.49},
            {"timestamp": "...", "head_id": "v010", "public_score": 0.55, "holdout_score": 0.48},
            {"timestamp": "...", "head_id": "v010", "public_score": 0.53, "holdout_score": 0.47},
        ],
    }
    mock = json.dumps({
        "decision": "rollback",
        "reasoning": "Three consecutive post-promotion scores regress below prior-head baseline; monotonic decline suggests bad promotion.",
        "confidence": 0.91,
        "concerns": [],
    })
    with patch("httpx.post", return_value=_mock_http_response(mock)):
        result = call_promotion_judge(payload)
    assert result.decision == "rollback"


def test_promotion_judge_canary_go_decision():
    payload = {
        "role": "canary", "mode": "go_fail", "lane": "geo",
        "checkpoints": [  # 10 entries, one per checkpoint
            {"iter": 2, "public_median": 0.50, "holdout_median": 0.45, "divergence": 0.05},
            # ... 10 rows
        ],
        "mann_kendall": {"tau": 0.93, "one_sided_p": 0.0003},
        "pre_canary_sanity": {"known_pair_delta": 0.12},
    }
    mock = json.dumps({
        "decision": "go",
        "reasoning": "Divergence trends up monotonically (tau=0.93, p<0.001); holdout clearly slower than public. Pre-canary sanity passed.",
        "confidence": 0.93,
        "concerns": [],
    })
    with patch("httpx.post", return_value=_mock_http_response(mock)):
        result = call_promotion_judge(payload)
    assert result.decision == "go"
```

Run: expect FAIL (modules don't exist).

- [ ] **Step 2: Implement the two judge modules**

Create `autoresearch/judges/quality_judge.py`:

```python
"""Quality-judge agent: advisory decisions about fixture quality, saturation, drift."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class QualityVerdict:
    verdict: str                 # fixture_quality: healthy|saturated|degenerate|unstable|cost_excess
                                 # saturation: rotate_now|rotate_soon|fine
                                 # calibration_drift: stable|magnitude_drift|variance_drift|reasoning_drift|mixed
                                 # content_drift: material|cosmetic|unknown
                                 # discriminability: separable|not_separable|insufficient_data
                                 # noise_escalation: sufficient|bump_seeds|bump_iterations
    reasoning: str
    confidence: float  # [0, 1]
    recommended_action: str | None = None


# PROMPT TEMPLATES LIVE ON THE JUDGE-SERVICE (judges/evolution/prompts/quality.md)
# — NOT in autoresearch-side code. See Plan A Phase 0c for isolation rationale.
# This autoresearch-side module is a thin HTTP client; it knows nothing about
# how the judge decides, only how to ask it.


import httpx, os

EVOLUTION_JUDGE_URL = os.environ.get("EVOLUTION_JUDGE_URL", "http://localhost:7200")
EVOLUTION_INVOKE_TOKEN = os.environ.get("EVOLUTION_INVOKE_TOKEN", "")


_SYSTEM_HEALTH_ROLES = {
    "saturation", "content_drift", "discriminability",
    "fixture_quality", "calibration_drift", "noise_escalation",
}


def call_quality_judge(payload: dict[str, Any]) -> QualityVerdict:
    """POST to evolution-judge-service /invoke/system_health/{role} and parse verdict.

    Dispatches to the single unified `system_health_agent` on the judge service
    via role-in-URL routing. All advisory / meta concerns go through this client.
    """
    role = payload.get("role")
    if role not in _SYSTEM_HEALTH_ROLES:
        raise ValueError(f"invalid system_health role: {role!r}")
    r = httpx.post(
        f"{EVOLUTION_JUDGE_URL}/invoke/system_health/{role}", json=payload,
        headers={"Authorization": f"Bearer {EVOLUTION_INVOKE_TOKEN}"}, timeout=300,
    )
    r.raise_for_status()
    data = r.json()
    return QualityVerdict(
        verdict=str(data["verdict"]),
        reasoning=str(data.get("reasoning", "")),
        confidence=float(data.get("confidence", 0.5)),
        recommended_action=data.get("recommended_action"),
    )
```

Create `autoresearch/judges/promotion_judge.py`:

```python
"""Promotion-judge agent: autonomous decisions about promote, rollback, canary GO/FAIL.

Cross-family by design: uses claude-opus-4-7 (Anthropic) while the primary
scoring judge uses gpt-5.4 (OpenAI). A variant that games the scoring judge
still has to pass a Claude-based promotion decision.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PromotionVerdict:
    decision: str                 # promotion: promote | reject
                                  # rollback: rollback | hold
                                  # canary: go | fail | revise
                                  #         (or checkpoint | skip | early_terminate_go
                                  #          | early_terminate_fail when mode=checkpoint_schedule)
    reasoning: str
    confidence: float             # [0, 1]
    concerns: list[str] = field(default_factory=list)


# PROMPT TEMPLATE LIVES ON THE JUDGE-SERVICE (judges/evolution/prompts/promotion.md)
# — NOT in autoresearch-side code. Cross-family role (Claude Opus 4.7) is
# enforced at the judge-service side via codex-vs-claude selection, not here.


import httpx, os

EVOLUTION_JUDGE_URL = os.environ.get("EVOLUTION_JUDGE_URL", "http://localhost:7200")
EVOLUTION_INVOKE_TOKEN = os.environ.get("EVOLUTION_INVOKE_TOKEN", "")


_DECISION_ROLES = {"promotion", "rollback", "canary"}


def call_promotion_judge(payload: dict[str, Any]) -> PromotionVerdict:
    """POST to evolution-judge-service /invoke/decide/{role} and parse verdict.

    Role routes to one of the 3 dedicated decision agents:
      - promotion → promotion_agent.py (promote | reject)
      - rollback  → rollback_agent.py  (rollback | hold)
      - canary    → canary_agent.py    (go | fail | revise, or checkpoint-schedule
                                         via payload.mode="checkpoint_schedule")
    """
    role = payload.get("role", "promotion")
    if role not in _DECISION_ROLES:
        raise ValueError(f"invalid decision role: {role!r}")
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
```

- [ ] **Step 3: Run tests and commit**

Judge invocation plumbing (CLI subcommands, HTTP services, prompt files) lives in Plan A Phase 0c; this step verifies the autoresearch-side clients call the right endpoints.

Run: `pytest tests/autoresearch/test_judges.py -v` — expect all PASS. Tests mock `httpx.post` (not an in-process `_invoke_model`) to verify `call_promotion_judge` POSTs to `${EVOLUTION_JUDGE_URL}/invoke/decide/{promotion|rollback|canary}` and `call_quality_judge` POSTs to `${EVOLUTION_JUDGE_URL}/invoke/system_health/{role}` with the right bearer token, and both parse responses correctly.

**Audit log lives on the judge-service side** (not on autoresearch host). Autoresearch-side `events.jsonl` still records `kind="promotion_decision"` etc. with the verdict but not the full reasoning — the full reasoning with prompt context lives on the judge-service's own events log, inaccessible to autoresearch processes. This is a feature: a worker agent can see "judge said promote" but can't exfiltrate "judge said promote because of <reasoning that would let me learn the rubric>."

```bash
git add autoresearch/judges/ tests/autoresearch/test_judges.py
git commit -m "feat(judges): autoresearch-side HTTP clients for quality + promotion judges (prompts live on judge-service per Plan A Phase 0c)"
```

**Cost / operational notes:**
- Quality-judge: ~30-40 calls/week. At ~$0.01-0.05 per Claude Opus 4.7 CLI invocation via subscription (amortized against fixed monthly fee), this is effectively free above the subscription.
- Promotion-judge: ~1-10 calls/day + ~1/week rollback + 1 canary GO/FAIL per holdout version. Same subscription-amortized cost.
- All judge calls go through `claude` CLI on the evolution-judge-service host. Autoresearch host has no Anthropic credentials (API key removed from env per Phase 0c). If the subscription is rate-limited, evolution loop pauses until the judge-service 503 clears — this is the deliberate no-fallback posture.

---

## Phase 1: Fixture Taxonomy Matrix (Design Artifact)

**Purpose:** Shared design document that drives fixture authoring for both pools. Maps the design space; every fixture placed on it. Can be drafted in parallel with Plan A.

**Files:**
- Create: `docs/plans/fixture-taxonomy-matrix.md`
- Create: `autoresearch/eval_suites/TAXONOMY.md`

- [ ] **Step 1: Define the 6 axes**

In `docs/plans/fixture-taxonomy-matrix.md`, document the axes:

1. **Domain**: geo / competitive / monitoring / storyboard
2. **Language**: en / de / fr / es / pt-BR / ja / zh / mixed
3. **Geography**: US / EU / LATAM / APAC / global
4. **Vertical**: SaaS-tech / ecommerce / CPG / finance / health / automotive / media / creator-economy / enterprise-b2b
5. **Adversarial condition**: standard / paywall / SPA / thin-content / thin-ads / regulatory / multi-segment / opaque / saturated-market / low-volume / non-verbal / cultural-distance / evolving-style
6. **Stressed rubric criteria** (per-domain subset): pick 1-3 of the 8 criteria in that domain's rubric that this fixture is specifically designed to stress

Each fixture gets one value on axes 1-5 and 1-3 criteria on axis 6.

- [ ] **Step 2: Place all 23 existing search-v1 fixtures on the matrix**

Go through `autoresearch/eval_suites/search-v1.json` fixture-by-fixture. For each, determine the axis values based on the fixture's actual content (look at the context URL, client, env vars).

Output: a markdown table in the matrix doc, one row per fixture:

```markdown
| Fixture ID | Pool | Domain | Lang | Geo | Vertical | Adversarial | Stressed Criteria |
|---|---|---|---|---|---|---|---|
| geo-semrush-pricing | search-v1 | geo | en | US | SaaS-tech | standard | GEO-1, GEO-5 |
| geo-ahrefs-pricing | search-v1 | geo | en | US | SaaS-tech | standard | GEO-1, GEO-7 |
| ... (23 rows) |
```

Expected finding: existing coverage is heavily concentrated in `(en, US, SaaS-tech, standard)`. Most cells are empty.

- [ ] **Step 3: Identify coverage gaps**

In the matrix doc, enumerate:
- **Empty cells** (combinations with zero fixtures)
- **Sparse cells** (only 1 fixture)
- **Rubric criteria covered by ≤1 fixture total** (high risk of un-tested criteria)

- [ ] **Step 4: Propose fills and pool assignments**

For each empty/sparse cell worth filling, propose a fixture and tag it `→ search-v1` or `→ holdout-v1` based on the heuristic:

- **search-v1**: "This represents realistic agency work we want the system to do well on." Variants will be evaluated on this fixture during evolution.
- **holdout-v1**: "This is an adversarial probe designed to catch overfitting that wouldn't show up on search-v1." Variants are never evaluated on this during proposer iteration.

Rule: no cell appears in both pools. One fixture per cell, assigned to exactly one pool.

Target: ~6-8 new search fixtures + 16 holdout fixtures proposed.

- [ ] **Step 5: Rubric-coverage matrix**

Separately, construct a (criterion × fixture) matrix across both pools. Each domain has 8 criteria; 8 × 4 = 32 criteria total. Verify every criterion is stressed by at least 2 fixtures in the combined pool. Where gaps remain, adjust fixture proposals to close them.

- [ ] **Step 6: Create TAXONOMY.md living index (search-v1 ONLY)**

Holdout rows live out-of-repo per the File Structure section above (proposer read path = in-repo). Create `autoresearch/eval_suites/TAXONOMY.md` (~100 lines) pointing at the in-repo matrix, summarizing current search-v1 coverage and latest matrix version. Note that holdout taxonomy lives at `~/.config/gofreddy/holdouts/holdout-v1-taxonomy.md` (600).

- [ ] **Step 7: Review and commit**

Sanity-check the search-v1 matrix: every existing fixture placed, proposed fills feasible, ≥2 stressors per criterion, pool assignments defensible. The out-of-repo holdout taxonomy is not committed.

```bash
git add docs/plans/fixture-taxonomy-matrix.md autoresearch/eval_suites/TAXONOMY.md
git commit -m "docs(fixture): add taxonomy matrix + rubric coverage matrix (search-v1; holdout rows out-of-repo)"
```

---

## Phase 2: Holdout-v1 Fixture Authoring (16 fixtures)

**Purpose:** Author the real holdout manifest. Uses Plan A's infrastructure end-to-end. Each fixture goes through the full per-fixture process before being committed to the manifest.

**Files:**
- Create: `~/.config/gofreddy/holdouts/holdout-v1.json` (out of repo)
- Create: `autoresearch/eval_suites/holdout-v1.json.example` (in repo, redacted reference)
- Populate: cache at `~/.local/share/gofreddy/fixture-cache/holdout-v1/...`

**16-fixture composition (finalized from Phase 1 taxonomy):**

| # | Fixture ID | Domain | Tier | Primary axes |
|---|---|---|---|---|
| 1 | geo-bmw-ev-de | geo | anchor | lang=de, vertical=auto, geo=EU |
| 2 | geo-nubank-br-pix | geo | rotating | lang=pt-BR, vertical=fintech, geo=LATAM |
| 3 | geo-stripe-docs-gated | geo | rotating | adversarial=paywall |
| 4 | geo-rakuten-travel-spa | geo | anchor | adversarial=SPA, lang=ja, geo=APAC |
| 5 | competitive-toyota-vs-byd-ev | competitive | rotating | vertical=auto, adversarial=thin-ads |
| 6 | competitive-nubank-vs-latam-banks | competitive | rotating | lang=multi, geo=LATAM, vertical=fintech |
| 7 | competitive-opaque-private-b2b | competitive | anchor | adversarial=opaque |
| 8 | competitive-axios-vs-semafor | competitive | anchor | vertical=media, adversarial=saturated |
| 9 | monitoring-unilever-cpg | monitoring | rotating | vertical=CPG |
| 10 | monitoring-deutsche-bank | monitoring | rotating | geo=EU, vertical=finance, regulatory |
| 11 | monitoring-twitch-low-volume | monitoring | anchor | adversarial=low-volume |
| 12 | monitoring-tsmc-apac | monitoring | anchor | lang=zh+en, geo=APAC, vertical=hardware |
| 13 | storyboard-tokyo-creative-ja | storyboard | anchor | lang=ja, adversarial=cultural-distance |
| 14 | storyboard-amixem-fr | storyboard | rotating | lang=fr |
| 15 | storyboard-music-creator-nonverbal | storyboard | anchor | adversarial=non-verbal |
| 16 | storyboard-pivoting-creator | storyboard | rotating | adversarial=evolving-style |

**Data-feasibility reminder from the data-dependency audit:** use `AUTORESEARCH_WEEK_RELATIVE=most_recent_complete` for ALL monitoring fixtures. Pinned historical fixtures are NOT viable — source retention is 30-90 days. Pinned-history support is blocked on a snapshot-cache infrastructure that doesn't currently exist in any provider; when that lands (separate initiative), holdout-v2 adds pinned fixtures. Not a decision to defer — an infrastructure limit.

**Per-fixture process:** run as a documented agent task (see Step A below). The 16-fixture loop becomes: bootstrap manifest (Step 0), wire sampler (Step 0b), dispatch an authoring agent 16 times (Step A), commit example + wire secrets (remaining steps). No new CLI command — the agent invokes the existing `freddy fixture {validate, envs, refresh, dry-run, discriminate}` primitives.

- [ ] **Step 0: Bootstrap the empty holdout manifest (once, before the first fixture)**

Before iterating 16 times, create the empty shell of `~/.config/gofreddy/holdouts/holdout-v1.json` with suite-level metadata. Step 6's append-fixture operation assumes the file exists with the right shape.

```bash
mkdir -p ~/.config/gofreddy/holdouts
cat > ~/.config/gofreddy/holdouts/holdout-v1.json <<'EOF'
{
  "suite_id": "holdout-v1",
  "version": "1.0",
  "eval_target": {
    "backend": "codex",
    "model": "gpt-5.4",
    "reasoning_effort": "high"
  },
  "rotation": {
    "strategy": "stratified",
    "anchors_per_domain": 2,
    "random_per_domain": 1,
    "seed_source": "generation"
  },
  "domains": {
    "geo": [],
    "competitive": [],
    "monitoring": [],
    "storyboard": []
  }
}
EOF
chmod 600 ~/.config/gofreddy/holdouts/holdout-v1.json
```

Then the per-fixture loop below appends into the appropriate `domains.<domain>` array during Step 6.

**Rotation math (per cycle, per variant):** 2 anchors + 1 random per domain × 4 domains = 12 fixtures (out of 16). Anchor set is fixed; rotating set cycles through the 8 rotating fixtures via deterministic PRF seeded on `variant_id`. This cuts holdout wall-time by ~25% per variant while preserving the 8-anchor stability guarantee.

- [ ] **Step 0b: Wire `_sample_fixtures` into `_run_holdout_suite` (Plan A amendment)**

`evaluate_variant._run_holdout_suite` (currently lines 1165-1201) iterates all fixtures per domain with no sampling. `evaluate_search` already has the right pattern at lines 1369-1371 — replicate it.

Edit `autoresearch/evaluate_variant.py::_run_holdout_suite` to apply the stratified sampler when the manifest specifies rotation:

```python
# Inside _run_holdout_suite, after loading fixtures_by_domain, before scoring:
rotation_config = suite_manifest.get("rotation")
if isinstance(rotation_config, dict) and rotation_config.get("strategy") == "stratified":
    fixtures_by_domain = _sample_fixtures(fixtures_by_domain, rotation_config, variant_id)
```

Add a test `tests/autoresearch/test_holdout_manifest_guards.py::test_holdout_applies_rotation_when_configured` that constructs a 16-fixture manifest with the rotation block, invokes `_run_holdout_suite` for two distinct variant_ids, and asserts (a) each run evaluates 12 fixtures (not 16), (b) the anchor set is stable across runs, (c) the random set differs across runs.

**Why this matters (feasibility):** Without sampling, every holdout sweep runs all 16 fixtures sequentially — 16 × (15 × 1200 + 180) ≈ 80 hours worst-case per variant, ~45-60 min expected-case per variant. With sampling: 12 × same ≈ 45 min expected-case, making the 2-week Phases 4-5 budget actually achievable. Without this wiring, the rotation config is decorative metadata that does nothing at runtime — a correctness-vs-documentation mismatch a later maintainer would waste hours chasing.

**Rotation partition is adaptive, not static.** Initial partition (8 anchors + 8 rotating, from the Phase 1 taxonomy) is the bootstrap; after observation, the partition should respond to data. Monthly, run `freddy fixture rotation-policy --pool holdout-v1` which invokes the system-health agent (role: `saturation`, `mode: "rotation_proposal"`). The judge reads (a) the saturation log (`~/.local/share/gofreddy/saturation-log.jsonl` — though it only tracks public fixtures for now; extend to holdout if monthly data warrants), (b) the discriminability-check history per holdout fixture (cache from Phase 2 Step 7 across cycles), and (c) the current anchor/rotating partition. Judge returns `{proposed_anchors: [fixture_id,...], proposed_rotating: [fixture_id,...], anchors_per_domain: int, random_per_domain: int, reasoning: str}`. Operator reviews, commits the updated manifest if convincing. Fixtures that consistently show highest discriminability and lowest MAD over 3+ months stabilize into the anchor set; saturated or low-signal fixtures rotate out.

```python
# cli/freddy/commands/fixture.py::rotation_policy_cmd
@app.command("rotation-policy")
def rotation_policy_cmd(
    pool: str = typer.Option(..., "--pool"),
    apply: bool = typer.Option(False, "--apply", help="Write proposed partition to manifest."),
) -> None:
    """Ask quality-judge to propose anchor/rotating partition based on observed data."""
    from autoresearch.judges.quality_judge import call_quality_judge
    # Gather: saturation log, per-fixture discriminability history, current partition
    payload = _gather_rotation_evidence(pool)
    # Rotation-partition proposal is a saturation-driven decision (which fixtures
    # have saturated vs still carry signal). The prompt dispatches on `mode`.
    verdict = call_quality_judge({"role": "saturation", "mode": "rotation_proposal", **payload})
    typer.echo(f"Verdict: {verdict.verdict}")
    typer.echo(f"Reasoning: {verdict.reasoning}")
    if apply and verdict.recommended_action:
        _update_manifest_partition(pool, verdict.recommended_action)
        typer.echo("✓ manifest partition updated")
```

- [ ] **Step A: Dispatch a fixture-authoring agent per fixture (no new CLI command)**

Per-fixture authoring is an orchestration task, not a reusable CLI. An authoring agent reads the scratch spec, drives the existing `freddy fixture {validate, envs, refresh, dry-run, discriminate}` primitives, calls the system-health agent at the health-decision point, and atomically appends to the manifest on a `healthy` verdict. The agent handles edge cases (env-var gaps, partial refresh state, duplicate ids) via reasoning, not rigid branches.

**Authoring agent task spec** (`docs/agent-tasks/author-holdout-fixture.md`):

```
GOAL: author one holdout-v1 fixture end-to-end from a scratch spec JSON.
      Either append to the target manifest on `healthy` verdict, or halt
      with a revision recommendation.

INPUTS:
  - fixture_id (string)
  - spec_path (path to scratch one-fixture manifest)
  - pool=holdout-v1, manifest_path, baseline=v006, seeds=5
  - discriminate_against (two pinned variants, e.g. "v001,v020")

STEPS (use reasoning for recovery, not rigid branches):
  1. `freddy fixture validate --spec <spec_path>` — fail fast on schema.
  2. `freddy fixture envs --spec <spec_path> --missing` — refuse with clear
     diagnostic if any vars are unset.
  3. `freddy fixture refresh --pool <pool> --fixture <id> --dry-run` for cost;
     then actual refresh.
  4. `freddy fixture dry-run <spec_path> --seeds <seeds> --baseline <baseline>`
     — collect median/MAD/cost/per-seed scores.
  5. `freddy fixture discriminate <id> --variants <discriminate_against>
     --seeds 10` — emits Wilcoxon p + Cliff's delta + raw distributions.
  6. POST to evolution-judge-service `/invoke/system_health/fixture_quality`
     with all evidence. Verdict ∈ {healthy, saturated, degenerate, unstable,
     cost_excess, needs_revision}.
  7. On `healthy`: atomically append spec to target manifest. Otherwise
     print verdict + reasoning, leave manifest untouched, exit non-zero.

EDGE CASES TO RECOVER FROM (without human intervention unless truly stuck):
  - partial refresh state from a prior attempt → decide reuse vs re-fetch
    based on cache age + content hash (ask system_health `content_drift`)
  - mid-pipeline failure → leave manifest untouched, report state
  - duplicate fixture_id → refuse; require explicit operator override

IDEMPOTENCY: re-running against the same fixture_id is safe if the prior
  run left the manifest untouched. If the manifest already contains the id,
  refuse without an explicit overwrite flag in the prompt.
```

Per-fixture invocation:

```bash
cat > /tmp/fixture-draft.json <<'EOF'
{"suite_id": "holdout-v1", "version": "1.0", "domains": {"geo": [{
  "fixture_id": "geo-bmw-ev-de", "client": "bmw",
  "context": "https://www.bmw.de/.../elektromobilitaet.html",
  "version": "1.0", "max_iter": 15, "timeout": 1200,
  "anchor": true, "env": {}
}]}}
EOF

# Dispatch the authoring agent (claude --print with the task spec above
# and the per-fixture inputs). The agent orchestrates existing primitives;
# no new CLI command is required.
claude --print --input-file docs/agent-tasks/author-holdout-fixture.md \
  --var fixture_id=geo-bmw-ev-de \
  --var spec_path=/tmp/fixture-draft.json \
  --var pool=holdout-v1 \
  --var manifest_path=~/.config/gofreddy/holdouts/holdout-v1.json \
  --var baseline=v006 --var seeds=5 --var discriminate_against=v001,v020
```

Run 16 times, once per row in the 16-fixture composition table above. Anchor/rotating split is carried by the `anchor: true/false` field in each spec.

**Why agent task, not CLI:** the pipeline has recovery-worthy edge cases (stale partial cache, env-var gaps, mid-pipeline failure). An agent reasons about whether pre-existing cache is reusable; a CLI with `if`-branches can't. The pipeline also runs ~16 times total — the amortization argument for a reusable CLI doesn't hold.

- [ ] **Step 8: Create redacted example file**

After all 16 fixtures are in `holdout-v1.json`, create `autoresearch/eval_suites/holdout-v1.json.example` as a redacted copy (mask brand names and private URLs; include `"is_redacted_example": true` at the top level as the loader-refusal sentinel). Reference only — never loaded.

- [ ] **Step 9: Set env wiring, exclude holdout dirs from backup/sync, and enforce holdout safety in code**

**9a. Shell profile env wiring.** Add to your shell profile (`~/.zshrc` or equivalent):

```bash
export EVOLUTION_HOLDOUT_MANIFEST=~/.config/gofreddy/holdouts/holdout-v1.json
export EVOLUTION_PRIVATE_ARCHIVE_DIR=~/.local/share/gofreddy/holdout-runs
```

**9b. File permissions on first create.**

```bash
chmod 600 ~/.config/gofreddy/holdouts/holdout-v1.json
chmod 700 ~/.config/gofreddy/holdouts/
chmod 700 ~/.local/share/gofreddy/holdout-runs/
chmod 700 ~/.local/share/gofreddy/fixture-cache/holdout-v1/  # created by first `freddy fixture refresh`
```

**9c. Exclude from backup/sync daemons.** 600 perms stop other local users, not backup/sync agents running as the same user. Add exclusions for each tool present on this machine:

```bash
# macOS Time Machine (immediate effect)
sudo tmutil addexclusion ~/.config/gofreddy/holdouts
sudo tmutil addexclusion ~/.local/share/gofreddy/holdout-runs
sudo tmutil addexclusion ~/.local/share/gofreddy/fixture-cache/holdout-v1

# Spotlight index (reduces search-leak surface)
touch ~/.config/gofreddy/holdouts/.metadata_never_index
touch ~/.local/share/gofreddy/holdout-runs/.metadata_never_index

# Generic cache-aware backup tools honor CACHEDIR.TAG
cat > ~/.local/share/gofreddy/fixture-cache/holdout-v1/CACHEDIR.TAG <<'EOF'
Signature: 8a477f597d28d172789f06886806bc55
# This file marks the directory as a cache; back-up tools that honor
# CACHEDIR.TAG (restic, borg, many cloud-backup agents) will skip it.
EOF

# iCloud Drive / Dropbox / Syncthing / cross-machine dotfile tools:
# manually exclude the full `~/.config/gofreddy/holdouts/` path in each
# tool's settings UI. `~/.local/share/` is typically NOT iCloud-synced
# on macOS, but verify with `mdfind -name 'holdout-v1.json'` after setup.
```

Also: audit `~/.zshrc` and `~/.zprofile` etc. — if they live in a dotfile sync tool (Dropbox, chezmoi pointed at iCloud, etc.), the `EVOLUTION_HOLDOUT_MANIFEST=~/.config/gofreddy/...` export line itself reveals the path to any agent that can read those files. Consider keeping the export in a non-synced file (e.g., `~/.zshrc.local` sourced from `~/.zshrc`).

**9d. Provider-side telemetry:** mitigated by 9f (dedicated holdout credentials separate from evolution runs). See header "Mitigated (not accepted)" for the trust boundary.

**9e. Enforce it in code so misconfiguration cannot silently leak holdout context.** Modify `autoresearch/evaluate_variant.py:_load_holdout_manifest` (line 282) to add three guards before it returns a manifest:

```python
def _load_holdout_manifest(env: dict[str, str], lane: str = "core") -> dict[str, Any] | None:
    lane = normalize_lane(lane)
    manifest_path_str = env.get("EVOLUTION_HOLDOUT_MANIFEST", "").strip()
    if not manifest_path_str:
        return None

    # Resolve symlinks + relative parts before any check. Defeats
    # `~/holdout.json -> /repo/.../holdout-v1.json.example` symlink attacks.
    manifest_path = Path(manifest_path_str).expanduser().resolve(strict=False)

    # Guard 1: refuse the in-repo example file or any path resolving
    # inside the repo. Finds the repo root via `.git` ancestor; falls
    # back to a substring check on `eval_suites` if no `.git` is found.
    if manifest_path.name.endswith(".example"):
        raise RuntimeError(
            f"EVOLUTION_HOLDOUT_MANIFEST refuses {manifest_path} — "
            "holdout must live outside the repo. Example files are reference-only."
        )
    for ancestor in manifest_path.parents:
        if (ancestor / ".git").exists():
            raise RuntimeError(
                f"EVOLUTION_HOLDOUT_MANIFEST refuses {manifest_path} — "
                "resolved path is inside a git repo. Holdout must live outside all repos."
            )
    if "eval_suites" in manifest_path.parts:
        raise RuntimeError(
            f"EVOLUTION_HOLDOUT_MANIFEST refuses {manifest_path} — "
            "eval_suites/ is the in-repo suite directory."
        )

    # Guard 2: refuse if file permissions are looser than 600 (group or
    # world can read/write). Prevents accidental leaks via shared systems.
    if manifest_path.exists():
        import stat
        mode = manifest_path.stat().st_mode
        if mode & (stat.S_IRWXG | stat.S_IRWXO):
            raise RuntimeError(
                f"EVOLUTION_HOLDOUT_MANIFEST {manifest_path} has loose permissions "
                f"(mode {oct(mode & 0o777)}). Run: chmod 600 {manifest_path}"
            )

    payload = _load_manifest_from_path(str(manifest_path))
    if payload is None:
        return None

    # Guard 3: refuse any manifest carrying the redaction sentinel — that
    # field is set in the in-repo .json.example file and must never match
    # the real holdout manifest.
    if isinstance(payload, dict) and payload.get("is_redacted_example") is True:
        raise RuntimeError(
            f"EVOLUTION_HOLDOUT_MANIFEST refuses {manifest_path} — "
            "payload carries is_redacted_example: true. This is the example file."
        )

    return _normalize_suite_manifest(
        _project_suite_manifest_for_lane(payload, lane),
        env=env,
        source=f"holdout:{lane}",
    )
```

The `autoresearch/eval_suites/holdout-v1.json.example` file (created in Step 8) must therefore include `"is_redacted_example": true` at the top level as a sentinel. Add it.

Also add tests in `tests/autoresearch/test_holdout_manifest_guards.py`:

```python
import json
import stat
from pathlib import Path
import pytest

# Unprefixed import: autoresearch/ is on sys.path via conftest.py.
from evaluate_variant import _load_holdout_manifest


def _write_minimal_holdout(path: Path, *, redacted: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "suite_id": "holdout-v1", "version": "1.0",
        "eval_target": {"backend": "codex", "model": "gpt-5.4"},
        "domains": {"geo": [{"fixture_id": "x", "client": "c", "context": "ctx", "version": "1.0"}]},
    }
    if redacted:
        payload["is_redacted_example"] = True
    path.write_text(json.dumps(payload))
    path.chmod(0o600)


def _env(manifest_path: Path) -> dict[str, str]:
    return {
        "EVOLUTION_HOLDOUT_MANIFEST": str(manifest_path),
        "EVOLUTION_EVAL_BACKEND": "codex",
        "EVOLUTION_EVAL_MODEL": "gpt-5.4",
    }


def test_refuses_example_path(tmp_path):
    fake = tmp_path / "holdout-v1.json.example"
    _write_minimal_holdout(fake)
    with pytest.raises(RuntimeError, match="refuses"):
        _load_holdout_manifest(_env(fake))


def test_refuses_in_repo_path(tmp_path):
    # Simulate a repo by creating a .git marker
    repo_root = tmp_path / "repo"
    (repo_root / ".git").mkdir(parents=True)
    fake = repo_root / "autoresearch" / "eval_suites" / "holdout-v1.json"
    _write_minimal_holdout(fake)
    with pytest.raises(RuntimeError, match="(inside a git repo|eval_suites/)"):
        _load_holdout_manifest(_env(fake))


def test_refuses_loose_permissions(tmp_path):
    fake = tmp_path / "holdout-v1.json"
    _write_minimal_holdout(fake)
    fake.chmod(0o644)
    with pytest.raises(RuntimeError, match="loose permissions"):
        _load_holdout_manifest(_env(fake))


def test_refuses_redaction_sentinel(tmp_path):
    fake = tmp_path / "holdout-v1.json"
    _write_minimal_holdout(fake, redacted=True)
    with pytest.raises(RuntimeError, match="is_redacted_example"):
        _load_holdout_manifest(_env(fake))


def test_loads_with_600_perms_and_no_sentinel(tmp_path):
    fake = tmp_path / "holdout-v1.json"
    _write_minimal_holdout(fake)
    result = _load_holdout_manifest(_env(fake))
    assert result is not None
    assert result["suite_id"] == "holdout-v1"
```

Run: `pytest tests/autoresearch/test_holdout_manifest_guards.py -v`
Expected: all 5 PASS.

Commit the guards (the real manifest content is never committed):

```bash
git add autoresearch/evaluate_variant.py tests/autoresearch/test_holdout_manifest_guards.py
git commit -m "feat(holdout): enforce out-of-repo path, 600 perms, and redaction sentinel at load time"
```

**9f. Process-boundary isolation for holdout refresh (production-required).**

Same-UID credential storage (chmod 600 + wrapper script) is behavioral security only: an adversarial variant prompt running in the evolution process could `open('~/.config/gofreddy/holdouts/.credentials')` directly. The whole point of holdout is catching a gaming proposer — so the threat model MUST assume the proposer can read any file the evolution process can read.

**Production isolation: holdout refresh runs on separate infrastructure the proposer process never touches.**

Choose one of the three deployments below based on your operating environment. All three achieve the same goal: holdout credentials exist ONLY on infrastructure where the proposer process doesn't execute.

**Option A — GitHub Actions workflow** (recommended if the repo has CI):

1. Provision `holdout-` prefixed provider keys (xpoz, scrape backend, OpenAI) as GitHub repo secrets: `HOLDOUT_FREDDY_API_KEY`, `HOLDOUT_XPOZ_API_KEY`, `HOLDOUT_OPENAI_API_KEY`.
2. Add `.github/workflows/holdout-refresh.yml`:

```yaml
name: holdout-refresh
on:
  schedule:
    - cron: '0 2 * * 1'  # Weekly, Mon 02:00 UTC
  workflow_dispatch:
    inputs:
      fixture_id:
        description: 'Fixture id to refresh (empty = --all-aging)'
        required: false
jobs:
  refresh:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.13' }
      - run: pip install -e .
      - name: Refresh holdout cache
        env:
          FREDDY_API_KEY: ${{ secrets.HOLDOUT_FREDDY_API_KEY }}
          XPOZ_API_KEY: ${{ secrets.HOLDOUT_XPOZ_API_KEY }}
          OPENAI_API_KEY: ${{ secrets.HOLDOUT_OPENAI_API_KEY }}
          EVOLUTION_HOLDOUT_MANIFEST: ${{ secrets.HOLDOUT_MANIFEST_CONTENT }}
        run: |
          echo "$EVOLUTION_HOLDOUT_MANIFEST" > /tmp/holdout-v1.json
          chmod 600 /tmp/holdout-v1.json
          FIXTURE="${{ github.event.inputs.fixture_id }}"
          if [ -z "$FIXTURE" ]; then
            freddy fixture refresh --manifest /tmp/holdout-v1.json --pool holdout-v1 --all-aging
          else
            freddy fixture refresh "$FIXTURE" --manifest /tmp/holdout-v1.json --pool holdout-v1
          fi
      - name: Upload cache artifacts
        uses: actions/upload-artifact@v4
        with:
          name: holdout-cache
          path: ~/.local/share/gofreddy/fixture-cache/holdout-v1/
          retention-days: 90
```

3. Operator fetches refreshed cache onto the evolution machine via `gh run download <run-id>` after a successful refresh. The evolution machine never has the holdout credentials, only the resulting cache artifacts.

4. Guardrail: a pre-commit hook refuses any commit containing `HOLDOUT_FREDDY_API_KEY` / `HOLDOUT_XPOZ_API_KEY` / `HOLDOUT_OPENAI_API_KEY` strings outside `.github/workflows/holdout-refresh.yml`, preventing accidental leakage of credential references into proposer-visible files.

**Option B — Dedicated VM / container** (if no GitHub Actions):

Run a dedicated container or VM (e.g., `holdout-refresher`) whose only task is to run `freddy fixture refresh` on a cron. Credentials live in the container's env or a mounted Docker secret. The evolution machine pulls refreshed cache from the container via rsync or S3. Example container spec (`ops/holdout-refresher/Dockerfile` + `compose.yml`) stays out-of-repo or in a separate ops repo the proposer never reads. Cron entry:

```bash
# /etc/cron.d/holdout-refresh on the dedicated host
0 2 * * 1 holdout-user FREDDY_API_KEY=$(cat /run/secrets/holdout_freddy_key) ... freddy fixture refresh --manifest /config/holdout-v1.json --pool holdout-v1 --all-aging
```

**Option C — Local-dev fallback (NOT production):**

For single-operator local development where the above is impractical, use the wrapper-script pattern with explicit trust-boundary documentation:

```bash
cat > ~/.config/gofreddy/holdouts/.credentials <<'EOF'
export HOLDOUT_FREDDY_API_KEY=...
export HOLDOUT_XPOZ_API_KEY=...
export HOLDOUT_OPENAI_API_KEY=...
EOF
chmod 600 ~/.config/gofreddy/holdouts/.credentials

cat > ~/.config/gofreddy/holdouts/refresh-holdout.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
source ~/.config/gofreddy/holdouts/.credentials
export FREDDY_API_KEY="$HOLDOUT_FREDDY_API_KEY"
export OPENAI_API_KEY="$HOLDOUT_OPENAI_API_KEY"
export XPOZ_API_KEY="$HOLDOUT_XPOZ_API_KEY"
exec "$@"
EOF
chmod 700 ~/.config/gofreddy/holdouts/refresh-holdout.sh
```

Document in `autoresearch/README.md` operational notes: "Local-dev holdout refresh uses `~/.config/gofreddy/holdouts/refresh-holdout.sh` as a trust-boundary shortcut. The proposer process runs as the same OS user and CAN read `.credentials` if instructed — this is a known gap that production deployment (Option A/B) closes. Local-dev is acceptable only when operator retains full visibility into every variant generated during the session."

(vi) Add to `autoresearch/README.md` "Operational notes" section: "Holdout refresh MUST run on a process-boundary-isolated environment (Option A/B above). The local-dev wrapper (Option C) is accepted only for single-operator development; document in the commit message if a production run uses C."

Commit:

```bash
git add autoresearch/README.md .github/workflows/holdout-refresh.yml
git commit -m "feat(holdout): process-boundary isolation for refresh (GitHub Actions primary; local wrapper as dev fallback)"
```

**9g. `verify-isolation` pre-flight (folded into `freddy fixture refresh --pool holdout-v1` precondition).**

No separate `freddy holdout` command group — the isolation check runs as a precondition inside `freddy fixture refresh` whenever `--pool holdout-v1` (or any pool with `on_miss: hard_fail` per pool_policies). Operator invokes the single `refresh` command; isolation verification happens transparently before the refresh proceeds. Keeps the CLI surface flat and eliminates one command group.

The three-option branching (A/B/C) works only if the active mode matches operator intent. An operator who intends Option A but runs on a machine without GitHub Actions configured silently falls back to fetching against stale cache; an operator running Option C on production silently keeps a same-UID credential file readable by every process. The Acceptance Criterion "commit message explicitly calls it out when C is used" relies on operator honesty, not on the harness.

Build a pre-flight command that actively inspects the environment and refuses holdout refresh if the active isolation mode is unclear or misconfigured.

```python
# cli/freddy/commands/holdout.py (new command group)
import os
import shutil
from pathlib import Path
import typer

app = typer.Typer(name="holdout", help="Holdout pool operations (verify isolation, refresh via CI).")


@app.command("verify-isolation")
def verify_isolation_cmd() -> None:
    """Detect active isolation mode and refuse holdout refresh if none is active.

    Checks in priority order:
    1. Option A (GitHub Actions): is GITHUB_ACTIONS=true AND are HOLDOUT_* secrets
       present in env?
    2. Option B (dedicated container): is the HOLDOUT_HOST env var set and
       different from the evolution host's hostname?
    3. Option C (local wrapper): is the current process invocation going
       through refresh-holdout.sh? Detect via a wrapper-set HOLDOUT_WRAPPER=1
       env var the wrapper script exports.

    Exits non-zero with a diagnostic if none match — refuses to proceed.
    """
    mode_a = os.environ.get("GITHUB_ACTIONS") == "true" and all(
        k in os.environ for k in ("HOLDOUT_FREDDY_API_KEY", "HOLDOUT_XPOZ_API_KEY")
    )
    mode_b = bool(os.environ.get("HOLDOUT_HOST"))
    mode_c = os.environ.get("HOLDOUT_WRAPPER") == "1"

    if mode_a:
        typer.echo("✓ isolation mode: A (GitHub Actions with HOLDOUT_* secrets)")
        return
    if mode_b:
        typer.echo(f"✓ isolation mode: B (dedicated host {os.environ['HOLDOUT_HOST']})")
        return
    if mode_c:
        typer.echo("✓ isolation mode: C (local-dev wrapper; trust-boundary shortcut — document in commit)")
        return

    # No mode active — fail loudly with diagnostic. No judge fallback for 4 booleans.
    gha = os.environ.get("GITHUB_ACTIONS") == "true"
    secrets_present = any(k in os.environ for k in ("HOLDOUT_FREDDY_API_KEY", "HOLDOUT_XPOZ_API_KEY"))
    diagnostic = (
        "misconfigured Option A (GITHUB_ACTIONS set but HOLDOUT_* secrets missing)"
        if gha and not secrets_present
        else "no active isolation mode: set HOLDOUT_HOST (Option B) or run through refresh-holdout.sh (Option C)"
        if not gha
        else "unknown configuration"
    )
    typer.echo(f"✗ {diagnostic}", err=True)
    raise typer.Exit(1)
```

Wire it into the GitHub Actions workflow + the local wrapper script as a pre-flight gate:

```yaml
# .github/workflows/holdout-refresh.yml — add before the refresh step
- name: Verify isolation mode
  run: freddy holdout verify-isolation
```

```bash
# refresh-holdout.sh — add HOLDOUT_WRAPPER flag and pre-flight check
export HOLDOUT_WRAPPER=1
freddy holdout verify-isolation  # refuses to proceed if misconfigured
exec "$@"
```

Tests `tests/freddy/holdout/test_verify_isolation.py`:
- `test_passes_on_github_actions_with_secrets` — sets env, exit 0
- `test_passes_on_dedicated_host` — sets HOLDOUT_HOST, exit 0
- `test_passes_on_wrapper_flag` — sets HOLDOUT_WRAPPER=1, exit 0
- `test_fails_on_github_actions_without_secrets` — exit 1, judge invoked
- `test_fails_on_bare_env` — no mode active, exit 1

Commit:
```bash
git add cli/freddy/commands/holdout.py tests/freddy/holdout/test_verify_isolation.py \
        .github/workflows/holdout-refresh.yml
git commit -m "feat(holdout): verify-isolation pre-flight (detects active A/B/C mode, refuses on misconfig)"
```

- [ ] **Step 10: Verify holdout loads end-to-end**

Run from the repo root (the `autoresearch/` directory is not a Python package, so add it to `sys.path` explicitly — or `cd autoresearch && python -c "..."`):

```bash
python -c "import sys; sys.path.insert(0, 'autoresearch'); from evaluate_variant import _load_holdout_manifest; import os; m = _load_holdout_manifest(dict(os.environ)); print(m['suite_id'], sum(len(m['domains'].get(d, [])) for d in ['geo','competitive','monitoring','storyboard']))"
```
Expected: `holdout-v1 16`

Note: this command requires `EVOLUTION_HOLDOUT_MANIFEST`, `EVOLUTION_EVAL_BACKEND`, and `EVOLUTION_EVAL_MODEL` env vars to be set in the current shell. If any are missing, `_load_holdout_manifest` / its manifest-normalization helper will raise — which is itself useful validation.

- [ ] **Step 11: Commit the example file (real manifest NEVER committed)**

```bash
git add autoresearch/eval_suites/holdout-v1.json.example
git commit -m "feat(holdout-v1): add redacted example holdout manifest"
```

History: git log on this example + lineage records on scored variants. No separate CHANGELOG.md (per-suite CHANGELOG contract dropped during scope review).

---

## Phase 3: Search-v1 Modest Expansion (6-8 fixtures)

**Purpose:** Fill search-v1 coverage gaps from Phase 1 with fixtures representing realistic agency work (NOT adversarial probes — those are in holdout).

**Files:**
- Modify: `autoresearch/eval_suites/search-v1.json` (append new fixtures, bump manifest version 1.0 → 1.1)

**Suggested targets** (exact fill depends on Phase 1 taxonomy output):

| Candidate | Domain | Gap filled |
|---|---|---|
| geo-airbnb-es | geo | lang=es, vertical=travel |
| geo-tesla-model-y-us | geo | vertical=auto (US version — pairs with holdout German BMW) |
| competitive-wise-vs-remitly | competitive | vertical=fintech, global money transfer |
| competitive-hellofresh-vs-home-chef | competitive | vertical=CPG/DTC |
| monitoring-netflix | monitoring | vertical=media, US but non-SaaS |
| monitoring-maersk | monitoring | vertical=shipping, geo=EU |
| storyboard-dude-perfect | storyboard | sports creator, underrepresented genre |
| storyboard-kurzgesagt-de | storyboard | educational, lang=de |

Pick 6-8 from this list (or equivalents identified in Phase 1). Each must fill a genuine gap on the taxonomy matrix.

**Per-fixture process** (the authoring loop from Phase 2 Steps 1-8, executed for each search expansion fixture with `--pool search-v1` and in-repo manifest):

- [ ] **Step 1-8: Per-fixture authoring loop**

For each of the 6-8 search expansion fixtures, execute the per-fixture process exactly as in Phase 2 Steps 1-8:

1. Write fixture spec to a scratch manifest
2. `freddy fixture validate <scratch>`
3. `freddy fixture envs <scratch> --missing`
4. `freddy fixture refresh <fixture_id> --dry-run` then without dry-run
5. `freddy fixture dry-run <fixture_id> --baseline v006 --seeds 5` (revise and retry until healthy)
6. Append to `autoresearch/eval_suites/search-v1.json` (NOT holdout-v1.json)
7. `freddy fixture discriminate` (optional for search; anchors in holdout only; requires `--seeds 5`)

Substitute `--pool search-v1` everywhere and commit to the in-repo manifest.

One commit per fixture is fine — small commits make review easier:

```bash
git add autoresearch/eval_suites/search-v1.json
git commit -m "feat(search-v1): add geo-airbnb-es fixture (lang=es, vertical=travel)"
```

- [ ] **Step 9: Set manifest version to 1.1**

After all new fixtures are added, set the suite-level `version` field in `autoresearch/eval_suites/search-v1.json` to `"1.1"`.

**Precondition:** Plan A Phase 1 (schema backfill) is expected to have already added `"version": "1.0"` at the suite level and stamped each existing fixture with `"version": "1.0"`. If the field is still absent when you open the file, that backfill has not landed yet — stop and resolve ordering before continuing.

Verify by reading the file:

```bash
python -c "import json; print(json.load(open('autoresearch/eval_suites/search-v1.json')).get('version'))"
```
Expected: `1.0` (before this step) → `1.1` (after this step).

Then apply the edit. Run:

```bash
freddy fixture validate autoresearch/eval_suites/search-v1.json
```
Expected: PASS with `search-v1@1.1: N fixture(s)` where N = 23 + (number added).

- [ ] **Step 10: Commit version bump**

```bash
git add autoresearch/eval_suites/search-v1.json
git commit -m "feat(search-v1): bump manifest version to 1.1 (v1.0 scores not comparable; rescore in Phase 4)"
```

---

## Phase 4: Migration — Existing search-v1 Onto New Infrastructure

**Purpose:** Every existing search-v1 fixture needs a cache entry and a baseline dry-run record. This is mechanical work but must happen before Phase 5 (canary) can run with cache-backed evaluation.

**Files:**
- Populate: `~/.local/share/gofreddy/fixture-cache/search-v1/...` for all ~30 fixtures
- Create: `docs/plans/search-v1-migration-scores.md` — table of baseline scores per fixture

- [ ] **Step 1: Batch refresh all search-v1 fixtures (with content-hash baseline)**

Run: `freddy fixture refresh --all-stale --manifest autoresearch/eval_suites/search-v1.json --pool search-v1 --cache-root ~/.local/share/gofreddy/fixture-cache`

Since no cache exists yet, all fixtures will be refreshed. Log total cost; this is a one-time upfront cost (~$50-150 depending on TikTok monitoring quantity).

Expected: all ~30 cache entries created.

Verify: `freddy fixture staleness --pool search-v1`
Expected: every fixture shows `fresh`.

**Content-hash drift detection (production guard against compromised upstream URLs).** The refresh path in Plan A writes each cache artifact as `{source}_{data_type}__{sha1(arg)[:12]}.json`. Extend the written `DataSourceRecord` to include a `content_sha1` field (sha1 of the artifact body) + a truncated content preview (first 2KB of text). On subsequent refreshes, compare the new content to the stored content via the `quality-judge` agent — it sees the diff and decides whether the change is material (CDN hijack, page rewrite) vs. cosmetic (ad carousel refresh, CSRF tokens, timestamps):

```python
# In Plan A's _run_source_fetch, after writing the cache artifact:
new_hash = hashlib.sha1(result.stdout.encode()).hexdigest()
old_record = existing_manifest.lookup(source, data_type, arg)
if old_record and old_record.content_sha1 != new_hash:
    from autoresearch.judges.quality_judge import call_quality_judge
    old_content = (cache_dir / old_record.cached_artifact).read_text()
    verdict = call_quality_judge({
        "role": "content_drift",
        "fixture_id": fixture_id,
        "anchor": bool(fixture.anchor),
        "source": source, "data_type": data_type, "arg": arg,
        "old_content_preview": old_content[:2048],
        "new_content_preview": result.stdout[:2048],
        "old_content_length": len(old_content),
        "new_content_length": len(result.stdout),
    })
    if verdict.verdict == "material":
        drift_log = Path.home() / ".local/share/gofreddy/content-drift.jsonl"
        drift_log.parent.mkdir(parents=True, exist_ok=True)
        drift_log.open("a").write(json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "fixture_id": fixture_id, "source": source, "data_type": data_type,
            "arg": arg, "verdict": verdict.verdict,
            "reasoning": verdict.reasoning, "confidence": verdict.confidence,
        }) + "\n")
        sys.stderr.write(
            f"⚠️  fixture {fixture_id} material content drift ({source}/{data_type}): "
            f"{verdict.reasoning}; review before next canary run.\n"
        )
```

Rationale: if a fixture's upstream URL is CDN-hijacked or the brand page is rewritten overnight, fetched content becomes attacker-controlled. Character-level diff ratios alone misfire on ad carousels and timestamps; the quality-judge sees the actual content and reasons about whether the change matters. Applies to both anchor AND rotating fixtures (the judge can factor `anchor` into its reasoning). Wire this into Plan A's `_run_source_fetch` as an additional step before Phase 4 Step 1 runs.

- [ ] **Step 2: Dispatch a migration-sweep agent across `search-v1` (no new CLI command)**

The 30-fixture sweep happens once. An orchestration agent enumerates the manifest, invokes `freddy fixture dry-run` per fixture, collects raw per-seed scores + cost, POSTs the batch to `system_health.fixture_quality` for verdicts, and writes the markdown report. Handles edge cases (skipped fixtures, stale-during-sweep, mid-run failure) via reasoning rather than rigid branches.

**Migration-sweep agent task spec** (`docs/agent-tasks/migrate-search-pool.md`):

```
GOAL: migrate every fixture in a pool's manifest onto the new fixture
      infrastructure. Produce a markdown report with per-fixture verdicts.
      Exit non-zero if any fixture is not `healthy`.

INPUTS:
  - manifest_path (e.g. autoresearch/eval_suites/search-v1.json)
  - pool (e.g. search-v1)
  - baseline (e.g. v006)
  - seeds (default 5)
  - output_path (e.g. docs/plans/search-v1-migration-scores.md)

STEPS:
  1. Parse the manifest via `freddy fixture validate --manifest <path>`.
  2. Record sweep_started_at.
  3. For each (domain, fixture) in the manifest:
       a. `freddy fixture dry-run <fixture> --seeds <seeds> --baseline <baseline>
          --raw-output` — emits raw per-seed scores + cost + fixture metadata
          as JSON. No thresholded verdict on the CLI side.
       b. Collect the raw output for batching.
  4. Single batched POST to `/invoke/system_health/fixture_quality` with
     `{items: [<one entry per fixture>]}` — agent returns per-fixture verdicts.
  5. Check for fixtures that aged during the sweep (cache mtime older than
     sweep_started_at minus one cycle). For any stale, re-dry-run + re-verdict.
  6. Render markdown atomically (build in memory, single write).
  7. Exit non-zero if any verdict is not `healthy`.

EDGE CASES TO RECOVER FROM:
  - per-fixture dry-run failure → record error row, continue sweep
  - cache aging during sweep → re-refresh + re-verdict, note in report
  - mid-run interruption → leave output file untouched (atomic write only)

IDEMPOTENCY: re-running is safe; the dry-run command does not mutate shared
  state. The markdown file is overwritten each run.
```

Per-pool invocation:

```bash
claude --print --input-file docs/agent-tasks/migrate-search-pool.md \
  --var manifest_path=autoresearch/eval_suites/search-v1.json \
  --var pool=search-v1 --var baseline=v006 --var seeds=5 \
  --var output_path=docs/plans/search-v1-migration-scores.md
```

Output: `docs/plans/search-v1-migration-scores.md` with per-fixture rows (fixture_id / domain / median / MAD / cost / verdict / reasoning). Median / MAD are computed in the dry-run command *for the human-facing report only* — the `system_health.fixture_quality` verdict is produced by the agent reading raw per-seed scores, not summary statistics.

**Why agent task, not CLI:** the sweep runs once. Building a `freddy fixture migrate` Typer command means ~100 lines of argument parsing, error handling, markdown rendering, and `if`-branches for recovery. An agent with the task spec above does the same thing by composing existing primitives — zero new Python.

- [ ] **Step 2a: Emit per-cycle saturation events into the unified events log**

No `saturation_log.py` module, no aggregator, no beat-rate summarizer, no threshold. At the end of `evaluate_variant.py::evaluate_search`, after per-fixture scores + baseline comparison are known, emit one event per public-suite fixture:

```python
# autoresearch/evaluate_variant.py — end of evaluate_search
from events import log_event  # Phase 0a unified log

for fixture_id, fixture_score, baseline_score in per_fixture_results:
    log_event(kind="saturation_cycle",
              cycle_id=cycle_id_from_variant(variant_id),
              fixture_id=fixture_id,
              candidate_score=fixture_score,
              baseline_score=baseline_score,
              baseline_beat=(fixture_score > baseline_score))
```

That's the whole write path — ~8 lines inside the existing finalize loop. No new module.

- [ ] **Step 2b: `freddy fixture staleness` surfaces saturation verdicts via the system-health agent**

Extend Plan A's `freddy fixture staleness` to call `system_health.saturation` in a single batched request. The agent reads `events.jsonl` directly (on the judge-service side, via the payload) and decides per-fixture whether to rotate. No code-side aggregation.

```python
# cli/freddy/commands/fixture.py::staleness_cmd — additional block
from autoresearch.judges.quality_judge import call_quality_judge

# Gather per-fixture cycle events from the unified log.
events_log = Path.home() / ".local/share/gofreddy/events.jsonl"
per_fixture_events: dict[str, list[dict]] = {}
if events_log.exists():
    for line in events_log.read_text().splitlines():
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("kind") != "saturation_cycle":
            continue
        fid = entry.get("fixture_id")
        if fid:
            per_fixture_events.setdefault(fid, []).append(entry)

# One batched call; agent returns a per-fixture verdict.
batch_items = [
    {"fixture_id": fid, "cycle_events": events}
    for fid, events in per_fixture_events.items()
    if len(events) >= 5  # cost guard: don't ask about fixtures with <5 data points
]
verdicts = {}
if batch_items:
    result = call_quality_judge({"role": "saturation", "items": batch_items})
    verdicts = {v["fixture_id"]: v for v in result.get("items", [])}

# In per-row render:
v = verdicts.get(row["fixture_id"])
if v and v.get("verdict") == "rotate_now":
    row["status"] = f"{row['status']} SATURATED"
```

The agent receives the **raw** cycle-event stream per fixture (candidate_score, baseline_score, baseline_beat flag) and decides. No recent_beat_rates() helper, no "how many beats out of how many cycles" summary statistic, no threshold. The agent's prompt knows saturation patterns (high beat rate sustained, vs. high-quality fixture on a strong proposer) and reasons from the raw history.

The `len(events) >= 5` skip is **not a judgment threshold** — it's a cost guard. Asking the agent to verdict a fixture with 2 cycles is paying for a judge call that can only return "insufficient data."

Tests: `tests/freddy/fixture/test_staleness_saturation.py` writes a fake `events.jsonl` with saturation_cycle entries across two fixtures, mocks `call_quality_judge` to return `[{"fixture_id": "geo-a", "verdict": "rotate_now"}, {"fixture_id": "geo-b", "verdict": "fine"}]`, invokes staleness, asserts `SATURATED` appears only on the geo-a row.

Commit:

```bash
git add autoresearch/evaluate_variant.py \
        cli/freddy/commands/fixture.py \
        tests/freddy/fixture/test_staleness_saturation.py
git commit -m "feat(fixture): emit saturation_cycle events; staleness surfaces agent verdict (no aggregator, no threshold)"
```

- [ ] **Step 3: Run autoresearch test suite**

Run: `pytest tests/autoresearch/ -x -q`
Expected: all pass. (Any canary-dependent tests should have been updated in Plan A Phase 11.)

- [ ] **Step 3b: Judge calibration anchor + drift detection**

Single-judge systems drift over time: model updates, provider rerankings, subtle prompt changes can all shift score distributions. Without a calibration anchor, we have no way to detect when "v007 scored 0.65 last month" means something different this month.

(i) Pick 3-5 **calibration variants** — historically stable variants with known-stable behavior, e.g., `v001`, `v006`, `v020`. Pick a **calibration fixture subset** (3-5 search-v1 fixtures spanning the 4 domains, no anchors).

(ii) Create `autoresearch/judge_calibration.py`:

```python
"""Judge calibration anchor — cross-family drift detection.

Monthly: `python autoresearch/judge_calibration.py --check`. Rescores a fixed
set of (variant, fixture) pairs with BOTH families and delegates the drift
decision to the system-health agent — Claude reads Codex's baseline+current
traces to judge Codex's drift, and vice-versa. Cross-family removes the
self-bias that would plague a same-family drift check.

Baseline lives on the judge-service filesystem (see Plan A Phase 0c isolation)
and stores both families' scores AND reasoning traces per pair. Deploys to
the baseline go through PR-gated `deploy-evolution-judge.yml` — no runtime
mutation API on evolution-judge-service. Rebaseline on any judge model
migration; record the CLI versions used.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Baseline lives on judge-service side (Phase 0c boundary). The autoresearch-
# side client calls /invoke/system_health/calibration_drift with the pair
# identifiers; the judge service loads the stored baseline + current traces,
# dispatches Claude-judging-Codex and Codex-judging-Claude, and returns an
# aggregated verdict. Autoresearch never sees the baseline contents.


def _pairs_from_manifest() -> list[dict]:
    """Read the frozen calibration-pair list from the pinned config.

    The set of pairs itself is managed on the judge-service side (PR-gated).
    Autoresearch holds only pair identifiers (variant_id + fixture_id) —
    scoring and drift-detection logic live judge-side.
    """
    cfg_path = Path(".config/gofreddy/calibration-pairs.json")
    return json.loads(cfg_path.read_text())["pairs"] if cfg_path.exists() else []


def check() -> int:
    """Monthly drift check — single HTTP call, aggregated cross-family verdict."""
    from autoresearch.judges.quality_judge import call_quality_judge
    pairs = _pairs_from_manifest()
    if not pairs:
        print("ERROR: no calibration-pairs config; deploy one via PR before --check.", file=sys.stderr)
        return 2
    verdict = call_quality_judge({
        "role": "calibration_drift",
        "pairs": pairs,  # identifiers only; judge-service loads baselines
        "check_timestamp": datetime.now(timezone.utc).isoformat(),
    })
    # Judge-service emits kind="judge_drift" on its own events log with full
    # baseline+reasoning comparisons (Phase 0c boundary). Autoresearch just
    # mirrors the top-line verdict for its own lineage.
    from events import log_event
    log_event(kind="judge_drift",
              verdict=verdict.verdict,
              reasoning=verdict.reasoning,
              confidence=verdict.confidence)
    if verdict.verdict == "stable":
        print(f"judge calibration clean: {verdict.reasoning}")
        return 0
    print(f"⚠️  judge drift: {verdict.verdict} — {verdict.reasoning}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--check":
        sys.exit(check())
    print(f"Usage: {sys.argv[0]} --check  (rebaselining is a PR-gated judge-service operation)", file=sys.stderr)
    sys.exit(2)
```

**Cross-family drift detection (judge-service side).** The agent prompt for `role="calibration_drift"` routes each pair through two fresh CLI invocations:

1. Codex (gpt-5.4) scores the pair with current prompts → get current Codex trace
2. Claude (Opus 4.7) scores the pair with current prompts → get current Claude trace
3. Load baseline (both families' scores + reasoning traces stored judge-side)
4. Invoke Claude with `"be maximally skeptical; superficial phrasing changes are NOT drift; changes in which criteria get weighted ARE drift"` — Claude reads Codex's baseline + current traces, returns a per-pair verdict
5. Invoke Codex with the same skeptical framing — Codex reads Claude's baseline + current traces, returns a per-pair verdict
6. Aggregate: if either family flags any pair as `reasoning_drift` or `variance_drift` or `magnitude_drift`, overall verdict is drifted; otherwise `stable`

Neither family self-judges. Baseline storage + PR-gated deploy prevents runtime tampering. Skeptical prompt framing fights the "same-ish" default. This is the cross-family safety design discussed in the architectural transcript.

(iii) Record the baseline now (one-time, after Phase 4 Step 2 migration scores exist):

```bash
python autoresearch/judge_calibration.py --record-baseline
```

(iv) Add a monthly cron / manual-reminder entry in `autoresearch/README.md` "Operational notes":

> **Judge drift check:** run `python autoresearch/judge_calibration.py --check` monthly. Non-zero exit indicates the quality-judge has determined the scoring distribution has materially drifted; investigate before trusting new scores in promotion decisions. The judge sees the full baseline and current distributions and decides — no fixed 2×MAD threshold.

(v) Add a test `tests/autoresearch/test_judge_calibration.py` that mocks both `_score` and `call_quality_judge`, writes a synthetic baseline, verifies `check()` returns 0 when the mocked judge says `stable` and 1 when it says any drift verdict (`magnitude_drift`, `variance_drift`, `reasoning_drift`, or `mixed`).

Commit:

```bash
git add autoresearch/judge_calibration.py tests/autoresearch/test_judge_calibration.py autoresearch/README.md
git commit -m "feat(autoresearch): judge calibration anchor + monthly drift-detection check"
```

- [ ] **Step 4: Run one full evolution iteration against v006 end-to-end — and pin the lane head so Phase 5 starts from a known baseline**

`evolve.sh score-current` is deprecated (removed per `autoresearch/evolve.py:102-106`; scoring now runs as the pre-flight step of `evolve.sh run`). Use a single `run` iteration instead, which exercises the pre-flight scoring against cache:

```bash
# Pin the lane head BEFORE the migration check so we can detect if the
# check auto-promoted a candidate and moved the baseline Phase 5 depends on.
CORE_HEAD_BEFORE=$(python -c "import json; print(json.load(open('autoresearch/archive/current.json'))['core'])")
echo "core lane head before migration check: $CORE_HEAD_BEFORE" >&2

./autoresearch/evolve.sh run --iterations 1 --candidates-per-iteration 1 --lane core

# Assert the lane head did not move. If it did, the one-iteration check
# auto-promoted a candidate and the Phase 5 canary would no longer be
# starting from v006. Roll back.
CORE_HEAD_AFTER=$(python -c "import json; print(json.load(open('autoresearch/archive/current.json'))['core'])")
if [ "$CORE_HEAD_AFTER" != "$CORE_HEAD_BEFORE" ]; then
    echo "ERROR: migration check auto-promoted $CORE_HEAD_AFTER over $CORE_HEAD_BEFORE" >&2
    echo "Rolling back: ./autoresearch/evolve.sh promote --undo" >&2
    ./autoresearch/evolve.sh promote --undo
    # Re-verify
    CORE_HEAD_AFTER=$(python -c "import json; print(json.load(open('autoresearch/archive/current.json'))['core'])")
    [ "$CORE_HEAD_AFTER" = "$CORE_HEAD_BEFORE" ] || { echo "Rollback failed"; exit 1; }
fi
echo "core lane head pinned: $CORE_HEAD_AFTER"
```

Expected: pre-flight re-scores v006 on `search-v1@1.1` with cache-first behavior, then produces one new candidate variant. The pre-flight-recorded v006 score should be in the same ballpark as v006's pre-migration score (± judge noise). The lane head ends at `$CORE_HEAD_BEFORE` regardless of whether the new candidate was promotion-eligible.

If score drifts significantly: investigate cache integration (Plan A Phase 8) before proceeding.

- [ ] **Step 5: Commit migration record**

```bash
git add docs/plans/search-v1-migration-scores.md autoresearch/GAPS.md
git commit -m "chore(migration): search-v1 fully onboarded to fixture infrastructure (GAPS 2/3/18 partial)"
```

---

## Phase 5: Overfit Canary Experiment

**Purpose:** Validate that holdout actually catches overfitting before enabling autonomous promotion. This is the go/no-go experiment.

**Timing constraint:** Execute Phases 2–5 within ~2 weeks. Monitoring fixtures drift weekly (`most_recent_complete`). If longer, re-run Phase 4 Step 2 before Phase 5 Step 3.

**Files:**
- Create: `docs/plans/overfit-canary-results.md`

- [ ] **Step 1: Freeze both suites**

Record: `search-v1@1.1`, `holdout-v1@1.0`. No fixture changes during the experiment.

- [ ] **Step 2: Select lane**

Pick `geo` (highest OOD coverage in holdout-v1 per the taxonomy).

- [ ] **Step 2.5: Pre-canary sanity — holdout must discriminate a known-different variant pair**

Before spending hours on a 20-iteration canary, verify holdout can actually measure improvement. Pick a variant pair known to differ in capability on geo — e.g., `(v001, v006)` or `(v001, v020)` — and score both on holdout:

```bash
EVOLUTION_HOLDOUT_MANIFEST=~/.config/gofreddy/holdouts/holdout-v1.json \
python autoresearch/evaluate_variant.py autoresearch/archive/v001 autoresearch/archive \
    --search-suite autoresearch/eval_suites/search-v1.json \
    --mode holdout --lane geo
# Repeat for v020 (or whichever pair)
```

Required outcome: |holdout_score(v020) - holdout_score(v001)| ≥ 0.10. If both variants score within 0.10 of each other on holdout, the fixtures are too hard for any current variant to move, and the canary cannot distinguish "holdout too hard for any proposer" from "proposer not improving." Abort the canary and revise holdout to include at least a few fixtures the known-good pair moves on.

Document the pair and the scores in `docs/plans/overfit-canary-results.md` as Section 1: Pre-canary sanity check.

- [ ] **Step 3: Run 20 evolution iterations on geo lane**

Run: `./autoresearch/evolve.sh run --lane geo --iterations 20 --candidates-per-iteration 3`

(Note: `run` is an explicit subcommand of `evolve.sh`. Flags on `run`: `--iterations`, `--candidates-per-iteration`, `--lane`, `--archive-dir`, `--backend`, `--model`, `--max-turns`. See `autoresearch/evolve.py:128-183`.)

Expected: ~60 new candidate variants produced (20 × 3), with promoted lane heads updated after each iteration's finalize step. Watch for divergence in evolve.sh output. Total wall-clock: many hours to days depending on session timeouts.

- [ ] **Step 4: Score checkpoints adaptively (promotion-judge decides cadence + seeds)**

The canary checkpoint schedule is **adaptive, not fixed.** A proposer that overfits in 3 iterations wastes 17 iterations of rigid schedule; a slow-burn divergence that emerges at iter 15 underfits a pre-iter-10 schedule. Instead, at each candidate iteration, ask the canary agent (role: `canary`, `mode: "checkpoint_schedule"`) whether this iteration should be a checkpoint, and ask the system-health agent (role: `noise_escalation`) how many seeds and what seed scheme to use.

```python
# Invoked inside the canary runner at each iteration (not only 2,4,6,…):
from autoresearch.judges.promotion_judge import call_promotion_judge
from autoresearch.judges.quality_judge import call_quality_judge

schedule_verdict = call_promotion_judge({
    "role": "canary",
    "mode": "checkpoint_schedule",
    "lane": "geo",
    "current_iter": iter_num,
    "completed_checkpoints": prior_checkpoints,  # list of prior entries
    "budget_remaining": {"iterations": 20 - iter_num, "judge_calls": budget_left},
})
# verdict.decision ∈ {"checkpoint", "skip", "early_terminate_go", "early_terminate_fail"}
# verdict.reasoning explains: "signal diverging fast — checkpoint now",
#   "noise dominated — skip 2 iterations", "10 clean checkpoints → GO",
#   "holdout tracks public through 8 checkpoints → FAIL without completing 20".

if schedule_verdict.decision in ("early_terminate_go", "early_terminate_fail"):
    return _finalize_canary_early(schedule_verdict)

if schedule_verdict.decision == "skip":
    continue

# Checkpoint requested: ask quality-judge for seed scheme + count
seeds_verdict = call_quality_judge({
    "role": "noise_escalation",
    "prior_checkpoint_iqrs": [c["public_iqr"] for c in prior_checkpoints],
    "prior_seed_counts": [c["seed_count"] for c in prior_checkpoints],
    "provider": "codex_gpt-5-4",
})
# verdict.verdict ∈ {"sufficient", "bump_seeds", "bump_iterations"}
# verdict.recommended_action carries concrete params, e.g.:
#   {"seed_count": 15, "seed_scheme": "primes"}
#   {"seed_count": 10, "seed_scheme": "sequential"}
# "primes" scheme: use 7919, 104729, 1299709, ... — diverse integers that
#   reduce risk of provider seed-hash collisions (vs. sequential 1..10).

seeds = seeds_verdict.recommended_action.get("seed_count", 10)
scheme = seeds_verdict.recommended_action.get("seed_scheme", "sequential")
seed_values = _materialize_seeds(scheme, seeds)  # helper: scheme → list[int]
```

Replaces the fixed `for seed in 1 2 3 4 5 6 7 8 9 10` loop with a seed scheme chosen per checkpoint. Replaces the fixed `at iterations 2, 4, 6, 8, 10, 12, 14, 16, 18, 20` cadence with judge-decided cadence.

Scoring mechanics (unchanged): `evaluate_variant.py` runs with `AUTORESEARCH_SEED=<seed>` per invocation, records per-seed composite + geo scores, computes median + IQR. Those raw stats feed the per-iteration judge calls above.

**Cost ceiling:** the judge tracks `budget_remaining` and can choose `early_terminate_fail` if the trajectory shows no diverging signal after N checkpoints — prevents running the full 20 iterations when signal is clearly absent.


- [ ] **Step 5: Construct divergence table + compute trend statistics**

Build the table in `docs/plans/overfit-canary-results.md` with median + IQR per checkpoint:

```markdown
| Iter | Variant | Public median (IQR) | Holdout median (IQR) | Divergence |
|---|---|---|---|---|
| 2  | v007 | 0.50 (0.04) | 0.45 (0.06) | 0.05 |
| 4  | v009 | 0.54 (0.05) | 0.46 (0.07) | 0.08 |
| ... | (10 rows) |
| 20 | v028 | 0.75 (0.04) | 0.48 (0.05) | 0.27 |
```

Compute Kendall's tau + p-value on the divergence series as a measurement — NOT as a threshold:

```python
from scipy.stats import kendalltau
divergences = [0.05, 0.08, 0.11, 0.13, 0.17, 0.19, 0.20, 0.24, 0.26, 0.27]
iters = list(range(1, len(divergences) + 1))
tau, pvalue = kendalltau(iters, divergences)
one_sided_p = pvalue / 2 if tau > 0 else 1 - pvalue / 2
# Record these numbers; the GO/FAIL decision is made by promotion-judge in Step 6.
```

Record `tau` and `one_sided_p` in the results doc alongside the trajectory table. These are inputs to the judge call in the next step.

- [ ] **Step 6: Promotion-judge decides canary GO / FAIL / REVISE**

The canary decision — "did the holdout prove that the proposer generalizes, and can we enable autonomous promotion?" — is too context-dependent for a bucket-table classifier. Hand the data to the canary agent (role: `canary`, `mode: "go_fail"`):

```python
from autoresearch.judges.promotion_judge import call_promotion_judge

verdict = call_promotion_judge({
    "role": "canary",
    "mode": "go_fail",
    "lane": "geo",
    "holdout_version": "v1.0",
    "checkpoints": [
        {"iter": 2,  "public_median": 0.50, "public_iqr": 0.04,
         "holdout_median": 0.45, "holdout_iqr": 0.06, "divergence": 0.05},
        # ... 10 rows
    ],
    "trend": {"tau": tau, "one_sided_p": one_sided_p},
    "pre_canary_sanity": {"known_pair_delta": 0.12},  # from Step 2.5
    "prior_canary_verdicts": [],  # list of previous canary attempts on this holdout
})
# verdict.decision ∈ {"go", "fail", "revise"}; verdict.reasoning has the "why".
```

The judge sees the full trajectory (not just a tau+p pair) and reasons about whether divergence is real, whether public is genuinely climbing (not flat), whether pre-canary sanity held, whether holdout appears inverted (public flat + holdout climbing = broken), and whether noise levels permit a confident call. It returns one of:

- `go` — enable autonomous promotion. Record verdict, commit results doc, ship.
- `fail` — holdout not doing its job. Revise rotating holdout fixtures, bump holdout-v1 → v1.1, rerun canary.
- `revise` — signal is present but weak/ambiguous. Judge's reasoning will specify what to do (extend checkpoints, pilot on one lane, revise specific fixtures).

**NO-GO termination rule:** if two consecutive canary runs both return `fail` or `revise`, pause Plan B. The judge's reasoning tells you whether to (a) escalate to the separate MAD-confidence-scoring initiative, (b) ship without autonomous promotion (keep `is_promotable` as operator-triggered), or (c) accept that holdout can't be authored against this proposer. The choice is still human — but the judge tells you why.

Pass `prior_canary_verdicts` on subsequent attempts so the judge can reason about persistent failure modes ("same rotation-tracks-public failure as last attempt → probably not a fixture problem").

- [ ] **Step 7: Document verdict**

Append to `docs/plans/overfit-canary-results.md`:

```markdown
## Verdict

**Status:** [GO | NO-GO]

**Reasoning:** [Free-form paragraph describing what the divergence pattern showed.]

**Next step:** [If GO: proceed to Phase 6 and enable autonomous promotion with the 2-condition gate. If NO-GO: revise holdout and rerun canary.]
```

- [ ] **Step 8: Commit** (fill in verdict before committing)

```bash
git add docs/plans/overfit-canary-results.md
git commit -m "docs(validation): overfit canary <GO|NO-GO> — <one-sentence finding>"
```

If NO-GO, stop here. Return to Phase 2 with holdout-v1.1 revisions, then rerun Phase 5 (subject to Step 6's termination rule).

---

## Phase 6: Enable Autonomous Promotion (Single-Judge Gate)

**Purpose:** With holdout validated, turn on autonomous promotion using a 6-gate rule: (1) holdout eligibility, (2) first-of-lane floor, (3) public-delta > epsilon, (4) holdout-delta > epsilon, (5) per-fixture win-rate ≥60%, (6) cross-family secondary judge (Claude Opus 4.7) confirms all 3-delta tests.

**Files:**
- Modify: `autoresearch/evolve_ops.py` — strengthen `is_promotable`
- Modify: `autoresearch/README.md` — document new rule
- Create: `tests/autoresearch/test_promotion_rule.py`

**Architectural note:** The existing `is_promotable` in `autoresearch/evolve_ops.py:241` returns a boolean from a hardcoded threshold check. This phase replaces it with a thin shim that gathers the full scoring context (primary + secondary judges, aggregate + per-fixture) and delegates the decision to the `promotion-judge` agent (Phase 0b). No magic numbers in `evolve_ops.py`; judgment lives in the agent, invariants stay as code.

- [ ] **Step 1: Write judge-mock tests for promotion rule**

Create `tests/autoresearch/test_promotion_rule.py`. Tests mock `call_promotion_judge` to return specific verdicts and assert `is_promotable` propagates them.

```python
from pathlib import Path
from unittest.mock import patch

# Unprefixed imports: autoresearch/ is on sys.path via conftest.py
from evolve_ops import is_promotable
from autoresearch.judges.promotion_judge import PromotionVerdict


def _entry(variant_id, public_score, *, secondary_public=None):
    """Minimum lineage entry shape for is_promotable.

    scores['composite'] and scores['<lane>'] are read by _objective_score_from_scores
    (see evaluate_variant.py:849). Per-fixture scores live under search_metrics.
    """
    entry = {
        "id": variant_id, "lane": "geo",
        "scores": {"composite": public_score, "geo": public_score},
        "search_metrics": {
            "suite_id": "search-v1", "composite": public_score,
            "domains": {"geo": {"score": public_score, "active": True,
                                "fixtures": {"geo-a": {"score": public_score}}}},
        },
        "promotion_summary": {"eligible_for_promotion": True, "holdout_composite": public_score - 0.05},
    }
    if secondary_public is not None:
        entry["secondary_scores"] = {"composite": secondary_public, "geo": secondary_public}
        entry["promotion_summary"]["secondary_holdout_composite"] = secondary_public - 0.05
        entry["search_metrics"]["domains"]["geo"]["fixtures"]["geo-a"]["secondary_score"] = secondary_public
    return entry


def _mock_verdict(decision: str, reasoning: str = "mock", confidence: float = 0.9):
    return PromotionVerdict(decision=decision, reasoning=reasoning, confidence=confidence, concerns=[])


def _patch_lineage_and_baseline(lineage_dict, baseline_entry):
    def _fake_lineage(_archive_dir):
        return lineage_dict
    return (
        patch("evolve_ops._load_latest_lineage", side_effect=_fake_lineage),
        patch("evaluate_variant._promotion_baseline", return_value=baseline_entry),
    )


def _run(lineage, baseline, variant_id, tmp_path, *, mock_decision="promote"):
    lin_patch, base_patch = _patch_lineage_and_baseline(lineage, baseline)
    with lin_patch, base_patch, patch(
        "autoresearch.judges.promotion_judge.call_promotion_judge",
        return_value=_mock_verdict(mock_decision),
    ):
        return is_promotable(tmp_path, variant_id, "geo")


def test_promotes_when_judge_says_promote(tmp_path):
    baseline = _entry("v006", 0.60, secondary_public=0.58)
    candidate = _entry("v007", 0.65, secondary_public=0.63)
    lineage = {"v006": baseline, "v007": candidate}
    assert _run(lineage, baseline, "v007", tmp_path, mock_decision="promote") is True


def test_rejects_when_judge_says_reject(tmp_path):
    baseline = _entry("v006", 0.60, secondary_public=0.58)
    candidate = _entry("v007", 0.65, secondary_public=0.63)
    lineage = {"v006": baseline, "v007": candidate}
    assert _run(lineage, baseline, "v007", tmp_path, mock_decision="reject") is False


def test_wrong_lane_short_circuits_judge(tmp_path):
    """Wrong-lane is an invariant guard, not a judgment call — judge never invoked."""
    candidate = dict(_entry("v007", 0.65), lane="core")
    lineage = {"v007": candidate}
    lin_patch, _ = _patch_lineage_and_baseline(lineage, None)
    with lin_patch, patch(
        "autoresearch.judges.promotion_judge.call_promotion_judge",
    ) as mock_judge:
        result = is_promotable(tmp_path, "v007", "geo")
    assert result is False
    mock_judge.assert_not_called()


def test_payload_contains_primary_and_secondary_scores(tmp_path):
    """Verify the judge receives complete cross-family data."""
    baseline = _entry("v006", 0.60, secondary_public=0.58)
    candidate = _entry("v007", 0.65, secondary_public=0.63)
    lineage = {"v006": baseline, "v007": candidate}
    lin_patch, base_patch = _patch_lineage_and_baseline(lineage, baseline)
    with lin_patch, base_patch, patch(
        "autoresearch.judges.promotion_judge.call_promotion_judge",
        return_value=_mock_verdict("promote"),
    ) as mock_judge:
        is_promotable(tmp_path, "v007", "geo")
    payload = mock_judge.call_args[0][0]
    assert payload["role"] == "promotion"
    assert payload["candidate"]["secondary_public_score"] is not None
    assert payload["baseline"]["secondary_public_score"] is not None
    assert "geo-a" in payload["candidate"]["per_fixture_primary"]
    assert "geo-a" in payload["candidate"]["per_fixture_secondary"]


def test_decision_logged_with_reasoning(tmp_path, monkeypatch):
    """Every judge call is persisted with reasoning trace."""
    import json
    log_path = tmp_path / "promotion-log.jsonl"
    monkeypatch.setattr("evolve_ops.PROMOTION_LOG", log_path)
    baseline = _entry("v006", 0.60, secondary_public=0.58)
    candidate = _entry("v007", 0.65, secondary_public=0.63)
    lineage = {"v006": baseline, "v007": candidate}
    lin_patch, base_patch = _patch_lineage_and_baseline(lineage, baseline)
    with lin_patch, base_patch, patch(
        "autoresearch.judges.promotion_judge.call_promotion_judge",
        return_value=_mock_verdict("reject", reasoning="insufficient holdout signal"),
    ):
        is_promotable(tmp_path, "v007", "geo")
    records = [json.loads(line) for line in log_path.read_text().splitlines() if line.strip()]
    assert len(records) == 1
    assert records[0]["decision"] == "reject"
    assert "insufficient holdout signal" in records[0]["reasoning"]


def test_promotes_first_of_lane_when_judge_approves(tmp_path):
    """No baseline; judge still sees the candidate scores and decides."""
    candidate = _entry("v007", 0.65, secondary_public=0.63)
    lineage = {"v007": candidate}
    assert _run(lineage, baseline=None, variant_id="v007", tmp_path=tmp_path, mock_decision="promote") is True


def test_rejects_first_of_lane_when_judge_rejects(tmp_path):
    """No baseline; judge sees a junk first variant and rejects."""
    candidate = _entry("v007", 0.15, secondary_public=0.13)
    lineage = {"v007": candidate}
    assert _run(lineage, baseline=None, variant_id="v007", tmp_path=tmp_path, mock_decision="reject") is False
```

- [ ] **Step 2: Run to verify failure**

Run: `pytest tests/autoresearch/test_promotion_rule.py -v`
Expected: FAIL — existing `is_promotable` at `evolve_ops.py:241` only checks `eligible_for_promotion`; it doesn't call the promotion-judge.

**Note on test rewrite:** tests in Step 1 currently assert threshold behavior ("+0.015 < epsilon → reject"). In the judge-based design they become mocked-judge tests: each case stubs `call_promotion_judge` to return a specific decision and asserts `is_promotable` propagates it. Rewrite tests before Step 3 lands — see Step 3d below.

- [ ] **Step 3: Promotion-judge drives `is_promotable` (replaces 3a/3b/3c)**

Replace the current threshold-driven `is_promotable` with a thin shim that gathers all measurements (primary scores, secondary scores, per-fixture breakdowns, holdout composites) and delegates the decision to the `promotion-judge` agent (Plan B Phase 0b). No magic numbers; the judge reasons about the full picture.

**Secondary-judge scoring infrastructure (lives on the evolution-judge-service per Plan A Phase 0c):**

Both primary (`codex` CLI → gpt-5.4) and secondary (`claude` CLI → claude-opus-4-7) scoring run on the **evolution-judge-service host**, not on the autoresearch host. `evaluate_search` / `evaluate_holdout` on the autoresearch side POST session artifacts (or artifact references) to the service via `/invoke/score`; the service executes BOTH CLI invocations and returns combined per-fixture + aggregate scores from both judges.

Lineage schema (unchanged — fields are populated from the service response):

- `entry["scores"]` — primary aggregate scores
- `entry["secondary_scores"]` — secondary aggregate scores
- `entry["search_metrics"]["domains"][domain]["fixtures"][fixture_id]["score"]` — primary per-fixture
- `entry["search_metrics"]["domains"][domain]["fixtures"][fixture_id]["secondary_score"]` — secondary per-fixture
- `entry["promotion_summary"]["holdout_composite"]` — primary holdout composite
- `entry["promotion_summary"]["secondary_holdout_composite"]` — secondary holdout composite

`evaluate_variant.py::_score_session` POSTs to `${EVOLUTION_JUDGE_URL}/invoke/score` with `{session_dir_ref, fixture, domain, lane, seeds}` and receives both primary+secondary score sets in one response. No separate `_score_session_secondary` function on the autoresearch side — the judge-service orchestrates both CLI invocations internally (parallelizable up to pool-of-3 per CLI). Extend `_aggregate_suite_results` to preserve both primary and secondary per-fixture scores in the lineage payload.

**Autoresearch host has no Anthropic/OpenAI credentials.** Autoresearch host has only:
- `EVOLUTION_JUDGE_URL` — where the judge service lives
- `EVOLUTION_INVOKE_TOKEN` — bearer token for service-to-service auth
- (trusted orchestrator only) `SESSION_ADMIN_TOKEN` — for session-judge prompt tuning

No `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `CLAUDE_API_KEY` / `CODEX_API_KEY` anywhere on the autoresearch host. The `claude` and `codex` CLI subscriptions live only on the evolution-judge-service host (and a separate session-judge-service host for session judges).

Cost: primary + secondary scoring are both CLI-subscription-auth calls — amortized against the fixed monthly subscription rather than per-token. Parallel throughput is bounded by the CLI pool-of-3 per judge type per service host. A full canary at 10 checkpoints × 10 seeds × 2 suites × 2 judges = 400 CLI invocations on the evolution-judge-service; at ~10s per call with pool-of-3 parallelism, ~22 minutes of judge-service wall-clock.

**`is_promotable` becomes a data-gather + judge-delegate shim:**

```python
# Module-level constants at top of evolve_ops.py:
# Promotion decisions, rollback checks, and other events use the unified
# events log from Phase 0a (`autoresearch/events.py::log_event`).


def _holdout_composite(entry: dict | None, *, key: str = "holdout_composite") -> float | None:
    if not isinstance(entry, dict):
        return None
    summary = entry.get("promotion_summary") or {}
    val = summary.get(key)
    return float(val) if isinstance(val, (int, float)) else None


def _per_fixture_scores(entry: dict | None, *, key: str = "score") -> dict[str, float]:
    """Extract per-fixture scores (primary by key='score', secondary by key='secondary_score')."""
    out: dict[str, float] = {}
    if not isinstance(entry, dict):
        return out
    sm = entry.get("search_metrics") or {}
    for _domain, payload in (sm.get("domains") or {}).items():
        if not isinstance(payload, dict):
            continue
        for fixture_id, record in (payload.get("fixtures") or {}).items():
            if not isinstance(record, dict):
                continue
            score = record.get(key)
            if isinstance(score, (int, float)):
                out[str(fixture_id)] = float(score)
    return out


def is_promotable(archive_dir: str | Path, variant_id: str, lane: str) -> bool:
    """Gather full scoring context, ask promotion-judge whether to promote.

    No hardcoded thresholds. The judge sees candidate + baseline scores from
    both primary and secondary judges (aggregate and per-fixture), holdout
    composites, and the lane's prior promotion history, then returns
    decision ∈ {promote, reject} with reasoning.

    Hard invariant kept programmatic: wrong-lane short-circuit (the judge
    should never be asked to decide about a lane-mismatched variant — that's
    a data bug, not a judgment call).
    """
    import evaluate_variant
    from autoresearch.judges.promotion_judge import call_promotion_judge

    latest = _load_latest_lineage(archive_dir)
    entry = latest.get(variant_id)
    base_record = {"variant_id": variant_id, "lane": lane}

    # Invariant (not judgment): the promotion check should only ever be called
    # for a variant whose lane matches. If not, data bug upstream.
    if str((entry or {}).get("lane") or "").strip().lower() != lane:
        _append_jsonl(PROMOTION_LOG, {
            **base_record, "decision": "reject", "reason": "wrong_lane",
            "source": "invariant_guard",
        })
        return False

    archive_root = Path(archive_dir).resolve()
    baseline_entry = evaluate_variant._promotion_baseline(archive_root, variant_id, lane)

    # Gather the full measurement stack for the judge.
    payload = {
        "role": "promotion",
        "candidate_id": variant_id, "lane": lane,
        "baseline_id": str(baseline_entry.get("id")) if baseline_entry else None,
        "candidate": {
            "public_score": evaluate_variant._objective_score_from_scores(
                entry.get("scores") if isinstance(entry, dict) else None, lane),
            "holdout_score": _holdout_composite(entry),
            "secondary_public_score": evaluate_variant._objective_score_from_scores(
                entry.get("secondary_scores") if isinstance(entry, dict) else None, lane),
            "secondary_holdout_score": _holdout_composite(entry, key="secondary_holdout_composite"),
            "per_fixture_primary": _per_fixture_scores(entry, key="score"),
            "per_fixture_secondary": _per_fixture_scores(entry, key="secondary_score"),
            "eligible_for_promotion_flag": bool(((entry or {}).get("promotion_summary") or {}).get("eligible_for_promotion")),
        },
        "baseline": None if baseline_entry is None else {
            "public_score": evaluate_variant._objective_score_from_scores(baseline_entry.get("scores"), lane),
            "holdout_score": _holdout_composite(baseline_entry),
            "secondary_public_score": evaluate_variant._objective_score_from_scores(
                baseline_entry.get("secondary_scores"), lane),
            "secondary_holdout_score": _holdout_composite(baseline_entry, key="secondary_holdout_composite"),
            "per_fixture_primary": _per_fixture_scores(baseline_entry, key="score"),
            "per_fixture_secondary": _per_fixture_scores(baseline_entry, key="secondary_score"),
        },
    }

    verdict = call_promotion_judge(payload)
    decision = verdict.decision == "promote"
    record = {
        **base_record,
        "decision": verdict.decision,
        "reasoning": verdict.reasoning,
        "confidence": verdict.confidence,
        "concerns": verdict.concerns,
        "payload_summary": {
            "cand_public": payload["candidate"]["public_score"],
            "cand_holdout": payload["candidate"]["holdout_score"],
            "cand_sec_public": payload["candidate"]["secondary_public_score"],
            "cand_sec_holdout": payload["candidate"]["secondary_holdout_score"],
            "base_id": payload["baseline_id"],
        },
    }
    _append_jsonl(PROMOTION_LOG, record)
    print(
        f"is_promotable: {variant_id} {verdict.decision.upper()} — {verdict.reasoning}",
        file=sys.stderr,
    )
    return decision
```

**Prerequisite (unchanged):** `evaluate_search` + `evaluate_holdout` must preserve per-fixture scores (primary AND secondary) in the lineage entry at `search_metrics.domains.<domain>.fixtures.<fixture_id>.{score,secondary_score}`. If the current aggregation step discards them, extend `_aggregate_suite_results` to keep them. Add a test `test_lineage_preserves_per_fixture_scores` asserting the shape is present after finalize.

**Audit log** — promotion decisions land in the unified events log via `log_event(kind="promotion_decision", ...)`. Query via `jq 'select(.kind=="promotion_decision")' ~/.local/share/gofreddy/events.jsonl`. Each record carries `{timestamp, kind, variant_id, lane, decision, reasoning, confidence, concerns, payload_summary}`. Spot-check weekly for reasoning quality / drift.

- [ ] **Step 3d: Rewrite promotion tests to mock the judge**

Replace the threshold-based tests in Step 1 with judge-mock tests. Each test stubs `call_promotion_judge` to return a specific `PromotionVerdict` and asserts `is_promotable` propagates the decision correctly.

```python
from unittest.mock import patch
from autoresearch.judges.promotion_judge import PromotionVerdict


def _mock_verdict(decision: str, reasoning: str = "mock", confidence: float = 0.9, concerns=None):
    return PromotionVerdict(decision=decision, reasoning=reasoning, confidence=confidence, concerns=concerns or [])


def _run(lineage, baseline, variant_id, tmp_path, mock_decision="promote"):
    from evolve_ops import is_promotable
    lin_patch, base_patch = _patch_lineage_and_baseline(lineage, baseline)
    with lin_patch, base_patch, patch(
        "autoresearch.judges.promotion_judge.call_promotion_judge",
        return_value=_mock_verdict(mock_decision),
    ):
        return is_promotable(tmp_path, variant_id, "geo")


def test_promotes_when_judge_says_promote(tmp_path):
    baseline = _entry("v006", 0.60, holdout_eligible=False)
    candidate = _entry("v007", 0.65, holdout_eligible=True)
    lineage = {"v006": baseline, "v007": candidate}
    assert _run(lineage, baseline, "v007", tmp_path, mock_decision="promote") is True


def test_rejects_when_judge_says_reject(tmp_path):
    baseline = _entry("v006", 0.60, holdout_eligible=False)
    candidate = _entry("v007", 0.65, holdout_eligible=True)
    lineage = {"v006": baseline, "v007": candidate}
    assert _run(lineage, baseline, "v007", tmp_path, mock_decision="reject") is False


def test_wrong_lane_short_circuits_judge(tmp_path):
    """Wrong-lane is an invariant guard, not a judgment call — judge never invoked."""
    from unittest.mock import patch
    from evolve_ops import is_promotable
    candidate = dict(_entry("v007", 0.65, holdout_eligible=True), lane="core")
    lineage = {"v007": candidate}
    lin_patch, _ = _patch_lineage_and_baseline(lineage, None)
    with lin_patch, patch(
        "autoresearch.judges.promotion_judge.call_promotion_judge",
    ) as mock_judge:
        result = is_promotable(tmp_path, "v007", "geo")
        assert result is False
        mock_judge.assert_not_called()


def test_payload_contains_primary_and_secondary_scores(tmp_path):
    """Verify the judge receives complete cross-family data."""
    from unittest.mock import patch
    from evolve_ops import is_promotable
    baseline = _entry("v006", 0.60, holdout_eligible=False)
    baseline["secondary_scores"] = {"composite": 0.58, "geo": 0.58}
    candidate = _entry("v007", 0.65, holdout_eligible=True)
    candidate["secondary_scores"] = {"composite": 0.63, "geo": 0.63}
    lineage = {"v006": baseline, "v007": candidate}
    lin_patch, base_patch = _patch_lineage_and_baseline(lineage, baseline)
    with lin_patch, base_patch, patch(
        "autoresearch.judges.promotion_judge.call_promotion_judge",
        return_value=_mock_verdict("promote"),
    ) as mock_judge:
        is_promotable(tmp_path, "v007", "geo")
    payload = mock_judge.call_args[0][0]
    assert payload["role"] == "promotion"
    assert payload["candidate"]["secondary_public_score"] is not None
    assert payload["baseline"]["secondary_public_score"] is not None


def test_decision_logged_with_reasoning(tmp_path, monkeypatch):
    """Every judge call is persisted with reasoning trace."""
    from unittest.mock import patch
    from evolve_ops import is_promotable, PROMOTION_LOG
    log_path = tmp_path / "promotion-log.jsonl"
    monkeypatch.setattr("evolve_ops.PROMOTION_LOG", log_path)
    baseline = _entry("v006", 0.60, holdout_eligible=False)
    candidate = _entry("v007", 0.65, holdout_eligible=True)
    lineage = {"v006": baseline, "v007": candidate}
    lin_patch, base_patch = _patch_lineage_and_baseline(lineage, baseline)
    with lin_patch, base_patch, patch(
        "autoresearch.judges.promotion_judge.call_promotion_judge",
        return_value=_mock_verdict("reject", reasoning="insufficient holdout signal"),
    ):
        is_promotable(tmp_path, "v007", "geo")
    records = [json.loads(line) for line in log_path.read_text().splitlines() if line.strip()]
    assert len(records) == 1
    assert records[0]["decision"] == "reject"
    assert "insufficient holdout signal" in records[0]["reasoning"]
```

Delete tests that asserted specific threshold behavior (`test_rejects_when_below_epsilon`, `test_rejects_when_first_of_lane_below_quality_floor`, `test_rejects_when_holdout_delta_within_epsilon`, etc.) — those thresholds no longer exist.

- [ ] **Step 4: Verify tests pass**

Run: `pytest tests/autoresearch/test_promotion_rule.py -v`
Expected: all 7 PASS.

Run: `pytest tests/autoresearch/ tests/freddy/ -x -q`
Expected: full suite still passes. In particular, `finalize_candidate_ids` and `write_finalized_shortlist` (which call `_promotion_baseline` directly) remain unchanged; the only new caller is `is_promotable`.

- [ ] **Step 5: Manual verification on geo lane**

`evolve.sh finalize` is deprecated (removed per `autoresearch/evolve.py:95-100`; finalize now runs automatically at the end of each `evolve.sh run` cycle when holdout is configured). Trigger it by running one iteration:

```bash
./autoresearch/evolve.sh run --iterations 1 --candidates-per-iteration 1 --lane geo
```

Expected: command completes without error. Either promotes the new candidate (if it beats baseline on both public and holdout) or reports no promotion due to the new 2-condition gate.

Spot-check the output manually: is the promotion decision defensible given the scores? If yes, ship. If no, investigate before enabling on other lanes.

- [ ] **Step 6: Auto-rollback via promotion-judge**

Autonomous promotion can make bad promotions. Production needs automatic detection-and-rollback, but "3 consecutive regressions below threshold X" is a judgment call — exactly the kind of threshold that's wrong in a new regime (new lane, post-judge-migration, different fixture distribution). Delegate to the `promotion-judge` agent (role: `rollback`).

**Why we still maintain a head-scores log:** the judge needs the trajectory. `_load_latest_lineage(archive_dir)` dedupes by variant id so there's no "N cycles of the same head re-scored" history in lineage. We maintain our own append-only log; the judge reads it.

Add to `autoresearch/evolve_ops.py`:

```python
HEAD_SCORES_LOG = Path.home() / ".local/share/gofreddy/head-scores.jsonl"
# REGRESSION events go through log_event(kind="regression_check", ...) — see Phase 0a.


def record_head_score(
    archive_dir: str | Path, lane: str, head_id: str,
    public_score: float, holdout_score: float | None,
    promoted_at: str,
) -> None:
    """Append this cycle's current-head scores to HEAD_SCORES_LOG.

    Called from evolve.py at the end of each run, after finalize has computed
    fresh scores for the current head. These scores become the trajectory
    the promotion-judge reads to decide whether to roll back.
    """
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "lane": lane,
        "head_id": str(head_id),
        "promoted_at": promoted_at,
        "public_score": float(public_score),
        "holdout_score": float(holdout_score) if holdout_score is not None else None,
    }
    _append_jsonl(HEAD_SCORES_LOG, record)


def check_and_rollback_regressions(archive_dir: str | Path, lane: str) -> bool:
    """Ask promotion-judge whether to roll back the current lane head.

    No hardcoded window or delta thresholds. The judge sees the full trajectory
    (pre-promotion baseline scores + post-promotion head scores) and decides
    `rollback` or `hold` with reasoning. Judge reasons about:
      - monotonic vs. noisy regression
      - magnitude vs. measurement noise
      - whether enough post-promotion data exists to be confident
      - whether the regression coincides with a known event
        (provider outage, fixture migration, etc. — operator can pass context)

    Returns True if rollback occurred, False otherwise. Decision appended to
    REGRESSION_LOG with reasoning trace.
    """
    from datetime import datetime
    from autoresearch.judges.promotion_judge import call_promotion_judge

    if not HEAD_SCORES_LOG.exists():
        return False

    # Parse defensively: every record must have (timestamp, lane, head_id,
    # promoted_at, public_score). A malformed record is a schema bug — log
    # loudly so it surfaces immediately instead of silently degrading the
    # rollback judgment.
    REQUIRED_FIELDS = {"timestamp", "lane", "head_id", "promoted_at", "public_score"}
    parsed_records: list[dict] = []
    with HEAD_SCORES_LOG.open() as handle:
        for line_no, raw in enumerate(handle, start=1):
            if not raw.strip():
                continue
            try:
                r = json.loads(raw)
            except json.JSONDecodeError as exc:
                sys.stderr.write(
                    f"⚠️  head-scores.jsonl line {line_no}: JSON parse error ({exc}); skipping\n"
                )
                continue
            if not isinstance(r, dict):
                sys.stderr.write(f"⚠️  head-scores.jsonl line {line_no}: not an object; skipping\n")
                continue
            missing = REQUIRED_FIELDS - set(r)
            if missing:
                sys.stderr.write(
                    f"⚠️  head-scores.jsonl line {line_no}: missing fields {sorted(missing)}; skipping\n"
                )
                continue
            # Parse timestamp as datetime so ordering is correct regardless of
            # string format drift (ISO-8601 with Z, with +00:00, epoch-ms, etc.).
            try:
                r["_timestamp_dt"] = datetime.fromisoformat(str(r["timestamp"]).replace("Z", "+00:00"))
                r["_promoted_at_dt"] = datetime.fromisoformat(str(r["promoted_at"]).replace("Z", "+00:00"))
            except (TypeError, ValueError) as exc:
                sys.stderr.write(
                    f"⚠️  head-scores.jsonl line {line_no}: unparseable timestamp ({exc}); skipping\n"
                )
                continue
            parsed_records.append(r)

    lane_records = [r for r in parsed_records if r["lane"] == lane]
    if not lane_records:
        return False
    lane_records.sort(key=lambda r: r["_timestamp_dt"])

    current_head_id = lane_records[-1]["head_id"]
    current_promoted_at = lane_records[-1]["_promoted_at_dt"]

    post_promotion = [
        r for r in lane_records
        if r["head_id"] == current_head_id and r["_timestamp_dt"] >= current_promoted_at
    ]
    pre_promotion = [
        r for r in lane_records
        if r["head_id"] != current_head_id and r["_timestamp_dt"] < current_promoted_at
    ]

    # Invariant (not judgment): no prior head → nothing to regress against.
    # Also: if there's literally one post-promotion entry, the judge can't
    # reason about trajectory yet — skip to save cost.
    if not pre_promotion or len(post_promotion) < 2:
        return False

    verdict = call_promotion_judge({
        "role": "rollback", "lane": lane,
        "current_head": current_head_id,
        "prior_head": pre_promotion[-1]["head_id"],
        "post_promotion_trajectory": post_promotion,
        "pre_promotion_trajectory": pre_promotion[-5:],  # last 5 entries is plenty of history
    })

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "lane": lane, "current_head": current_head_id,
        "prior_head": pre_promotion[-1]["head_id"],
        "decision": verdict.decision,
        "reasoning": verdict.reasoning,
        "confidence": verdict.confidence,
        "concerns": verdict.concerns,
    }

    if verdict.decision == "rollback":
        _append_jsonl(REGRESSION_LOG, record)
        print(
            f"⚠️  AUTO-ROLLBACK: {current_head_id} → {pre_promotion[-1]['head_id']}: "
            f"{verdict.reasoning}",
            file=sys.stderr,
        )
        subprocess.run(
            ["./autoresearch/evolve.sh", "promote", "--undo", "--lane", lane],
            check=True,
        )
        return True

    _append_jsonl(REGRESSION_LOG, record)
    return False
```

**Wiring** (two insertion points in `autoresearch/evolve.py`, at the end of each `run` iteration, post-finalize):

```python
# After finalize completes, before the iteration-end marker:

# 1. Re-score current head to produce this cycle's head-score entry.
head_id, head_lane = _load_current_head(archive_dir, lane)
head_public_score = _rescore_head_on_public_suite(head_id, lane)  # cache-first, cheap
head_holdout_score = _latest_holdout_score(head_id, lane)  # None if no fresh holdout
promoted_at = _load_head_promoted_at(archive_dir, head_id)
record_head_score(
    archive_dir, lane, head_id,
    public_score=head_public_score,
    holdout_score=head_holdout_score,
    promoted_at=promoted_at,
)

# 2. Check and act.
check_and_rollback_regressions(archive_dir, lane)
```

`_rescore_head_on_public_suite` calls `evaluate_search` on the current head via cache (`FREDDY_FIXTURE_POOL=search-v1`). Cost: ~zero after first cycle because cache is warm. `_latest_holdout_score` reads the most-recent finalize record's holdout composite if it exists; holdout scoring is not re-run per cycle because holdout runs are expensive (tens of minutes). Limitation: holdout regressions are captured less often than public ones — document in README. If per-cycle holdout rescoring proves necessary in practice, it lands in a follow-up initiative once cost/signal is measured.

Add tests `tests/autoresearch/test_regression_rollback.py`:

```python
def test_no_rollback_when_log_absent(tmp_path): ...                    # HEAD_SCORES_LOG missing, judge never invoked
def test_no_rollback_when_only_one_prior_entry(tmp_path): ...          # invariant: need ≥2 post-promotion entries
def test_rollback_when_judge_says_rollback(tmp_path): ...              # judge returns "rollback" → runs promote --undo
def test_no_rollback_when_judge_says_hold(tmp_path): ...               # judge returns "hold" → no-op
def test_decision_logged_with_reasoning(tmp_path): ...                 # REGRESSION_LOG contains reasoning trace
def test_rollback_passes_trajectory_to_judge(tmp_path): ...            # verify payload shape
```

Mock both `subprocess.run` (to assert `evolve.sh promote --undo --lane <lane>` command shape) and `call_promotion_judge`. Seed HEAD_SCORES_LOG inline via `tmp_path / "head-scores.jsonl"` and patch `HEAD_SCORES_LOG` to that path.

- [ ] **Step 7: Document new rule (+ rollback + audit log)**

Update `autoresearch/README.md` "Evolution Loop" section:
- Document the 2-condition promotion rule (holdout eligible + public delta > 0.02).
- Document the auto-rollback: current head reverts automatically after 3 consecutive cycles underperforming the prior head by >0.02.
- Document the unified events log at `~/.local/share/gofreddy/events.jsonl` (kinds: `promotion_decision`, `regression_check`, `saturation_cycle`, `judge_drift`, `judge_raw`, `content_drift`). Provide a sample `jq` query for "every rollback in the last 30 days": `jq 'select(.kind=="regression_check" and .decision=="rollback")' events.jsonl`.
- Note that MAD confidence scoring and IRT dashboard are separate initiatives (not part of this plan).

- [ ] **Step 8: Commit**

```bash
git add autoresearch/evolve_ops.py autoresearch/evolve.py autoresearch/README.md \
        tests/autoresearch/test_promotion_rule.py \
        tests/autoresearch/test_regression_rollback.py
git commit -m "feat(evolve): autonomous promotion gate + audit log + auto-rollback on persistent regression"
```

---


## Acceptance Criteria (done = all hold)

- `docs/plans/fixture-taxonomy-matrix.md` (in-repo) contains search-v1 only (~30 entries); `~/.config/gofreddy/holdouts/holdout-v1-taxonomy.md` (out-of-repo, 600) contains the 16 holdout entries.
- `~/.config/gofreddy/holdouts/holdout-v1.json` exists with 16 fixtures, permissions `600`
- `autoresearch/eval_suites/holdout-v1.json.example` exists in-repo, redacted, carries `"is_redacted_example": true` at the top level
- `autoresearch/eval_suites/search-v1.json` bumped to version `1.1` with 6-8 new fixtures
- `freddy fixture staleness --pool holdout-v1` shows all 16 as `fresh`
- `freddy fixture staleness --pool search-v1` shows all ~30 as `fresh`
- `docs/plans/search-v1-migration-scores.md` has baseline dry-run scores for every search-v1 fixture
- `docs/plans/overfit-canary-results.md` exists with pre-canary sanity result + 20-iteration checkpoints (5 seeds each) + pattern-based verdict
- If GO: one iteration of `./autoresearch/evolve.sh run --lane geo --iterations 1 --candidates-per-iteration 1` triggers the 2-condition promotion gate; `is_promotable` unit tests pass
- If NO-GO after one revision cycle: plan pauses at Phase 5 per the termination rule in Step 6; next step is the separate MAD-confidence-scoring initiative, NOT a third holdout revision
- No in-repo file (TAXONOMY.md, fixture-taxonomy-matrix.md, lineage artifacts committed to git) names any holdout fixture_id

**Production hardening:**

- Holdout refresh runs on process-boundary-isolated infrastructure: `.github/workflows/holdout-refresh.yml` exists and succeeds on `workflow_dispatch`; cache artifacts land on the evolution machine via `gh run download`. Evolution runs do NOT have access to holdout credentials (verifiable: `env | grep -i holdout` during `./autoresearch/evolve.sh run` returns nothing). If local-dev fallback (Option C) is used, the commit message explicitly calls it out.
- `autoresearch/saturation_log.py` exists; post-finalize writes one tuple per public fixture via `log_event(kind="saturation_cycle", ...)` to the unified events log; `freddy fixture staleness` tags fixtures the quality-judge flags as `rotate_now` (no hardcoded beat-rate threshold)
- `autoresearch/judge_calibration.py` exists; baseline is recorded; `--check` returns 0 on a stable judge and 1 when any calibration pair drifts beyond 2×MAD
- `events.jsonl` records every `is_promotable` decision as `kind="promotion_decision"` and every rollback check as `kind="regression_check"`
- `check_and_rollback_regressions` runs after each `evolve.sh run` finalize; auto-rollback test suite passes
- Anchor fixtures' refresh flow stores `content_sha1`; quality-judge verdict of `material` writes `kind="content_drift"` to events.jsonl and stderr

---

## Execution Options

Prerequisite and phase sequencing are in the top-of-doc header. Recommended hybrid: subagent-driven for Phases 2–3 (fixture authoring benefits from per-phase review); inline for Phases 1/4/5/6.

**After Plan B lands:** the separate initiatives covering MAD confidence scoring, `lane_checks.sh` correctness gates, lane scheduling rework, and the IRT benchmark-health dashboard can proceed. None is required for the 6-gate promotion rule this plan ships.
