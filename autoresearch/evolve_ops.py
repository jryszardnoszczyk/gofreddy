#!/usr/bin/env python3
"""Evolution loop operations — Python APIs for evolve.py.

Each function takes explicit Python arguments and returns values directly.
Called by evolve.py (the orchestrator) without subprocess indirection.
"""

from __future__ import annotations

import json
import os
import sys
import threading
from pathlib import Path
from typing import Any

# Module-level lock serialising the lineage append + head pointer write.
# mark_promoted is read-modify-write on lineage.jsonl; without this lock,
# concurrent finalists from parallel_for would clobber each other.
_LINEAGE_LOCK = threading.Lock()

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from frontier import entry_active_for_lane as _entry_active_for_lane  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers shared across several functions
# ---------------------------------------------------------------------------

def _load_latest_lineage(archive_dir: str | Path) -> dict[str, dict[str, Any]]:
    """Read lineage.jsonl and return {id: latest_entry} dict."""
    lineage = Path(archive_dir).resolve() / "lineage.jsonl"
    latest: dict[str, dict[str, Any]] = {}
    if not lineage.exists():
        return latest
    for raw in lineage.read_text().splitlines():
        line = raw.strip()
        if not line:
            continue
        payload = json.loads(line)
        latest[payload["id"]] = payload
    return latest


# ---------------------------------------------------------------------------
# load_repo_env_defaults
# ---------------------------------------------------------------------------

_ALLOWED_ENV_KEYS_EXPLICIT = (
    "EVOLUTION_EVAL_BACKEND",
    "EVOLUTION_EVAL_MODEL",
    "EVOLUTION_EVAL_REASONING_EFFORT",
    "EVOLUTION_HOLDOUT_MANIFEST",
    "EVOLUTION_HOLDOUT_JSON",
    "EVOLUTION_PRIVATE_ARCHIVE_DIR",
    "FREDDY_API_URL",
    "FREDDY_API_KEY",
    "OPENAI_API_KEY",
)
"""Explicit per-key allowlist for non-fixture env config."""


_ALLOWED_ENV_KEY_PREFIXES = (
    # Fixture context placeholders for monitoring (any new monitoring
    # fixture that adds env-var context auto-loads via this prefix). Pre-fix
    # we had to add each new fixture's UUID to an explicit list, which broke
    # silently — `--lane all` failed mid-run when a fixture referenced an
    # unallowlisted UUID. The prefix-based load is convention over
    # configuration: declare the key in .env with the canonical prefix and
    # it loads.
    "AUTORESEARCH_SEARCH_MONITORING_",
    "AUTORESEARCH_HOLDOUT_MONITORING_",
)


def _is_allowed_env_key(key: str) -> bool:
    if key in _ALLOWED_ENV_KEYS_EXPLICIT:
        return True
    return any(key.startswith(prefix) for prefix in _ALLOWED_ENV_KEY_PREFIXES)


# Backwards-compat: some external callers may import the explicit tuple.
_ALLOWED_ENV_KEYS = _ALLOWED_ENV_KEYS_EXPLICIT


def load_repo_env_defaults(env_file: str | Path) -> list[tuple[str, str]]:
    """Parse .env file and return list of (key, value) tuples for allowed keys.

    Output is tab-separated lines suitable for bash consumption.
    """
    env_path = Path(env_file).resolve()
    if not env_path.exists():
        return []

    payload: dict[str, str] = {}
    ordered_keys: list[str] = []  # preserve .env order for prefix-loaded keys
    for raw in env_path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if not _is_allowed_env_key(key):
            continue
        if key not in payload:
            ordered_keys.append(key)
        payload[key] = value.strip().strip("'\"")

    # Stable order: explicit-allowlist keys first (in declaration order),
    # then prefix-loaded keys in .env order. Prevents .env shuffles from
    # changing the resulting env-injection order.
    results: list[tuple[str, str]] = []
    explicit_seen = set()
    for key in _ALLOWED_ENV_KEYS_EXPLICIT:
        if key in payload:
            results.append((key, payload[key]))
            explicit_seen.add(key)
    for key in ordered_keys:
        if key not in explicit_seen:
            results.append((key, payload[key]))
    return results


# ---------------------------------------------------------------------------
# normalize_lane
# ---------------------------------------------------------------------------

def normalize_lane(lane: str) -> str:
    """Normalize a lane name. Returns the canonical lane string."""
    from lane_paths import normalize_lane as _normalize_lane
    return _normalize_lane(lane)


# ---------------------------------------------------------------------------
# load_search_config
# ---------------------------------------------------------------------------

def load_search_config(default_suite_path: str | Path, lane: str) -> list[str]:
    """Load search config and return [suite_path, suite_id, backend, model, reasoning].

    Each element is printed as a separate line for bash mapfile consumption.
    """
    import evaluate_variant

    search_path = Path(default_suite_path).resolve()
    manifest = evaluate_variant._project_suite_manifest_for_lane(
        json.loads(search_path.read_text()), lane
    )
    eval_target = manifest.get("eval_target") or {}
    return [
        str(search_path),
        manifest.get("suite_id", ""),
        str(eval_target.get("backend", "")).strip(),
        str(eval_target.get("model", "")).strip(),
        str(eval_target.get("reasoning_effort", "")).strip(),
    ]


# ---------------------------------------------------------------------------
# configure_eval_target_env — pure bash, no heredoc (kept as bash)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# ensure_lane_heads
# ---------------------------------------------------------------------------

def ensure_lane_heads(archive_dir: str | Path) -> dict[str, str]:
    """Initialize current heads and return {lane: variant_id} manifest."""
    from lane_runtime import initialize_current_heads

    manifest = initialize_current_heads(Path(archive_dir).resolve())
    return manifest


# ---------------------------------------------------------------------------
# current_head_variant_id
# ---------------------------------------------------------------------------

def current_head_variant_id(archive_dir: str | Path, lane: str) -> str | None:
    """Return the current head variant ID for a lane, or None."""
    from archive_index import current_variant_id

    return current_variant_id(Path(archive_dir).resolve(), lane=lane)


# ---------------------------------------------------------------------------
# set_current_head
# ---------------------------------------------------------------------------

def set_current_head(archive_dir: str | Path, lane: str, variant_id: str) -> None:
    """Set the current head for a lane."""
    from lane_runtime import set_current_head as _set_current_head

    _set_current_head(Path(archive_dir).resolve(), lane, variant_id)


# ---------------------------------------------------------------------------
# baseline_seeded
# ---------------------------------------------------------------------------

def baseline_seeded(archive_dir: str | Path, suite_id: str, lane: str) -> bool:
    """Check if the baseline is seeded for the given suite and lane.

    Returns True (exit 0) if seeded, False (exit 1) if not.

    Post-audit 2026-05-07: lane gate uses ``_entry_active_for_lane`` so a
    multi-lane scored entry (lane=core, domains[lane].active=True) is
    correctly recognized as the baseline for the workflow lane being
    queried — was rejected pre-fix, blocking the search-suite from
    treating v006 as seeded.
    """
    from archive_index import current_variant_id

    archive_root = Path(archive_dir).resolve()
    current_id = current_variant_id(archive_root, lane=lane)
    lineage = archive_root / "lineage.jsonl"
    if current_id is None or not lineage.exists():
        return False
    latest: dict[str, dict[str, Any]] = {}
    for raw in lineage.read_text().splitlines():
        line = raw.strip()
        if not line:
            continue
        latest[json.loads(line)["id"]] = json.loads(line)
    entry = latest.get(current_id)
    if not entry:
        return False
    if not _entry_active_for_lane(entry, lane):
        return False
    search_metrics = entry.get("search_metrics") or {}
    scores = entry.get("scores") or {}
    if search_metrics.get("suite_id") != suite_id:
        return False
    objective_key = "composite" if lane == "core" else lane
    if not isinstance(scores.get(objective_key), (int, float)):
        return False
    return True


# ---------------------------------------------------------------------------
# holdout_configured
# ---------------------------------------------------------------------------

def holdout_configured() -> bool:
    """Check if holdout is configured in the environment."""
    import evaluate_variant

    return evaluate_variant._holdout_configured(os.environ.copy())


# ---------------------------------------------------------------------------
# promotion_reason
# ---------------------------------------------------------------------------

def promotion_reason(archive_dir: str | Path, variant_id: str) -> str:
    """Return the promotion reason string for a variant."""
    latest = _load_latest_lineage(archive_dir)
    candidate = latest.get(variant_id)
    if not candidate:
        raise SystemExit(1)
    summary = candidate.get("promotion_summary") or {}
    return str(summary.get("reason") or "")


# ---------------------------------------------------------------------------
# variant_has_search_metrics
# ---------------------------------------------------------------------------

def variant_has_search_metrics(archive_dir: str | Path, variant_id: str, lane: str) -> bool:
    """Check if a variant has search metrics for the given lane.

    Post-audit 2026-05-07: lane gate uses ``_entry_active_for_lane`` so
    multi-lane scored entries (lane=core, domains[lane].active=True)
    correctly report having search metrics for the queried workflow lane.
    """
    latest = _load_latest_lineage(archive_dir)
    entry = latest.get(variant_id) or {}
    if not _entry_active_for_lane(entry, lane):
        return False
    search_metrics = entry.get("search_metrics") or {}
    return bool(str(search_metrics.get("suite_id") or ""))


# ---------------------------------------------------------------------------
# is_promotable
# ---------------------------------------------------------------------------

def _holdout_composite(entry: dict | None, *, key: str = "holdout_composite") -> float | None:
    if not isinstance(entry, dict):
        return None
    summary = entry.get("promotion_summary") or {}
    val = summary.get(key)
    return float(val) if isinstance(val, (int, float)) else None


def _per_fixture_scores(
    entry: dict | None,
    *,
    key: str = "score",
    lane: str | None = None,
) -> dict[str, float]:
    """Extract per-fixture scores (primary: key='score', secondary: 'secondary_score').

    Reads from ``search_metrics.domains.<domain>.fixtures_detail`` — the
    per-fixture dict keyed by fixture_id populated by
    ``_aggregate_suite_results`` (Plan A Phase 7 Step 2.5a). ``fixtures`` at
    the same level is an int count, not a mapping, and is ignored here.

    ``lane`` parameter (post-audit 2026-05-07) restricts the result to a
    single workflow lane's fixtures. Pre-fix the function returned ALL
    active-domain fixtures regardless of the lane being judged — the
    promotion judge for ``--lane geo`` was seeing baseline fixtures from
    competitive + monitoring + storyboard mixed with geo, irrelevant
    cross-lane noise it cannot disambiguate. Now:

    - ``lane=None`` (default): return all domains (back-compat for
      ``emit_saturation_cycle_events`` and any caller that genuinely
      wants the full set).
    - ``lane="core"``: same as None — core ran cross-lane and the
      promotion judge for core SHOULD see all active-domain fixtures.
    - ``lane="<workflow>"``: restrict to that single domain's fixtures.

    Archive entries scored before Plan A Phase 7 Step 2.5a landed lack
    ``fixtures_detail`` entirely; those return ``{}`` and the promotion
    judge correctly reasons on sparse signal.
    """
    out: dict[str, float] = {}
    if not isinstance(entry, dict):
        return out
    sm = entry.get("search_metrics") or {}
    domains = sm.get("domains") or {}
    if lane is not None and lane != "core":
        # Workflow lane: restrict to the single domain matching the lane.
        payload = domains.get(lane)
        domain_iter = [(lane, payload)] if isinstance(payload, dict) else []
    else:
        domain_iter = list(domains.items())
    for _domain, payload in domain_iter:
        if not isinstance(payload, dict):
            continue
        detail = payload.get("fixtures_detail")
        if not isinstance(detail, dict):
            continue  # no per-fixture detail preserved for this domain
        for fixture_id, record in detail.items():
            if not isinstance(record, dict):
                continue
            score = record.get(key)
            if isinstance(score, (int, float)):
                out[str(fixture_id)] = float(score)
    return out


def emit_saturation_cycle_events(
    archive_dir: str | Path, lane: str,
    new_head_id: str, prior_head_id: str | None,
) -> int:
    """Emit one ``kind="saturation_cycle"`` event per public fixture that
    was scored on both the new head and the prior head.

    Payload per event: ``{fixture_id, candidate_score, baseline_score,
    baseline_beat, lane}``. ``baseline_beat`` is True when the new head's
    per-fixture score strictly exceeds the prior head's. When ``prior_head_id``
    is None (first-of-lane promotion) or when either head lacks
    ``fixtures_detail`` for a given fixture, no event is emitted for that
    fixture (rotation agent's threshold is 3+ months of events anyway; zero
    events for a fixture just means "no saturation signal yet").

    Returns the count of events emitted. Used by
    ``docs/agent-tasks/rotation-policy.md`` via ``read_events(kind="saturation_cycle")``.
    """
    from autoresearch.events import log_event

    if prior_head_id is None or prior_head_id == new_head_id:
        return 0
    latest = _load_latest_lineage(archive_dir)
    new_entry = latest.get(new_head_id) or {}
    prior_entry = latest.get(prior_head_id) or {}

    new_scores = _per_fixture_scores(new_entry, lane=lane)
    prior_scores = _per_fixture_scores(prior_entry, lane=lane)

    emitted = 0
    for fixture_id, cand_score in new_scores.items():
        base_score = prior_scores.get(fixture_id)
        if base_score is None:
            continue  # prior head didn't score this fixture — no comparison
        log_event(
            kind="saturation_cycle",
            fixture_id=fixture_id,
            lane=lane,
            candidate_score=float(cand_score),
            baseline_score=float(base_score),
            baseline_beat=bool(cand_score > base_score),
            candidate_id=new_head_id,
            baseline_id=prior_head_id,
        )
        emitted += 1
    return emitted


def is_promotable(archive_dir: str | Path, variant_id: str, lane: str) -> bool:
    """Gather full scoring context, delegate promote/reject to the promotion judge.

    No hardcoded thresholds. The judge sees candidate + baseline scores from
    both primary and secondary judges (aggregate + per-fixture), holdout
    composites, and the lane's prior promotion context, then returns a
    decision ∈ {promote, reject, abstain} with reasoning + optional concerns.

    Hard invariant kept programmatic: wrong-lane short-circuit (the judge
    should never be asked to decide about a lane-mismatched variant — that
    is a data bug, not a judgment call). Post-audit 2026-05-07: the
    short-circuit uses ``_entry_active_for_lane`` so multi-lane scored
    candidates (lane=core, domains[lane].active=True) are accepted as
    valid candidates for the workflow lane being judged. Pre-fix the
    label-only check rejected them as "wrong_lane" even though they had
    legitimate per-lane scoring data.

    Abstain handling (belt + suspenders):
      - ``decision != promote/reject`` → False (don't promote on incomplete signal)
      - ``concerns[*].severity == "blocking"`` → False even if decision="promote"

    Judge-unreachable:
      - ``JudgeUnreachable`` raised → False, event kind=promotion_decision
        with reason=judge_unreachable. Matches Plan A Phase 0c: no threshold
        fallback; operator re-runs once the judge is back.
    """
    import evaluate_variant
    from autoresearch.events import log_event
    from autoresearch.judges.promotion_judge import (
        call_promotion_judge,
        JudgeUnreachable,
    )

    latest = _load_latest_lineage(archive_dir)
    entry = latest.get(variant_id)
    base_record = {"variant_id": variant_id, "lane": lane}

    if not _entry_active_for_lane(entry, lane):
        log_event(
            kind="promotion_decision",
            decision="reject", reason="wrong_lane", source="invariant_guard",
            **base_record,
        )
        return False

    archive_root = Path(archive_dir).resolve()
    baseline_entry = evaluate_variant._promotion_baseline(archive_root, variant_id, lane)

    # Re-score baseline on monitoring fixtures (content-drift-contaminated).
    # Monitoring fixtures target different content every week; the baseline's
    # stored scores may reflect a different week's world than the candidate's
    # fresh scores. Re-score so both sides see this cycle's content.
    if baseline_entry is not None:
        baseline_entry = evaluate_variant._refresh_monitoring_scores_for_baseline(
            baseline_entry, lane, archive_root,
        )

    payload = {
        "role": "promotion",
        "candidate_id": variant_id,
        "lane": lane,
        "baseline_id": str(baseline_entry.get("id")) if baseline_entry else None,
        "candidate": {
            "public_score": evaluate_variant._objective_score_from_scores(
                entry.get("scores") if isinstance(entry, dict) else None, lane),
            "holdout_score": _holdout_composite(entry),
            "secondary_public_score": evaluate_variant._objective_score_from_scores(
                entry.get("secondary_scores") if isinstance(entry, dict) else None, lane),
            "secondary_holdout_score": _holdout_composite(entry, key="secondary_holdout_composite"),
            "per_fixture_primary": _per_fixture_scores(entry, key="score", lane=lane),
            "per_fixture_secondary": _per_fixture_scores(entry, key="secondary_score", lane=lane),
            "eligible_for_promotion_flag": bool(
                ((entry or {}).get("promotion_summary") or {}).get("eligible_for_promotion")
            ),
        },
        "baseline": None if baseline_entry is None else {
            "public_score": evaluate_variant._objective_score_from_scores(
                baseline_entry.get("scores"), lane),
            "holdout_score": _holdout_composite(baseline_entry),
            "secondary_public_score": evaluate_variant._objective_score_from_scores(
                baseline_entry.get("secondary_scores"), lane),
            "secondary_holdout_score": _holdout_composite(baseline_entry, key="secondary_holdout_composite"),
            "per_fixture_primary": _per_fixture_scores(baseline_entry, key="score", lane=lane),
            "per_fixture_secondary": _per_fixture_scores(baseline_entry, key="secondary_score", lane=lane),
        },
    }

    try:
        verdict = call_promotion_judge(payload)
    except JudgeUnreachable as exc:
        log_event(
            kind="promotion_decision",
            decision="reject", reason="judge_unreachable",
            error=str(exc)[:200], source="service_outage",
            **base_record,
        )
        print(
            f"is_promotable: {variant_id} REJECT (judge unreachable) — {exc}",
            file=sys.stderr,
        )
        return False

    blocking_concerns = [
        c for c in verdict.concerns
        if isinstance(c, dict) and str(c.get("severity", "")).lower() == "blocking"
    ]
    if verdict.decision not in {"promote", "reject"} or blocking_concerns:
        log_event(
            kind="judge_abstain",
            decision=verdict.decision,
            reasoning=verdict.reasoning,
            confidence=verdict.confidence,
            concerns=verdict.concerns,
            blocking_concerns=blocking_concerns,
            **base_record,
        )
        print(
            f"is_promotable: {variant_id} ABSTAIN "
            f"(decision={verdict.decision!r}, blocking_concerns={len(blocking_concerns)}) "
            f"— {verdict.reasoning}",
            file=sys.stderr,
        )
        return False

    decision = verdict.decision == "promote"
    log_event(
        kind="promotion_decision",
        decision=verdict.decision,
        reasoning=verdict.reasoning,
        confidence=verdict.confidence,
        concerns=verdict.concerns,
        payload_summary={
            "cand_public": payload["candidate"]["public_score"],
            "cand_holdout": payload["candidate"]["holdout_score"],
            "cand_sec_public": payload["candidate"]["secondary_public_score"],
            "cand_sec_holdout": payload["candidate"]["secondary_holdout_score"],
            "base_id": payload["baseline_id"],
        },
        **base_record,
    )
    print(
        f"is_promotable: {variant_id} {verdict.decision.upper()} — {verdict.reasoning}",
        file=sys.stderr,
    )
    return decision


# ---------------------------------------------------------------------------
# record_head_score + check_and_rollback_regressions  (Plan B Phase 6 Step 6)
# ---------------------------------------------------------------------------

ROLLBACK_COOLDOWN_CYCLES = 3
"""Invariant (not judgment): prevent rollback thrash by requiring ≥N
post-promotion cycles between two consecutive rollbacks on the same lane."""

ROLLBACK_DRY_RUN_UNTIL_ISO = "2026-05-15T00:00:00Z"
"""LEGACY constant — kept for backwards compat with anything that imports it.
The actual gate is now ``_auto_rollback_enabled()`` below, which defaults to
DRY-RUN regardless of date. Operator must explicitly opt in via
``AUTORESEARCH_AUTO_ROLLBACK=1``."""


def _auto_rollback_enabled() -> bool:
    """True only when the operator has explicitly opted into live auto-rollback.

    Pre-fix this was gated on a hardcoded date (``ROLLBACK_DRY_RUN_UNTIL_ISO``)
    that would auto-flip live on 2026-05-15. That's a time-bomb: the default
    behavior changes on a calendar tick, not on observed safety. Replaced
    with an explicit env-var opt-in so the operator has positive control.

    To enable auto-rollback after observing the agent's judgment in dry-run
    logs:  ``export AUTORESEARCH_AUTO_ROLLBACK=1``.

    Default = False. Without the flag, the rollback agent's decisions are
    LOGGED with ``decision="rollback_dry_run"`` and the ``promote --undo``
    subprocess is NOT executed, regardless of date.
    """
    return os.environ.get("AUTORESEARCH_AUTO_ROLLBACK", "").strip() == "1"


def record_head_score(
    *, lane: str, head_id: str, public_score: float,
    holdout_score: float | None, promoted_at: str,
) -> None:
    """Emit ``kind="head_score"`` after each promotion — feeds the rollback agent."""
    from autoresearch.events import log_event

    log_event(
        kind="head_score",
        lane=lane,
        head_id=str(head_id),
        promoted_at=promoted_at,
        public_score=float(public_score),
        holdout_score=float(holdout_score) if holdout_score is not None else None,
    )


def check_and_rollback_regressions(archive_dir: str | Path, lane: str) -> bool:
    """Ask rollback_agent whether to revert the current lane head.

    The agent reads the raw pre+post trajectory from the unified events log.
    No delta threshold, no window count — agent decides. Returns True when a
    rollback was EXECUTED (not when one was logged in dry-run).

    Invariants (programmatic guards, not judgments):
      * wrong-lane: only processes ``head_score`` entries matching ``lane``.
      * cooldown: requires ≥``ROLLBACK_COOLDOWN_CYCLES`` post-promotion
        samples since the last recorded ``decision="rollback"`` on this lane.
      * need prior head + ≥2 post-promotion samples on the current head
        before asking the agent.

    Dry-run gate: by default, rollback decisions are logged as
    ``kind="regression_check"`` with ``decision="rollback_dry_run"`` but
    the subprocess ``promote --undo`` is NOT run. Operator must explicitly
    opt in via ``AUTORESEARCH_AUTO_ROLLBACK=1`` to enable live execution.
    The caller's return is False in dry-run mode.
    """
    import datetime as _dt
    import subprocess as _subprocess
    from autoresearch.events import log_event, read_events
    from autoresearch.judges.promotion_judge import (
        call_promotion_judge, JudgeUnreachable,
    )

    records = [r for r in read_events(kind="head_score") if r.get("lane") == lane]
    if not records:
        return False
    current_head = records[-1]["head_id"]
    post = [r for r in records if r["head_id"] == current_head]
    pre = [r for r in records if r["head_id"] != current_head]
    if not pre or len(post) < 2:
        return False

    # Cooldown.
    prior_rollbacks = [
        r for r in read_events(kind="regression_check")
        if r.get("lane") == lane and r.get("decision") == "rollback"
    ]
    if prior_rollbacks:
        last_rollback_ts = prior_rollbacks[-1].get("timestamp", "")
        post_since_rollback = [
            r for r in records if r.get("timestamp", "") > last_rollback_ts
        ]
        if len(post_since_rollback) < ROLLBACK_COOLDOWN_CYCLES:
            return False

    try:
        verdict = call_promotion_judge({
            "role": "rollback", "lane": lane,
            "current_head": current_head,
            "prior_head": pre[-1]["head_id"],
            "post_promotion_trajectory": post,
            "pre_promotion_trajectory": pre[-5:],
        })
    except JudgeUnreachable as exc:
        log_event(
            kind="regression_check",
            lane=lane, current_head=current_head,
            decision="skip", reason="judge_unreachable",
            error=str(exc)[:200],
        )
        return False

    log_event(
        kind="regression_check",
        lane=lane, current_head=current_head,
        prior_head=pre[-1]["head_id"],
        decision=verdict.decision,
        reasoning=verdict.reasoning,
        confidence=verdict.confidence,
        concerns=verdict.concerns,
    )

    if verdict.decision != "rollback":
        return False

    # Dry-run gate: auto-rollback is OFF by default. Operator must export
    # AUTORESEARCH_AUTO_ROLLBACK=1 to enable live execution. Pre-fix this
    # was gated on a hardcoded ISO date that would auto-flip live on
    # 2026-05-15 — a time-bomb where default behavior changes on a calendar
    # tick rather than observed safety. Now an explicit operator opt-in.
    if not _auto_rollback_enabled():
        log_event(
            kind="regression_check",
            lane=lane, current_head=current_head,
            decision="rollback_dry_run",
            reasoning=(
                "would rollback but AUTORESEARCH_AUTO_ROLLBACK env var not "
                "set; export AUTORESEARCH_AUTO_ROLLBACK=1 to enable live mode"
            ),
            original_agent_reasoning=verdict.reasoning,
        )
        print(
            f"⚠️  AUTO-ROLLBACK (DRY-RUN — opt-in env var unset): would "
            f"revert {current_head} → {pre[-1]['head_id']}: {verdict.reasoning}",
            file=sys.stderr,
        )
        return False

    # Live rollback.
    print(
        f"⚠️  AUTO-ROLLBACK: {current_head} → {pre[-1]['head_id']}: "
        f"{verdict.reasoning}",
        file=sys.stderr,
    )
    _subprocess.run(
        ["./autoresearch/evolve.sh", "promote", "--undo", "--lane", lane],
        check=True,
    )
    return True


# ---------------------------------------------------------------------------
# mark_promoted
# ---------------------------------------------------------------------------

def mark_promoted(archive_dir: str | Path, variant_id: str, timestamp: str) -> None:
    """Mark a variant as promoted in lineage.jsonl.

    Read-modify-write on lineage.jsonl. Callers that may run concurrently
    (parallel finalists) must use ``promote_atomic`` rather than calling
    this directly so the read + append are serialised.
    """
    archive_root = Path(archive_dir).resolve()
    lineage = archive_root / "lineage.jsonl"
    latest: dict[str, dict[str, Any]] = {}
    for raw in lineage.read_text().splitlines():
        line = raw.strip()
        if not line:
            continue
        payload = json.loads(line)
        latest[payload["id"]] = payload
    if variant_id not in latest:
        raise SystemExit(f"Variant not found in lineage: {variant_id}")
    entry = dict(latest[variant_id])
    entry["promoted_at"] = timestamp
    with lineage.open("a") as handle:
        handle.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------------
# promote_atomic
# ---------------------------------------------------------------------------

def promote_atomic(
    archive_dir: str | Path,
    lane: str,
    variant_id: str,
    timestamp: str,
) -> None:
    """Single critical section for promotion: lineage append + head pointer write.

    Holds ``_LINEAGE_LOCK`` across both writes so concurrent finalists never
    clobber each other's lineage append or head update.
    """
    with _LINEAGE_LOCK:
        mark_promoted(archive_dir, variant_id, timestamp)
        set_current_head(archive_dir, lane, variant_id)


# ---------------------------------------------------------------------------
# previous_promoted_variant
# ---------------------------------------------------------------------------

def previous_promoted_variant(archive_dir: str | Path, lane: str) -> str:
    """Return the variant ID of the previously promoted variant (for rollback)."""
    latest = _load_latest_lineage(archive_dir)
    promoted = [
        entry
        for entry in latest.values()
        if entry.get("promoted_at") and _entry_active_for_lane(entry, lane)
    ]
    promoted.sort(key=lambda entry: str(entry.get("promoted_at") or ""))
    if len(promoted) < 2:
        raise SystemExit("No previous promoted variant to rollback to")
    return promoted[-2]["id"]


# ---------------------------------------------------------------------------
# holdout_suite_id
# ---------------------------------------------------------------------------

def holdout_suite_id(lane: str) -> str | None:
    """Return the holdout suite ID, or None if not configured."""
    import evaluate_variant

    manifest = evaluate_variant._load_holdout_manifest(os.environ.copy(), lane)
    if manifest is None:
        return None
    return str(manifest["suite_id"])


# ---------------------------------------------------------------------------
# finalize_candidate_ids
# ---------------------------------------------------------------------------

def finalize_candidate_ids(
    archive_dir: str | Path,
    search_suite_path: str | Path,
    lane: str,
) -> list[str]:
    """Return list of variant IDs that are frontier finalization candidates."""
    import evaluate_variant
    from archive_index import load_json, ordered_latest_entries
    from frontier import best_variant_in_lane, has_search_metrics

    archive_root = Path(archive_dir).resolve()
    suite_manifest = load_json(Path(search_suite_path).resolve(), default={})
    # Post-audit 2026-05-07: lane filter uses _entry_active_for_lane so
    # multi-lane scored entries (lane=core, domains[lane].active=True)
    # are accepted as workflow-lane candidates, not silently dropped.
    entries = [
        entry
        for entry in ordered_latest_entries(archive_root)
        if _entry_active_for_lane(entry, lane)
    ]
    entries = [
        entry
        for entry in entries
        if entry.get("status") != "discarded" and has_search_metrics(entry)
    ]
    baseline_entry = evaluate_variant._promotion_baseline(archive_root, "", lane)
    baseline_id = str(baseline_entry["id"]) if baseline_entry else None

    # Phase 2 (Unit 5): per-lane single-best replaces the 3-objective Pareto.
    best = best_variant_in_lane(entries, lane)
    frontier_entries = [best] if best is not None else []

    result: list[str] = []
    for entry in frontier_entries:
        variant_id = str(entry.get("id") or "")
        if not variant_id or variant_id == baseline_id:
            continue
        if not (archive_root / variant_id).is_dir():
            continue
        result.append(variant_id)
    return result


# ---------------------------------------------------------------------------
# finalize_status
# ---------------------------------------------------------------------------

def finalize_status(
    archive_dir: str | Path,
    variant_id: str,
    lane: str,
) -> tuple[bool, str]:
    """Return (eligible, reason) for a variant's finalize status."""
    import evaluate_variant

    archive_root = Path(archive_dir).resolve()
    manifest = evaluate_variant._load_holdout_manifest(os.environ.copy(), lane)
    if manifest is None:
        raise SystemExit(2)
    suite_id = str(manifest["suite_id"])
    eligible, reason, _record = evaluate_variant._private_finalize_status(
        archive_dir=archive_root,
        variant_id=variant_id,
        suite_id=suite_id,
        lane=lane,
    )
    return eligible, reason


# ---------------------------------------------------------------------------
# best_finalized_variant
# ---------------------------------------------------------------------------

def best_finalized_variant(
    archive_dir: str | Path,
    suite_id: str,
    lane: str,
    candidate_ids: list[str] | None = None,
) -> str | None:
    """Return the best finalized variant ID, or None."""
    import evaluate_variant

    archive_root = Path(archive_dir).resolve()
    best = evaluate_variant._best_finalized_candidate(
        archive_dir=archive_root,
        suite_id=suite_id,
        lane=lane,
        candidate_ids=candidate_ids or None,
    )
    if not isinstance(best, dict):
        return None
    return str(best["variant_id"])


# ---------------------------------------------------------------------------
# write_finalized_shortlist
# ---------------------------------------------------------------------------

def write_finalized_shortlist(
    archive_dir: str | Path,
    suite_id: str,
    lane: str,
    variant_ids: list[str],
) -> str | None:
    """Write the finalized shortlist and return the path (or None)."""
    import evaluate_variant

    archive_root = Path(archive_dir).resolve()
    baseline_entry = evaluate_variant._promotion_baseline(archive_root, "", lane)
    baseline_variant_id = str(baseline_entry["id"]) if baseline_entry else None
    results: list[dict[str, Any]] = []
    for variant_id in variant_ids:
        record = evaluate_variant._load_private_finalize_result(variant_id, suite_id)
        if isinstance(record, dict):
            results.append(record)
    path = evaluate_variant._write_private_finalized_shortlist(
        suite_id=suite_id,
        baseline_variant_id=baseline_variant_id,
        lane=lane,
        results=results,
    )
    return str(path) if path is not None else None


# ---------------------------------------------------------------------------
# prepare_meta_workspace
# ---------------------------------------------------------------------------

def prepare_meta_workspace(
    archive_dir: str | Path,
    variant_id: str,
    workspace_root: str | Path,
    lane: str,
) -> tuple[str, str]:
    """Prepare the meta workspace and return (visible_root, variant_workspace)."""
    import archive_index

    archive_root = Path(archive_dir).resolve()
    visible_root, variant_workspace = archive_index.prepare_meta_workspace(
        archive_dir=archive_root,
        variant_id=variant_id,
        workspace_root=Path(workspace_root).resolve(),
        lane=lane,
    )
    return str(visible_root), str(variant_workspace)


# ---------------------------------------------------------------------------
# write_lane_context
# ---------------------------------------------------------------------------

def write_lane_context(archive_root: str | Path, lane: str) -> None:
    """Write lane-context.md to the archive root."""
    from lane_paths import LANES, lane_prefixes, normalize_lane as _normalize_lane

    archive_root_path = Path(archive_root).resolve()
    lane = _normalize_lane(lane)
    lines = [f"# Lane Context", "", f"Active lane: `{lane}`", ""]
    if lane == "core":
        lines.extend(
            [
                "Editable scope:",
                "- Any shared-core path not owned by a workflow lane.",
                "- Workflow-owned paths are read-only in this pass.",
                "",
                "Workflow-owned prefixes:",
            ]
        )
        for workflow_lane in (item for item in LANES if item != "core"):
            lines.append(
                f"- `{workflow_lane}`: "
                + ", ".join(f"`{prefix}`" for prefix in lane_prefixes(workflow_lane))
            )
    else:
        prefixes = lane_prefixes(lane)
        lines.extend(
            [
                "Editable scope:",
                *[f"- `{prefix}`" for prefix in prefixes],
                "",
                "All other paths are read-only reference material for this pass.",
            ]
        )

        lines.extend(
            [
                "",
                "Do not edit shared-core paths from a workflow lane. If a shared-core change seems necessary, leave evidence in the mutation and let the core lane handle it.",
            ]
        )

    (archive_root_path / "lane-context.md").write_text("\n".join(lines).rstrip() + "\n")


# ---------------------------------------------------------------------------
# sync_meta_workspace
# ---------------------------------------------------------------------------

def sync_meta_workspace(
    source_variant_dir: str | Path,
    target_variant_dir: str | Path,
    lane: str,
) -> None:
    """Sync variant workspace back from meta workspace."""
    import archive_index

    archive_index.sync_variant_workspace(
        Path(source_variant_dir).resolve(),
        Path(target_variant_dir).resolve(),
        lane=lane,
    )


# ---------------------------------------------------------------------------
# variant_in_lineage (inline heredoc at the candidate loop end)
# ---------------------------------------------------------------------------

def variant_in_lineage(archive_dir: str | Path, variant_id: str) -> bool:
    """Check if a variant ID exists in lineage.jsonl."""
    latest = _load_latest_lineage(archive_dir)
    return variant_id in latest


if __name__ == "__main__":
    pass
