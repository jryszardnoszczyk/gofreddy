"""autoresearch_v2/tools/score_holdout.py — call evolution-judge over the 6 holdout fixtures.

Run all holdout fixtures for a lane through the evolution-judge HTTP service
(:7200, endpoint `/invoke/score`), return composite + per-fixture breakdown.
Agent calls this on `keep` decisions to validate the candidate against the
hidden 6-fixture set.

Holdout isolation guarantee:
  - The agent never sees fixture.context text.
  - The return value contains only {composite, per-fixture composite/status/
    wall-time/deliverables_count}. No fixture content, no judge prompts, no
    deliverable text.

Stream A integration:
  - Writes to `lanes/<lane>/holdout_results.tsv` so downstream tools can read
    holdout composites. Mirrors v1's `_update_lineage_holdout_metrics` port.

Rubric hash hook (Stream C C4-lean):
  - Validates `rubric_hash` in judge response against `RUBRIC_VERSION` from
    `src/evaluation/rubrics.py` (when import succeeds; soft-failure if
    rubrics module unavailable).

Required env:
  - EVOLUTION_JUDGE_URL    default http://localhost:7200
  - EVOLUTION_INVOKE_TOKEN bearer for /invoke/score
  - EVOLUTION_HOLDOUT_MANIFEST  path to holdout-v1.json manifest

Optional env:
  - JUDGE_RETRY_TOTAL_BUDGET_S  cumulative retry budget (default 600s)
  - AUTORESEARCH_EVAL_FIX_HOLDOUT etc.  Stream A flags (passed through to runner)
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable, Sequence

# When invoked as a standalone script (`python3 autoresearch_v2/tools/
# score_holdout.py`), sys.path's first entry is this file's directory —
# not the repo root — so `from autoresearch_v2.tools.run_experiment import
# ...` fails with ModuleNotFoundError. Add the repo root explicitly so
# the package import resolves regardless of invocation mode (pytest, -m,
# or direct script).
_REPO_ROOT_FOR_IMPORTS = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT_FOR_IMPORTS) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT_FOR_IMPORTS))

# Public exceptions
class JudgeUnreachable(RuntimeError):
    """Raised when evolution-judge HTTP call fails after all retries."""


class JudgeRubricMismatch(RuntimeError):
    """Raised when judge response rubric_hash != current RUBRIC_VERSION."""


# Retry config — port verbatim from v1 evaluate_variant.py:_post_with_retry
_JUDGE_RETRY_DELAYS = (2.0, 8.0, 30.0)
_JUDGE_RETRY_ATTEMPTS = len(_JUDGE_RETRY_DELAYS) + 1
_JUDGE_RETRY_TOTAL_BUDGET_S_DEFAULT = 600.0

# Artifact payload caps — port verbatim from v1
_TEXT_EXTS = frozenset({
    ".md", ".markdown", ".json", ".jsonl", ".yaml", ".yml",
    ".txt", ".csv", ".tsv", ".html", ".htm", ".xml", ".srt", ".vtt",
})
_MAX_PAYLOAD_BYTES = 800_000
_MAX_FILE_BYTES = 200_000


def _repo_root() -> Path:
    override = os.environ.get("AUTORESEARCH_V2_ROOT")
    if override:
        return Path(override).resolve()
    return Path(__file__).resolve().parent.parent.parent


def _retry_budget() -> float:
    return float(os.environ.get("JUDGE_RETRY_TOTAL_BUDGET_S", _JUDGE_RETRY_TOTAL_BUDGET_S_DEFAULT))


def _holdout_manifest_path() -> Path:
    env = os.environ.get("EVOLUTION_HOLDOUT_MANIFEST", "").strip()
    if not env:
        raise RuntimeError(
            "EVOLUTION_HOLDOUT_MANIFEST is unset. Holdout scoring requires the "
            "hidden manifest at ~/.config/gofreddy/holdouts/holdout-v1.json."
        )
    return Path(env).expanduser().resolve()


def load_manifest(path: Path | None = None) -> dict[str, Any]:
    p = path or _holdout_manifest_path()
    if not p.is_file():
        raise RuntimeError(f"holdout manifest missing: {p}")
    try:
        payload = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise RuntimeError(f"holdout manifest at {p} is not valid JSON: {e}")
    if not isinstance(payload, dict):
        raise RuntimeError(f"holdout manifest at {p} must be a JSON object")
    _reject_redacted(payload, str(p))
    return payload


def _reject_redacted(payload: dict[str, Any], source: str) -> None:
    """Refuse manifests with placeholder/redacted markers — caller pointed at
    the example manifest by mistake. Mirrors v1's `_reject_redacted_example`.
    """
    blob = json.dumps(payload)
    markers = ("<REDACTED", "REDACTED>", "PLACEHOLDER", "fill-this-in", "TODO_FILL")
    for marker in markers:
        if marker in blob:
            raise RuntimeError(
                f"holdout manifest at {source} contains placeholder marker "
                f"{marker!r}. Point EVOLUTION_HOLDOUT_MANIFEST at a real "
                f"manifest, not the redacted example."
            )


def _gather_artifacts(session_dir: Path) -> tuple[dict[str, str], dict[str, Any]]:
    """Read text artifacts from session_dir, applying v1's caps + skips.
    Returns (artifacts, meta).
    """
    artifacts: dict[str, str] = {}
    total_bytes = 0
    skipped_binary = 0
    skipped_too_large = 0
    truncated = False
    if not session_dir.is_dir():
        return artifacts, {"missing_session_dir": True}

    for path in sorted(session_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(session_dir).as_posix()
        if rel.startswith("logs/"):
            continue
        if path.suffix.lower() not in _TEXT_EXTS:
            skipped_binary += 1
            continue
        try:
            size = path.stat().st_size
            if size > _MAX_FILE_BYTES:
                skipped_too_large += 1
                continue
            if total_bytes + size > _MAX_PAYLOAD_BYTES:
                truncated = True
                break
            artifacts[rel] = path.read_text(encoding="utf-8", errors="replace")
            total_bytes += size
        except (OSError, UnicodeError):
            continue

    meta = {
        "total_bytes": total_bytes,
        "skipped_binary": skipped_binary,
        "skipped_too_large": skipped_too_large,
        "truncated": truncated,
    }
    return artifacts, meta


def post_with_retry(
    *,
    endpoint: str,
    request_body: dict[str, Any],
    token: str,
    fixture_id: str,
    domain: str,
    poster: Callable | None = None,
    sleeper: Callable[[float], None] | None = None,
) -> Any:
    """POST to evolution-judge with exponential backoff. Ports v1 contract.

    `poster(endpoint, json, headers, timeout)` and `sleeper(seconds)` are
    injectable for tests.
    """
    if not token:
        raise JudgeUnreachable(
            "EVOLUTION_INVOKE_TOKEN is unset/empty; cannot call evolution judge."
        )

    if poster is None:
        import httpx  # lazy import — keep module-load surface stable
        def poster(endpoint, json, headers, timeout):
            return httpx.post(endpoint, json=json, headers=headers, timeout=timeout)
    if sleeper is None:
        sleeper = time.sleep

    budget = _retry_budget()
    started = time.monotonic()
    last_error: str = ""
    for attempt in range(1, _JUDGE_RETRY_ATTEMPTS + 1):
        elapsed = time.monotonic() - started
        if elapsed >= budget and attempt > 1:
            raise JudgeUnreachable(
                f"evolution-judge /invoke/score: retry budget {budget}s "
                f"exhausted ({elapsed:.0f}s; last={last_error})"
            )
        try:
            response = poster(
                endpoint,
                json=request_body,
                headers={"Authorization": f"Bearer {token}"},
                timeout=1800.0,
            )
        except Exception as exc:  # httpx.HTTPError + OSError — keep test-friendly
            last_error = repr(exc)
            if attempt < _JUDGE_RETRY_ATTEMPTS:
                sleeper(_JUDGE_RETRY_DELAYS[attempt - 1])
                continue
            raise JudgeUnreachable(
                f"evolution-judge unreachable after {_JUDGE_RETRY_ATTEMPTS} attempts: {exc}"
            ) from exc

        # Got a response — classify.
        if getattr(response, "status_code", 500) >= 500:
            text = getattr(response, "text", "")
            last_error = f"HTTP {response.status_code}: {text[:200]}"
            if "codex credits exhausted" in text.lower():
                raise JudgeUnreachable(
                    "codex credits exhausted (judge HTTP 500). Refresh credits "
                    "or set EVOLUTION_JUDGE_SECONDARY=opencode."
                )
            if attempt < _JUDGE_RETRY_ATTEMPTS:
                sleeper(_JUDGE_RETRY_DELAYS[attempt - 1])
                continue
            raise JudgeUnreachable(
                f"evolution-judge HTTP {response.status_code} after "
                f"{_JUDGE_RETRY_ATTEMPTS} attempts"
            )
        return response

    raise JudgeUnreachable(f"exhausted retries ({last_error})")  # pragma: no cover


def _current_rubric_version() -> str | None:
    """Best-effort read of RUBRIC_VERSION from src/evaluation/rubrics.py.
    Returns None if module is unavailable (no rubric-hash check).
    """
    try:
        sys.path.insert(0, str(_repo_root()))
        from src.evaluation import rubrics  # type: ignore
        return getattr(rubrics, "RUBRIC_VERSION", None)
    except Exception:
        return None
    finally:
        if sys.path and sys.path[0] == str(_repo_root()):
            sys.path.pop(0)


def _check_rubric_hash(response_data: dict[str, Any]) -> None:
    expected = _current_rubric_version()
    if expected is None:
        return
    got = response_data.get("rubric_hash")
    if got and got != expected:
        raise JudgeRubricMismatch(
            f"judge response rubric_hash {got!r} != current RUBRIC_VERSION {expected!r}"
        )


def _score_one_fixture(
    *,
    lane: str,
    fixture: dict[str, Any],
    runner: Callable[..., dict],
    poster: Callable | None,
    sleeper: Callable[[float], None] | None,
    judge_url: str,
    token: str,
) -> dict[str, Any]:
    """Run + score a single holdout fixture. Returns isolated breakdown
    (no fixture content)."""
    fixture_id = fixture.get("fixture_id") or fixture.get("id", "")
    client = fixture.get("client") or fixture_id
    context = fixture.get("context", "")
    max_iter = int(fixture.get("max_iter", 30))
    timeout = int(fixture.get("timeout", 1800))

    run_result = runner(
        domain=lane,
        client=client,
        context=context,
        max_iter=max_iter,
        timeout=timeout,
    )

    session_dir = Path(run_result["session_dir"])
    artifacts, payload_meta = _gather_artifacts(session_dir)
    request_body = {
        "domain": lane,
        "session_dir": str(session_dir),
        "session_ref": str(session_dir),
        "fixture_id": fixture_id,
        "fixture": {
            "fixture_id": fixture_id,
            "client": client,
            "context": context,
            "suite_id": fixture.get("suite_id", "holdout-v1"),
            "version": fixture.get("version"),
            "domain": lane,
        },
        "suite_id": fixture.get("suite_id", "holdout-v1"),
        "artifacts": artifacts,
        "__payload_meta__": payload_meta,
    }

    try:
        response = post_with_retry(
            endpoint=f"{judge_url}/invoke/score",
            request_body=request_body,
            token=token,
            fixture_id=fixture_id,
            domain=lane,
            poster=poster,
            sleeper=sleeper,
        )
    except JudgeUnreachable:
        raise

    status_code = getattr(response, "status_code", 0)
    if status_code >= 400:
        # 4xx — judge rejected payload. Surface as zero-score, structural-fail.
        return {
            "fixture_id": fixture_id,
            "composite": 0.0,
            "status": f"judge_4xx_{status_code}",
            "wall_time_seconds": run_result.get("wall_time_seconds", 0.0),
            "deliverables_count": len(artifacts),
        }

    data = response.json() if hasattr(response, "json") else {}
    _check_rubric_hash(data)

    composite = float(data.get("score", data.get("composite", 0.0)))
    return {
        "fixture_id": fixture_id,
        "composite": composite,
        "status": "scored",
        "wall_time_seconds": run_result.get("wall_time_seconds", 0.0),
        "deliverables_count": len(artifacts),
    }


def _write_holdout_tsv(lane: str, composite: float, per_fixture: Sequence[dict]) -> Path:
    path = _repo_root() / "autoresearch_v2" / "lanes" / lane / "holdout_results.tsv"
    path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not path.exists()
    with path.open("a", encoding="utf-8") as fh:
        if new_file:
            fh.write("\t".join(["timestamp", "lane", "composite", "per_fixture_json"]) + "\n")
        breakdown = json.dumps(per_fixture, separators=(",", ":"))
        fh.write("\t".join([
            dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            lane,
            f"{composite:.4f}",
            breakdown,
        ]) + "\n")
    return path


def score_holdout(
    *,
    lane: str,
    manifest_path: Path | None = None,
    runner: Callable[..., dict] | None = None,
    poster: Callable | None = None,
    sleeper: Callable[[float], None] | None = None,
    judge_url: str | None = None,
    token: str | None = None,
    write_tsv: bool = True,
) -> dict[str, Any]:
    """Run all holdout fixtures for `lane`. Return aggregated composite +
    isolated per-fixture breakdown.
    """
    payload = load_manifest(manifest_path)
    domains = payload.get("domains", {})
    if not isinstance(domains, dict):
        raise RuntimeError("holdout manifest missing 'domains' object")
    fixtures = domains.get(lane)
    if not fixtures:
        raise RuntimeError(f"holdout manifest has no fixtures for lane {lane!r}")
    if not isinstance(fixtures, list):
        raise RuntimeError(f"holdout manifest entry for {lane!r} must be a list")

    if runner is None:
        from autoresearch_v2.tools.run_experiment import run_experiment as runner  # type: ignore

    judge_url = judge_url or os.environ.get("EVOLUTION_JUDGE_URL", "http://localhost:7200")
    token = token if token is not None else os.environ.get("EVOLUTION_INVOKE_TOKEN", "")

    per_fixture: list[dict[str, Any]] = []
    wall_total = 0.0
    failures = 0
    for fixture in fixtures:
        try:
            result = _score_one_fixture(
                lane=lane,
                fixture=fixture,
                runner=runner,
                poster=poster,
                sleeper=sleeper,
                judge_url=judge_url,
                token=token,
            )
        except JudgeUnreachable as e:
            failures += 1
            per_fixture.append({
                "fixture_id": fixture.get("fixture_id", "?"),
                "composite": 0.0,
                "status": "judge_unreachable",
                "wall_time_seconds": 0.0,
                "deliverables_count": 0,
                "error": str(e)[:300],
            })
            continue
        per_fixture.append(result)
        wall_total += result["wall_time_seconds"]

    scored = [r for r in per_fixture if r["status"] == "scored"]
    composite = sum(r["composite"] for r in scored) / len(scored) if scored else 0.0

    result = {
        "lane": lane,
        "composite": round(composite, 4),
        "fixtures_total": len(fixtures),
        "fixtures_scored": len(scored),
        "fixtures_failed": failures + (len(fixtures) - len(scored) - failures),
        "wall_time_seconds": round(wall_total, 2),
        "per_fixture": per_fixture,
    }
    if write_tsv and scored:
        _write_holdout_tsv(lane, composite, per_fixture)
    return result


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        description="Run all holdout fixtures for a lane and report composite.",
    )
    p.add_argument("--lane", required=True)
    p.add_argument("--no-write-tsv", action="store_true",
                   help="Don't append to lanes/<lane>/holdout_results.tsv")
    args = p.parse_args(argv)

    try:
        result = score_holdout(lane=args.lane, write_tsv=not args.no_write_tsv)
    except (RuntimeError, JudgeRubricMismatch) as e:
        sys.stderr.write(f"score_holdout: {e}\n")
        return 2

    print(json.dumps(result, indent=2))
    return 0 if result["fixtures_scored"] > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
