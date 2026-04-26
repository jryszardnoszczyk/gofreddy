#!/usr/bin/env python3
"""Manifest-driven variant evaluation for autoresearch evolution."""

from __future__ import annotations

import argparse
import glob
import json
import math
import os
import random
import re
import shutil
import signal
import statistics
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from archive_index import (
    append_lineage_entries,
    append_lineage_entry,
    current_variant_id,
    load_json,
    load_latest_lineage,
    ordered_latest_entries,
    refresh_archive_outputs,
    summarize_variant_diff,
)
from frontier import DOMAINS, has_search_metrics
from lane_paths import WORKFLOW_LANES, normalize_lane, path_owned_by_lane

ENV_REF = re.compile(r"^\$\{([A-Z0-9_]+)\}$")
DELIVERABLES = {
    "geo": "optimized/*.md",
    "competitive": "brief.md",
    "monitoring": "digest.md",
    "storyboard": "stories/*.json",
}
# Intermediate artifacts that indicate the session did real work even if
# final deliverables aren't produced yet.  Used by _has_deliverables to
# recognize partial-but-valid sessions.
_INTERMEDIATE_ARTIFACTS = {
    "monitoring": "mentions/*.json",
    "storyboard": "patterns/*.json",
}


def _geometric_mean(scores: list[float], *, floor: float = 0.01) -> float:
    """Geometric mean with a floor so a single near-zero score doesn't zero the product."""
    if not scores:
        return 0.0
    floored = [max(float(s), floor) for s in scores]
    return math.prod(floored) ** (1 / len(floored))


def _resolve_week_relative(env_map: dict[str, str], today: date | None = None) -> dict[str, str]:
    """Expand AUTORESEARCH_WEEK_RELATIVE into concrete WEEK_START / WEEK_END dates.

    Accepts ``most_recent_complete`` or ``most_recent_complete_minus_1``; unset values
    pass through unchanged so non-monitoring fixtures aren't affected.  ``today``
    defaults to UTC so evaluators running in different local timezones resolve to
    the same week boundaries.
    """
    spec = env_map.get("AUTORESEARCH_WEEK_RELATIVE", "").strip()
    if not spec:
        return env_map
    if spec not in ("most_recent_complete", "most_recent_complete_minus_1"):
        raise ValueError(f"Unknown AUTORESEARCH_WEEK_RELATIVE: {spec!r}")
    today = today or datetime.now(timezone.utc).date()
    days_since_sunday = (today.weekday() + 1) % 7 or 7
    last_sunday = today - timedelta(days=days_since_sunday)
    last_monday = last_sunday - timedelta(days=6)
    offset = 1 if spec == "most_recent_complete_minus_1" else 0
    resolved = dict(env_map)
    resolved["AUTORESEARCH_WEEK_START"] = (last_monday - timedelta(weeks=offset)).isoformat()
    resolved["AUTORESEARCH_WEEK_END"] = (last_sunday - timedelta(weeks=offset)).isoformat()
    return resolved


@dataclass(frozen=True)
class EvalTarget:
    """Explicit session-eval target for benchmark execution."""

    backend: str
    model: str
    reasoning_effort: str | None


@dataclass(frozen=True)
class Fixture:
    """One search-suite fixture from a suite manifest."""

    suite_id: str
    domain: str
    fixture_id: str
    client: str
    context: str
    version: str
    max_iter: int
    timeout: int
    env: dict[str, str]
    anchor: bool = False


@dataclass(frozen=True)
class SessionRun:
    """Filesystem output for one benchmark execution."""

    fixture: Fixture
    session_dir: Path | None
    produced_output: bool
    runner_exit_code: int | None
    wall_time_seconds: float


def _repo_root() -> Path:
    for parent in SCRIPT_DIR.parents:
        if (parent / "cli" / "pyproject.toml").exists():
            return parent
    return SCRIPT_DIR.parent


def _resolve_path(path_str: str | None, *, base: Path) -> Path | None:
    if not path_str:
        return None
    raw = Path(path_str)
    return raw if raw.is_absolute() else (base / raw).resolve()


def _active_domains_from_manifest(payload: dict[str, Any]) -> tuple[str, ...]:
    objective_domain = str(payload.get("objective_domain", "")).strip().lower()
    if objective_domain:
        if objective_domain not in DOMAINS:
            raise RuntimeError(f"Suite manifest objective_domain must be one of {DOMAINS}, got {objective_domain!r}.")
        return (objective_domain,)

    raw_active_domains = payload.get("active_domains")
    if isinstance(raw_active_domains, list) and raw_active_domains:
        active_domains = tuple(str(domain).strip().lower() for domain in raw_active_domains if str(domain).strip())
        invalid = [domain for domain in active_domains if domain not in DOMAINS]
        if invalid:
            raise RuntimeError(f"Suite manifest active_domains contains invalid domains: {invalid!r}.")
        return active_domains
    return DOMAINS


def _suite_active_domains(suite_manifest: dict[str, Any]) -> tuple[str, ...]:
    return _active_domains_from_manifest(suite_manifest)


def _project_suite_manifest_for_lane(
    suite_manifest: dict[str, Any],
    lane: str,
) -> dict[str, Any]:
    lane = normalize_lane(lane)
    active_domains = DOMAINS if lane == "core" else (lane,)
    projected_domains: dict[str, list[dict[str, Any]]] = {}
    raw_domains = suite_manifest.get("domains") or {}
    for domain in DOMAINS:
        fixtures = raw_domains.get(domain)
        projected_domains[domain] = list(fixtures) if domain in active_domains and isinstance(fixtures, list) else []

    projected = {**suite_manifest, "domains": projected_domains, "active_domains": list(active_domains)}
    if lane == "core":
        projected.pop("objective_domain", None)
    else:
        projected["objective_domain"] = lane
    return projected


def _require_eval_target(
    env: dict[str, str],
    suite_manifest: dict[str, Any],
) -> EvalTarget:
    backend = env.get("EVOLUTION_EVAL_BACKEND", "").strip().lower()
    model = env.get("EVOLUTION_EVAL_MODEL", "").strip()
    if backend not in {"claude", "codex"}:
        raise RuntimeError(
            "EVOLUTION_EVAL_BACKEND is required and must be one of: claude, codex."
        )
    if not model:
        raise RuntimeError("EVOLUTION_EVAL_MODEL is required.")

    suite_target = suite_manifest.get("eval_target")
    if isinstance(suite_target, dict):
        suite_backend = str(suite_target.get("backend", "")).strip().lower()
        suite_model = str(suite_target.get("model", "")).strip()
        if suite_backend and suite_backend != backend:
            raise RuntimeError(
                f"EVOLUTION_EVAL_BACKEND={backend!r} does not match suite eval_target.backend={suite_backend!r}."
            )
        if suite_model and suite_model != model:
            raise RuntimeError(
                f"EVOLUTION_EVAL_MODEL={model!r} does not match suite eval_target.model={suite_model!r}."
            )

    reasoning_effort = env.get("EVOLUTION_EVAL_REASONING_EFFORT", "").strip() or None
    if not reasoning_effort and isinstance(suite_target, dict):
        reasoning_effort = str(suite_target.get("reasoning_effort", "")).strip() or None
    return EvalTarget(backend=backend, model=model, reasoning_effort=reasoning_effort)


def _expand_manifest_value(value: Any, env: dict[str, str], *, field_name: str) -> Any:
    if isinstance(value, str):
        match = ENV_REF.fullmatch(value.strip())
        if match:
            env_var = match.group(1)
            resolved = env.get(env_var, "").strip()
            if not resolved:
                raise RuntimeError(
                    f"Fixture field {field_name!r} requires environment variable {env_var}, but it is not set."
                )
            return resolved
        return value
    if isinstance(value, list):
        return [_expand_manifest_value(item, env, field_name=field_name) for item in value]
    if isinstance(value, dict):
        return {
            key: _expand_manifest_value(item, env, field_name=f"{field_name}.{key}")
            for key, item in value.items()
        }
    return value


def _normalize_suite_manifest(
    payload: dict[str, Any],
    *,
    env: dict[str, str],
    source: str,
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise RuntimeError(f"Suite manifest is not valid JSON: {source}")
    suite_id = str(payload.get("suite_id", "")).strip()
    if not suite_id:
        raise RuntimeError(f"Suite manifest is missing suite_id: {source}")
    domains = payload.get("domains")
    if not isinstance(domains, dict):
        raise RuntimeError(f"Suite manifest is missing domains: {source}")
    active_domains = _active_domains_from_manifest(payload)

    normalized_domains: dict[str, list[dict[str, Any]]] = {}
    for domain in DOMAINS:
        fixtures = domains.get(domain)
        if domain not in active_domains:
            normalized_domains[domain] = []
            continue
        if not isinstance(fixtures, list) or not fixtures:
            raise RuntimeError(f"Suite manifest must define at least one fixture for domain={domain}.")
        normalized: list[dict[str, Any]] = []
        for fixture in fixtures:
            if not isinstance(fixture, dict):
                raise RuntimeError(f"Fixture payload must be an object in suite={suite_id}, domain={domain}.")
            normalized.append(_expand_manifest_value(fixture, env, field_name=f"{suite_id}.{domain}"))
        normalized_domains[domain] = normalized

    return {**payload, "domains": normalized_domains, "active_domains": list(active_domains)}


def _load_suite_manifest(path: Path, env: dict[str, str]) -> dict[str, Any]:
    payload = load_json(path)
    return _normalize_suite_manifest(payload, env=env, source=str(path))

def _load_manifest_from_path(manifest_path: str) -> dict[str, Any] | None:
    if manifest_path:
        payload = load_json(Path(manifest_path).resolve())
        if not isinstance(payload, dict):
            raise RuntimeError(f"Suite manifest is not valid JSON: {manifest_path}")
        return payload
    return None


def _reject_redacted_example(payload: dict[str, Any], source: str) -> None:
    """Refuse a holdout payload carrying the redacted-example sentinel.

    Accidentally pointing ``EVOLUTION_HOLDOUT_MANIFEST`` at
    ``autoresearch/eval_suites/holdout-v1.json.example`` (or any manifest
    derived from it without scrubbing the sentinel) would cause holdout
    sessions to run against REDACTED stub URLs. Fail loud instead.
    """
    if payload.get("is_redacted_example") is True:
        raise RuntimeError(
            f"refusing to load redacted-example holdout manifest ({source}): "
            "`is_redacted_example: true` sentinel is set. The in-repo .example "
            "file is a shape reference only; real holdout manifests live "
            "out-of-repo at ~/.config/gofreddy/holdouts/ (chmod 600)."
        )


def _load_holdout_manifest(env: dict[str, str], lane: str = "core") -> dict[str, Any] | None:
    lane = normalize_lane(lane)
    manifest_path = env.get("EVOLUTION_HOLDOUT_MANIFEST", "").strip()
    payload = _load_manifest_from_path(manifest_path)
    if payload is None:
        return None
    _reject_redacted_example(payload, manifest_path or "EVOLUTION_HOLDOUT_MANIFEST")
    return _normalize_suite_manifest(
        _project_suite_manifest_for_lane(payload, lane),
        env=env,
        source=f"holdout:{lane}",
    )


def _holdout_configured(env: dict[str, str]) -> bool:
    return bool(env.get("EVOLUTION_HOLDOUT_MANIFEST", "").strip())


def _fixture_from_payload(suite_id: str, domain: str, payload: dict[str, Any]) -> Fixture:
    fixture_id = str(payload.get("fixture_id", "")).strip()
    client = str(payload.get("client", "")).strip()
    context = str(payload.get("context", "")).strip()
    if not fixture_id or not client or not context:
        raise RuntimeError(f"Fixture in suite={suite_id}, domain={domain} must define fixture_id, client, and context.")
    version = payload.get("version")
    if not isinstance(version, str) or not version.strip():
        raise RuntimeError(
            f"Fixture {fixture_id!r} in suite={suite_id} missing required 'version' field"
        )
    env_payload = payload.get("env") or {}
    if not isinstance(env_payload, dict):
        raise RuntimeError(f"Fixture {fixture_id} env payload must be an object.")
    raw_env = {str(key): str(value) for key, value in env_payload.items()}
    return Fixture(
        suite_id=suite_id,
        domain=domain,
        fixture_id=fixture_id,
        client=client,
        context=context,
        version=version.strip(),
        max_iter=int(payload.get("max_iter", 3)),
        timeout=int(payload.get("timeout", 300)),
        env=_resolve_week_relative(raw_env),
        anchor=bool(payload.get("anchor", False)),
    )


def _suite_fixtures(suite_manifest: dict[str, Any]) -> dict[str, list[Fixture]]:
    suite_id = str(suite_manifest["suite_id"])
    fixtures: dict[str, list[Fixture]] = {}
    active_domains = set(_suite_active_domains(suite_manifest))
    for domain in DOMAINS:
        if domain not in active_domains:
            fixtures[domain] = []
            continue
        fixtures[domain] = [
            _fixture_from_payload(suite_id, domain, payload)
            for payload in suite_manifest["domains"][domain]
        ]
    return fixtures


def _sample_fixtures(
    fixtures_by_domain: dict[str, list[Fixture]],
    rotation_config: dict[str, Any],
    variant_id: str,
) -> dict[str, list[Fixture]]:
    """Stratified sampling: anchors + random per domain.

    When ``seed_source=="generation"`` the seed comes from EVOLUTION_COHORT_ID
    so variants within the same cohort evaluate on an identical fixture subset
    and their composites stay comparable. Monitoring arc-pair fixtures
    (AUTORESEARCH_MONITORING_ARC_PAIR_ID) are sampled atomically — if one is
    picked, all siblings run in ARC_ROLE order so t0's digest is available
    before t1 requests it.
    """
    seed_source = str(rotation_config.get("seed_source", "variant_id"))
    if seed_source == "generation":
        cohort_env = os.environ.get("EVOLUTION_COHORT_ID", "").strip()
        if cohort_env:
            seed: str = f"cohort-{cohort_env}"
        else:
            print(
                "WARN: EVOLUTION_COHORT_ID not set; falling back to variant-id-derived "
                "cohort. Cross-variant scores within a generation may not be comparable.",
                file=sys.stderr,
            )
            cohort_size = int(rotation_config.get("cohort_size", 3))
            try:
                # Variant IDs are 1-indexed (v001, v002, ...).  Use the same
                # (n - 1) // cohort_size mapping as evolve.py so standalone
                # evaluation and evolution-driven evaluation land on the same
                # cohort boundaries.
                n = int(variant_id.lstrip("v"))
                seed = f"cohort-derived-{(n - 1) // max(cohort_size, 1)}"
            except ValueError:
                seed = variant_id
    else:
        seed = variant_id
    rng = random.Random(seed)
    n_random = int(rotation_config.get("random_per_domain", 1))
    sampled: dict[str, list[Fixture]] = {}
    for domain, fixtures in fixtures_by_domain.items():
        anchors = [f for f in fixtures if f.anchor]
        pool = [f for f in fixtures if not f.anchor]
        pairs: dict[str, list[Fixture]] = {}
        singletons: list[Fixture] = []
        for f in pool:
            pid = f.env.get("AUTORESEARCH_MONITORING_ARC_PAIR_ID", "")
            if pid:
                pairs.setdefault(pid, []).append(f)
            else:
                singletons.append(f)
        pair_reps = [
            sorted(siblings, key=lambda x: x.env.get("AUTORESEARCH_MONITORING_ARC_ROLE", ""))[0]
            for siblings in pairs.values()
        ]
        combined = singletons + pair_reps
        picks = rng.sample(combined, min(n_random, len(combined)))
        expanded: list[Fixture] = []
        for p in picks:
            pid = p.env.get("AUTORESEARCH_MONITORING_ARC_PAIR_ID", "")
            if pid:
                expanded.extend(
                    sorted(pairs[pid], key=lambda x: x.env.get("AUTORESEARCH_MONITORING_ARC_ROLE", ""))
                )
            else:
                expanded.append(p)
        sampled[domain] = anchors + expanded
    return sampled


def _has_deliverables(session_dir: Path, domain: str) -> bool:
    if list(session_dir.glob(DELIVERABLES[domain])):
        return True
    intermediate = _INTERMEDIATE_ARTIFACTS.get(domain)
    return bool(intermediate and list(session_dir.glob(intermediate)))


_REPO_ROOT_FOR_MANIFEST = SCRIPT_DIR.parent


def _check_critique_manifest(variant_dir: Path) -> bool:
    """Re-compute the critique-prompt manifest in an isolated subprocess
    and compare it to the manifest the variant was clone-stamped with.

    Grace manifests (``{"grace": true, ...}``) skip hash enforcement so
    pre-Unit-7-era variants still validate. The grace path is intended
    for one-shot backfill via ``autoresearch/scripts/rebuild_manifests.py``;
    fresh clones written by ``evolve.py`` always carry a strict manifest.

    Returns ``False`` (and prints ``L1 FAIL: ...``) on any of:
      - missing ``critique_manifest.json``,
      - malformed JSON,
      - subprocess introspection failure,
      - hash mismatch (with the offending symbol named).

    The introspection runs as ``python3 -I -c <bootstrap>`` so ambient
    ``PYTHONPATH`` / user site-packages cannot inject a fake
    ``session_evaluator``. The repo root is the only path inserted, by
    the bootstrap itself.
    """
    manifest_path = variant_dir / "critique_manifest.json"
    if not manifest_path.exists():
        print(
            f"L1 FAIL: critique_manifest.json missing in {variant_dir}",
            file=sys.stderr,
        )
        return False
    try:
        bundled = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(
            f"L1 FAIL: critique_manifest.json unreadable: {exc}",
            file=sys.stderr,
        )
        return False
    if not isinstance(bundled, dict):
        print("L1 FAIL: critique_manifest.json must be a JSON object", file=sys.stderr)
        return False

    if bundled.get("grace") is True:
        # Grace manifest: pre-Unit-7-era variant backfilled by
        # rebuild_manifests.py. Pass through without enforcement; we
        # explicitly do not attempt to detect retroactive tampering of
        # variants that were already on disk before R-#13 landed.
        return True

    bootstrap = (
        "import sys, json;"
        f"sys.path.insert(0, {str(_REPO_ROOT_FOR_MANIFEST)!r});"
        "from autoresearch.critique_manifest import compute_expected_hashes;"
        "print(json.dumps(compute_expected_hashes()))"
    )
    proc = subprocess.run(
        ["python3", "-I", "-c", bootstrap],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if proc.returncode != 0:
        print(
            f"L1 FAIL: critique manifest introspection failed "
            f"(exit={proc.returncode}): {proc.stderr.strip() or proc.stdout.strip()}",
            file=sys.stderr,
        )
        return False
    try:
        expected = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        print(
            f"L1 FAIL: critique manifest introspection returned bad JSON: {exc}",
            file=sys.stderr,
        )
        return False

    bundled_hashes = {k: v for k, v in bundled.items() if k != "grace"}

    expected_keys = set(expected)
    bundled_keys = set(bundled_hashes)
    if expected_keys != bundled_keys:
        missing = sorted(expected_keys - bundled_keys)
        extra = sorted(bundled_keys - expected_keys)
        print(
            f"L1 FAIL: critique_manifest.json key mismatch "
            f"(missing={missing}, extra={extra})",
            file=sys.stderr,
        )
        return False

    for symbol, expected_hash in expected.items():
        if bundled_hashes[symbol] != expected_hash:
            print(
                f"L1 FAIL: critique_manifest.json hash mismatch for {symbol!r} "
                f"(bundled={bundled_hashes[symbol]}, expected={expected_hash}). "
                f"This means the canonical critique-prompt symbol has been "
                f"tampered with, or the variant predates the current "
                f"session_evaluator.py and needs a manifest rebuild.",
                file=sys.stderr,
            )
            return False
    return True


def layer1_validate(variant_dir: Path) -> bool:
    """Static validation: critique-manifest hash check, compile Python,
    parse shell, verify session programs.

    The hash check runs FIRST (before py_compile / bash -n) so a tampered
    variant fails fast and we don't waste time compiling files we'll
    refuse to run anyway. R-#13 + R-#24.
    """
    if not _check_critique_manifest(variant_dir):
        return False

    if not (variant_dir / "run.py").exists():
        print("L1 FAIL: run.py not found", file=sys.stderr)
        return False

    for path_str in glob.glob(str(variant_dir / "**" / "*.py"), recursive=True):
        result = subprocess.run(
            ["python3", "-m", "py_compile", path_str],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"L1 FAIL: {path_str}: {result.stderr.strip()}", file=sys.stderr)
            return False

    for path_str in glob.glob(str(variant_dir / "**" / "*.sh"), recursive=True):
        result = subprocess.run(["bash", "-n", path_str], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"L1 FAIL: {path_str}: {result.stderr.strip()}", file=sys.stderr)
            return False

    # Gap 30: Verify run.py imports resolve (catches missing dependencies)
    import_check = subprocess.run(
        ["python3", "-c", "import run"],
        capture_output=True,
        text=True,
        timeout=15,
        cwd=str(variant_dir),
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    if import_check.returncode != 0:
        print(f"L1 FAIL: run.py import: {import_check.stderr.strip()}", file=sys.stderr)
        return False

    for domain in DOMAINS:
        program_path = variant_dir / "programs" / f"{domain}-session.md"
        if not program_path.exists():
            print(f"L1 FAIL: missing program file: {program_path}", file=sys.stderr)
            return False
    return True


def _runner_env(eval_target: EvalTarget, fixture: Fixture) -> dict[str, str]:
    env = os.environ.copy()
    env["EVAL_BACKEND_OVERRIDE"] = eval_target.backend
    env["EVAL_MODEL_OVERRIDE"] = eval_target.model
    env["AUTORESEARCH_SESSION_BACKEND"] = eval_target.backend
    env["AUTORESEARCH_SESSION_MODEL"] = eval_target.model
    if eval_target.reasoning_effort:
        env["AUTORESEARCH_SESSION_REASONING_EFFORT"] = eval_target.reasoning_effort
    elif "AUTORESEARCH_SESSION_REASONING_EFFORT" not in env and "CODEX_REASONING_EFFORT" in env:
        env["AUTORESEARCH_SESSION_REASONING_EFFORT"] = env["CODEX_REASONING_EFFORT"]
    for key in ("CODEX_SANDBOX", "CODEX_APPROVAL_POLICY", "CODEX_WEB_SEARCH"):
        session_key = f"AUTORESEARCH_SESSION_{key.removeprefix('CODEX_')}"
        if session_key not in env and key in env:
            env[session_key] = env[key]
    if env.get("AUTORESEARCH_SESSION_SANDBOX", "").strip().lower() == "seatbelt":
        env["AUTORESEARCH_SESSION_SANDBOX"] = "workspace-write"
    env.update(fixture.env)
    env["AUTORESEARCH_FIXTURE_ID"] = fixture.fixture_id
    env["AUTORESEARCH_FRESH"] = "true"
    # Phase 8: inject FREDDY_FIXTURE_* so the variant's freddy CLI calls read
    # from the fixture cache instead of hitting providers live. Pool drives
    # miss semantics (search-v1 → live-fetch fallback; holdout-* → hard-fail).
    # Existing FREDDY_FIXTURE_CACHE_DIR is respected so tests can point at
    # tmp dirs; default is the shared per-user cache root.
    env["FREDDY_FIXTURE_CACHE_DIR"] = os.environ.get(
        "FREDDY_FIXTURE_CACHE_DIR",
        str(Path.home() / ".local/share/gofreddy/fixture-cache"),
    )
    env["FREDDY_FIXTURE_POOL"] = fixture.suite_id
    env["FREDDY_FIXTURE_ID"] = fixture.fixture_id
    env["FREDDY_FIXTURE_VERSION"] = fixture.version
    return env


class JudgeUnreachable(RuntimeError):
    """Raised when an evolution-judge HTTP call fails.

    The evolve loop halts immediately on this; there is no retry or
    fallback (see plan § "Judge-service unreachable behavior").
    """


def _score_env() -> dict[str, str]:
    env = os.environ.copy()
    # Scrub tokens that must never reach untrusted variant subprocesses.
    # Leave SESSION_INVOKE_TOKEN (variants need to call session judges);
    # drop EVOLUTION_INVOKE_TOKEN and any model-provider API keys.
    for key in (
        "EVOLUTION_INVOKE_TOKEN",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "CLAUDE_API_KEY",
        "CODEX_API_KEY",
    ):
        env.pop(key, None)
    repo_root = _repo_root()
    cli_path = str(repo_root / "cli")
    existing_pythonpath = [part for part in env.get("PYTHONPATH", "").split(os.pathsep) if part]
    if cli_path not in existing_pythonpath:
        env["PYTHONPATH"] = os.pathsep.join([cli_path, *existing_pythonpath])
    return env


def _supports_process_groups() -> bool:
    return hasattr(os, "setsid") and hasattr(os, "killpg")


def _terminate_process(process: subprocess.Popen, reason: str, grace_seconds: int = 10):
    if process.poll() is not None:
        return
    print(f"  Stopping fixture process ({reason}).", file=sys.stderr)
    try:
        if _supports_process_groups():
            os.killpg(process.pid, signal.SIGTERM)
        else:
            process.terminate()
        process.wait(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        if _supports_process_groups():
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
        process.wait()


def _run_fixture_session(variant_dir: Path, fixture: Fixture, eval_target: EvalTarget) -> SessionRun:
    env = _runner_env(eval_target, fixture)
    command = [
        "python3",
        str(variant_dir / "run.py"),
        "--strategy",
        "fresh",
        "--domain",
        fixture.domain,
        fixture.client,
        fixture.context,
        str(fixture.max_iter),
        str(fixture.timeout),
    ]
    timeout = fixture.timeout * fixture.max_iter + 180

    started = time.monotonic()
    process = subprocess.Popen(
        command,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=_supports_process_groups(),
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
        exit_code = process.returncode
        if exit_code != 0 and stderr:
            print(
                f"  runner error for {fixture.fixture_id}: {stderr.strip()}",
                file=sys.stderr,
            )
    except subprocess.TimeoutExpired:
        _terminate_process(process, f"timeout for {fixture.fixture_id}")
        process.wait()
        print(f"  runner timed out for {fixture.fixture_id}", file=sys.stderr)
        exit_code = 124
    except BaseException:
        _terminate_process(process, f"exception for {fixture.fixture_id}")
        raise

    wall_time_seconds = round(time.monotonic() - started, 3)
    session_dir = variant_dir / "sessions" / fixture.domain / fixture.client
    produced = session_dir.exists() and _has_deliverables(session_dir, fixture.domain)
    return SessionRun(
        fixture=fixture,
        session_dir=session_dir if session_dir.exists() else None,
        produced_output=produced,
        runner_exit_code=exit_code,
        wall_time_seconds=wall_time_seconds,
    )


# --- Inner-vs-outer correlation telemetry (R-#14) -----------------------------
# Observation signal: measures whether the outer evaluator's KEEP rate agrees
# with the inner phase KEEP rate recorded in results.jsonl. Large |delta| does
# NOT gate anything (no-caps philosophy) — it logs a WARN + appends to the
# variant's eval_digest.md so drift is visible for the premise revisit.
#
# Phase tags we consider "substantive" — gather/done bookkeeping rows are
# excluded so neutral housekeeping can't dominate the ratio. Spec per plan
# Unit 3: analyze | synthesize | verify | session_eval | evaluate.
_INNER_PHASE_TAGS = frozenset({
    "analyze",
    "analyze_patterns",
    "synthesize",
    "verify",
    "session_eval",
    "session_evaluator_guard",
    "evaluate",
    "plan_story",
    "ideate",
    "optimize",
    "generate_frames",
})
# Token sets drawn from the status values actually observed in archived
# results.jsonl across all four domains.
_KEEP_TOKENS = frozenset({
    "kept", "keep", "pass", "ok", "approved", "verified",
    "complete", "done",
})
_REWORK_TOKENS = frozenset({
    "rework", "rework_required", "revise", "fail", "failed",
    "rejected", "retry", "discarded", "error", "blocked",
})
_INNER_PASS_DELTA_THRESHOLD = 0.15


def _extract_inner_pass_rate(session_dir: Path | None) -> dict[str, Any]:
    """Parse ``results.jsonl`` and return inner KEEP rate + raw counts.

    Returns a dict with keys ``inner_pass_rate`` (float in [0, 1] or ``None``
    when no substantive rows were seen), ``keeps``, ``reworks``, and
    ``total_considered``. Phase-filtered: rows whose ``type`` is not in
    ``_INNER_PHASE_TAGS`` are ignored so gather/select bookkeeping noise can't
    dominate. Structural-gate rows are always considered because they carry
    the strongest pass/fail signal.
    """
    result: dict[str, Any] = {
        "inner_pass_rate": None,
        "keeps": 0,
        "reworks": 0,
        "total_considered": 0,
    }
    if session_dir is None:
        return result
    results_path = Path(session_dir) / "results.jsonl"
    if not results_path.exists():
        return result
    keeps = 0
    reworks = 0
    try:
        lines = results_path.read_text().splitlines()
    except OSError:
        return result
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, dict):
            continue
        row_type = str(row.get("type", "")).strip().lower()
        status = str(row.get("status", "")).strip().lower()
        if not status:
            continue
        # structural_gate carries the strongest signal — always count it.
        # Other rows must be in our phase-tag set to filter out gather/select
        # bookkeeping that would otherwise dominate with "done".
        if row_type != "structural_gate" and row_type not in _INNER_PHASE_TAGS:
            continue
        if status in _KEEP_TOKENS:
            keeps += 1
        elif status in _REWORK_TOKENS:
            reworks += 1
    total = keeps + reworks
    result["keeps"] = keeps
    result["reworks"] = reworks
    result["total_considered"] = total
    if total > 0:
        result["inner_pass_rate"] = round(keeps / total, 4)
    return result


def _outer_pass_from_score(score: float, structural_passed: bool) -> float:
    """Convert the outer-evaluator verdict into a binary KEEP/REWORK signal.

    Uses the same 0.5 threshold as the eval-digest criterion-failure block
    so this observation stays consistent with how the pipeline already
    describes "passing".
    """
    return 1.0 if (structural_passed and score >= 0.5) else 0.0


def _score_session(
    run: SessionRun,
    *,
    variant_id: str,
    campaign_id: str,
) -> dict[str, Any]:
    # Inner-vs-outer correlation (R-#14): compute once per session. Error
    # return paths still carry inner stats so aggregates aren't silently biased
    # toward "no data".
    inner_stats = _extract_inner_pass_rate(run.session_dir)
    inner_pass_rate = inner_stats["inner_pass_rate"]

    def _correlation_fields(outer: float) -> dict[str, Any]:
        if inner_pass_rate is None:
            delta: float | None = None
        else:
            delta = round(outer - inner_pass_rate, 4)
        return {
            "inner_pass_rate": inner_pass_rate,
            "outer_pass_rate": outer,
            "pass_rate_delta": delta,
            "inner_counts": {
                "keeps": inner_stats["keeps"],
                "reworks": inner_stats["reworks"],
                "total_considered": inner_stats["total_considered"],
            },
        }

    if run.session_dir is None or not run.produced_output:
        return {
            "fixture_id": run.fixture.fixture_id,
            "suite_id": run.fixture.suite_id,
            "client": run.fixture.client,
            "context": run.fixture.context,
            "score": 0.0,
            "dimension_scores": [],
            "grounding_passed": True,
            "structural_passed": False,
            "evaluation_id": None,
            "dqs_score": None,
            "produced_output": False,
            "wall_time_seconds": run.wall_time_seconds,
            "max_iter": run.fixture.max_iter,
            "timeout": run.fixture.timeout,
            **_correlation_fields(0.0),
        }

    # HTTP client to evolution-judge-service. No retry, no fallback —
    # unreachable judge logs an event and propagates JudgeUnreachable so
    # the evolve loop halts.
    import httpx  # local import keeps top-of-file surface stable
    from autoresearch.events import log_event

    judge_url = os.environ.get("EVOLUTION_JUDGE_URL", "http://localhost:7200")
    endpoint = f"{judge_url}/invoke/score"
    token = os.environ.get("EVOLUTION_INVOKE_TOKEN", "")
    # The variant_scorer prompt template interpolates `domain`, `fixture`,
    # `session_ref`, and `artifacts`. Sending only `{session_dir, fixture_id}`
    # leaves the prompt's {fixture}/{artifacts} blocks as `{}` and the judge
    # correctly returns score 0 with rationale "no input to evaluate".
    fixture_payload = {
        "fixture_id": run.fixture.fixture_id,
        "suite_id": run.fixture.suite_id,
        "client": run.fixture.client,
        "context": run.fixture.context,
        "version": run.fixture.version,
        "domain": run.fixture.domain,
    }
    # Bounded text-artifact materialization — judges score textual content
    # (markdown / json / yaml / txt). Binary frames (PNG/JPG/etc) are not
    # judge-readable and inflate the prompt past codex's context window;
    # storyboard mrbeast hit 7MB of PNG frames after PR #19 caused codex to
    # crash on stdin. Total payload also capped to keep all variants within
    # the model's context budget.
    _TEXT_EXTS = {
        ".md", ".markdown", ".json", ".jsonl", ".yaml", ".yml",
        ".txt", ".csv", ".tsv", ".html", ".htm", ".xml", ".srt", ".vtt",
    }
    _MAX_PAYLOAD_BYTES = 800_000  # ~200K tokens, well under gpt-5.4's 200K window
    _MAX_FILE_BYTES = 200_000     # cap any single artifact

    artifacts_payload: dict[str, Any] = {}
    total_bytes = 0
    skipped_binary = 0
    skipped_too_large = 0
    truncated_payload = False
    try:
        for path in sorted(run.session_dir.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(run.session_dir).as_posix()
            if rel.startswith("logs/"):
                continue  # per-iteration logs aren't useful to the judge
            if path.suffix.lower() not in _TEXT_EXTS:
                skipped_binary += 1
                continue
            try:
                size = path.stat().st_size
                if size > _MAX_FILE_BYTES:
                    skipped_too_large += 1
                    continue
                if total_bytes + size > _MAX_PAYLOAD_BYTES:
                    truncated_payload = True
                    break
                artifacts_payload[rel] = path.read_text(encoding="utf-8", errors="replace")
                total_bytes += size
            except (OSError, UnicodeError):
                continue
    except OSError:
        pass
    if truncated_payload or skipped_binary or skipped_too_large:
        artifacts_payload["__payload_meta__"] = {
            "total_bytes": total_bytes,
            "skipped_binary": skipped_binary,
            "skipped_too_large": skipped_too_large,
            "truncated": truncated_payload,
        }

    request_body: dict[str, Any] = {
        "domain": run.fixture.domain,
        "session_dir": str(run.session_dir),
        "session_ref": str(run.session_dir),
        "fixture_id": run.fixture.fixture_id,
        "fixture": fixture_payload,
        "suite_id": run.fixture.suite_id,
        "campaign_id": campaign_id,
        "variant_id": variant_id,
        "artifacts": artifacts_payload,
    }
    try:
        response = httpx.post(
            endpoint,
            json=request_body,
            headers={"Authorization": f"Bearer {token}"},
            timeout=400.0,
        )
    except (httpx.HTTPError, OSError) as exc:
        log_event(
            kind="judge_unreachable",
            endpoint="/invoke/score",
            payload_summary={
                "fixture_id": run.fixture.fixture_id,
                "domain": run.fixture.domain,
                "variant_id": variant_id,
            },
            error=repr(exc),
        )
        raise JudgeUnreachable(f"evolution-judge /invoke/score unreachable: {exc}") from exc

    if response.status_code >= 500:
        log_event(
            kind="judge_unreachable",
            endpoint="/invoke/score",
            payload_summary={
                "fixture_id": run.fixture.fixture_id,
                "domain": run.fixture.domain,
                "variant_id": variant_id,
            },
            error=f"HTTP {response.status_code}: {response.text[:500]}",
        )
        raise JudgeUnreachable(
            f"evolution-judge /invoke/score returned {response.status_code}"
        )

    if response.status_code >= 400:
        # 4xx = the service is reachable but rejected the request (bad
        # token, malformed payload, unknown role). Keep the legacy
        # "structural-fail, zero score" shape so upstream aggregation
        # still works, same as a 4xx from the old subprocess path.
        print(
            f"  evaluate variant HTTP {response.status_code} for {run.fixture.fixture_id}: "
            f"{response.text[:200]}",
            file=sys.stderr,
        )
        return {
            "fixture_id": run.fixture.fixture_id,
            "suite_id": run.fixture.suite_id,
            "client": run.fixture.client,
            "context": run.fixture.context,
            "score": 0.0,
            "dimension_scores": [],
            "grounding_passed": True,
            "structural_passed": False,
            "evaluation_id": None,
            "dqs_score": None,
            "produced_output": run.produced_output,
            "wall_time_seconds": run.wall_time_seconds,
            "max_iter": run.fixture.max_iter,
            "timeout": run.fixture.timeout,
            **_correlation_fields(0.0),
        }

    try:
        data = response.json()
    except json.JSONDecodeError:
        print(
            f"  evaluate variant returned invalid JSON for {run.fixture.fixture_id}: {response.text[:200]}",
            file=sys.stderr,
        )
        return {
            "fixture_id": run.fixture.fixture_id,
            "suite_id": run.fixture.suite_id,
            "client": run.fixture.client,
            "context": run.fixture.context,
            "score": 0.0,
            "dimension_scores": [],
            "grounding_passed": True,
            "structural_passed": False,
            "evaluation_id": None,
            "dqs_score": None,
            "produced_output": run.produced_output,
            "wall_time_seconds": run.wall_time_seconds,
            "max_iter": run.fixture.max_iter,
            "timeout": run.fixture.timeout,
            **_correlation_fields(0.0),
        }

    # The judge-service returns either the legacy flat shape
    # ``{domain_score, structural_passed, grounding_passed, ...}`` OR the
    # variant_scorer-native shape ``{primary, secondary, aggregate: {aggregate_score, structural_passed, grounding_passed}}``.
    # Normalize both into the legacy locals below.
    aggregate = data.get("aggregate") if isinstance(data, dict) else None
    if isinstance(aggregate, dict):
        outer_score_raw = aggregate.get("aggregate_score")
        structural_raw = aggregate.get("structural_passed")
        grounding_raw = aggregate.get("grounding_passed")
        dqs_score = aggregate.get("dqs_score") or data.get("dqs_score")
        dimension_scores_raw = aggregate.get("dimension_scores") or data.get("dimension_scores", [])
        evaluation_id = aggregate.get("evaluation_id") or data.get("evaluation_id")
    else:
        outer_score_raw = data.get("domain_score")
        structural_raw = data.get("structural_passed")
        grounding_raw = data.get("grounding_passed")
        dqs_score = data.get("dqs_score")
        dimension_scores_raw = data.get("dimension_scores", [])
        evaluation_id = data.get("evaluation_id")

    if run.fixture.domain == "monitoring" and dqs_score is not None and run.session_dir is not None:
        try:
            meta_path = run.session_dir / "digest-meta.json"
            existing = load_json(meta_path, default={}) or {}
            existing["dqs_score"] = dqs_score
            meta_path.write_text(json.dumps(existing, indent=2) + "\n")
        except OSError as exc:
            print(f"  warning: failed to persist dqs_score for {run.fixture.fixture_id}: {exc}", file=sys.stderr)

    outer_score = float(outer_score_raw or 0.0)
    structural_passed = bool(structural_raw)
    return {
        "fixture_id": run.fixture.fixture_id,
        "suite_id": run.fixture.suite_id,
        "client": run.fixture.client,
        "context": run.fixture.context,
        "score": outer_score,
        "dimension_scores": [
            float(score) for score in (dimension_scores_raw or []) if isinstance(score, (int, float))
        ],
        "grounding_passed": bool(grounding_raw),
        "structural_passed": structural_passed,
        "evaluation_id": evaluation_id,
        "dqs_score": dqs_score,
        "produced_output": run.produced_output,
        "wall_time_seconds": run.wall_time_seconds,
        "max_iter": run.fixture.max_iter,
        "timeout": run.fixture.timeout,
        **_correlation_fields(_outer_pass_from_score(outer_score, structural_passed)),
    }


def _aggregate_suite_results(
    suite_manifest: dict[str, Any],
    fixtures_by_domain: dict[str, list[Fixture]],
    scored_fixtures: dict[str, list[dict[str, Any]]],
) -> tuple[dict[str, float], dict[str, Any]]:
    active_domains = _suite_active_domains(suite_manifest)
    objective_domain = str(suite_manifest.get("objective_domain", "")).strip().lower() or None
    domain_scores: dict[str, float] = {}
    domain_metrics: dict[str, Any] = {}
    composite_components: list[float] = []
    total_wall_time = 0.0

    for domain in DOMAINS:
        fixtures = scored_fixtures.get(domain, [])
        fixture_scores = [float(item.get("score", 0.0) or 0.0) for item in fixtures]
        domain_score = round(_geometric_mean(fixture_scores), 4) if fixture_scores else 0.0
        domain_scores[domain] = domain_score

        fixture_sd = round(statistics.stdev(fixture_scores), 4) if len(fixture_scores) >= 2 else 0.0
        wall_time = round(sum(float(item.get("wall_time_seconds", 0.0) or 0.0) for item in fixtures), 3)
        total_wall_time += wall_time
        # Phase 7 Step 2.5(a): additive `fixtures_detail` alongside `fixtures: int`.
        # Maps fixture_id → {score, secondary_score} for Plan B's promotion agent
        # to consult per-fixture without parsing the raw results list. The
        # secondary score is the mean of dimension_scores when present, else 0.0.
        fixtures_detail: dict[str, dict[str, float]] = {}
        for item in fixtures:
            fid = str(item.get("fixture_id") or "")
            if not fid:
                continue
            dim_scores = item.get("dimension_scores") or []
            dim_numeric = [float(s) for s in dim_scores if isinstance(s, (int, float))]
            secondary = round(sum(dim_numeric) / len(dim_numeric), 4) if dim_numeric else 0.0
            fixtures_detail[fid] = {
                "score": float(item.get("score", 0.0) or 0.0),
                "secondary_score": secondary,
            }
        domain_metrics[domain] = {
            "score": domain_score,
            "fixture_sd": fixture_sd,
            "fixtures": len(fixtures_by_domain.get(domain, [])),
            "fixtures_detail": fixtures_detail,
            "wall_time_seconds": wall_time,
            "results": fixtures,
            "active": domain in active_domains,
        }
        if domain in active_domains:
            composite_components.append(domain_score)

    composite = round(sum(composite_components) / len(composite_components), 4) if composite_components else 0.0
    scores = {**domain_scores, "composite": composite}

    # Inner-vs-outer correlation (R-#14): aggregate mean delta across fixtures.
    # Only fixtures with a non-None delta (i.e. results.jsonl actually produced
    # substantive phase rows) contribute; "no data" fixtures don't bias the
    # average toward zero.
    delta_values: list[float] = []
    inner_values: list[float] = []
    outer_values: list[float] = []
    for domain in DOMAINS:
        for item in scored_fixtures.get(domain, []):
            delta = item.get("pass_rate_delta")
            if isinstance(delta, (int, float)):
                delta_values.append(float(delta))
            inner = item.get("inner_pass_rate")
            if isinstance(inner, (int, float)):
                inner_values.append(float(inner))
            outer = item.get("outer_pass_rate")
            if isinstance(outer, (int, float)):
                outer_values.append(float(outer))
    mean_pass_rate_delta = (
        round(sum(delta_values) / len(delta_values), 4) if delta_values else None
    )
    mean_inner_pass_rate = (
        round(sum(inner_values) / len(inner_values), 4) if inner_values else None
    )
    mean_outer_pass_rate = (
        round(sum(outer_values) / len(outer_values), 4) if outer_values else None
    )

    search_metrics = {
        "suite_id": suite_manifest["suite_id"],
        "composite": composite,
        "wall_time_seconds": round(total_wall_time, 3),
        "active_domains": list(active_domains),
        "objective_domain": objective_domain,
        "objective_score": domain_scores.get(objective_domain, composite) if objective_domain else composite,
        "mean_pass_rate_delta": mean_pass_rate_delta,
        "mean_inner_pass_rate": mean_inner_pass_rate,
        "mean_outer_pass_rate": mean_outer_pass_rate,
        "domains": {
            domain: {
                "score": metrics["score"],
                "fixtures": metrics["fixtures"],
                "wall_time_seconds": metrics["wall_time_seconds"],
                "active": bool(metrics["active"]),
            }
            for domain, metrics in domain_metrics.items()
        },
    }
    return scores, {"search_metrics": search_metrics, "domains": domain_metrics}


def _lineage_entry(
    *,
    variant_dir: Path,
    archive_dir: Path,
    existing_entry: dict[str, Any] | None,
    eval_target: EvalTarget,
    search_manifest: dict[str, Any] | None,
    holdout_manifest: dict[str, Any] | None,
    meta_backend: str | None,
    meta_model: str | None,
    scores: dict[str, float],
    search_metrics: dict[str, Any],
    promotion_summary: dict[str, Any],
    holdout_ran: bool,
    lane: str,
    parent_id: str | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Build lineage entry for a variant, atomically updating parent children count.

    Returns (child_entry, entries_to_append) where entries_to_append includes
    the parent's updated snapshot (if parent_id is set) followed by the child entry.
    Callers write entries_to_append in a single append_lineage_entries call so the
    parent-child link is atomic within a single process.
    """
    variant_id = variant_dir.name
    if not parent_id:
        parent_id = os.environ.get("EVOLUTION_PARENT_ID") or (existing_entry or {}).get("parent")
    changed_files, _diffstat = summarize_variant_diff(archive_dir, variant_id, parent_id)
    existing_entry = existing_entry or {}

    # R-#29: pick up the parent-selection agent rationale (if any) set by evolve.py.
    selection_rationale = os.environ.get("EVOLUTION_SELECTION_RATIONALE") or existing_entry.get("selection_rationale")
    child_entry = {
        "id": variant_id,
        "lane": lane,
        "parent": parent_id,
        "selection_rationale": selection_rationale,
        "children": int(existing_entry.get("children", 0) or 0),
        "timestamp": existing_entry.get("timestamp") or datetime.now(timezone.utc).isoformat(),
        "backend": meta_backend or existing_entry.get("backend"),
        "model": meta_model or existing_entry.get("model"),
        "eval_target": {
            "backend": eval_target.backend,
            "model": eval_target.model,
            "reasoning_effort": eval_target.reasoning_effort,
        },
        "scores": scores,
        "search_metrics": search_metrics,
        "holdout_metrics": {
            "ran": holdout_ran,
        },
        "suite_versions": {
            "search": search_manifest["suite_id"] if isinstance(search_manifest, dict) else None,
        },
        "changed_files": changed_files,
        "campaign_ids": {
            "search": f"{search_manifest['suite_id']}:{variant_id}" if isinstance(search_manifest, dict) else None,
        },
        "promotion_summary": promotion_summary,
        "promoted_at": existing_entry.get("promoted_at"),
    }

    entries_to_append: list[dict[str, Any]] = []
    if parent_id:
        latest = load_latest_lineage(archive_dir)
        parent_entry = latest.get(parent_id)
        if parent_entry:
            updated_parent = dict(parent_entry)
            updated_parent["children"] = int(updated_parent.get("children", 0) or 0) + 1
            entries_to_append.append(updated_parent)
    entries_to_append.append(child_entry)

    return child_entry, entries_to_append


def _write_scores_file(
    variant_dir: Path,
    *,
    scores: dict[str, float],
    eval_target: EvalTarget,
    suite_manifest: dict[str, Any],
    domains: dict[str, Any],
    lane: str,
    smoke_summary: dict[str, Any] | None = None,
    inner_metrics: dict[str, Any] | None = None,
) -> None:
    payload = {
        **scores,
        "lane": lane,
        "suite_id": suite_manifest["suite_id"],
        "eval_target": {
            "backend": eval_target.backend,
            "model": eval_target.model,
            "reasoning_effort": eval_target.reasoning_effort,
        },
        "search_metrics": domains["search_metrics"],
        "domains": domains["domains"],
        "smoke_summary": smoke_summary or {},
        "inner_metrics": inner_metrics or {},
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }
    # Serialize before opening the target so a json.dumps exception can't
    # truncate an existing scores.json; atomic rename keeps readers from
    # seeing a partial write if the process is killed mid-write (SIGALRM).
    serialized = json.dumps(payload, indent=2) + "\n"
    target = variant_dir / "scores.json"
    tmp = target.with_suffix(".json.tmp")
    tmp.write_text(serialized)
    os.replace(tmp, target)


def _objective_score_from_scores(scores: dict[str, Any] | None, lane: str) -> float:
    if not isinstance(scores, dict):
        return 0.0
    key = "composite" if lane == "core" else lane
    value = scores.get(key, 0.0)
    if isinstance(value, (int, float)):
        return float(value)
    return 0.0


def _entry_lane(entry: dict[str, Any] | None) -> str:
    raw_lane = ""
    if isinstance(entry, dict):
        raw_lane = str(entry.get("lane") or "").strip().lower()
    return raw_lane or "core"


def _promotion_baseline(archive_dir: Path, variant_id: str, lane: str = "core") -> dict[str, Any] | None:
    latest = load_latest_lineage(archive_dir)
    current_id = current_variant_id(archive_dir, lane=lane)
    if current_id and current_id != variant_id:
        current_entry = latest.get(current_id)
        if current_entry and has_search_metrics(current_entry) and _entry_lane(current_entry) == lane:
            return current_entry
    promoted = [
        entry
        for entry in latest.values()
        if entry.get("promoted_at")
        and entry.get("id") != variant_id
        and has_search_metrics(entry)
        and _entry_lane(entry) == lane
    ]
    promoted.sort(key=lambda entry: str(entry.get("promoted_at") or ""))
    return promoted[-1] if promoted else None


def _search_promotion_summary(
    *,
    variant_entry: dict[str, Any],
    baseline_entry: dict[str, Any] | None,
    search_suite_manifest: dict[str, Any],
    require_holdout: bool,
    holdout_scores: dict[str, Any] | None = None,
    secondary_holdout_scores: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Summarize promotion eligibility after a search evaluation.

    Phase 7 Step 2.5(b): emits ``holdout_composite`` and
    ``secondary_holdout_composite`` (floats or None) alongside the existing
    ``eligible_for_promotion`` / ``reason`` keys so Plan B's ``is_promotable``
    agent can read them directly from the lineage entry instead of from the
    private ``finalize_result.json``. When holdout wasn't run this cycle,
    both composite fields are ``None``.
    """

    def _composite_from(scores: dict[str, Any] | None) -> float | None:
        if not isinstance(scores, dict):
            return None
        value = scores.get("composite")
        if isinstance(value, (int, float)):
            return float(value)
        return None

    holdout_composite = _composite_from(holdout_scores)
    secondary_holdout_composite = _composite_from(secondary_holdout_scores)

    if require_holdout:
        return {
            "eligible_for_promotion": False,
            "reason": "holdout_required",
            "holdout_composite": holdout_composite,
            "secondary_holdout_composite": secondary_holdout_composite,
        }
    return {
        "eligible_for_promotion": True,
        "reason": "search_scored",
        "holdout_composite": holdout_composite,
        "secondary_holdout_composite": secondary_holdout_composite,
    }


def _private_holdout_root() -> Path | None:
    private_dir_raw = os.environ.get("EVOLUTION_PRIVATE_ARCHIVE_DIR", "").strip()
    if private_dir_raw:
        return Path(private_dir_raw).resolve()
    return Path(tempfile.gettempdir()).resolve() / "autoresearch-holdouts"


def _private_result_path(id_key: str, kind: str, lane: str = "core") -> Path | None:
    """One path helper for holdout private results, keyed on kind.

    kind must be one of {"holdout", "finalize", "shortlist"}.

    For holdout/finalize, id_key is a variant_id and the file lives under
    <root>/<variant_id>/<kind>_result.json.

    For shortlist, id_key is a suite_id and the file lives under
    <root>/_finalized/<lane>--<safe_suite_id>.json.
    """
    root = _private_holdout_root()
    if root is None:
        return None
    if kind == "holdout":
        return root / id_key / "holdout_result.json"
    if kind == "finalize":
        return root / id_key / "finalize_result.json"
    if kind == "shortlist":
        safe_suite_id = str(id_key).replace("/", "_")
        return root / "_finalized" / f"{lane}--{safe_suite_id}.json"
    raise ValueError(f"_private_result_path: unknown kind {kind!r}")


def _load_private_result(id_key: str, kind: str, suite_id: str, lane: str = "core") -> dict[str, Any] | None:
    """One loader for holdout private results, dispatched on kind.

    Preserves distinct validation per kind so error messages stay specific.
    """
    result_path = _private_result_path(id_key, kind, lane)
    if result_path is None or not result_path.exists():
        return None
    payload = load_json(result_path, default=None)
    if not isinstance(payload, dict):
        return None
    if str(payload.get("suite_id") or "") != suite_id:
        return None
    if kind == "shortlist":
        payload_lane = str(payload.get("lane") or "").strip().lower() or "core"
        if payload_lane != lane:
            return None
    return payload


def _write_private_result(id_key: str, kind: str, payload: dict[str, Any], lane: str = "core") -> Path | None:
    """One writer for holdout private results, dispatched on kind.

    Writes the payload dict as JSON to the path determined by kind.
    Returns the path written, or None if the private root is not configured.
    """
    result_path = _private_result_path(id_key, kind, lane)
    if result_path is None:
        return None
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(payload, indent=2) + "\n")
    return result_path


def _private_finalize_status(
    *,
    archive_dir: Path,
    variant_id: str,
    suite_id: str,
    lane: str = "core",
) -> tuple[bool, str, dict[str, Any] | None]:
    record = _load_private_result(variant_id, "finalize", suite_id)
    if not isinstance(record, dict):
        return False, "not_finalized", None

    baseline_entry = _promotion_baseline(archive_dir, variant_id, lane)
    current_baseline_id = str(baseline_entry["id"]) if baseline_entry else None
    record_baseline_id = str(record.get("baseline_variant_id") or "") or None
    if record_baseline_id != current_baseline_id:
        return False, "baseline_changed", record

    if bool(record.get("eligible_for_promotion")):
        return True, "holdout_passed", record
    return False, str(record.get("reason") or "finalized_failed"), record


def _best_finalized_candidate(
    *,
    archive_dir: Path,
    suite_id: str,
    lane: str = "core",
    candidate_ids: list[str] | None = None,
) -> dict[str, Any] | None:
    if candidate_ids is None:
        shortlist = _load_private_result(suite_id, "shortlist", suite_id, lane=lane)
        if isinstance(shortlist, dict):
            candidates = shortlist.get("candidates")
            if isinstance(candidates, list):
                candidate_ids = [
                    str(candidate.get("variant_id") or "")
                    for candidate in candidates
                    if isinstance(candidate, dict) and str(candidate.get("variant_id") or "")
                ]
        if candidate_ids is None:
            candidate_ids = [
                str(entry.get("id") or "")
                for entry in ordered_latest_entries(archive_dir)
                if has_search_metrics(entry)
                and _entry_lane(entry) == lane
            ]

    best: dict[str, Any] | None = None
    for variant_id in candidate_ids:
        eligible, _reason, record = _private_finalize_status(
            archive_dir=archive_dir,
            variant_id=variant_id,
            suite_id=suite_id,
            lane=lane,
        )
        if not eligible or not isinstance(record, dict):
            continue
        objective_score = _objective_score_from_scores(record.get("scores"), lane)
        holdout_composite = float((record.get("scores") or {}).get("composite", 0.0) or 0.0)
        candidate = {
            "variant_id": variant_id,
            "holdout_objective": objective_score,
            "holdout_composite": holdout_composite,
            "record": record,
        }
        if best is None or objective_score > float(best["holdout_objective"]) or (
            objective_score == float(best["holdout_objective"])
            and variant_id < str(best["variant_id"])
        ):
            best = candidate
    return best


def _write_holdout_result_with_artifacts(
    *,
    variant_id: str,
    suite_manifest: dict[str, Any],
    scores: dict[str, float],
    aggregated: dict[str, Any],
    workspace_variant_dir: Path | None = None,
) -> None:
    """Write holdout result JSON and optionally copy session/metrics artifacts."""
    payload = {
        "variant_id": variant_id,
        "suite_id": suite_manifest["suite_id"],
        "scores": scores,
        "aggregated": aggregated,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }
    written = _write_private_result(variant_id, "holdout", payload)
    if written is None or workspace_variant_dir is None:
        return
    private_dir = written.parent
    for name in ("sessions", "metrics"):
        source = workspace_variant_dir / name
        if not source.exists():
            continue
        target = private_dir / name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target)


def _write_finalize_result(
    *,
    variant_id: str,
    suite_manifest: dict[str, Any],
    scores: dict[str, float],
    baseline_variant_id: str | None,
    baseline_holdout_scores: dict[str, float] | None,
    eligible: bool,
    reason: str,
) -> dict[str, Any] | None:
    """Build and write a finalize result, returning the payload or None."""
    baseline_composite = None
    if isinstance(baseline_holdout_scores, dict):
        baseline_composite = baseline_holdout_scores.get("composite")
    payload = {
        "variant_id": variant_id,
        "suite_id": suite_manifest["suite_id"],
        "baseline_variant_id": baseline_variant_id,
        "baseline_holdout_composite": baseline_composite,
        "scores": scores,
        "eligible_for_promotion": eligible,
        "reason": reason,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }
    written = _write_private_result(variant_id, "finalize", payload)
    return payload if written is not None else None


def _write_finalized_shortlist(
    *,
    suite_id: str,
    baseline_variant_id: str | None,
    lane: str = "core",
    results: list[dict[str, Any]],
) -> Path | None:
    """Build and write the finalized shortlist, returning the path or None."""
    ordered = sorted(
        results,
        key=lambda item: (
            0 if item.get("eligible_for_promotion") else 1,
            -_objective_score_from_scores(item.get("scores"), lane),
            str(item.get("variant_id") or ""),
        ),
    )
    payload = {
        "suite_id": suite_id,
        "lane": lane,
        "baseline_variant_id": baseline_variant_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "candidates": [
            {
                "variant_id": item.get("variant_id"),
                "holdout_objective": _objective_score_from_scores(item.get("scores"), lane),
                "holdout_composite": float((item.get("scores") or {}).get("composite", 0.0) or 0.0),
                "eligible_for_promotion": bool(item.get("eligible_for_promotion")),
                "reason": item.get("reason"),
                "evaluated_at": item.get("evaluated_at"),
                "baseline_variant_id": item.get("baseline_variant_id"),
                "baseline_holdout_composite": item.get("baseline_holdout_composite"),
            }
            for item in ordered
        ],
    }
    return _write_private_result(suite_id, "shortlist", payload, lane=lane)


def _copy_variant_for_holdout(variant_dir: Path) -> tuple[tempfile.TemporaryDirectory[str], Path]:
    """Clone the variant into an isolated workspace so holdout traces stay private."""
    temp_kwargs: dict[str, str] = {"prefix": f"autoresearch-holdout-{variant_dir.name}-"}
    private_root = _private_holdout_root()
    if private_root is not None:
        workspace_root = private_root / "_workspaces"
        workspace_root.mkdir(parents=True, exist_ok=True)
        temp_kwargs["dir"] = str(workspace_root)
    temp_dir = tempfile.TemporaryDirectory(**temp_kwargs)
    workspace_variant_dir = Path(temp_dir.name) / variant_dir.name
    shutil.copytree(
        variant_dir,
        workspace_variant_dir,
        ignore=shutil.ignore_patterns(
            "sessions",
            "metrics",
            "runs",
            "__pycache__",
            ".pytest_cache",
            "meta-session.log",
        ),
    )
    return temp_dir, workspace_variant_dir


def _run_holdout_suite(
    *,
    variant_dir: Path,
    variant_id: str,
    suite_manifest: dict[str, Any],
    eval_target: EvalTarget,
) -> tuple[dict[str, float], dict[str, Any]]:
    fixtures_by_domain = _suite_fixtures(suite_manifest)
    # Phase 7 Step 2.5(c): apply rotation sampling when the holdout manifest
    # declares one. Plan B's holdout-v1 deliberately omits `rotation` so this
    # gate no-ops (all fixtures run every cycle); when a future holdout suite
    # wants rotation, it declares `"rotation": {"strategy": "stratified", ...}`
    # in the manifest and we sample before iterating.
    rotation_config = suite_manifest.get("rotation")
    if isinstance(rotation_config, dict) and rotation_config.get("strategy") == "stratified":
        cohort_id = os.environ.get("EVOLUTION_COHORT_ID", "").strip() or variant_id
        fixtures_by_domain = _sample_fixtures(fixtures_by_domain, rotation_config, cohort_id)
    holdout_campaign_id = f"{suite_manifest['suite_id']}:{variant_id}"

    print(f"Holdout: running {suite_manifest['suite_id']} for {variant_id}...")
    scored_fixtures: dict[str, list[dict[str, Any]]] = {domain: [] for domain in DOMAINS}
    holdout_workspace, holdout_variant_dir = _copy_variant_for_holdout(variant_dir)
    try:
        for domain in DOMAINS:
            for fixture in fixtures_by_domain[domain]:
                print(f"  {domain}: {fixture.fixture_id}")
                session_run = _run_fixture_session(holdout_variant_dir, fixture, eval_target)
                scored_fixtures[domain].append(
                    _score_session(
                        session_run,
                        variant_id=variant_id,
                        campaign_id=holdout_campaign_id,
                    )
                )

        holdout_scores, aggregated = _aggregate_suite_results(suite_manifest, fixtures_by_domain, scored_fixtures)
        _write_holdout_result_with_artifacts(
            variant_id=variant_id,
            suite_manifest=suite_manifest,
            scores=holdout_scores,
            aggregated=aggregated,
            workspace_variant_dir=holdout_variant_dir,
        )
        return holdout_scores, aggregated
    finally:
        holdout_workspace.cleanup()


def _baseline_holdout_scores(
    *,
    archive_dir: Path,
    variant_id: str,
    holdout_manifest: dict[str, Any],
    eval_target: EvalTarget,
    lane: str,
) -> tuple[dict[str, Any] | None, dict[str, float] | None]:
    baseline_entry = _promotion_baseline(archive_dir, variant_id, lane)
    if baseline_entry is None:
        return None, None

    baseline_id = str(baseline_entry["id"])
    suite_id = str(holdout_manifest["suite_id"])
    cached = _load_private_result(baseline_id, "holdout", suite_id)
    if isinstance(cached, dict) and isinstance(cached.get("scores"), dict):
        return baseline_entry, cached["scores"]

    baseline_variant_dir = archive_dir / baseline_id
    if not baseline_variant_dir.is_dir():
        raise RuntimeError(f"Promoted baseline directory is missing: {baseline_variant_dir}")

    baseline_scores, _aggregated = _run_holdout_suite(
        variant_dir=baseline_variant_dir,
        variant_id=baseline_id,
        suite_manifest=holdout_manifest,
        eval_target=eval_target,
    )
    return baseline_entry, baseline_scores


# ---------------------------------------------------------------------------
# Phase 7 Step 2.5(d): monitoring-fixture baseline re-scoring for is_promotable.
# ---------------------------------------------------------------------------


def _is_monitoring_fixture_result(fixture_result: dict[str, Any]) -> bool:
    """True when a scored-fixture row belongs to a monitoring (weekly) fixture.

    Detection is doubly-sourced so a manifest-only flag suffices:
      * fixture env includes ``AUTORESEARCH_WEEK_RELATIVE=most_recent_complete``
        (stored under ``fixture_env`` when we have the suite manifest available), or
      * the fixture's source command starts with ``["freddy", "monitor"]``.
    Callers that only have the scored dict pass ``fixture_env=None`` and rely
    on the source-command fallback (the monitoring domain is keyed on
    ``AUTORESEARCH_FIXTURE_ID``).
    """
    env = fixture_result.get("fixture_env")
    if isinstance(env, dict):
        spec = str(env.get("AUTORESEARCH_WEEK_RELATIVE", "")).strip().lower()
        if spec == "most_recent_complete":
            return True
    command = fixture_result.get("source_command")
    if isinstance(command, list) and len(command) >= 2:
        if str(command[0]).lower() == "freddy" and str(command[1]).lower() == "monitor":
            return True
    return False


def _monitoring_fixture_ids_from_manifest(
    suite_manifest: dict[str, Any] | None,
) -> set[str]:
    """Return the set of fixture_ids whose env declares weekly-relative semantics."""
    if not isinstance(suite_manifest, dict):
        return set()
    ids: set[str] = set()
    for domain, fixtures in (suite_manifest.get("domains") or {}).items():
        if not isinstance(fixtures, list):
            continue
        for payload in fixtures:
            if not isinstance(payload, dict):
                continue
            env = payload.get("env") or {}
            if not isinstance(env, dict):
                continue
            spec = str(env.get("AUTORESEARCH_WEEK_RELATIVE", "")).strip().lower()
            if spec == "most_recent_complete":
                fid = str(payload.get("fixture_id") or "").strip()
                if fid:
                    ids.add(fid)
    return ids


def _refresh_monitoring_scores_for_baseline(
    baseline_entry: dict[str, Any],
    lane: str,
    archive_root: Path,
    *,
    suite_manifest: dict[str, Any] | None = None,
    rescore_fn: Any = None,
) -> dict[str, Any]:
    """Re-score the baseline on THIS cycle's monitoring fixtures.

    Monitoring fixtures use ``AUTORESEARCH_WEEK_RELATIVE=most_recent_complete``
    and target different content weekly. Stored baseline scores were computed
    on the baseline's promotion-time content (possibly weeks ago), so comparing
    fresh candidate scores against them is apples-to-oranges. This helper
    re-evaluates only the monitoring fixtures against the current cycle's
    cache for the baseline variant; non-monitoring fixtures are untouched.

    Returns a shallow clone of ``baseline_entry`` with updated monitoring
    fixture scores inside ``search_metrics.domains`` and the composite updated.
    When ``rescore_fn`` is ``None`` the helper falls back to returning the
    cloned entry unchanged — callers can wire in the full rescoring path; this
    keeps the helper unit-testable in isolation.
    """

    def _clone(value: Any) -> Any:
        if isinstance(value, dict):
            return {k: _clone(v) for k, v in value.items()}
        if isinstance(value, list):
            return [_clone(v) for v in value]
        return value

    cloned = _clone(baseline_entry) if isinstance(baseline_entry, dict) else {}
    monitoring_ids = _monitoring_fixture_ids_from_manifest(suite_manifest)
    search_metrics = cloned.get("search_metrics") if isinstance(cloned.get("search_metrics"), dict) else {}
    domains = search_metrics.get("domains") if isinstance(search_metrics.get("domains"), dict) else {}
    fixtures_detail = {}
    for domain_meta in domains.values():
        if not isinstance(domain_meta, dict):
            continue
        detail = domain_meta.get("fixtures_detail")
        if isinstance(detail, dict):
            fixtures_detail.update(detail)

    # Per-fixture rescore: only monitoring fixtures (by manifest signal OR by
    # the stored row having AUTORESEARCH_WEEK_RELATIVE=most_recent_complete).
    # If no rescore_fn is provided the helper returns the clone unchanged —
    # the public promotion path in Plan B supplies the actual rescorer.
    if rescore_fn is None:
        return cloned

    targets: set[str] = set(monitoring_ids)
    for fid, detail in fixtures_detail.items():
        if isinstance(detail, dict) and _is_monitoring_fixture_result(detail):
            targets.add(fid)

    for fid in list(targets):
        try:
            fresh = rescore_fn(baseline_entry, fid, lane, archive_root)
        except Exception as exc:  # noqa: BLE001 — propagate context in message
            print(
                f"  monitoring rescore failed for {fid}: {exc}; "
                f"leaving baseline score untouched",
                file=sys.stderr,
            )
            continue
        if not isinstance(fresh, dict):
            continue
        new_score = fresh.get("score")
        new_secondary = fresh.get("secondary_score")
        for domain_meta in domains.values():
            if not isinstance(domain_meta, dict):
                continue
            detail = domain_meta.get("fixtures_detail")
            if not isinstance(detail, dict) or fid not in detail:
                continue
            entry = detail[fid]
            if isinstance(new_score, (int, float)):
                entry["score"] = float(new_score)
            if isinstance(new_secondary, (int, float)):
                entry["secondary_score"] = float(new_secondary)
    return cloned


# ---------------------------------------------------------------------------
# Phase 7 Step 3: evaluate_single_fixture — judge-based calibration entry point.
# ---------------------------------------------------------------------------


def _find_one_fixture(suite_manifest: dict[str, Any], fixture_id: str) -> tuple[Fixture, str]:
    """Return ``(Fixture, domain)`` for ``fixture_id`` in ``suite_manifest``.

    Raises ``KeyError`` (with a human-readable message) when the fixture is
    absent. Used by ``evaluate_single_fixture`` and ``freddy fixture dry-run``.
    """
    suite_id = str(suite_manifest.get("suite_id") or "").strip() or "unknown"
    for domain, fixtures in (suite_manifest.get("domains") or {}).items():
        if not isinstance(fixtures, list):
            continue
        for payload in fixtures:
            if isinstance(payload, dict) and str(payload.get("fixture_id") or "") == fixture_id:
                return _fixture_from_payload(suite_id, str(domain), payload), str(domain)
    raise KeyError(f"fixture {fixture_id!r} not found in suite manifest {suite_id!r}")


def evaluate_single_fixture(
    fixture_id: str,
    *,
    manifest_path: str | Path,
    pool: str,
    baseline: str,
    seeds: int,
    cache_root: str | Path,
    archive_root: str | Path | None = None,
    lane: str = "core",
) -> dict[str, Any]:
    """Run one fixture through one baseline variant ``seeds`` times.

    Bypasses the full evaluation orchestration — no stratified sampling,
    no ``scores.json`` write, no lineage append. Reuses the
    same ``_run_fixture_session`` + ``_score_session`` helpers that
    ``evaluate_search`` / ``evaluate_holdout`` call per fixture. Seeds semantics
    match SCHEMA.md: ``AUTORESEARCH_SEED`` is a per-replicate label for
    log/artifact naming only; the variant sampler does not read it and variance
    comes from inherent LLM nondeterminism.

    Returns a dict with the shape the dry-run orchestrator expects:
    ``{per_seed_scores, structural_passed, cost_usd, duration_seconds,
    fixture_id, fixture_version, warnings}``.
    """
    manifest_file = Path(manifest_path)
    suite_payload = json.loads(manifest_file.read_text())
    suite_id = str(suite_payload.get("suite_id") or "")
    if pool != suite_id:
        raise ValueError(
            f"pool {pool!r} does not match manifest.suite_id {suite_id!r}. "
            "Pool and suite_id must agree."
        )

    # Prune the manifest to just the target fixture's domain before
    # env-expansion. Full-suite entry points normalize every domain and
    # require env vars for every fixture. Single-fixture mode pins
    # active_domains to the one containing the target, so unrelated
    # fixtures in other domains are not loaded and their env vars are
    # not required.
    target_domain: str | None = None
    target_entries: list[dict[str, Any]] = []
    for dom, entries in (suite_payload.get("domains") or {}).items():
        if not isinstance(entries, list):
            continue
        matches = [
            e for e in entries
            if isinstance(e, dict) and e.get("fixture_id") == fixture_id
        ]
        if matches:
            target_domain = dom
            target_entries = matches
            break
    if target_domain is None:
        raise KeyError(
            f"fixture {fixture_id!r} not found in manifest {suite_id!r}"
        )
    pruned_payload = dict(suite_payload)
    pruned_payload["domains"] = {target_domain: target_entries}
    pruned_payload["active_domains"] = [target_domain]

    normalized = _normalize_suite_manifest(
        pruned_payload, env=os.environ.copy(), source=str(manifest_file),
    )
    fixture_spec, domain = _find_one_fixture(normalized, fixture_id)

    archive_dir = Path(archive_root) if archive_root else SCRIPT_DIR / "archive"
    variant_dir = archive_dir / baseline
    if not variant_dir.is_dir():
        raise RuntimeError(
            f"Baseline variant directory missing: {variant_dir}. "
            f"(archive_root={archive_dir}, baseline={baseline!r})"
        )

    # EvalTarget: prefer manifest-declared override, else fall back to a
    # session-invoked default. This reuses the same env-resolution the other
    # entry points use so single-fixture runs stay comparable.
    try:
        eval_target = _require_eval_target(os.environ.copy(), normalized)
    except Exception:
        eval_target = EvalTarget(backend="codex", model="gpt-5.4", reasoning_effort=None)

    per_seed: list[float] = []
    total_cost = 0.0
    warnings: list[str] = []
    structural_passed = True
    started = time.monotonic()

    for seed in range(seeds):
        prior = os.environ.get("AUTORESEARCH_SEED")
        os.environ["AUTORESEARCH_SEED"] = str(seed)
        try:
            session_run = _run_fixture_session(variant_dir, fixture_spec, eval_target)
            score_result = _score_session(
                session_run,
                variant_id=baseline,
                campaign_id=f"dryrun:{fixture_id}:{seed}",
            )
        finally:
            if prior is None:
                os.environ.pop("AUTORESEARCH_SEED", None)
            else:
                os.environ["AUTORESEARCH_SEED"] = prior

        per_seed.append(float(score_result.get("score", 0.0) or 0.0))
        wall = score_result.get("wall_time_seconds")
        if isinstance(wall, (int, float)):
            total_cost += 0.0  # score dict has no cost; surface duration below
        if not bool(score_result.get("structural_passed", True)):
            structural_passed = False
        extra_warnings = score_result.get("warnings")
        if isinstance(extra_warnings, list):
            warnings.extend(str(w) for w in extra_warnings)

    duration = int(round(time.monotonic() - started))
    # Cost attribution lives on the judge side; if the score dict exposes a
    # per-session cost we'll plumb it in. Today the aggregate cost reported
    # back to dry-run is zero — the judge emits a qualitative verdict and
    # does not need a cost gate to make that call.
    _ = cache_root  # reserved for future cache-read wiring
    _ = lane
    return {
        "fixture_id": fixture_id,
        "fixture_version": fixture_spec.version,
        "domain": domain,
        "per_seed_scores": per_seed,
        "structural_passed": structural_passed,
        "cost_usd": total_cost,
        "duration_seconds": duration,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Temporary compatibility aliases — removed when evolve.sh heredocs migrate
# to evolve_ops.py (Unit 11 / R15).  These allow evolve.sh to keep calling
# the old names until the heredoc migration lands.
# ---------------------------------------------------------------------------

def _load_private_finalize_result(variant_id: str, suite_id: str) -> dict[str, Any] | None:
    return _load_private_result(variant_id, "finalize", suite_id)

def _private_finalized_shortlist_path(suite_id: str, lane: str = "core") -> Path | None:
    return _private_result_path(suite_id, "shortlist", lane)

_write_private_finalized_shortlist = _write_finalized_shortlist


def _write_eval_digest(
    variant_dir: Path,
    scored_fixtures: dict[str, list[dict[str, Any]]],
    smoke_summary: dict[str, Any],
    aggregated: dict[str, Any],
) -> Path:
    """Write structured evaluation digest for meta agent consumption."""
    search_metrics = aggregated.get("search_metrics", {})
    digest_path = variant_dir / "eval_digest.md"
    lines = [
        f"# Evaluation Digest for {variant_dir.name}\n",
        "## Summary",
        f"- Composite: {search_metrics.get('composite', 0):.3f}",
        f"- Fixtures with output: {smoke_summary.get('fixtures_with_output', '?')}/{smoke_summary.get('fixtures_total', '?')}",
        f"- Total time: {search_metrics.get('wall_time_seconds', 0):.0f}s\n",
        "## Per-Fixture Results",
        "| Domain | Fixture | Score | Structural | Time |",
        "|--------|---------|-------|------------|------|",
    ]
    for domain, fixtures in scored_fixtures.items():
        for f in fixtures:
            lines.append(
                f"| {domain} | {f.get('fixture_id', '')} | {f.get('score', 0):.3f} "
                f"| {'Pass' if f.get('structural_passed') else 'FAIL'} "
                f"| {f.get('wall_time_seconds', 0):.0f}s |"
            )

    lines.append("\n## Criterion Failures")
    has_failures = False
    for domain, fixtures in scored_fixtures.items():
        for f in fixtures:
            if f.get("score", 1) < 0.5:
                dims = f.get("dimension_scores", [])
                if isinstance(dims, list) and dims:
                    # Handle both dict format (with name/score) and flat float format
                    failed_parts: list[str] = []
                    for idx, d in enumerate(dims):
                        if isinstance(d, dict):
                            if d.get("score", 1) < 0.5:
                                failed_parts.append(f"[{d.get('name', f'dim{idx}')}: {d.get('score', 0):.2f}]")
                        elif isinstance(d, (int, float)) and d < 0.5:
                            failed_parts.append(f"[dim{idx}: {d:.2f}]")
                    if failed_parts:
                        lines.append(f"- **{f.get('fixture_id', '')}:** " + ", ".join(failed_parts))
                        has_failures = True
    if not has_failures:
        lines.append("- No criterion failures below 0.5")

    # Inner-vs-outer correlation telemetry (R-#14). Observation only — no gate.
    mean_delta = search_metrics.get("mean_pass_rate_delta")
    mean_inner = search_metrics.get("mean_inner_pass_rate")
    mean_outer = search_metrics.get("mean_outer_pass_rate")
    if isinstance(mean_delta, (int, float)):
        lines.append("\n## Inner-vs-Outer Correlation")
        lines.append(
            f"- mean_pass_rate_delta: {mean_delta:+.3f} "
            f"(inner={mean_inner if mean_inner is not None else 'n/a'}, "
            f"outer={mean_outer if mean_outer is not None else 'n/a'})"
        )
        if abs(float(mean_delta)) > _INNER_PASS_DELTA_THRESHOLD:
            warn_line = (
                f"WARN: pass_rate_delta={mean_delta:+.3f} exceeds "
                f"±0.15 threshold (inner={mean_inner}, outer={mean_outer}) "
                "— observation only, no gate"
            )
            lines.append(warn_line)
            print(warn_line, file=sys.stderr)

    digest_path.write_text("\n".join(lines) + "\n")
    return digest_path


def _load_parent_scores(archive_dir: Path, parent_id: str) -> dict[str, list[dict[str, Any]]] | None:
    """Load parent's per-fixture scores from scores.json, keyed by domain."""
    scores_path = archive_dir / parent_id / "scores.json"
    payload = load_json(scores_path, default=None)
    if not isinstance(payload, dict):
        return None
    domains = payload.get("domains")
    if not isinstance(domains, dict):
        return None
    result: dict[str, list[dict[str, Any]]] = {}
    for domain, domain_data in domains.items():
        if isinstance(domain_data, dict):
            results = domain_data.get("results")
            if isinstance(results, list):
                result[domain] = results
    return result or None


def _run_and_score_fixture(
    variant_dir: Path,
    fixture: Fixture,
    eval_target: EvalTarget,
    variant_id: str,
    campaign_id: str,
    skip_sessions: bool = False,
) -> tuple[str, str, dict[str, Any], bool]:
    """Run + score one fixture. Returns (domain, fixture_id, result, produced_output).

    Thread-safe: no shared mutable state is accessed or modified.
    When *skip_sessions* is True, session execution is skipped and only
    existing output is scored (rescore-only mode).
    """
    if skip_sessions:
        session_dir = variant_dir / "sessions" / fixture.domain / fixture.client
        produced = session_dir.exists() and _has_deliverables(session_dir, fixture.domain)
        session_run = SessionRun(
            fixture=fixture,
            session_dir=session_dir if session_dir.exists() else None,
            produced_output=produced,
            runner_exit_code=0,
            wall_time_seconds=0.0,
        )
    else:
        session_run = _run_fixture_session(variant_dir, fixture, eval_target)
    result = _score_session(
        session_run, variant_id=variant_id, campaign_id=campaign_id,
    )
    return (fixture.domain, fixture.fixture_id, result, session_run.produced_output)


def evaluate_search(
    *,
    variant_dir: Path,
    archive_dir: Path,
    require_holdout: bool,
    search_manifest: dict[str, Any],
    lane: str,
    skip_sessions: bool = False,
) -> dict[str, Any]:
    variant_id = variant_dir.name
    if not layer1_validate(variant_dir):
        raise SystemExit(0)

    env = os.environ.copy()
    eval_target = _require_eval_target(env, search_manifest)
    fixtures_by_domain = _suite_fixtures(search_manifest)
    # Gap 3: Apply stratified sampling if rotation config is present
    rotation_config = search_manifest.get("rotation")
    if isinstance(rotation_config, dict) and rotation_config.get("strategy") == "stratified":
        fixtures_by_domain = _sample_fixtures(fixtures_by_domain, rotation_config, variant_id)
    holdout_configured = _holdout_configured(env)
    meta_backend = env.get("EVOLUTION_META_BACKEND", "").strip().lower() or None
    meta_model = env.get("EVOLUTION_META_MODEL", "").strip() or None
    search_campaign_id = f"{search_manifest['suite_id']}:{variant_id}"

    # Gap 28: Determine which domains need evaluation vs cache from parent
    parent_id = (env.get("EVOLUTION_PARENT_ID") or "").strip() or None
    affected_domains = set(DOMAINS)
    parent_cached_scores: dict[str, list[dict[str, Any]]] | None = None
    if parent_id:
        try:
            changed_files, _ = summarize_variant_diff(archive_dir, variant_id, parent_id)
        except Exception:
            changed_files = None
        if changed_files is not None:
            affected_domains = set()
            for f in changed_files:
                matched_lane = False
                for wl in WORKFLOW_LANES:
                    if path_owned_by_lane(f, wl):
                        affected_domains.add(wl)
                        matched_lane = True
                if not matched_lane:
                    # Core file changed — all domains affected
                    affected_domains = set(DOMAINS)
                    break
        parent_cached_scores = _load_parent_scores(archive_dir, parent_id)

    print(f"L2/L3: Running search suite {search_manifest['suite_id']} for {variant_id}...")
    scored_fixtures: dict[str, list[dict[str, Any]]] = {domain: [] for domain in DOMAINS}
    any_output = False

    # Seed scored_fixtures from the parent cache for unchanged domains, then
    # collect all fixtures for affected domains into a single unsharded pass.
    all_fixtures: list[Fixture] = []
    for domain in DOMAINS:
        if domain not in affected_domains:
            # Gap 28: Use cached parent scores for unchanged domains
            if parent_cached_scores and domain in parent_cached_scores:
                scored_fixtures[domain] = parent_cached_scores[domain]
                print(f"  {domain}: cached from parent {parent_id}")
                any_output = True
            continue
        fixtures = fixtures_by_domain[domain]
        for fixture in fixtures:
            all_fixtures.append(fixture)
            print(f"  {domain}: {fixture.fixture_id}")

    if all_fixtures:
        # Phase 4 (Unit 9): each fixture runs exactly once.
        # Variance reduction is the fixture set's job (Unit 14), not
        # repeated runs. karpathy discipline — see plan rationale.
        with ThreadPoolExecutor(max_workers=len(all_fixtures)) as executor:
            futures = [
                executor.submit(
                    _run_and_score_fixture, variant_dir, f, eval_target,
                    variant_id, search_campaign_id, skip_sessions,
                )
                for f in all_fixtures
            ]
            try:
                for future in as_completed(futures):
                    domain_, _fid, result, produced = future.result()
                    scored_fixtures[domain_].append(result)
                    any_output = any_output or produced
            except Exception:
                for future in futures:
                    if not future.done():
                        future.cancel()
                raise

    smoke_summary: dict[str, Any] = {
        "suite_id": search_manifest["suite_id"],
        "fixtures_total": sum(len(fixtures_by_domain.get(d, [])) for d in DOMAINS),
        "fixtures_with_output": sum(
            1 for d in DOMAINS for f in scored_fixtures.get(d, [])
            if f.get("produced_output") or f.get("score", 0) > 0
        ),
        "cached_domains": [d for d in DOMAINS if d not in affected_domains],
        "domains": {
            domain: {
                "fixtures": len(fixtures_by_domain.get(domain, [])),
                "fixtures_with_output": sum(
                    1 for f in scored_fixtures.get(domain, [])
                    if f.get("produced_output") or f.get("score", 0) > 0
                ),
            }
            for domain in DOMAINS
        },
    }

    scores, aggregated = _aggregate_suite_results(search_manifest, fixtures_by_domain, scored_fixtures)
    if not any_output:
        for domain in DOMAINS:
            scores[domain] = 0.0
        scores["composite"] = 0.0
        aggregated["search_metrics"]["composite"] = 0.0
        for domain in DOMAINS:
            aggregated["search_metrics"]["domains"][domain]["score"] = 0.0

    # harness.telemetry is imported lazily because it pulls in archive/current_runtime/
    # scripts/ via harness/__init__.py sys.path manipulation; that mirror may not be
    # materialized in every caller (tests, one-off scoring).
    try:
        from harness.telemetry import compute_inner_keep_rate
    except ImportError as exc:
        print(f"  warning: harness.telemetry unavailable ({exc}); inner_metrics empty", file=sys.stderr)
        inner_metrics = {}
    else:
        inner_metrics = compute_inner_keep_rate(variant_dir)

    _write_scores_file(
        variant_dir,
        scores=scores,
        eval_target=eval_target,
        suite_manifest=search_manifest,
        domains=aggregated,
        lane=lane,
        smoke_summary=smoke_summary,
        inner_metrics=inner_metrics,
    )

    # Generate eval digest for meta agent visibility
    _write_eval_digest(variant_dir, scored_fixtures, smoke_summary, aggregated)

    latest = load_latest_lineage(archive_dir)
    existing_entry = latest.get(variant_id)
    candidate_entry = {
        "id": variant_id,
        "lane": lane,
        "scores": scores,
        "search_metrics": aggregated["search_metrics"],
    }
    promotion_summary = _search_promotion_summary(
        variant_entry=candidate_entry,
        baseline_entry=None,
        search_suite_manifest=search_manifest,
        require_holdout=require_holdout,
    )
    parent_id = os.environ.get("EVOLUTION_PARENT_ID") or (existing_entry or {}).get("parent")
    entry, lineage_batch = _lineage_entry(
        variant_dir=variant_dir,
        archive_dir=archive_dir,
        existing_entry=existing_entry,
        eval_target=eval_target,
        search_manifest=search_manifest,
        holdout_manifest=None,
        meta_backend=meta_backend,
        meta_model=meta_model,
        scores=scores,
        search_metrics=aggregated["search_metrics"],
        promotion_summary=promotion_summary,
        holdout_ran=False,
        lane=lane,
        parent_id=parent_id or None,
    )
    entry["campaign_ids"]["search"] = search_campaign_id
    append_lineage_entries(archive_dir, lineage_batch)
    refresh_archive_outputs(archive_dir, suite_manifest=search_manifest)
    result = {
        "variant_id": variant_id,
        "suite_id": search_manifest["suite_id"],
        "scores": scores,
        "search_metrics": aggregated["search_metrics"],
        "smoke_summary": smoke_summary,
        "holdout_configured": holdout_configured,
        "promotion_summary": promotion_summary,
    }
    print(json.dumps(result, indent=2))
    return result


def evaluate_holdout(
    *,
    variant_dir: Path,
    archive_dir: Path,
    search_manifest: dict[str, Any],
    lane: str,
) -> dict[str, Any]:
    env = os.environ.copy()
    holdout_manifest = _load_holdout_manifest(env, lane)
    if holdout_manifest is None:
        raise RuntimeError(
            "Holdout evaluation requires EVOLUTION_HOLDOUT_MANIFEST."
        )

    variant_id = variant_dir.name
    eval_target = _require_eval_target(env, holdout_manifest)
    latest = load_latest_lineage(archive_dir)
    existing_entry = latest.get(variant_id)
    if existing_entry is None:
        raise RuntimeError(f"Variant must have search metrics before holdout evaluation: {variant_id}")
    if not has_search_metrics(existing_entry):
        raise RuntimeError(f"Variant must have search metrics before holdout evaluation: {variant_id}")

    cached_holdout = _load_private_result(variant_id, "holdout", str(holdout_manifest["suite_id"]))
    if isinstance(cached_holdout, dict) and isinstance(cached_holdout.get("scores"), dict):
        holdout_scores = cached_holdout["scores"]
    else:
        holdout_scores, _aggregated = _run_holdout_suite(
            variant_dir=variant_dir,
            variant_id=variant_id,
            suite_manifest=holdout_manifest,
            eval_target=eval_target,
        )
    baseline_entry, baseline_holdout_scores = _baseline_holdout_scores(
        archive_dir=archive_dir,
        variant_id=variant_id,
        holdout_manifest=holdout_manifest,
        eval_target=eval_target,
        lane=lane,
    )

    # Inline _eligible_for_promotion: candidate > baseline (Unit 6 / R11)
    if baseline_entry is None or baseline_holdout_scores is None:
        eligible, reason = True, "holdout_passed"
    elif _objective_score_from_scores(holdout_scores, lane) > _objective_score_from_scores(baseline_holdout_scores, lane):
        eligible, reason = True, "holdout_passed"
    else:
        eligible, reason = False, "holdout_not_better_than_baseline"

    finalization_record = _write_finalize_result(
        variant_id=variant_id,
        suite_manifest=holdout_manifest,
        scores=holdout_scores,
        baseline_variant_id=str(baseline_entry["id"]) if baseline_entry else None,
        baseline_holdout_scores=baseline_holdout_scores,
        eligible=eligible,
        reason=reason,
    )

    result = {
        "variant_id": variant_id,
        "suite_id": holdout_manifest["suite_id"],
        "baseline_variant_id": str(baseline_entry["id"]) if baseline_entry else None,
        "scores": holdout_scores,
        "eligible_for_promotion": eligible,
        "reason": reason,
    }
    if isinstance(finalization_record, dict):
        result["evaluated_at"] = finalization_record.get("evaluated_at")
    print(json.dumps(result, indent=2))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate an autoresearch variant.")
    parser.add_argument(
        "variant_dir",
        nargs="?",
        help="Variant directory to evaluate (omit in --single-fixture mode).",
    )
    parser.add_argument(
        "archive_dir",
        nargs="?",
        help="Archive directory containing lineage.jsonl (omit in --single-fixture mode).",
    )
    parser.add_argument(
        "--mode",
        choices=("search", "holdout"),
        default="search",
        help="Which evaluation path to execute.",
    )
    parser.add_argument(
        "--search-suite",
        help="Path to the public search suite manifest.",
    )
    parser.add_argument(
        "--lane",
        default=os.environ.get("EVOLUTION_LANE", "core"),
        help="Evolution lane being evaluated.",
    )
    parser.add_argument(
        "--require-holdout",
        action="store_true",
        default=False,
        help="Require holdout evaluation for promotion eligibility.",
    )
    parser.add_argument(
        "--skip-sessions",
        action="store_true",
        default=False,
        help="Rescore only: skip session execution, score existing session output.",
    )
    # --single-fixture mode (Phase 7 dry-run subprocess contract).
    parser.add_argument(
        "--single-fixture",
        default=None,
        metavar="<pool>:<fixture_id>",
        help=(
            "Run one fixture, return {per_seed_scores, structural_passed, "
            "cost_usd, duration_seconds} JSON on stdout. Requires --manifest + "
            "--seeds; optional --baseline-variant, --cache-root."
        ),
    )
    parser.add_argument(
        "--manifest",
        default=None,
        help="Suite manifest path for --single-fixture mode.",
    )
    parser.add_argument(
        "--seeds",
        type=int,
        default=3,
        help="Replicate count for --single-fixture mode.",
    )
    parser.add_argument(
        "--baseline-variant",
        default="v006",
        help="Baseline variant id for --single-fixture mode.",
    )
    parser.add_argument(
        "--cache-root",
        default=None,
        help="Cache root for --single-fixture mode (default: ~/.local/share/gofreddy/fixture-cache).",
    )
    parser.add_argument(
        "--json-output",
        action="store_true",
        default=False,
        help="Emit JSON to stdout (default in --single-fixture mode).",
    )
    args = parser.parse_args()

    if args.single_fixture:
        pool, _, fixture_id = args.single_fixture.partition(":")
        if not pool or not fixture_id:
            parser.error("--single-fixture must be '<pool>:<fixture_id>'")
        if not args.manifest:
            parser.error("--single-fixture requires --manifest")
        cache_root = args.cache_root or str(
            Path.home() / ".local/share/gofreddy/fixture-cache"
        )
        result = evaluate_single_fixture(
            fixture_id,
            manifest_path=args.manifest,
            pool=pool,
            baseline=args.baseline_variant,
            seeds=args.seeds,
            cache_root=cache_root,
        )
        print(json.dumps(result, indent=2))
        return

    if not args.variant_dir or not args.archive_dir or not args.search_suite:
        parser.error(
            "variant_dir, archive_dir, and --search-suite are required unless "
            "--single-fixture is used"
        )

    lane = normalize_lane(args.lane)
    require_holdout: bool = args.require_holdout

    variant_dir = Path(args.variant_dir).resolve()
    archive_dir = Path(args.archive_dir).resolve()

    search_manifest_path = _resolve_path(args.search_suite, base=SCRIPT_DIR)
    if search_manifest_path is None:
        raise RuntimeError("Could not resolve the search suite manifest path.")

    search_manifest = _normalize_suite_manifest(
        _project_suite_manifest_for_lane(load_json(search_manifest_path), lane),
        env=os.environ.copy(),
        source=str(search_manifest_path),
    )

    if args.mode == "search":
        evaluate_search(
            variant_dir=variant_dir,
            archive_dir=archive_dir,
            require_holdout=require_holdout,
            search_manifest=search_manifest,
            lane=lane,
            skip_sessions=args.skip_sessions,
        )
        return
    evaluate_holdout(
        variant_dir=variant_dir,
        archive_dir=archive_dir,
        search_manifest=search_manifest,
        lane=lane,
    )


if __name__ == "__main__":
    main()
