#!/usr/bin/env python3
"""Evolution loop operations — Python APIs for evolve.py.

Each function takes explicit Python arguments and returns values directly.
Called by evolve.py (the orchestrator) without subprocess indirection.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))


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

_ALLOWED_ENV_KEYS = (
    "EVOLUTION_EVAL_BACKEND",
    "EVOLUTION_EVAL_MODEL",
    "EVOLUTION_EVAL_REASONING_EFFORT",
    "AUTORESEARCH_SEARCH_MONITORING_SHOPIFY_CONTEXT",
    "AUTORESEARCH_SEARCH_MONITORING_LULULEMON_CONTEXT",
    "AUTORESEARCH_SEARCH_MONITORING_NOTION_CONTEXT",
    "EVOLUTION_HOLDOUT_MANIFEST",
    "EVOLUTION_HOLDOUT_JSON",
    "EVOLUTION_PRIVATE_ARCHIVE_DIR",
    "FREDDY_API_URL",
    "FREDDY_API_KEY",
    "OPENAI_API_KEY",
)


def load_repo_env_defaults(env_file: str | Path) -> list[tuple[str, str]]:
    """Parse .env file and return list of (key, value) tuples for allowed keys.

    Output is tab-separated lines suitable for bash consumption.
    """
    env_path = Path(env_file).resolve()
    if not env_path.exists():
        return []

    payload: dict[str, str] = {}
    for raw in env_path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key not in _ALLOWED_ENV_KEYS:
            continue
        payload[key] = value.strip().strip("'\"")

    results: list[tuple[str, str]] = []
    for key in _ALLOWED_ENV_KEYS:
        if key in payload:
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
    if str(entry.get("lane") or "").strip().lower() != lane:
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
    """Check if a variant has search metrics for the given lane."""
    latest = _load_latest_lineage(archive_dir)
    entry = latest.get(variant_id) or {}
    if str(entry.get("lane") or "").strip().lower() != lane:
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


def _per_fixture_scores(entry: dict | None, *, key: str = "score") -> dict[str, float]:
    """Extract per-fixture scores (primary: key='score', secondary: 'secondary_score').

    Current lineage shape in the archive is ``fixtures: <int>`` (a count), not
    ``fixtures: {fixture_id: {...}}`` — ``_aggregate_suite_results`` doesn't
    preserve per-fixture records yet (Plan B Phase 6 prerequisite). Until that
    ships, treat non-dict ``fixtures`` as "no per-fixture detail available"
    and return an empty dict; the promotion judge already reasons correctly
    on sparse signal (verdict=reject with concerns naming the missing data).
    """
    out: dict[str, float] = {}
    if not isinstance(entry, dict):
        return out
    sm = entry.get("search_metrics") or {}
    for _domain, payload in (sm.get("domains") or {}).items():
        if not isinstance(payload, dict):
            continue
        fixtures = payload.get("fixtures")
        if not isinstance(fixtures, dict):
            continue  # fixture count (int) or other shape — no per-fixture detail
        for fixture_id, record in fixtures.items():
            if not isinstance(record, dict):
                continue
            score = record.get(key)
            if isinstance(score, (int, float)):
                out[str(fixture_id)] = float(score)
    return out


def is_promotable(archive_dir: str | Path, variant_id: str, lane: str) -> bool:
    """Gather full scoring context, delegate promote/reject to the promotion judge.

    No hardcoded thresholds. The judge sees candidate + baseline scores from
    both primary and secondary judges (aggregate + per-fixture), holdout
    composites, and the lane's prior promotion context, then returns a
    decision ∈ {promote, reject, abstain} with reasoning + optional concerns.

    Hard invariant kept programmatic: wrong-lane short-circuit (the judge
    should never be asked to decide about a lane-mismatched variant — that
    is a data bug, not a judgment call).

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

    if str((entry or {}).get("lane") or "").strip().lower() != lane:
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
            "per_fixture_primary": _per_fixture_scores(entry, key="score"),
            "per_fixture_secondary": _per_fixture_scores(entry, key="secondary_score"),
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
            "per_fixture_primary": _per_fixture_scores(baseline_entry, key="score"),
            "per_fixture_secondary": _per_fixture_scores(baseline_entry, key="secondary_score"),
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
"""First-week observation window: before this date, rollback decisions are
LOGGED as ``rollback_dry_run`` but the ``promote --undo`` command is NOT
executed. Operator audits the agent's judgment before it gets write access.
Update this constant via PR, not runtime."""


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

    Dry-run window: while ``datetime.utcnow() < ROLLBACK_DRY_RUN_UNTIL_ISO``,
    rollback decisions are logged as ``kind="regression_check"`` with
    ``decision="rollback_dry_run"`` but the subprocess ``promote --undo``
    is NOT run. The caller's return is False in that case.
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

    # Dry-run window check.
    now_iso = _dt.datetime.now(_dt.timezone.utc).isoformat().replace("+00:00", "Z")
    if now_iso < ROLLBACK_DRY_RUN_UNTIL_ISO:
        log_event(
            kind="regression_check",
            lane=lane, current_head=current_head,
            decision="rollback_dry_run",
            reasoning=(
                f"would rollback but dry-run window active until "
                f"{ROLLBACK_DRY_RUN_UNTIL_ISO}"
            ),
            original_agent_reasoning=verdict.reasoning,
        )
        print(
            f"⚠️  AUTO-ROLLBACK (DRY-RUN): would revert {current_head} → "
            f"{pre[-1]['head_id']}: {verdict.reasoning}",
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
    """Mark a variant as promoted in lineage.jsonl."""
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
# previous_promoted_variant
# ---------------------------------------------------------------------------

def previous_promoted_variant(archive_dir: str | Path, lane: str) -> str:
    """Return the variant ID of the previously promoted variant (for rollback)."""
    latest = _load_latest_lineage(archive_dir)
    promoted = [
        entry
        for entry in latest.values()
        if entry.get("promoted_at") and str(entry.get("lane") or "").strip().lower() == lane
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
    entries = [
        entry
        for entry in ordered_latest_entries(archive_root)
        if str(entry.get("lane") or "").strip().lower() == lane
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
    manifest = evaluate_variant._load_holdout_manifest(os.environ.copy())
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
