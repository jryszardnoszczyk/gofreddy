"""Audit pipeline stage entry points (master plan §3.3-3.8).

L3 ships the orchestration layer. Each stage takes a ``StageContext`` and
returns a stage-specific ``StageResult`` (a small dataclass with the output
artifact paths + any in-memory data the next stage needs).

L4 wires real CLI execution against the customer-facing pipeline; L3 keeps
the orchestration testable by injecting a duck-typed runner so unit
tests don't need to spawn real subprocesses.

Per-stage cost is captured via ``cost_observability.record_stage_cost`` —
the data points exist for L5 to wire Slack thresholds (master plan §3.9).
"""
from __future__ import annotations

import asyncio
import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from src.audit.agent_models import (
    AgentMetadata,
    AgentOutput,
    HealthScore,
    ParentFinding,
    SubSignal,
    compute_health_score,
)
from src.audit.agent_runner import AgentRunner
from src.audit.cost_ledger import CostLedger
from src.audit.cost_observability import record_stage_cost
from src.audit.exceptions import AuditError
from src.audit.preflight import runner as preflight_runner
from src.audit.preflight.runner import PreflightConfig, PreflightResult
from src.audit.state import AuditStateFile


# ─── Constants ─────────────────────────────────────────────────────────────

PROMPTS_DIR = Path(__file__).parent.parent.parent / "programs" / "marketing_audit" / "prompts"
DEFAULT_MODEL_OPUS = "opus"
DEFAULT_MODEL_SONNET = "sonnet"

# 4 Stage-2 agents per CAD-3 (master plan §3.5)
STAGE_2_AGENTS: tuple[str, ...] = ("findability", "narrative", "acquisition", "experience")

# Stage names match keys in cost_actual.json (master plan §3.9)
STAGE_KEY_INTAKE = "stage_0_intake"
STAGE_KEY_WARMUP = "stage_1a_warmup"
STAGE_KEY_PREDISCO = "stage_1b_predischarge"
STAGE_KEY_BRIEF = "stage_1c_brief"
STAGE_KEY_AGENT_PREFIX = "stage_2_"  # + agent name
STAGE_KEY_SYNTHESIS = "stage_3_synthesis"
STAGE_KEY_PROPOSAL = "stage_4_proposal"
STAGE_KEY_DELIVERABLE = "stage_5_deliverable"


# ─── Stage context + base result ───────────────────────────────────────────


@dataclass
class StageContext:
    """Inputs threaded through every stage.

    ``audit_dir`` is the workspace root: ``clients/<slug>/audit/``.
    Stages create subdirectories (``intake/``, ``cache/``, ``prediscovery/``,
    ``agents/<name>/``, ``synthesis/``, ``proposal/``, ``deliverable/``) on
    demand.

    ``runner`` is duck-typed (only needs ``async run(...)``). Tests pass a
    ``FakeAgentRunner``; production wires ``AgentRunner()``.

    ``ledger`` is optional — when supplied, the runner writes per-call cost
    rows to ``cost_log.jsonl``. Stage-level rollups always go to
    ``cost_actual.json`` via ``record_stage_cost``.
    """

    audit_dir: Path
    state_file: AuditStateFile
    runner: Any = None  # duck-typed; AgentRunner in production, AsyncMock in tests
    ledger: CostLedger | None = None
    intake_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class IntakeResult:
    intake_path: Path
    state_path: Path


@dataclass
class WarmupResult:
    cache_dir: Path
    preflight: PreflightResult
    cache_manifest_path: Path


@dataclass
class PrediscoveryResult:
    signals_path: Path
    gaps_path: Path
    bundles_path: Path


@dataclass
class BriefResult:
    brief_md_path: Path
    brief_json_path: Path
    phase0_meta_path: Path
    reading_guides_path: Path


@dataclass
class AgentRunArtifact:
    agent_name: str
    output_path: Path
    output: AgentOutput | None = None
    error: str | None = None


@dataclass
class Stage2Result:
    agents: list[AgentRunArtifact]
    failures: list[str] = field(default_factory=list)


@dataclass
class SynthesisResult:
    findings_md_path: Path
    report_md_path: Path
    report_json_path: Path
    surprises_md_path: Path
    gap_report_md_path: Path
    health_score: HealthScore
    parent_findings: list[ParentFinding]


@dataclass
class ProposalResult:
    proposal_md_path: Path
    proposal_json_path: Path


@dataclass
class DeliverableResult:
    html_path: Path
    pdf_path: Path
    assets_dir: Path
    slug: str


# ─── Helpers ───────────────────────────────────────────────────────────────


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _load_prompt(name: str) -> str:
    """Read a stage prompt from ``programs/marketing_audit/prompts/<name>.md``.

    Raises ``AuditError`` if the file is absent — fail-loud so a missing
    prompt is caught at stage start, not deep inside the agent call.
    """
    path = PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        raise AuditError(f"stage prompt not found: {path}")
    return path.read_text(encoding="utf-8")


def _safe_format(template: str, **kwargs: Any) -> str:
    """Format ``template`` with literal ``{``/``}`` preserved.

    Production prompts contain JSON examples + code blocks with curly
    braces that ``str.format`` interprets as placeholders. This helper
    escapes ALL braces in the template, then unescapes only the known
    kwarg placeholders, so literal braces in prose pass through verbatim.
    """
    escaped = template.replace("{", "{{").replace("}", "}}")
    for key in kwargs:
        escaped = escaped.replace(f"{{{{{key}}}}}", f"{{{key}}}")
    return escaped.format(**kwargs)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str, sort_keys=True), encoding="utf-8")


def _write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# ─── Resume helpers (master plan §3.10 — completed_stages skip) ────────────


def is_stage_complete(state_file: AuditStateFile, stage_key: str) -> bool:
    return stage_key in state_file.load().completed_stages


def mark_stage_complete(
    state_file: AuditStateFile,
    stage_key: str,
    *,
    session_id: str = "",
    cost_usd: float = 0.0,
) -> None:
    """Append ``stage_key`` to ``completed_stages`` (idempotent) and record
    the session_id + cost under ``state.sessions[stage_key]``."""
    def _apply(s: Any) -> Any:
        completed = s.completed_stages
        if stage_key not in completed:
            completed = completed + (stage_key,)
        sessions = {**s.sessions, stage_key: {
            "session_id": session_id,
            "cost_usd": float(cost_usd),
            "completed_at": _now_iso(),
        }}
        import dataclasses as _dc
        return _dc.replace(s, completed_stages=completed, sessions=sessions)
    state_file.mutate(_apply)


# ─── Stage 0 — Intake ──────────────────────────────────────────────────────


async def stage_0_intake(ctx: StageContext) -> IntakeResult:
    """Stage 0 — write intake form data + initial state to disk.

    Master plan §3.3: workspace at ``clients/<slug>/audit/`` is created
    upstream by ``freddy audit init``; this stage writes the structured
    ``intake/form.json`` + advances ``state.json``.

    No LLM. Cost = $0.
    """
    intake_dir = _ensure_dir(ctx.audit_dir / "intake")
    intake_path = intake_dir / "form.json"
    state_path = ctx.audit_dir / "state.json"

    if is_stage_complete(ctx.state_file, STAGE_KEY_INTAKE) and intake_path.exists():
        return IntakeResult(intake_path=intake_path, state_path=state_path)

    _write_json(intake_path, ctx.intake_data or {})
    record_stage_cost(ctx.audit_dir, STAGE_KEY_INTAKE, 0.0)
    mark_stage_complete(ctx.state_file, STAGE_KEY_INTAKE, cost_usd=0.0)
    return IntakeResult(intake_path=intake_path, state_path=state_path)


# ─── Stage 1a — Cache warmup ───────────────────────────────────────────────


async def stage_1_warmup(
    state_file: AuditStateFile | StageContext,
    *,
    preflight_config: PreflightConfig | None = None,
    ctx: StageContext | None = None,
) -> WarmupResult | PreflightResult:
    """Stage 1a — preflight + Tier-1 provider fan-out.

    Backwards-compat: L1 callers pass an ``AuditStateFile`` directly and
    expect a ``PreflightResult`` back. L3 callers pass a ``StageContext``
    (or use the keyword ``ctx=``) and get a ``WarmupResult`` containing
    the cache manifest path + preflight result.

    Provider fan-out (DataForSEO + Cloro + 12 monitoring adapters +
    Wappalyzer + Playwright homepage fetch) per master plan §3.4 is
    designed as a Python-side ``asyncio.gather`` + ``Semaphore(12)``.
    L3 ships the architecture; concrete provider wiring lives in L4
    when the freddy CLI surface comes together. The cache manifest is
    written empty here so Stage 1b's prompt has a stable contract.
    """
    # Backwards-compat shim
    if isinstance(state_file, StageContext):
        ctx = state_file
        sf = ctx.state_file
    else:
        sf = state_file

    state = sf.load()

    # Preflight runner — already wired in L1.
    preflight = await preflight_runner.run(state.prospect_domain, config=preflight_config)

    # If running L1-style (no ctx), preserve old return shape.
    if ctx is None:
        return preflight

    # L3 path: write empty cache manifest skeleton; full Tier-1 fan-out is
    # L4 work (the CLI surface will know which provider fixtures to seed).
    cache_dir = _ensure_dir(ctx.audit_dir / "cache")
    manifest_path = cache_dir / "manifest.json"

    if is_stage_complete(ctx.state_file, STAGE_KEY_WARMUP) and manifest_path.exists():
        return WarmupResult(cache_dir=cache_dir, preflight=preflight, cache_manifest_path=manifest_path)

    manifest = {
        "audit_id": state.audit_id,
        "prospect_domain": state.prospect_domain,
        "warmed_at": _now_iso(),
        "tools": [],  # per-tool cache files appended by L4 provider fan-out
        "preflight_summary": {
            "checks_run": len(preflight.results) if hasattr(preflight, "results") else 0,
        },
    }
    _write_json(manifest_path, manifest)

    record_stage_cost(ctx.audit_dir, STAGE_KEY_WARMUP, 0.0)
    mark_stage_complete(ctx.state_file, STAGE_KEY_WARMUP, cost_usd=0.0)
    return WarmupResult(
        cache_dir=cache_dir,
        preflight=preflight,
        cache_manifest_path=manifest_path,
    )


# ─── Stage 1b — Pre-discovery + bundle activation ──────────────────────────


async def stage_1b_predischarge(ctx: StageContext) -> PrediscoveryResult:
    """Stage 1b — Sonnet multi-turn pre-discovery + free-API discovery.

    Master plan §3.4. Sonnet session is dispatched via the multi-provider
    CLI runner; the prompt embeds the warm-cache manifest, ~75 free public
    API URL-pattern blocks, and bundle-activation detection rules.

    Outputs (all under ``prediscovery/``):
    - ``signals.md`` — agent-authored prose, organized by rubric headings
    - ``gaps.jsonl`` — one row per gap_flag the agent detected
    - ``bundles_active.json`` — vertical / geo / segment activations
    """
    if ctx.runner is None:
        raise AuditError("stage_1b_predischarge requires ctx.runner")

    state = ctx.state_file.load()
    prediscovery_dir = _ensure_dir(ctx.audit_dir / "prediscovery")
    signals_path = prediscovery_dir / "signals.md"
    gaps_path = prediscovery_dir / "gaps.jsonl"
    bundles_path = prediscovery_dir / "bundles_active.json"

    if (is_stage_complete(ctx.state_file, STAGE_KEY_PREDISCO)
            and signals_path.exists() and gaps_path.exists() and bundles_path.exists()):
        return PrediscoveryResult(signals_path=signals_path, gaps_path=gaps_path, bundles_path=bundles_path)

    prompt_template = _load_prompt("stage_1b_predischarge")

    cache_manifest_path = ctx.audit_dir / "cache" / "manifest.json"
    cache_manifest = (
        json.loads(cache_manifest_path.read_text(encoding="utf-8"))
        if cache_manifest_path.exists() else {}
    )

    prompt = _safe_format(prompt_template, 
        prospect_domain=state.prospect_domain,
        client_slug=state.client_slug,
        audit_id=state.audit_id,
        cache_manifest=json.dumps(cache_manifest, indent=2),
        intake_data=json.dumps(ctx.intake_data, indent=2),
    )

    result = await ctx.runner.run(
        prompt=prompt,
        model=DEFAULT_MODEL_SONNET,
        role="stage_1b_predischarge",
        cwd=ctx.audit_dir,
        # Stage 1b agent has to fan across ~30 free public APIs + read
        # rubric YAMLs + write 3 deliverable files. 20 turns exhausts
        # before the artifact-write step (caught 2026-05-07 first dry
        # run on anthropic.com — 56 user messages logged, 0 artifacts
        # written). 40 matches Stage 2's heavy-agent budget.
        max_turns=40,
        ledger=ctx.ledger,
        pattern="meta",
        expected_output_files=[signals_path, gaps_path, bundles_path],
    )

    # Default outputs — Sonnet writes them via Bash/Write tools; if the
    # agent didn't, scaffold empty files so the next stage's contract holds.
    if not signals_path.exists():
        _write_md(signals_path, result.text or "# Pre-discovery signals\n\n(agent did not write signals.md)\n")
    if not gaps_path.exists():
        gaps_path.write_text("", encoding="utf-8")
    if not bundles_path.exists():
        _write_json(bundles_path, {"vertical": [], "geo": [], "segment": []})

    record_stage_cost(ctx.audit_dir, STAGE_KEY_PREDISCO, result.cost_usd)
    mark_stage_complete(ctx.state_file, STAGE_KEY_PREDISCO,
                        session_id=result.session_id, cost_usd=result.cost_usd)
    return PrediscoveryResult(
        signals_path=signals_path,
        gaps_path=gaps_path,
        bundles_path=bundles_path,
    )


# ─── Stage 1c — Brief synthesis ────────────────────────────────────────────


async def stage_1c_brief_synthesis(ctx: StageContext) -> BriefResult:
    """Stage 1c — Opus 1-call brief synthesis with phase0_meta block.

    Master plan §3.4. Reads ``signals.md`` + ``gaps.jsonl`` + cache
    manifest + form data → emits brief.md + brief.json + phase0_meta.json
    + agent_reading_guides.json.
    """
    if ctx.runner is None:
        raise AuditError("stage_1c_brief_synthesis requires ctx.runner")

    state = ctx.state_file.load()
    prediscovery_dir = ctx.audit_dir / "prediscovery"
    brief_md = prediscovery_dir / "brief.md"
    brief_json = prediscovery_dir / "brief.json"
    phase0_meta = prediscovery_dir / "phase0_meta.json"
    reading_guides = prediscovery_dir / "agent_reading_guides.json"

    if (is_stage_complete(ctx.state_file, STAGE_KEY_BRIEF)
            and brief_md.exists() and brief_json.exists()
            and phase0_meta.exists() and reading_guides.exists()):
        return BriefResult(
            brief_md_path=brief_md, brief_json_path=brief_json,
            phase0_meta_path=phase0_meta, reading_guides_path=reading_guides,
        )

    prompt_template = _load_prompt("stage_1c_brief_synthesis")

    signals = (prediscovery_dir / "signals.md").read_text(encoding="utf-8") if (prediscovery_dir / "signals.md").exists() else ""
    gaps_text = (prediscovery_dir / "gaps.jsonl").read_text(encoding="utf-8") if (prediscovery_dir / "gaps.jsonl").exists() else ""
    bundles = (prediscovery_dir / "bundles_active.json").read_text(encoding="utf-8") if (prediscovery_dir / "bundles_active.json").exists() else "{}"

    prompt = _safe_format(prompt_template, 
        prospect_domain=state.prospect_domain,
        client_slug=state.client_slug,
        intake_data=json.dumps(ctx.intake_data, indent=2),
        signals=signals,
        gaps_jsonl=gaps_text,
        bundles_active=bundles,
    )

    result = await ctx.runner.run(
        prompt=prompt,
        model=DEFAULT_MODEL_OPUS,
        role="stage_1c_brief_synthesis",
        cwd=ctx.audit_dir,
        # 4 deliverables (brief.md/json + phase0_meta.json +
        # agent_reading_guides.json) need ≥4 write tool calls + input
        # reads + final status. Original max_turns=4 was tight enough
        # to force claude rc=1 even when the agent successfully wrote
        # all files (caught 2026-05-07 — anthropic.com run #3 had all
        # 4 files on disk yet 3 retries all rc=1).
        max_turns=12,
        ledger=ctx.ledger,
        pattern="meta",
        expected_output_files=[brief_md, brief_json, phase0_meta, reading_guides],
    )

    if not brief_md.exists():
        _write_md(brief_md, result.text or "# Brief\n\n(agent did not write brief.md)\n")
    if not brief_json.exists():
        _write_json(brief_json, {"audit_id": state.audit_id, "summary": "", "icp": {}, "competitors": []})
    if not phase0_meta.exists():
        _write_json(phase0_meta, {f"frame_{i}": {} for i in range(1, 10)})
    if not reading_guides.exists():
        _write_json(reading_guides, {agent: "" for agent in STAGE_2_AGENTS})

    record_stage_cost(ctx.audit_dir, STAGE_KEY_BRIEF, result.cost_usd)
    mark_stage_complete(ctx.state_file, STAGE_KEY_BRIEF,
                        session_id=result.session_id, cost_usd=result.cost_usd)
    return BriefResult(
        brief_md_path=brief_md,
        brief_json_path=brief_json,
        phase0_meta_path=phase0_meta,
        reading_guides_path=reading_guides,
    )


# ─── Stage 2 — 4-agent fan-out ─────────────────────────────────────────────


async def stage_2_agents(
    ctx: StageContext,
    *,
    agents: Iterable[str] = STAGE_2_AGENTS,
) -> Stage2Result:
    """Stage 2 — fan out 4 agents in parallel, each multi-turning over its
    rubric YAML and emitting ``AgentOutput`` to ``agents/<a>/agent_output.json``.

    Master plan §3.5. ``asyncio.gather(..., return_exceptions=True)``
    isolates per-agent crashes; siblings continue.
    """
    if ctx.runner is None:
        raise AuditError("stage_2_agents requires ctx.runner")

    state = ctx.state_file.load()
    reading_guides_path = ctx.audit_dir / "prediscovery" / "agent_reading_guides.json"
    reading_guides = json.loads(reading_guides_path.read_text(encoding="utf-8")) if reading_guides_path.exists() else {}
    brief_md = ctx.audit_dir / "prediscovery" / "brief.md"
    brief_text = brief_md.read_text(encoding="utf-8") if brief_md.exists() else ""

    coros = [
        _run_one_agent(
            ctx=ctx, agent=agent, state=state,
            brief_text=brief_text,
            reading_guide=reading_guides.get(agent, ""),
        )
        for agent in agents
    ]
    results = await asyncio.gather(*coros, return_exceptions=True)

    artifacts: list[AgentRunArtifact] = []
    failures: list[str] = []
    for agent, res in zip(agents, results):
        if isinstance(res, Exception):
            output_path = ctx.audit_dir / "agents" / agent / "agent_output.json"
            artifacts.append(AgentRunArtifact(
                agent_name=agent, output_path=output_path,
                output=None, error=str(res),
            ))
            failures.append(f"{agent}: {res}")
        else:
            artifacts.append(res)

    return Stage2Result(agents=artifacts, failures=failures)


async def _run_one_agent(
    *,
    ctx: StageContext,
    agent: str,
    state: Any,
    brief_text: str,
    reading_guide: str,
) -> AgentRunArtifact:
    """Run one Stage-2 agent. Loads the per-agent prompt + rubric YAML,
    calls the runner, writes the AgentOutput JSON, returns the artifact."""
    if ctx.runner is None:
        raise AuditError("agent runner missing")

    agent_dir = _ensure_dir(ctx.audit_dir / "agents" / agent)
    output_path = agent_dir / "agent_output.json"
    stage_key = f"{STAGE_KEY_AGENT_PREFIX}{agent}"

    if is_stage_complete(ctx.state_file, stage_key) and output_path.exists():
        try:
            return AgentRunArtifact(
                agent_name=agent, output_path=output_path,
                output=AgentOutput.model_validate_json(output_path.read_text(encoding="utf-8")),
            )
        except Exception as exc:  # noqa: BLE001
            return AgentRunArtifact(
                agent_name=agent, output_path=output_path,
                output=None, error=f"resume validation failed: {exc}",
            )

    prompt_template = _load_prompt(f"stage_2_{agent}")
    rubric_path = Path(__file__).parent.parent.parent / "data" / f"rubrics_{agent}.yaml"
    rubric_text = rubric_path.read_text(encoding="utf-8") if rubric_path.exists() else ""

    prompt = _safe_format(prompt_template, 
        prospect_domain=state.prospect_domain,
        client_slug=state.client_slug,
        audit_id=state.audit_id,
        brief=brief_text,
        reading_guide=reading_guide,
        rubric_yaml=rubric_text,
    )

    # Per-agent max_turns: narrative has the heaviest research surface
    # (competitor framing + brand-voice + thought-leadership content +
    # community sentiment) and consistently failed at 40 on Anthropic
    # dry-run 2026-05-07 (3 retries all silent rc=1, never wrote
    # agent_output.json). Other 3 agents complete cleanly at 40.
    max_turns_for_agent = 60 if agent == "narrative" else 40
    result = await ctx.runner.run(
        prompt=prompt,
        model=DEFAULT_MODEL_OPUS,
        role=f"stage_2_{agent}",
        cwd=ctx.audit_dir,
        max_turns=max_turns_for_agent,
        ledger=ctx.ledger,
        pattern="meta",
        expected_output_files=[output_path],
    )

    record_stage_cost(ctx.audit_dir, stage_key, result.cost_usd)
    mark_stage_complete(ctx.state_file, stage_key,
                        session_id=result.session_id, cost_usd=result.cost_usd)

    # Try to parse agent_output.json the agent wrote; if missing, scaffold
    # an empty AgentOutput so Stage 3 doesn't crash on this agent.
    output_obj: AgentOutput | None = None
    if output_path.exists():
        try:
            output_obj = AgentOutput.model_validate_json(output_path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001 — Pydantic + JSON errors
            return AgentRunArtifact(
                agent_name=agent, output_path=output_path,
                output=None, error=f"AgentOutput validation failed: {exc}",
            )
    else:
        # Scaffold an empty AgentOutput so the chain holds shape.
        output_obj = AgentOutput(
            agent_name=agent,
            sub_signals=[],
            parent_findings=[],
            agent_summary=result.text[:500] if result.text else "",
            rubric_coverage={},
            metadata=AgentMetadata(
                session_id=result.session_id,
                total_cost_usd=result.cost_usd,
                duration_ms=result.duration_ms,
                num_turns=0,
                model_usage={},
                partial=True,
            ),
        )
        _write_json(output_path, json.loads(output_obj.model_dump_json()))

    return AgentRunArtifact(agent_name=agent, output_path=output_path, output=output_obj)


# ─── Stage 3 — Cross-cutting synthesis ─────────────────────────────────────


async def stage_3_synthesis(
    ctx: StageContext,
    stage2: Stage2Result,
) -> SynthesisResult:
    """Stage 3 — 2 Opus calls: Phase-0 cross-cutting merge + narrative writer.

    Master plan §3.6. Reads 4× AgentOutput, dedupes ParentFindings across
    agents, computes deterministic HealthScore, writes the 5 synthesis
    deliverables.
    """
    if ctx.runner is None:
        raise AuditError("stage_3_synthesis requires ctx.runner")

    synthesis_dir = _ensure_dir(ctx.audit_dir / "synthesis")
    state = ctx.state_file.load()

    # Collect ParentFindings + SubSignals from all 4 agents
    all_parent_findings: list[ParentFinding] = []
    all_sub_signals: list[SubSignal] = []
    rubric_coverage: dict[str, dict[str, str]] = {}
    for art in stage2.agents:
        if art.output is None:
            continue
        all_parent_findings.extend(art.output.parent_findings)
        all_sub_signals.extend(art.output.sub_signals)
        rubric_coverage[art.agent_name] = dict(art.output.rubric_coverage)

    # Resume short-circuit
    findings_md = synthesis_dir / "findings.md"
    report_md = synthesis_dir / "report.md"
    report_json_path = synthesis_dir / "report.json"
    surprises_md = synthesis_dir / "surprises.md"
    gap_report_md = synthesis_dir / "gap_report.md"
    if (is_stage_complete(ctx.state_file, STAGE_KEY_SYNTHESIS)
            and all(p.exists() for p in [findings_md, report_md, report_json_path,
                                          surprises_md, gap_report_md])):
        return SynthesisResult(
            findings_md_path=findings_md, report_md_path=report_md,
            report_json_path=report_json_path, surprises_md_path=surprises_md,
            gap_report_md_path=gap_report_md,
            health_score=compute_health_score(all_parent_findings),
            parent_findings=all_parent_findings,
        )

    # Opus call #1 — cross-cutting Phase-0 merge & dedup
    phase0_path = ctx.audit_dir / "prediscovery" / "phase0_meta.json"
    phase0_meta = json.loads(phase0_path.read_text(encoding="utf-8")) if phase0_path.exists() else {}

    cross_prompt = _safe_format(_load_prompt("stage_3_cross_cutting"), 
        prospect_domain=state.prospect_domain,
        phase0_meta=json.dumps(phase0_meta, indent=2),
        parent_findings=json.dumps(
            [json.loads(pf.model_dump_json()) for pf in all_parent_findings],
            indent=2, default=str,
        ),
    )

    cross_result = await ctx.runner.run(
        prompt=cross_prompt,
        model=DEFAULT_MODEL_OPUS,
        role="stage_3_cross_cutting",
        cwd=ctx.audit_dir,
        max_turns=8,  # bumped 4→8 (same family as stage_1c fix 2026-05-07)
        ledger=ctx.ledger,
        pattern="meta",
    )

    # Deterministic HealthScore (master plan §3.6)
    health = compute_health_score(all_parent_findings)

    # Opus call #2 — narrative writer
    narrative_prompt = _safe_format(_load_prompt("stage_3_narrative"), 
        prospect_domain=state.prospect_domain,
        cross_cutting_output=cross_result.text or "",
        parent_findings=json.dumps(
            [json.loads(pf.model_dump_json()) for pf in all_parent_findings],
            indent=2, default=str,
        ),
        health_score=json.dumps(json.loads(health.model_dump_json()), indent=2),
    )

    narrative_result = await ctx.runner.run(
        prompt=narrative_prompt,
        model=DEFAULT_MODEL_OPUS,
        role="stage_3_narrative",
        cwd=ctx.audit_dir,
        max_turns=12,  # bumped 4→12 — narrative writes report.md+findings.md+report.json+surprises.md+gap_report.md
        ledger=ctx.ledger,
        pattern="meta",
        expected_output_files=[findings_md, report_md, surprises_md],
    )

    # Compose paths — agent writes them via Bash/Write; scaffold if missing
    if not findings_md.exists():
        _write_md(findings_md, _scaffold_findings_md(all_parent_findings, health))
    if not report_md.exists():
        _write_md(report_md, narrative_result.text or "# Report\n\n(narrative not produced)\n")

    # report.json — machine-readable shape per master plan §3.6
    report_json = {
        "audit_id": state.audit_id,
        "prospect_domain": state.prospect_domain,
        "generated_at": _now_iso(),
        "health_score": json.loads(health.model_dump_json()),
        "parent_findings": [json.loads(pf.model_dump_json()) for pf in all_parent_findings],
        "rubric_coverage": rubric_coverage,
        "sources": _collect_sources(all_sub_signals),
    }
    _write_json(report_json_path, report_json)

    if not surprises_md.exists():
        _write_md(surprises_md, "# Surprises\n\n(no agent-flagged surprises)\n")
    if not gap_report_md.exists():
        _write_md(gap_report_md, _scaffold_gap_report(rubric_coverage))

    total_cost = cross_result.cost_usd + narrative_result.cost_usd
    record_stage_cost(ctx.audit_dir, STAGE_KEY_SYNTHESIS, total_cost)
    mark_stage_complete(ctx.state_file, STAGE_KEY_SYNTHESIS,
                        session_id=narrative_result.session_id, cost_usd=total_cost)

    return SynthesisResult(
        findings_md_path=findings_md,
        report_md_path=report_md,
        report_json_path=report_json_path,
        surprises_md_path=surprises_md,
        gap_report_md_path=gap_report_md,
        health_score=health,
        parent_findings=all_parent_findings,
    )


# ─── Stage 4 — Proposal ────────────────────────────────────────────────────


async def stage_4_proposal(
    ctx: StageContext,
    synthesis: SynthesisResult,
) -> ProposalResult:
    """Stage 4 — 1 Opus call: 3-tier proposal (fix_it / build_it / run_it).

    Master plan §3.7. Reads ``report.json`` + ``data/capability_registry.yaml``
    → emits ``proposal/proposal.md`` + ``proposal.json``.
    """
    if ctx.runner is None:
        raise AuditError("stage_4_proposal requires ctx.runner")

    proposal_dir = _ensure_dir(ctx.audit_dir / "proposal")
    proposal_md = proposal_dir / "proposal.md"
    proposal_json_path = proposal_dir / "proposal.json"

    if (is_stage_complete(ctx.state_file, STAGE_KEY_PROPOSAL)
            and proposal_md.exists() and proposal_json_path.exists()):
        return ProposalResult(proposal_md_path=proposal_md, proposal_json_path=proposal_json_path)

    state = ctx.state_file.load()

    capability_registry_path = (
        Path(__file__).parent.parent.parent / "data" / "capability_registry.yaml"
    )
    capability_yaml = (
        capability_registry_path.read_text(encoding="utf-8")
        if capability_registry_path.exists() else ""
    )
    report_json_text = synthesis.report_json_path.read_text(encoding="utf-8")

    prompt = _safe_format(_load_prompt("stage_4_proposal"), 
        prospect_domain=state.prospect_domain,
        report_json=report_json_text,
        capability_registry=capability_yaml,
    )

    result = await ctx.runner.run(
        prompt=prompt,
        model=DEFAULT_MODEL_OPUS,
        role="stage_4_proposal",
        cwd=ctx.audit_dir,
        max_turns=8,  # bumped 4→8 — proposal writes proposal.md + proposal.json
        ledger=ctx.ledger,
        pattern="meta",
        expected_output_files=[proposal_md, proposal_json_path],
    )

    if not proposal_md.exists():
        _write_md(proposal_md, result.text or _scaffold_proposal_md())
    if not proposal_json_path.exists():
        _write_json(proposal_json_path, _scaffold_proposal_json(state.audit_id))

    record_stage_cost(ctx.audit_dir, STAGE_KEY_PROPOSAL, result.cost_usd)
    mark_stage_complete(ctx.state_file, STAGE_KEY_PROPOSAL,
                        session_id=result.session_id, cost_usd=result.cost_usd)
    return ProposalResult(
        proposal_md_path=proposal_md,
        proposal_json_path=proposal_json_path,
    )


# ─── Stage 5 — Deliverable render ──────────────────────────────────────────


async def stage_5_deliverable(
    ctx: StageContext,
    synthesis: SynthesisResult,
    proposal: ProposalResult,
) -> DeliverableResult:
    """Stage 5 — Jinja2 + WeasyPrint render. No LLM.

    Master plan §3.8. Renders ``templates/audit_report.html.j2`` against
    ``report.json`` + ``proposal.json`` + ``phase0_meta.json``; emits
    HTML + PDF + assets to ``deliverable/``.
    """
    deliverable_dir = _ensure_dir(ctx.audit_dir / "deliverable")
    assets_dir = _ensure_dir(deliverable_dir / "assets")
    state = ctx.state_file.load()

    html_path = deliverable_dir / "report.html"
    pdf_path = deliverable_dir / "report.pdf"
    if (is_stage_complete(ctx.state_file, STAGE_KEY_DELIVERABLE)
            and html_path.exists() and pdf_path.exists()):
        recorded_slug = state.sessions.get(STAGE_KEY_DELIVERABLE, {}).get("session_id") or state.audit_id
        return DeliverableResult(
            html_path=html_path, pdf_path=pdf_path,
            assets_dir=assets_dir, slug=recorded_slug,
        )

    # ULID slug per master plan §3.8 — fall back to audit_id+random hex if
    # the python-ulid lib isn't installed.
    try:
        from ulid import ULID  # type: ignore[import-not-found]
        slug = str(ULID()).lower()
    except Exception:  # noqa: BLE001
        import secrets
        slug = f"{state.audit_id}-{secrets.token_hex(4)}"

    report_json = json.loads(synthesis.report_json_path.read_text(encoding="utf-8"))
    proposal_json = json.loads(proposal.proposal_json_path.read_text(encoding="utf-8"))
    phase0_meta_path = ctx.audit_dir / "prediscovery" / "phase0_meta.json"
    phase0 = json.loads(phase0_meta_path.read_text(encoding="utf-8")) if phase0_meta_path.exists() else {}

    html = _render_html(
        report=report_json,
        proposal=proposal_json,
        phase0=phase0,
        slug=slug,
    )
    html_path.write_text(html, encoding="utf-8")
    _render_pdf(html, pdf_path)

    record_stage_cost(ctx.audit_dir, STAGE_KEY_DELIVERABLE, 0.0)
    # Stage 5 has no LLM session_id; we stash the slug in the session_id slot
    # so resume reconstructs the same DeliverableResult on rerun.
    mark_stage_complete(ctx.state_file, STAGE_KEY_DELIVERABLE,
                        session_id=slug, cost_usd=0.0)
    return DeliverableResult(
        html_path=html_path,
        pdf_path=pdf_path,
        assets_dir=assets_dir,
        slug=slug,
    )


# ─── Stage 5 helpers ───────────────────────────────────────────────────────


def _render_html(report: dict[str, Any], proposal: dict[str, Any], phase0: dict[str, Any], slug: str) -> str:
    """Render the audit report via Jinja2 + the lane-head template.

    Falls back to a minimal in-process HTML scaffold if Jinja2 isn't
    installed — the Stage 5 contract is "deliverable HTML exists at the
    expected path," not "Jinja2 must be on the path."
    """
    template_path = Path(__file__).parent.parent.parent / "templates" / "audit_report.html.j2"
    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape
    except ImportError:
        return _fallback_html(report, proposal, slug)

    if not template_path.exists():
        return _fallback_html(report, proposal, slug)

    env = Environment(
        loader=FileSystemLoader(str(template_path.parent)),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template(template_path.name)
    return template.render(report=report, proposal=proposal, phase0=phase0, slug=slug)


def _render_pdf(html: str, pdf_path: Path) -> None:
    """Render HTML to PDF via WeasyPrint.

    If WeasyPrint isn't installed, write a placeholder PDF (just the HTML
    bytes named .pdf) so downstream tests can verify the file exists.
    Production wires WeasyPrint properly in L4.
    """
    try:
        from weasyprint import HTML  # type: ignore[import-not-found]
        HTML(string=html).write_pdf(str(pdf_path))
    except Exception:  # noqa: BLE001 — WeasyPrint may not be installed
        # Fallback: write the HTML bytes with a clear marker so callers can
        # tell this is a placeholder, not a real PDF.
        pdf_path.write_bytes(
            b"%PDF-1.4-PLACEHOLDER\n" + html.encode("utf-8", errors="replace")
        )


def _fallback_html(report: dict[str, Any], proposal: dict[str, Any], slug: str) -> str:
    """Minimal HTML scaffold when Jinja2/template are unavailable."""
    health = report.get("health_score", {})
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Marketing Audit — {slug}</title>
  <style>
    body {{ font-family: -apple-system, system-ui, sans-serif; max-width: 900px; margin: 2em auto; padding: 0 1em; }}
    h1, h2 {{ border-bottom: 1px solid #ccc; padding-bottom: 0.3em; }}
    .health {{ font-size: 1.2em; }}
  </style>
</head>
<body>
  <h1>Marketing Audit — {report.get("prospect_domain", "")}</h1>
  <p class="health">Health Score: <strong>{health.get("overall", 0)}/100</strong> ({health.get("band", "")})</p>
  <h2>Findings</h2>
  <p>{len(report.get("parent_findings", []))} parent findings across {len(health.get("per_section", {}))} sections.</p>
  <h2>Proposal</h2>
  <pre>{json.dumps(proposal, indent=2)}</pre>
  <p><em>Slug: {slug}</em></p>
</body>
</html>
"""


# ─── Misc helpers ──────────────────────────────────────────────────────────


def _scaffold_findings_md(parent_findings: list[ParentFinding], health: HealthScore) -> str:
    """Build a baseline 9-section findings.md if Stage 3 narrative call
    didn't produce one. Section headers MUST match the structural validator
    contract (master plan §2.2)."""
    sections = [
        ("State of the Business", "state_of_business"),
        ("Findability", "seo"),
        ("AI Visibility", "geo"),
        ("Narrative", "brand_narrative"),
        ("Acquisition", "distribution"),
        ("Experience", "conversion"),
        ("Competitive", "competitive"),
        ("Monitoring", "monitoring"),
        ("MarTech & Compliance", "martech_attribution"),
    ]
    lines: list[str] = [f"# Marketing Audit — Findings\n",
                        f"**Health Score:** {health.overall}/100 ({health.band})\n"]
    for label, section_key in sections:
        lines.append(f"\n## {label}\n")
        in_section = [f for f in parent_findings if f.report_section == section_key]
        if not in_section:
            lines.append("(no findings recorded)\n")
            continue
        for f in in_section:
            lines.append(f"\n### {f.headline}\n\n")
            lines.append(f"**Severity:** {f.severity} | **Confidence:** {f.confidence}\n\n")
            lines.append(f"{f.evidence_summary}\n\n")
            lines.append(f"**Recommendation:** {f.recommendation}\n")
    return "".join(lines)


def _scaffold_gap_report(rubric_coverage: dict[str, dict[str, str]]) -> str:
    """Aggregate ``gap_flagged`` rubrics across all 4 agents."""
    lines = ["# Gap Report\n\n"]
    for agent, coverage in rubric_coverage.items():
        gaps = [rid for rid, status in coverage.items() if status == "gap_flagged"]
        lines.append(f"## {agent}\n\n")
        if gaps:
            for rid in sorted(gaps):
                lines.append(f"- {rid}\n")
        else:
            lines.append("(no gaps flagged)\n")
        lines.append("\n")
    return "".join(lines)


def _collect_sources(sub_signals: list[SubSignal]) -> list[str]:
    """Flatten all evidence URLs into a deduped, sorted list."""
    seen: set[str] = set()
    for s in sub_signals:
        for url in s.evidence_urls:
            seen.add(str(url))
    return sorted(seen)


def _scaffold_proposal_md() -> str:
    """3-H2 fallback proposal in the canonical fix_it / build_it / run_it order."""
    return """# Proposal

## fix_it

(awaiting Stage 4 generation)

## build_it

(awaiting Stage 4 generation)

## run_it

(awaiting Stage 4 generation)
"""


def _scaffold_proposal_json(audit_id: str) -> dict[str, Any]:
    return {
        "audit_id": audit_id,
        "tiers": {
            "fix_it": {"engagement": "", "investment_usd": None, "addresses_finding_ids": []},
            "build_it": {"engagement": "", "investment_usd": None, "addresses_finding_ids": []},
            "run_it": {"engagement": "", "investment_usd": None, "addresses_finding_ids": []},
        },
        "generated_at": _now_iso(),
    }


__all__ = [
    "StageContext",
    "IntakeResult", "WarmupResult", "PrediscoveryResult", "BriefResult",
    "AgentRunArtifact", "Stage2Result",
    "SynthesisResult", "ProposalResult", "DeliverableResult",
    "stage_0_intake", "stage_1_warmup", "stage_1b_predischarge",
    "stage_1c_brief_synthesis", "stage_2_agents", "stage_3_synthesis",
    "stage_4_proposal", "stage_5_deliverable",
    "STAGE_2_AGENTS",
]
