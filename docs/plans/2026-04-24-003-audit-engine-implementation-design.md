---
title: "Implementation design: Audit engine (src/audit/) + marketing_audit autoresearch lane"
type: implementation-design
status: active
date: 2026-04-24
scope: Workload-specific. Audit engine and its self-improving autoresearch lane only. Not a generic runtime.
consumers:
  - implementing agent building src/audit/ and the marketing_audit lane
sources:
  - docs/plans/2026-04-20-002-feat-automated-audit-pipeline-plan.md (engine spec / market-domain knowledge)
  - docs/plans/2026-04-22-005-marketing-audit-lens-catalog.md (locked 149-lens catalog, v2 2026-04-23)
  - docs/plans/2026-04-22-006-marketing-audit-lens-ranking.md (lens tiers + cutoff)
  - docs/plans/2026-04-24-001-audit-pipeline-research-record.md (borrowable primitives from harness/ + autoresearch/)
  - docs/plans/2026-04-23-003-agency-integration-plan.md (phasing context; Bundle 9 + Bundle 10 collapse into this doc)
  - docs/plans/2026-04-23-004-ral-runtime-design.md (informational — generic runtime, not in scope here)
---

# Implementation design: Audit engine + marketing_audit lane

## 0. What this doc is

**Source-material hierarchy:**

- Plan 002 = what to build (market/domain knowledge, 10 implementation units U1–U10, 6-stage pipeline, gates, commercial flow)
- Catalog 005 + ranking 006 = content (149 always-on lenses + 25 vertical + 10 geo + 5 segment bundles + 9 Phase-0 meta-frames, locked v2)
- Research record 2026-04-24-001 = how to wire it (12 harness primitives + 17 autoresearch primitives + 10 net-new gaps with file:line refs)
- This doc = the executable bridge — file paths, module layout, exact edits, rubric prompt sketches, dependency-aware execution sequence

Implementing agents read this doc as the primary reference and dip into 002 / 005 / the research record when a specific detail is cited. They do **not** re-research harness or autoresearch; the record is authoritative.

## 1. Scope boundaries

**In scope:**
- `src/audit/` — the audit engine (greenfield Python module)
- `src/evaluation/` extension with MA-1..MA-8 rubric for the marketing_audit domain
- `autoresearch/` lane registration edits (5 files) + 3 new autoresearch files
- `configs/audit/lenses.yaml` — the lens registry (transcription of catalog 005 into YAML)
- `cli/freddy/commands/audit.py` — audit CLI
- New cross-cutting primitives: `evolve_lock` mutex, engagement long-loop judge, pin tag

**Out of scope:**
- Generic RAL runtime (covered by `2026-04-23-004-ral-runtime-design.md` — informational only)
- Lens catalog content edits (catalog 005 is locked v2 2026-04-23 — this doc wraps runtime around it)
- Agency-platform expansion (weekly briefs, content factory, video studio — all deferred per agency-integration plan)

## 2. Locked architectural decisions

Resolving the 6 open questions from research record §7 and the agency-integration plan's 10 decisions. These are locked. Changing one requires revisiting this design.

| # | Question | Decision | Rationale |
|---|---|---|---|
| 1 | asyncio vs threading for Stage 2 | **asyncio + Semaphore(7)** | SDK is async-native; `asyncio.gather(return_exceptions=True)` gives partial completion when one lens fails; TaskGroup's fail-fast kills the audit |
| 2 | Checkpoint granularity | **per-lens** (`stage2_subsignals/L<id>_*.json`) | Resume correctness; operator can re-run one failed lens without redoing 148 others |
| 3 | Worktree per audit | **no** | Audit doesn't mutate the repo; state isolated to `clients/<slug>/audit/` |
| 4 | Concurrency model | **single-worker per audit in v1** (active_run lock per slug); **queue + multiple workers in v2** | Simpler first; scales when a second concurrent audit becomes necessary |
| 5 | Engine choice | **SDK for all agent roles** (Claude); Codex CLI optional for one judge only if needed | Plan 002 commits to SDK; per-role `max_budget_usd` requires SDK |
| 6 | Inner loop on-by-default | **opt-in per agent role** via variant config; v3 becomes evolvable | Adds cost when judges fail; start conservative |
| 7 | Stage-prompt externalization | **prompts live in `autoresearch/archive/current_runtime/programs/marketing_audit/prompts/`** — loaded by audit engine at runtime | Enables meta-agent mutation without touching `src/audit/` code |
| 8 | Runtime materialization | **`runtime_bootstrap.py` materializes marketing_audit variant into `archive/current_runtime/` same as other lanes**; audit engine reads prompts from there | Reuses production pattern; audit runs against promoted variant automatically |
| 9 | Concurrency between evolve and live audit | **global `state.evolve_lock` mutex** — live audit refuses to start if evolve active; evolve refuses if any audit active | Prevents rate-limit thrash and state-machine corruption |
| 10 | Telemetry blindness | **MA-1..MA-8 scores + ship-gate edit counts + engagement signals NEVER land in variant workspace**; live at `autoresearch/metrics/marketing_audit/` and `audits/lineage.jsonl` | Anti-Goodhart; prevents meta-agent from gaming judges |
| 11 | Autoresearch evaluator dependency | **pin to git tag `autoresearch-audit-stable-YYYYMMDD` at first audit ship** | Autoresearch has 27 commits / 60d, 11% fix rate; don't rebuild audit on shifting sand |
| 12 | Fitness weight for engagement signal | **first 3 generations weight engagement = 0; rebalance once 60d lag has data** | Signal lag means early variants only have 3 signals; engagement comes online later |

## 3. Complete module map

New and modified files, grouped by subsystem.

### 3.1 `src/audit/` — the audit engine (greenfield)

```
src/audit/
├── __init__.py
├── cli_entrypoints.py        # thin wrappers; actual CLI in cli/freddy/commands/audit.py
├── state.py                  # AuditState dataclass; atomic JSON persist (borrows harness/sessions.py)
├── sessions.py               # SessionsFile per-role session_id tracking (ports harness/sessions.py:56-102)
├── cost_ledger.py            # per-call max_budget_usd + per-stage soft warn + total hard breaker
├── graceful_stop.py          # atomic flag + SIGTERM handler (ports harness/run.py:344-350)
├── agent_runner.py           # ClaudeSDKClient wrapper: cost capture, session persist, tenacity retries, fallback_model
├── resume.py                 # _viable_resume_id + skip-completed-lenses logic
├── cleanup.py                # atexit + SIGTERM handlers with signal.alarm(5) cap on slack notification
├── events.py                 # per-audit events.jsonl + optional global append (flock concurrent safety)
├── prompts_loader.py         # loads stage prompts from autoresearch/archive/current_runtime/programs/marketing_audit/prompts/
│
├── preflight/                # Stage-1a deterministic pre-pass + audit-level preflight
│   ├── __init__.py
│   ├── audit_preflight.py    # port harness/preflight.py pattern; audit-specific checks
│   ├── dns_email_security.py # SPF, DKIM, DMARC
│   ├── well_known.py         # robots.txt, sitemap.xml, security.txt, humans.txt
│   ├── json_ld.py            # parse homepage JSON-LD; extract org + product schema
│   ├── trust_badges.py       # regex scan for trust-signal badges
│   ├── security_headers.py   # CSP, HSTS, X-Content-Type-Options, etc.
│   ├── social_meta.py        # OG + Twitter card tags
│   ├── brand_assets.py       # logo URL, favicon, apple-touch-icon
│   └── tooling_fingerprint.py # detect analytics, CDP, CRM, marketing tools from DOM + HTTP headers
│
├── stages/                   # Stage runners
│   ├── __init__.py
│   ├── _base.py              # Stage ABC with StageResult TypedDict
│   ├── stage_0_intake.py
│   ├── stage_1a_preflight.py # orchestrator calling preflight/ modules
│   ├── stage_1b_signals.py   # bundle-activation signal detection
│   ├── stage_2_lenses.py     # parallel lens fan-out (asyncio + Semaphore(7))
│   ├── stage_3_synthesis.py  # SubSignal → ParentFinding aggregation
│   ├── stage_4_proposal.py
│   ├── stage_5_deliverable.py # Jinja2 + WeasyPrint
│   └── stage_6_publish.py    # R2 upload + Cloudflare Worker relay + Slack
│
├── bundles.py                # conditional bundle activation (25 vertical + 10 geo + 5 segment)
├── lenses.py                 # lenses.yaml loader + per-lens dispatch
├── subsignals.py             # SubSignal parsing with skip-not-raise; ports harness/findings.py:68-90
├── synthesis.py              # SubSignal → ParentFinding aggregation (net-new primitive)
├── inner_loop.py             # judge → revise-once-on-fail → skip-not-raise (opt-in per role)
│
├── judges/                   # audit-specific judges
│   ├── __init__.py
│   ├── paraphrase.py         # verify evidence quotes exist (thin wrapper over src/evaluation/judges/)
│   ├── calibration.py        # adjust gradient scores (thin wrapper)
│   └── engagement.py         # long-loop T+60d, reads audits/lineage.jsonl, writes back fitness signal
│
├── render.py                 # Jinja2 → HTML, WeasyPrint → PDF (Stage 5 helpers)
├── publish.py                # R2 upload + Cloudflare Worker relay
├── payment.py                # Stripe Checkout (phase 2 — stub in phase 1 with manual invoice CLI)
│
├── exceptions.py             # CostBreakerExceeded, RateLimitHit, EngineExhausted, WalltimeExceeded, CostCeilingReached, ViableResumeFailed, MalformedSubSignalError (logged not raised)
│
└── templates/                # Jinja2 templates
    ├── deliverable.html.j2
    ├── deliverable_print.css
    └── free_scan.html.j2
```

### 3.2 `cli/freddy/commands/audit.py`

Typer subcommand group:

```
freddy audit run --client <slug> --domain <host>
freddy audit run --resume <audit_id>
freddy audit scan --domain <host>                     # Free AI Visibility Scan (lead-magnet)
freddy audit status <audit_id>
freddy audit costs <audit_id>
freddy audit publish <audit_id>                       # ship gate
freddy audit invoice <audit_id> --email <addr>        # phase-1 manual invoicing
freddy audit attach-gsc <audit_id> --service-account <path>
freddy audit attach-budget <audit_id> --budget-usd <n>
freddy audit attach-winloss <audit_id> --file <path>  # PII redaction applied
```

Other 002 attach commands (ads, esp, survey, assets, demo, crm) deferred to phase 2 per agency-integration plan.

### 3.3 `src/evaluation/` — extension for marketing_audit domain

Edits to existing files (~30 LOC total per research §3.8):

```
src/evaluation/models.py:160          # add "marketing_audit" to domain Literal
src/evaluation/rubrics.py             # add MA-1..MA-8 RubricTemplate instances
src/evaluation/service.py             # add entries to _DOMAIN_CRITERIA + _JUDGE_PRIMARY_DELIVERABLE
src/evaluation/structural.py          # add marketing_audit structural validator
src/evaluation/judges/marketing_audit.py  # NEW file — audit-specific judge orchestration if needed
```

### 3.4 `autoresearch/` — lane registration

Exact 5-file edits:

```
autoresearch/lane_runtime.py:12       # LANES += ("marketing_audit",)
autoresearch/lane_paths.py:36-37,44-77 # LANES + WORKFLOW_PREFIXES for marketing_audit
autoresearch/evolve.py:44             # ALL_LANES += ("marketing_audit",)
autoresearch/frontier.py:15-16        # LANES + DOMAINS (reframe if non-domain)
autoresearch/evaluate_variant.py:44-49 # DELIVERABLES["marketing_audit"] = {...}
```

Three new files:

```
autoresearch/archive/current_runtime/programs/marketing_audit-session.md
autoresearch/archive/current_runtime/programs/marketing_audit-evaluation-scope.yaml
autoresearch/archive/current_runtime/programs/marketing_audit/prompts/     # mutable stage prompts live here
    stage_0_intake.md
    stage_1a_preflight.md
    stage_1b_signals.md
    stage_2_lens_meta.md
    stage_3_synthesis.md
    stage_4_proposal.md
    inner_loop_critic.md
autoresearch/eval_suites/marketing-audit-v1.json
autoresearch/critique_manifest_marketing_audit.json  # SHA256 of MA-1..MA-8 frozen boundary
```

### 3.5 `configs/audit/lenses.yaml` — lens registry

Single YAML transcribing catalog 005 (149 always-on + 25 vertical + 10 geo + 5 segment + 9 Phase-0 meta-frames). Per-lens fields:

```yaml
- id: L0012
  name: "Organic Search Visibility Depth"
  tier: 1
  rank: 12
  phase: 1                 # 0 = Phase-0 meta-frame, 1a = deterministic pre-pass, 1b = signal detection, 2 = lens, 3 = synthesis
  providers: ["dataforseo", "gsc"]
  detection_signals: []    # empty = always-on
  cost_est_usd: 0.45
  timeout_s: 45
  subsignal_schema:        # Pydantic schema for the SubSignal this lens emits
    severity: enum[high|medium|low]
    evidence: list[str]
    metric_values: dict
  rubric_anchors:          # optional per-lens scoring guidance for Stage 3 synthesis
    high: "..."
    medium: "..."
    low: "..."
```

Size estimate: ~1,500–2,000 lines of YAML for 198 total entries. Transcription from 005 is ~4–6 hours of careful work (not mechanical). See §9.1.

### 3.6 Global state

```
~/.local/share/gofreddy/
    events.jsonl             # global events log (ports autoresearch/events.py)
    state.active_audits/     # one lock file per in-flight audit (slug-based)
    state.evolve_lock        # global mutex between evolve and any live audit
```

Per-audit state:

```
clients/<slug>/audit/<audit_id>/
    state.json               # AuditState (atomic writes)
    cost_log.jsonl           # per-call cost (append-only)
    events.jsonl             # per-audit event trail
    sessions/
        pre_discovery.json
        <role>.json
    stage1a_preflight/       # deterministic pre-pass outputs
        dns_email_security.json
        well_known.json
        ...
    stage1b_signals/
        vertical_detected.json
        geo_detected.json
        segment_detected.json
    stage2_subsignals/
        L<id>_<slug>.json    # per-lens atomic write; enables per-lens resume
    stage3_synthesis/
        findings.md
        report.md
        report.json
    proposal/
        proposal.md
    deliverable/
        report.html
        report.pdf
    gap_report.md            # malformed SubSignals logged here
```

Global audit lineage:

```
audits/lineage.jsonl         # per-audit row; feeds marketing_audit fitness function
```

## 4. Bundle A — Audit engine foundation

Goal: every primitive the stages will rely on. No audit logic yet; just the infrastructure that supports it.

Dependencies: none (builds from the two borrowed systems).

### 4.1 `src/audit/state.py`

AuditState dataclass with atomic persistence. Port `harness/sessions.py:56-102` `SessionsFile` pattern.

```python
# src/audit/state.py
from __future__ import annotations
import json
import os
import tempfile
import threading
from dataclasses import dataclass, field, asdict
from pathlib import Path
from datetime import datetime

@dataclass
class AuditState:
    audit_id: str
    client_slug: str
    prospect_domain: str
    status: str                  # "intake" | "stage_1a" | "stage_1b" | "stage_2" | "stage_3" | ...
    created_at: str
    updated_at: str
    total_cost_usd: float = 0.0
    soft_warn_fired: bool = False
    hard_breaker_fired: bool = False
    graceful_stop_requested: bool = False
    sessions: dict = field(default_factory=dict)   # role -> {session_id, last_turn, last_cost_usd, status}
    completed_lenses: list[str] = field(default_factory=list)
    failed_lenses: list[str] = field(default_factory=list)
    bundles_activated: list[str] = field(default_factory=list)
    pause_reason: str | None = None                # None | "cost_ceiling" | "awaiting_input_gsc" | "awaiting_payment" | "awaiting_operator_review"

class AuditStateFile:
    def __init__(self, path: Path):
        self._path = path
        self._lock = threading.Lock()

    def load(self) -> AuditState:
        with self._lock:
            raw = json.loads(self._path.read_text())
            return AuditState(**raw)

    def save(self, state: AuditState):
        with self._lock:
            state.updated_at = datetime.utcnow().isoformat()
            tmp = self._path.with_suffix(".tmp")
            tmp.write_text(json.dumps(asdict(state), indent=2))
            os.replace(tmp, self._path)  # atomic rename

    def update(self, mutator):
        """Read-mutate-write atomic."""
        with self._lock:
            state = AuditState(**json.loads(self._path.read_text()))
            mutator(state)
            self.save(state)
```

Key invariant: every mutation goes through `update()` so concurrent Stage-2 lens agents don't clobber each other's partial writes.

### 4.2 `src/audit/sessions.py`

Port `harness/sessions.py:56-102` essentially verbatim; namespaced per audit. Captures `ClaudeSDKClient` `ResultMessage.session_id` on FIRST turn and persists immediately (research §2.1 gotcha: if crash before first ResultMessage, session can't resume).

### 4.3 `src/audit/cost_ledger.py`

Net-new primitive (research §4 gap #1). Neither harness nor autoresearch has per-call cost cap.

```python
# src/audit/cost_ledger.py
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
import json
from pathlib import Path

SOFT_WARN_USD = 100.0
HARD_BREAKER_USD = 150.0
SCAN_CEILING_USD = 2.0

class CostCeilingReached(Exception):
    def __init__(self, ceiling: float, current: float):
        self.ceiling = ceiling
        self.current = current
        super().__init__(f"cost ceiling {ceiling} reached (current={current})")

class CostLedger:
    def __init__(self, cost_log_path: Path, audit_state, mode: str = "audit"):
        """mode: 'audit' uses SOFT_WARN_USD / HARD_BREAKER_USD; 'scan' uses SCAN_CEILING_USD."""
        self._log = cost_log_path
        self._state = audit_state
        self._mode = mode
        self._soft = SCAN_CEILING_USD * 0.8 if mode == "scan" else SOFT_WARN_USD
        self._hard = SCAN_CEILING_USD if mode == "scan" else HARD_BREAKER_USD

    def record(self, role: str, cost_usd: float, metadata: dict):
        with self._log.open("a") as f:
            f.write(json.dumps({
                "role": role,
                "cost_usd": cost_usd,
                "metadata": metadata,
                "ts": datetime.utcnow().isoformat(),
            }) + "\n")
        self._state.update(lambda s: setattr(s, "total_cost_usd", s.total_cost_usd + cost_usd))

        total = self._state.load().total_cost_usd
        if total >= self._hard:
            self._state.update(lambda s: setattr(s, "hard_breaker_fired", True))
            self._state.update(lambda s: setattr(s, "pause_reason", "cost_ceiling"))
            raise CostCeilingReached(self._hard, total)
        if total >= self._soft and not self._state.load().soft_warn_fired:
            self._state.update(lambda s: setattr(s, "soft_warn_fired", True))
            # Slack notification here
```

Per-agent budget via SDK `max_budget_usd`:

```python
# inside agent_runner.py
options = ClaudeAgentOptions(
    model="claude-sonnet-4-6",
    fallback_model="claude-haiku-4-5-20251001",
    max_budget_usd=per_role_budget,  # loaded from variant config
    max_turns=20,
)
```

### 4.4 `src/audit/graceful_stop.py`

Port `harness/run.py:344-350` atomic flag + SIGTERM handler.

```python
# src/audit/graceful_stop.py
import signal
import threading

class GracefulStop:
    def __init__(self, state_file):
        self._state_file = state_file
        self._lock = threading.Lock()
        signal.signal(signal.SIGTERM, self._handle_sigterm)
        signal.signal(signal.SIGINT, self._handle_sigterm)

    def _handle_sigterm(self, signum, frame):
        with self._lock:
            self._state_file.update(
                lambda s: setattr(s, "graceful_stop_requested", True)
            )

    def requested(self) -> bool:
        return self._state_file.load().graceful_stop_requested
```

Stage-2 fan-out and any loop that can run long check `graceful_stop.requested()` between items and break cleanly.

### 4.5 `src/audit/agent_runner.py`

Thin SDK wrapper combining: cost capture on `ResultMessage`, session_id persist, tenacity retries with jitter, `fallback_model`, `max_budget_usd`, silent-hang detection, rate-limit handling.

```python
# src/audit/agent_runner.py (sketch)
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
import tenacity
from datetime import datetime, timedelta

class AgentRunner:
    def __init__(self, state, sessions, cost_ledger, graceful_stop, config):
        self._state = state
        self._sessions = sessions
        self._cost = cost_ledger
        self._stop = graceful_stop
        self._config = config

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential_jitter(initial=1, max=30),
        retry=tenacity.retry_if_exception_type(TransientAgentError),
    )
    async def run(self, role: str, prompt: str, *, resume_session_id: str | None = None) -> ResultMessage:
        if self._stop.requested():
            raise GracefulStopRequested()
        options = ClaudeAgentOptions(
            model=self._config.model_for(role),
            fallback_model=self._config.fallback_for(role),
            max_budget_usd=self._config.budget_for(role),
            max_turns=self._config.max_turns_for(role),
            resume_session_id=resume_session_id,
        )
        client = ClaudeSDKClient(options=options)
        try:
            first_result = True
            async for msg in client.stream(prompt):
                if isinstance(msg, ResultMessage):
                    if first_result:
                        self._sessions.record(role, msg)  # capture session_id ASAP
                        first_result = False
                    self._cost.record(role, msg.total_cost_usd, {"turns": msg.num_turns})
                    return msg
        finally:
            await client.close()
```

### 4.6 `src/audit/preflight/audit_preflight.py`

Port `harness/preflight.py:40-280` pattern. Audit-specific checks per research §2.9:

```python
# src/audit/preflight/audit_preflight.py (sketch)
REQUIRED_ENV_VARS = [
    "CLAUDE_CODE_OAUTH_TOKEN",  # or ANTHROPIC_API_KEY
    "DATAFORSEO_LOGIN", "DATAFORSEO_PASSWORD",
    "COMPETITIVE_ADYNTEL_API_KEY", "COMPETITIVE_ADYNTEL_EMAIL",
    "CLORO_API_KEY",
    "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET",
    "CLOUDFLARE_WORKER_URL", "CLOUDFLARE_WORKER_SECRET",
    "SLACK_WEBHOOK_URL",
]

def check_all(config, audit_id) -> PreflightResult:
    checks = [
        check_required_env(REQUIRED_ENV_VARS),
        check_no_production_env(),                          # refuse if ENVIRONMENT=production
        check_cli_tools(["claude", "freddy"]),
        check_auth_claude(),
        check_target_reachable(config.prospect_domain),
        check_r2_writable(config.r2_bucket),
        check_cloudflare_worker(config.worker_url),
        check_dataforseo_credits(min_balance=5.00),
        check_cloro_credits(min_balance=5.00),
        check_active_run_lock(config.client_slug),          # refuse if another audit on this slug in flight
        check_cost_ceiling_sane(config.soft_warn, config.hard_breaker),
        check_sitemap_size(config.prospect_domain, max_urls=500, override=config.override_preflight),
        check_domain_age(config.prospect_domain, min_days=30),
        check_evolve_lock_clear(),                          # refuse if evolve running
    ]
    return PreflightResult.from_checks(checks)
```

### 4.7 `src/audit/events.py` + `src/audit/cleanup.py`

- Events: port `autoresearch/events.py` append-only + flock pattern. Per-audit file + optional global append.
- Cleanup: port `harness/worktree.py:236-254`. atexit + SIGTERM handlers flush state, flush events, clear active_run lock, send Slack, `signal.alarm(5)` cap on handlers.

### 4.8 `src/audit/resume.py`

Port `harness/run.py:78-101`:

```python
def _viable_resume_id(session_id: str) -> bool:
    encoded_cwd = str(Path.cwd()).replace("/", "-")
    sdk_jsonl = Path.home() / ".claude" / "projects" / encoded_cwd / f"{session_id}.jsonl"
    return sdk_jsonl.exists()

def build_resume_plan(state: AuditState) -> ResumePlan:
    plan = ResumePlan()
    for role, session_data in state.sessions.items():
        if not _viable_resume_id(session_data["session_id"]):
            plan.must_restart.append(role)
        else:
            plan.can_resume.append(role)
    plan.stage_2_skip = list(state.completed_lenses)
    return plan
```

Operator confirms un-resumable sessions before `freddy audit run --resume` proceeds.

### 4.9 Done signal for Bundle A

- `freddy audit run --client fixture --domain example.com --preflight-only` completes preflight and prints clean pass/fail matrix.
- State file written atomically; concurrent writes from two test threads never corrupt.
- SIGTERM to a running audit sets graceful_stop_requested and the process exits 0 within 5s.
- Events file rotates at 100 MB; flock prevents concurrent-writer corruption.

## 5. Bundle B — Audit engine stages (the product core)

Depends on: Bundle A.

Goal: implement Stages 0–4 per plan 002 U3, U4, U5 §Stage 3 + §Stage 4.

### 5.1 Stage 0 — Intake

Cheap LLM prompt summarizing prospect + capturing operator-supplied context (vertical hint, known competitor list if any, goals). Output: `state.json.intake`.

### 5.2 Stage 1a — Deterministic pre-pass

Orchestrator that dispatches to 8 Python check modules under `src/audit/preflight/`. No LLM. Results land in `stage1a_preflight/*.json`. Run in parallel (`asyncio.gather`); each check has internal timeout (~5s).

Pattern for each check module:

```python
# src/audit/preflight/dns_email_security.py
async def check(prospect_domain: str) -> CheckResult:
    spf = await _probe_txt(prospect_domain, "v=spf1")
    dkim = await _probe_dkim_selectors(prospect_domain)
    dmarc = await _probe_txt(f"_dmarc.{prospect_domain}", "v=DMARC1")
    return CheckResult(
        signals={"spf": spf.present, "dkim": dkim.selectors, "dmarc": dmarc.present},
        severity=_compute_severity(spf, dkim, dmarc),
        evidence=[spf.record, *dkim.records, dmarc.record],
    )
```

### 5.3 Stage 1b — Bundle-activation signals

Lightweight detection sweep that fires once. Detects: vertical (b2b_saas, ecommerce, marketplace, etc.), geo (us, eu, apac, etc.), segment (enterprise, mid-market, smb). Signals derived from Stage 1a outputs + homepage crawl + tooling fingerprint.

Outputs: `stage1b_signals/*.json`. Fed into `src/audit/bundles.py`:

```python
# src/audit/bundles.py
def activate_bundles(signals: SignalSet, lenses_yaml: dict) -> list[str]:
    activated = []
    for bundle_id, bundle in lenses_yaml["vertical_bundles"].items():
        if _signals_match(signals, bundle["detection_signals"]):
            activated.append(bundle_id)
    # repeat for geo_bundles + segment_bundles
    return activated
```

Dispatched lens IDs = always-on 149 + all activated-bundle lenses.

### 5.4 Stage 2 — Parallel lens fan-out

Core engine loop. `asyncio.gather(return_exceptions=True)` over all dispatched lenses; `Semaphore(7)` caps concurrency (tunable).

```python
# src/audit/stages/stage_2_lenses.py (sketch)
async def run(state: AuditState, config: AuditConfig) -> None:
    lens_ids = _select_lenses(state.bundles_activated, state.completed_lenses)
    sem = asyncio.Semaphore(config.stage_2_concurrency or 7)

    async def run_one_lens(lens_id: str):
        async with sem:
            if graceful_stop.requested():
                return
            if lens_id in state.completed_lenses:
                return  # resume: skip already-done
            try:
                prompt = prompts_loader.load_stage_2_prompt(lens_id)
                result = await agent_runner.run(
                    role=f"lens_{lens_id}",
                    prompt=prompt,
                )
                subsignal = _parse_subsignal(result.content, lens_id)
                _write_subsignal_atomic(state.audit_dir, lens_id, subsignal)
                state.update(lambda s: s.completed_lenses.append(lens_id))
            except MalformedSubSignalError as e:
                logger.warning(f"lens {lens_id} malformed; skip-not-raise", exc_info=e)
                _append_gap_report(state.audit_dir, lens_id, str(e))
                state.update(lambda s: s.failed_lenses.append(lens_id))
            except CostCeilingReached:
                # Propagate — stops the whole audit cleanly
                raise
            except Exception as e:
                logger.warning(f"lens {lens_id} crashed; skip-not-raise", exc_info=e)
                _append_gap_report(state.audit_dir, lens_id, str(e))
                state.update(lambda s: s.failed_lenses.append(lens_id))

    results = await asyncio.gather(
        *[run_one_lens(lid) for lid in lens_ids],
        return_exceptions=True,
    )
```

**Key property:** one bad lens doesn't kill the audit. Cost ceiling DOES kill the audit (intentionally — $150 is a hard ceiling).

Atomic SubSignal write:

```python
def _write_subsignal_atomic(audit_dir: Path, lens_id: str, subsignal: dict):
    target = audit_dir / "stage2_subsignals" / f"{lens_id}.json"
    tmp = target.with_suffix(".tmp")
    tmp.write_text(json.dumps(subsignal, indent=2))
    os.replace(tmp, target)  # atomic
```

### 5.5 Stage 3 — Synthesis (SubSignal → ParentFinding)

Net-new primitive per catalog 005. Takes collected SubSignals + stage 1a signals + stage 1b signals → produces ParentFindings organized by marketing-area section (9 sections per catalog 005).

```python
# src/audit/synthesis.py (sketch)
async def synthesize(state: AuditState, config: AuditConfig) -> None:
    subsignals = _load_all_subsignals(state.audit_dir)
    # Per catalog 005, aggregate SubSignals → ParentFindings by section
    sections = {
        "findability_and_discovery": [],
        "narrative_and_positioning": [],
        "consideration_path": [],
        "conversion_path": [],
        # ... 9 total per 005
    }
    for section_name in sections:
        subsignals_for_section = [s for s in subsignals if s.section == section_name]
        prompt = prompts_loader.load_synthesis_prompt(section_name)
        prompt_with_subsignals = _render_prompt(prompt, subsignals_for_section)
        result = await agent_runner.run(
            role=f"synthesis_{section_name}",
            prompt=prompt_with_subsignals,
        )
        parent_findings = _parse_parent_findings(result.content)
        # Optional inner loop (opt-in per role)
        if config.inner_loop_enabled_for(f"synthesis_{section_name}"):
            parent_findings = await _inner_loop_critique(parent_findings, ...)
        sections[section_name] = parent_findings
    _write_findings_md(state.audit_dir, sections)
    _write_report_md(state.audit_dir, sections)
    _write_report_json(state.audit_dir, sections)
```

Section boundaries and aggregation rules come from catalog 005 §Marketing-Areas View.

### 5.6 Stage 4 — Proposal generation

Per plan 002 U6 (capability registry). Reads `configs/audit/capability_registry.yaml` (ported from plan 002 U6 §722), picks 3–5 recommended capabilities for the prospect based on section findings, generates a priced proposal.

### 5.7 Inner loop (opt-in)

Net-new primitive (research §4 gap #2). Wraps a single agent call with judge → revise-once-on-fail pattern:

```python
# src/audit/inner_loop.py (sketch)
async def with_critique(
    produce: Callable[[], Awaitable[Any]],
    critique: Callable[[Any], Awaitable[CritiqueResult]],
    revise: Callable[[Any, CritiqueResult], Awaitable[Any]],
    *,
    max_revisions: int = 1,
) -> Any:
    output = await produce()
    for _ in range(max_revisions):
        result = await critique(output)
        if result.passed:
            return output
        try:
            output = await revise(output, result)
        except Exception:
            logger.warning("inner-loop revise failed; skip-not-raise, returning last output")
            return output
    return output
```

Opt-in per role via variant config `programs/marketing_audit/prompts/inner_loop_enabled.yaml`.

### 5.8 Done signal for Bundle B

- `freddy audit run --client fixture --domain example.com` completes Stages 0–4 end-to-end (skipping Bundle C render+publish) under the $100 soft ceiling on a fixture prospect.
- Per-lens SubSignal files written atomically; a deliberately malformed lens output does NOT abort the audit.
- Forcing a $150 cost ceiling mid-audit persists state with `pause_reason="cost_ceiling"` and exits 0.
- `freddy audit run --resume <id>` skips completed lenses and continues.

## 6. Bundle C — Deliverable + publish

Depends on: Bundle B (ParentFindings must exist).

Goal: Stage 5 (render) + Stage 6 (publish). Plan 002 U5.

### 6.1 `src/audit/render.py`

```python
# src/audit/render.py (sketch)
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

def render_html(audit_dir: Path, client_branding: ClientBranding) -> Path:
    env = Environment(loader=FileSystemLoader("src/audit/templates"))
    template = env.get_template("deliverable.html.j2")
    findings = json.loads((audit_dir / "stage3_synthesis" / "report.json").read_text())
    html = template.render(
        findings=findings,
        branding=client_branding,
        generated_at=datetime.utcnow().isoformat(),
    )
    html = _sanitize(html)  # nh3 allowlist
    out = audit_dir / "deliverable" / "report.html"
    out.write_text(html)
    return out

def render_pdf(html_path: Path) -> Path:
    pdf_path = html_path.with_suffix(".pdf")
    HTML(
        filename=str(html_path),
        base_url="about:blank",  # SSRF prevention
        url_fetcher=_safe_url_fetcher,  # deny external except data: URIs
    ).write_pdf(str(pdf_path))
    return pdf_path
```

Separate template for Free AI Visibility Scan (reduced scope, no PDF, cost-ceiling $2).

### 6.2 `src/audit/publish.py`

R2 upload + Cloudflare Worker relay + Slack. Plan 002 U5 specifies the Cloudflare Worker contract.

### 6.3 Free-scan hosting

Decision: R2 with public-read bucket + short-form URL `https://audits.gofreddy.com/scan/<hash>`. Hash = SHA256(prospect_domain + salt). Cloudflare Worker serves from R2.

Full audit PDFs sit behind signed URLs, expiry 7 days, re-generated on demand.

### 6.4 Payment gate (phase 2 stub)

Phase 1: `freddy audit invoice <audit_id> --email <addr>` emits a rendered invoice and sends via Resend. Manual payment tracking.

Phase 2: Stripe Checkout integration per plan 002 U10. Not in this bundle; `src/audit/payment.py` has a single `phase_1_invoice_stub()` function placeholder.

### 6.5 Done signal for Bundle C

- `freddy audit publish <audit_id>` renders HTML + PDF (under $2 for scan, no additional cost for full audit — render is local), uploads to R2, relays via Cloudflare Worker, Slack-notifies on success.
- `freddy audit scan --domain example.com` produces a public URL under $2 total.
- PDF opens cleanly in Chrome, Safari, Acrobat.

## 7. Bundle D — MA-1..MA-8 evaluation domain

Depends on: none (parallel with Bundles A/B/C).

Goal: extend `src/evaluation/` to score marketing_audit deliverables (per research §3.8).

### 7.1 Edits to `src/evaluation/`

Per research §5.2 items 9–12:

**`src/evaluation/models.py:160`** — add to Literal:
```python
Domain = Literal["geo", "competitive", "monitoring", "storyboard", "marketing_audit"]
```

**`src/evaluation/rubrics.py`** — add 8 RubricTemplate instances (full prompt sketches in §7.3 below).

**`src/evaluation/service.py`** — add entries:
```python
_DOMAIN_CRITERIA["marketing_audit"] = [
    "MA-1", "MA-2", "MA-3", "MA-4", "MA-5", "MA-6", "MA-7", "MA-8"
]
_JUDGE_PRIMARY_DELIVERABLE["marketing_audit"] = "findings.md"
```

**`src/evaluation/structural.py`** — add validator:
```python
def _validate_marketing_audit(audit_dir: Path) -> StructuralResult:
    required = [
        "stage3_synthesis/findings.md",
        "stage3_synthesis/report.md",
        "stage3_synthesis/report.json",
        "deliverable/report.html",
        "deliverable/report.pdf",
        "state.json",
    ]
    missing = [p for p in required if not (audit_dir / p).exists()]
    if missing:
        return StructuralResult(passed=False, errors=[f"missing {p}" for p in missing])
    # Validate findings.md has ≥1 ParentFinding per section; ≥3 total SubSignals cited
    # Validate state.json.total_cost_usd <= state.json.hard_breaker
    # Validate deliverable/report.pdf is non-zero and PDF magic bytes present
    return StructuralResult(passed=True, ...)
```

### 7.2 Fitness function (per catalog 005 + research §3.13)

```python
# src/evaluation/fitness/marketing_audit.py (new file)
def compute_fitness(
    ma_composite: float,           # geometric_mean of MA-1..MA-8 normalized scores
    ship_gate_edits: int,          # operator edits between synthesis.md and published version
    engagement_60d: float | None,  # None for audits <60d old
    cost_discipline: float,        # 1.0 if under ceiling + per-stage within estimate; penalized otherwise
    generation_index: int,         # 0-indexed; first 3 weight engagement=0
) -> float:
    w_ma = 0.4
    w_edits = 0.2
    w_engagement = 0.2 if generation_index >= 3 and engagement_60d is not None else 0.0
    w_cost = 0.2
    # Renormalize if engagement weight is 0
    total = w_ma + w_edits + w_engagement + w_cost
    return (
        w_ma * ma_composite
        + w_edits * (1.0 - _normalize_edits(ship_gate_edits))
        + w_engagement * (engagement_60d or 0.0)
        + w_cost * cost_discipline
    ) / total
```

### 7.3 MA-1..MA-8 rubric prompt sketches

Frozen at ship time; SHA256-hashed into `autoresearch/critique_manifest_marketing_audit.json`.

**MA-1 (Gradient, 1–5) — Observational grounding**

```
You are a marketing-audit quality evaluator. Score how strongly the
findings in this audit's `findings.md` tie to specific cited observations.

Anchors:
  1 — claims are generic boilerplate that would fit any prospect
  3 — mixed; some findings cite specific URLs / metrics / screenshots,
      others are recycled frameworks
  5 — every finding ties to at least one specific cited observation
      (URL + metric + timestamp, or URL + quoted text + placement detail)

Evidence requirement: for score ≥4, paste the three cited observations
with surrounding context that best support this score.

Output JSON:
  {"score": int, "rationale": str, "evidence_quotes": [str, str, str]}
```

**MA-2 (Checklist, 4 items) — Recommendation actionability**

```
Audit findings include recommendations. For each recommendation,
check whether it contains ALL of:
  [ ] A named action (specific verb, specific target)
  [ ] An effort sizing (hours/sprints/team-composition)
  [ ] A dated deadline or bounded timeframe
  [ ] Consistency with the prospect's stated capabilities

Score = fraction of recommendations that have all 4, scaled 0.0..1.0.

Output JSON: {"score": float, "per_recommendation": [{...}], "rationale": str}
```

**MA-3 (Gradient, 1–5) — Competitive honesty**

```
Rate whether the findings name the prospect's competitive losses
specifically.

Anchors:
  1 — no competitor named or losses acknowledged
  3 — competitors named but losses softened ("X does Y slightly better")
  5 — specific named loss with evidence
      ("Competitor X ranks for query Y where prospect does not;
       Competitor Z's pricing page converts at Z% higher based on visible
       copy + offer differences")

Cushioning / hedging language scores LOWER, not higher.

Output JSON: {"score": int, "rationale": str, "cited_losses": [str]}
```

**MA-4 (Checklist, 4 items) — Cost discipline**

```
Check the audit's cost_log.jsonl and state.json:
  [ ] Total cost ≤ $150 hard ceiling
  [ ] No stage's cumulative cost exceeds its estimate by >50%
  [ ] `hard_breaker_fired` is False in final state
  [ ] `soft_warn_fired` fired at most once and was acknowledged

Score = fraction passed, scaled 0.0..1.0.

Output JSON: {"score": float, "per_check": [{...}], "rationale": str}
```

**MA-5 (Gradient, 1–5) — Bundle applicability**

```
Check whether the bundles activated in Stage 1b match the detection
signals observed in Stage 1a + 1b.

Anchors:
  1 — bundles activated with zero matching signals (noise)
  3 — mixed; some bundles justified, others appear to be defaults
  5 — every activated bundle has at least one explicit detection signal
      AND every signal triggered the correct bundle

Look at state.bundles_activated and stage1b_signals/*.json.

Output JSON: {"score": int, "per_bundle": [{...}], "rationale": str}
```

**MA-6 (Gradient, 1–5) — Deliverable polish**

```
Open the audit's deliverable/report.html and deliverable/report.pdf.
Assess:
  - Typography + spacing + hierarchy (print-quality?)
  - Image / screenshot inclusion quality
  - Links clickable in HTML; footnotes/appendix resolve in PDF
  - Client branding applied (logo, color palette)
  - No obvious rendering errors (broken images, overflow, encoding issues)

Anchors:
  1 — renders broken or obviously unprofessional
  3 — functional but rough; agency would embarrass itself by shipping
  5 — ready to ship to a paying client as-is

Output JSON: {"score": int, "rationale": str, "flagged_issues": [str]}
```

**MA-7 (Gradient, 1–5) — Prioritization**

```
Rate whether the top 3 actions are unmistakably separated from
secondary items.

Anchors:
  1 — bullet-list of equal-weight items; reader can't tell what to do
      first
  3 — ordered list but ordering rationale unclear
  5 — top 3 actions visually distinguished AND reasoning given
      (why these three, why in this order)

Output JSON: {"score": int, "rationale": str, "top_3_quoted": [str]}
```

**MA-8 (Checklist, 4 items) — Data gap recalibration**

```
Check the audit's gap_report.md + findings.md:
  [ ] Every failed lens in gap_report.md is either (a) mentioned in
      findings.md with a "gap" note OR (b) explicitly excluded as
      not-applicable
  [ ] Findings whose supporting SubSignals failed have confidence
      lowered accordingly
  [ ] Optional enrichments (GSC, budget, winloss) that were NOT attached
      are called out rather than silently omitted
  [ ] Data quality score (DQS) matches gap count (high failures → low DQS)

Score = fraction passed, scaled 0.0..1.0.

Output JSON: {"score": float, "per_check": [{...}], "rationale": str}
```

### 7.4 Critique manifest

Freeze these 8 prompts + the structural validator + the fitness function at ship time. SHA256 them into `autoresearch/critique_manifest_marketing_audit.json`. Layer1 validation in `evaluate_variant.py` rejects any variant whose hash drifts (research §3.7).

### 7.5 Done signal for Bundle D

- `src/evaluation/service.py evaluate_marketing_audit(audit_dir)` returns MA-1..MA-8 scores + geometric mean composite.
- Structural validator rejects a deliberately-broken audit dir (missing files, invalid state).
- Critique manifest hash check passes on clean state and fails on any rubric edit.

## 8. Bundle E — Marketing_audit lane + cross-cutting glue

Depends on: Bundles A, B, C (engine must run end-to-end to produce replay artifacts), D (scoring must exist).

Goal: register the autoresearch lane; wire the engagement judge; lock concurrency.

### 8.1 Lane registration (exact 5-file edits)

**`autoresearch/lane_runtime.py:12`**
```python
# before
LANES = ("core", "geo", "competitive", "monitoring", "storyboard")
# after
LANES = ("core", "geo", "competitive", "monitoring", "storyboard", "marketing_audit")
```

**`autoresearch/lane_paths.py:36-37`**
```python
LANES = ("core", "geo", "competitive", "monitoring", "storyboard", "marketing_audit")
```

**`autoresearch/lane_paths.py:44-77`** — add to `WORKFLOW_PREFIXES`:
```python
WORKFLOW_PREFIXES["marketing_audit"] = (
    "programs/marketing_audit",
    "scripts/marketing_audit",
)
```

**`autoresearch/evolve.py:44`**
```python
ALL_LANES = ("core", "geo", "competitive", "monitoring", "storyboard", "marketing_audit")
```

**`autoresearch/frontier.py:15-16`**
```python
LANES = ("core", "geo", "competitive", "monitoring", "storyboard", "marketing_audit")
DOMAINS = ("geo", "competitive", "monitoring", "storyboard", "marketing_audit")
```

**`autoresearch/frontier.py:82-86`** — `objective_score()`:
```python
def objective_score(lane: str, scores: dict) -> float:
    if lane == "core":
        return _composite(scores)
    return scores.get(f"{lane}_domain_score", 0.0)
```

marketing_audit inherits the workflow-lane branch.

**`autoresearch/evaluate_variant.py:44-49`** — add `DELIVERABLES` entry:
```python
DELIVERABLES["marketing_audit"] = {
    "primary": "audits/<replay_id>/stage3_synthesis/findings.md",
    "artifacts": [
        "audits/<replay_id>/stage3_synthesis/report.json",
        "audits/<replay_id>/deliverable/report.html",
        "audits/<replay_id>/deliverable/report.pdf",
        "audits/<replay_id>/state.json",
        "audits/<replay_id>/gap_report.md",
    ],
}
```

### 8.2 New autoresearch files

**`autoresearch/archive/current_runtime/programs/marketing_audit-session.md`**

Full session program per agency-integration plan §7.1 (already spec'd; copy verbatim, tighten with current catalog 005 references).

**`autoresearch/archive/current_runtime/programs/marketing_audit-evaluation-scope.yaml`**

```yaml
domain: marketing_audit
outputs:
  - "audits/{replay_id}/stage3_synthesis/findings.md"
  - "audits/{replay_id}/deliverable/report.html"
  - "audits/{replay_id}/deliverable/report.pdf"
  - "audits/{replay_id}/state.json"
source_data:
  - "prospects/{replay_id}/intake.json"
  - "prospects/{replay_id}/crawl/*"
  - "prospects/{replay_id}/attachments/*"
transient:
  - "audits/{replay_id}/stage2_subsignals/*.json"
  - "audits/{replay_id}/cost_log.jsonl"
  - "audits/{replay_id}/events.jsonl"
  - "logs/**/*"
notes: |
  Variants mutate stage prompts + stage-1a thresholds + bundle dispatch logic.
  Lens definitions in configs/audit/lenses.yaml are OUT OF MUTATION SCOPE (locked v2 2026-04-23).
  MA-1..MA-8 rubric is OUT OF MUTATION SCOPE (frozen via critique_manifest_marketing_audit.json).
  Judges (src/evaluation/ and src/audit/judges/) are OUT OF MUTATION SCOPE.
```

**`autoresearch/archive/current_runtime/programs/marketing_audit/prompts/*.md`**

Mutable stage prompts. Audit engine's `prompts_loader.py` resolves these via `archive/current.json` → materialized runtime.

Initial seed prompts written to match plan 002 U3–U6 specs.

**`autoresearch/eval_suites/marketing-audit-v1.json`**

Fixture suite for holdout replay. Initially 5 hand-curated past audits per agency-integration plan Decision #12 + research §6.2:

```json
{
  "suite_id": "marketing-audit-v1",
  "version": "1.0",
  "domains": {
    "marketing_audit": {
      "fixtures": [
        {
          "fixture_id": "saas_b2b_us_enterprise_v1",
          "prospect_intake": "fixtures/marketing_audit/saas_b2b_us_enterprise/intake.json",
          "prospect_crawl_snapshot": "fixtures/marketing_audit/saas_b2b_us_enterprise/crawl/",
          "expected_deliverable_quality_floor": 0.65,
          "version": "1.0",
          "max_iter": 1,
          "timeout": 3600,
          "env": {}
        }
      ]
    }
  }
}
```

Grow to 5 over first month. Cap at 5 initially per research §6.2 ($300–900/generation holdout cost).

Holdout suite lives in non-repo env per research §3.12:
```bash
export EVOLUTION_HOLDOUT_MANIFEST=/private/path/holdout-marketing-audit-v1.json
```

### 8.3 `src/audit/judges/engagement.py` — long-loop judge

Net-new primitive (research §4 gap #3). Writes engagement-conversion signal back to `audits/lineage.jsonl` when JR records `engagement_signed_usd` at T+60d.

```python
# src/audit/judges/engagement.py (sketch)
from pathlib import Path
import json
import fcntl

def record_engagement(audit_id: str, engagement_signed_usd: float | None):
    """Called by JR via `freddy audit record-engagement <audit_id> --usd <n>`."""
    lineage_path = Path("audits/lineage.jsonl")
    # Read all rows, update the audit_id row, rewrite with flock
    with lineage_path.open("r+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        rows = [json.loads(line) for line in f]
        for row in rows:
            if row["audit_id"] == audit_id:
                row["engagement_signed_usd"] = engagement_signed_usd
                row["engagement_recorded_at"] = datetime.utcnow().isoformat()
        f.seek(0)
        f.truncate()
        for row in rows:
            f.write(json.dumps(row) + "\n")

def compute_engagement_signal(lineage_row: dict) -> float | None:
    """Called during fitness scoring. None if <60d since audit."""
    audit_age_days = _days_since(lineage_row["shipped_at"])
    if audit_age_days < 60:
        return None
    engagement = lineage_row.get("engagement_signed_usd")
    if engagement is None:
        return 0.0  # 60d passed without engagement recorded
    return min(1.0, engagement / 30000.0)  # normalize; 30k = max engagement weight
```

### 8.4 `evolve_lock` global mutex

Net-new primitive (research §6.4).

```python
# src/audit/concurrency.py (sketch)
from pathlib import Path
import fcntl

EVOLVE_LOCK_PATH = Path.home() / ".local" / "share" / "gofreddy" / "state.evolve_lock"

class EvolveLock:
    def __init__(self):
        self._fh = None

    def acquire_for_audit(self):
        """Called by freddy audit run. Fails if evolve is active."""
        self._fh = EVOLVE_LOCK_PATH.open("w")
        try:
            fcntl.flock(self._fh, fcntl.LOCK_SH | fcntl.LOCK_NB)  # shared lock (multiple audits ok)
        except BlockingIOError:
            raise EvolveLockContended("evolve currently running; refuse to start audit")

    def acquire_for_evolve(self):
        """Called by evolve.sh. Fails if any audit is active."""
        self._fh = EVOLVE_LOCK_PATH.open("w")
        try:
            fcntl.flock(self._fh, fcntl.LOCK_EX | fcntl.LOCK_NB)  # exclusive; waits for all audits
        except BlockingIOError:
            raise EvolveLockContended("audits currently running; refuse to start evolve")

    def release(self):
        if self._fh:
            fcntl.flock(self._fh, fcntl.LOCK_UN)
            self._fh.close()
```

Wire into `autoresearch/evolve.py` top-of-run and `src/audit/cli_entrypoints.py` top-of-run.

### 8.5 Pin autoresearch evaluator at ship time

Research §6.1 + Decision #11. At audit first-ship:

```bash
git tag autoresearch-audit-stable-20260501 <commit-sha>
git push origin autoresearch-audit-stable-20260501
```

Document the pin in `docs/plans/2026-04-24-002-audit-engine-implementation-design.md` (this doc) under §Operational notes (§9.2 below).

Audit CI / deployment pulls `src/evaluation/` and `autoresearch/evaluate_variant.py` at the pinned tag; main may move without affecting audit. Unpin intentionally when: (a) autoresearch GAPS.md P0 pre-blockers resolved, (b) audit CI gating run on new candidate commit, (c) JR approval.

### 8.6 Done signal for Bundle E

- `./autoresearch/evolve.sh --lane marketing_audit --iterations 1 --candidates-per-iteration 1` runs end-to-end against one fixture audit, emits one candidate variant, scores it with MA-1..MA-8, writes lineage row with `lane: "marketing_audit"`.
- `freddy audit run --client fixture` refuses to start if evolve is running; evolve refuses to start if any audit is running.
- `freddy audit record-engagement <audit_id> --usd 15000` updates `audits/lineage.jsonl`; next fitness computation includes the signal after T+60d.
- Pinned autoresearch tag exists and CI pulls from it.

## 9. Dependency-aware execution sequence

```
A (foundation) ──▶ B (stages) ──▶ C (deliverable+publish)
                      │
                      ▼
A ──▶ B ──────────────┼──▶ E (lane + glue)
                      │        ▲
                      └──▶ D (MA-1..MA-8) ─┘
```

Critical path: A → B → C (product ships).
Parallel track: D can be built independently after research record is finalized.
E depends on A+B+C+D (needs engine to replay audits + scoring to judge them).

**Recommended order:**

1. Bundle A — 1 week (mostly porting + adapting harness primitives)
2. Bundle B — 2 weeks (stages 0–4, lens registry transcription happens here)
3. Bundle C — 1 week (render + publish; some of this is straightforward Jinja2/WeasyPrint)
4. Bundle D — 1 week (can be parallel with B or C; 30 LOC of evaluation extension + rubric prompt writing + testing)
5. Bundle E — 1 week (lane registration + 3 new files + evolve_lock + pin + engagement judge)

**Total: ~6 weeks sequential, ~4–5 weeks with Bundle D parallelized.**

First audit produced at end of Bundle C (~4 weeks). First evolved variant at end of Bundle E (~6 weeks).

## 10. Risk mitigations (embedded as code/config choices)

Per research §6. Every risk has a concrete mitigation in the design above.

| Risk | Mitigation location |
|---|---|
| Autoresearch coupling (11% fix rate) | §8.5 pin at ship; Decision #11 |
| Holdout cost ($300–900/gen) | §8.2 cap fixture count at 5; §8.1 DELIVERABLES entry; Decision #12 weight engagement=0 early |
| Meta-agent timeout on 149-lens context | §8.2 prompts split per stage; meta-agent mutates one stage prompt per generation |
| Cross-lane resource contention | §8.4 `evolve_lock` mutex |
| Goodhart on judges | §7.4 critique manifest freeze; §2 Decision #10 telemetry blindness; engagement judge is ground-truth check |
| Lineage pollution | §8.1 lane field on every lineage row (existing autoresearch pattern) |
| Engagement signal lag 60d | §7.2 fitness weight 0 for first 3 generations |

## 11. Open items requiring JR decisions (content, not infrastructure)

Everything else is locked. These are the JR-owned calls:

1. **Lens YAML transcription.** Catalog 005 is 46 KB prose describing ~200 lenses. Translating to `configs/audit/lenses.yaml` is ~4–6 hours of careful work per entry: id, rank, tier, providers, detection signals, phase, cost estimate, subsignal schema, rubric anchors. Either JR does it, or one implementing agent is allocated to this subtask with JR reviewing each section. Not mechanical — needs judgment on provider mapping per lens.

2. **Free-scan lead-magnet scope.** Design locks in public-read R2 + Cloudflare Worker at `https://audits.gofreddy.com/scan/<hash>` with ceiling $2. Confirm:
   - Is `audits.gofreddy.com` the right subdomain?
   - Is Cloudflare Worker domain already registered?
   - What email capture happens in the scan flow?

3. **Capability registry content.** Plan 002 U6 specifies `src/audit/capability_registry.yaml` with capability definitions + price multipliers (small=0.8, mid=1.0, enterprise=1.3) + jr_time_hours. That content is operator-owned; Bundle B includes the loader but the registry entries come from JR.

4. **Cloudflare Worker secret + R2 bucket credentials.** Needed for Bundle C. Phase 1 ops task.

5. **Resend API key + audience id.** Phase 1 if manual invoicing via email. Otherwise deferred to Bundle C phase 2.

6. **Pin date for autoresearch evaluator.** §8.5 says tag at first ship; JR decides which commit is stable enough.

## 12. Appendix — Copy-pasteable file-level edit list

### New files to create (in order)

```
# Bundle A
src/audit/__init__.py
src/audit/state.py
src/audit/sessions.py
src/audit/cost_ledger.py
src/audit/graceful_stop.py
src/audit/agent_runner.py
src/audit/resume.py
src/audit/cleanup.py
src/audit/events.py
src/audit/prompts_loader.py
src/audit/concurrency.py
src/audit/exceptions.py
src/audit/preflight/__init__.py
src/audit/preflight/audit_preflight.py
src/audit/preflight/dns_email_security.py
src/audit/preflight/well_known.py
src/audit/preflight/json_ld.py
src/audit/preflight/trust_badges.py
src/audit/preflight/security_headers.py
src/audit/preflight/social_meta.py
src/audit/preflight/brand_assets.py
src/audit/preflight/tooling_fingerprint.py

# Bundle B
src/audit/stages/__init__.py
src/audit/stages/_base.py
src/audit/stages/stage_0_intake.py
src/audit/stages/stage_1a_preflight.py
src/audit/stages/stage_1b_signals.py
src/audit/stages/stage_2_lenses.py
src/audit/stages/stage_3_synthesis.py
src/audit/stages/stage_4_proposal.py
src/audit/bundles.py
src/audit/lenses.py
src/audit/subsignals.py
src/audit/synthesis.py
src/audit/inner_loop.py
src/audit/judges/__init__.py
src/audit/judges/paraphrase.py
src/audit/judges/calibration.py
configs/audit/lenses.yaml                   # large YAML; JR-coordinated transcription
configs/audit/capability_registry.yaml      # JR-owned content

# Bundle C
src/audit/stages/stage_5_deliverable.py
src/audit/stages/stage_6_publish.py
src/audit/render.py
src/audit/publish.py
src/audit/payment.py                         # phase 1: stub with invoice_stub()
src/audit/templates/deliverable.html.j2
src/audit/templates/deliverable_print.css
src/audit/templates/free_scan.html.j2
cli/freddy/commands/audit.py

# Bundle D
src/evaluation/fitness/marketing_audit.py
src/evaluation/judges/marketing_audit.py
tests/evaluation/test_marketing_audit_rubric.py
autoresearch/critique_manifest_marketing_audit.json

# Bundle E
src/audit/judges/engagement.py
autoresearch/archive/current_runtime/programs/marketing_audit-session.md
autoresearch/archive/current_runtime/programs/marketing_audit-evaluation-scope.yaml
autoresearch/archive/current_runtime/programs/marketing_audit/prompts/stage_0_intake.md
autoresearch/archive/current_runtime/programs/marketing_audit/prompts/stage_1a_preflight.md
autoresearch/archive/current_runtime/programs/marketing_audit/prompts/stage_1b_signals.md
autoresearch/archive/current_runtime/programs/marketing_audit/prompts/stage_2_lens_meta.md
autoresearch/archive/current_runtime/programs/marketing_audit/prompts/stage_3_synthesis.md
autoresearch/archive/current_runtime/programs/marketing_audit/prompts/stage_4_proposal.md
autoresearch/archive/current_runtime/programs/marketing_audit/prompts/inner_loop_critic.md
autoresearch/eval_suites/marketing-audit-v1.json
```

### Existing files to edit

```
# Bundle D
src/evaluation/models.py:160                    # add "marketing_audit" to Literal
src/evaluation/rubrics.py                       # add 8 MA RubricTemplate instances
src/evaluation/service.py                       # _DOMAIN_CRITERIA, _JUDGE_PRIMARY_DELIVERABLE
src/evaluation/structural.py                    # add _validate_marketing_audit

# Bundle E — autoresearch lane registration
autoresearch/lane_runtime.py:12
autoresearch/lane_paths.py:36-37,44-77
autoresearch/evolve.py:44
autoresearch/frontier.py:15-16
autoresearch/evaluate_variant.py:44-49

# Bundle E — wiring
autoresearch/evolve.py                          # acquire EvolveLock at top of run
```

### Test coverage targets

```
tests/audit/test_state.py                       # atomic persist, concurrent safety
tests/audit/test_cost_ledger.py                 # soft warn, hard breaker, scan mode
tests/audit/test_graceful_stop.py               # flag propagation on SIGTERM
tests/audit/test_resume.py                      # viable_resume_id + skip-completed
tests/audit/test_subsignals.py                  # skip-not-raise on malformed
tests/audit/test_stage_2_parallel.py            # one lens crash ≠ audit crash
tests/audit/test_synthesis.py                   # SubSignal → ParentFinding
tests/audit/test_render.py                      # HTML + PDF render, SSRF guard
tests/evaluation/test_marketing_audit_rubric.py # MA-1..MA-8 scoring
tests/autoresearch/test_marketing_audit_lane.py # lane registration + evolve smoke
tests/audit/test_evolve_lock.py                 # concurrency guarantees
tests/audit/test_engagement_judge.py            # T+60d signal write-back
```

---

## 13. What this doc replaces / supersedes

- Collapses agency-integration plan §6 (Bundle 9) and §7 (Bundle 10) into this single design
- Leaves agency-integration plan §3 (Bundle 0 pre-flight), §4 (Bundle 1 analytical uplift), §5 (Bundle 2 client platform lite) intact as prerequisites that still need to ship separately
- Leaves other agency-integration plan bundles (3, 4, 5, 6, 7, 8) as future scope, explicitly deferred

## 14. End of design

Next action: implementing agent reads §2 (locked decisions), §3 (module map), §4–§8 (bundle details), §12 (file list). Begin with Bundle A.

No further research required. Research record at `docs/plans/2026-04-24-001-audit-pipeline-research-record.md` is authoritative for primitives; this doc is authoritative for how they combine into the audit product.
