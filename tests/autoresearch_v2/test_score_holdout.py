"""Tests for autoresearch_v2/tools/score_holdout.py.

Real evolution-judge HTTP isn't available in tests; instead we inject a
`poster` callable that returns canned responses, and a `runner` callable
that stubs run_experiment's session_dir return value.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from autoresearch_v2.tools import score_holdout


# --- fixtures ----------------------------------------------------------------


def _manifest(tmp_path: Path, fixtures: list[dict], lane: str = "geo") -> Path:
    payload = {"domains": {lane: fixtures}}
    p = tmp_path / "holdout-v1.json"
    p.write_text(json.dumps(payload))
    return p


def _session_dir(tmp_path: Path, name: str = "fixture-1") -> Path:
    d = tmp_path / "sessions" / "geo" / name
    d.mkdir(parents=True)
    (d / "session.md").write_text("# session\n## Status: COMPLETE\n")
    (d / "optimized.md").write_text("# optimized deliverable\n")
    return d


def _runner_factory(session_dir: Path, wall: float = 100.0):
    def runner(*, domain, client, context, max_iter, timeout):
        return {
            "session_dir": str(session_dir),
            "exit_code": 0,
            "wall_time_seconds": wall,
            "deliverable_present": True,
        }
    return runner


class _FakeResponse:
    def __init__(self, *, status_code: int = 200, body: dict | None = None, text: str = ""):
        self.status_code = status_code
        self._body = body if body is not None else {"score": 5.0}
        self.text = text or json.dumps(self._body)

    def json(self):
        return self._body


def _poster_factory(responses: list[_FakeResponse]):
    """Return a poster that yields `responses` in order; raises if exhausted."""
    queue = list(responses)

    def poster(endpoint, json, headers, timeout):
        if not queue:
            raise RuntimeError("poster called more times than canned responses")
        return queue.pop(0)
    return poster


@pytest.fixture
def tmp_repo(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("AUTORESEARCH_V2_ROOT", str(tmp_path))
    monkeypatch.delenv("EVOLUTION_HOLDOUT_MANIFEST", raising=False)
    monkeypatch.setenv("EVOLUTION_INVOKE_TOKEN", "test-token")
    return tmp_path


# --- happy path -------------------------------------------------------------


def test_happy_path_all_six_score_real_judge_shape(tmp_repo: Path, monkeypatch):
    """Real judge returns {aggregate: {aggregate_score: <num>, ...}}, NOT a
    top-level 'score' field. Discovered in U10 spike attempt 5 — the meta-
    agent diagnosed silent fallback to 0.0 for all 4 baseline fixtures."""
    fixtures = [{"fixture_id": f"geo-fx-{i}", "client": f"c{i}", "context": "x"} for i in range(6)]
    manifest = _manifest(tmp_repo, fixtures)
    monkeypatch.setenv("EVOLUTION_HOLDOUT_MANIFEST", str(manifest))

    runner = _runner_factory(_session_dir(tmp_repo), wall=10.0)
    poster = _poster_factory([
        _FakeResponse(body={
            "aggregate": {
                "aggregate_score": 4.5 + i * 0.1,
                "structural_passed": True,
                "grounding_passed": True,
            },
        })
        for i in range(6)
    ])

    result = score_holdout.score_holdout(lane="geo", runner=runner, poster=poster)
    assert result["fixtures_scored"] == 6
    assert pytest.approx(result["composite"], abs=0.01) == sum(4.5 + i * 0.1 for i in range(6)) / 6


def test_happy_path_top_level_score_legacy_shape(tmp_repo: Path, monkeypatch):
    """Top-level 'score' field — legacy/test-double shape — still works
    via the fallback chain in case the judge response shape ever changes."""
    fixtures = [{"fixture_id": f"geo-fx-{i}", "client": f"c{i}", "context": "x"} for i in range(6)]
    manifest = _manifest(tmp_repo, fixtures)
    monkeypatch.setenv("EVOLUTION_HOLDOUT_MANIFEST", str(manifest))

    runner = _runner_factory(_session_dir(tmp_repo), wall=10.0)
    poster = _poster_factory([_FakeResponse(body={"score": 4.5 + i * 0.1}) for i in range(6)])

    result = score_holdout.score_holdout(lane="geo", runner=runner, poster=poster)
    assert result["fixtures_total"] == 6
    assert result["fixtures_scored"] == 6
    assert result["fixtures_failed"] == 0
    # mean of 4.5..5.0
    assert pytest.approx(result["composite"], abs=0.01) == sum(4.5 + i * 0.1 for i in range(6)) / 6
    # holdout_results.tsv written
    tsv = tmp_repo / "autoresearch_v2" / "lanes" / "geo" / "holdout_results.tsv"
    assert tsv.is_file()
    assert "composite" in tsv.read_text().splitlines()[0]


def test_per_fixture_breakdown_excludes_fixture_content(tmp_repo: Path, monkeypatch):
    """Holdout isolation: per_fixture entries MUST NOT include fixture.context
    or other content that would leak holdout details to the agent."""
    fixtures = [{"fixture_id": "geo-1", "client": "c1", "context": "SECRET-CONTEXT-DO-NOT-LEAK"}]
    manifest = _manifest(tmp_repo, fixtures)
    monkeypatch.setenv("EVOLUTION_HOLDOUT_MANIFEST", str(manifest))

    runner = _runner_factory(_session_dir(tmp_repo))
    poster = _poster_factory([_FakeResponse(body={"score": 4.0})])

    result = score_holdout.score_holdout(lane="geo", runner=runner, poster=poster, write_tsv=False)
    blob = json.dumps(result)
    assert "SECRET-CONTEXT-DO-NOT-LEAK" not in blob
    assert result["per_fixture"][0]["fixture_id"] == "geo-1"
    assert "context" not in result["per_fixture"][0]


# --- manifest validation ----------------------------------------------------


def test_missing_env_var_raises(tmp_repo: Path, monkeypatch):
    monkeypatch.delenv("EVOLUTION_HOLDOUT_MANIFEST", raising=False)
    with pytest.raises(RuntimeError, match="EVOLUTION_HOLDOUT_MANIFEST"):
        score_holdout.score_holdout(lane="geo", runner=lambda **k: {}, poster=lambda **k: None)


def test_missing_manifest_file_raises(tmp_repo: Path, monkeypatch):
    monkeypatch.setenv("EVOLUTION_HOLDOUT_MANIFEST", str(tmp_repo / "missing.json"))
    with pytest.raises(RuntimeError, match="missing"):
        score_holdout.score_holdout(lane="geo", runner=lambda **k: {}, poster=lambda **k: None)


def test_redacted_manifest_refused(tmp_repo: Path, monkeypatch):
    manifest = tmp_repo / "redacted.json"
    manifest.write_text(json.dumps({"domains": {"geo": [{"fixture_id": "<REDACTED-ID>"}]}}))
    monkeypatch.setenv("EVOLUTION_HOLDOUT_MANIFEST", str(manifest))
    with pytest.raises(RuntimeError, match="REDACTED"):
        score_holdout.score_holdout(lane="geo", runner=lambda **k: {}, poster=lambda **k: None)


def test_no_fixtures_for_lane(tmp_repo: Path, monkeypatch):
    manifest = _manifest(tmp_repo, [], lane="geo")
    monkeypatch.setenv("EVOLUTION_HOLDOUT_MANIFEST", str(manifest))
    with pytest.raises(RuntimeError, match="no fixtures"):
        score_holdout.score_holdout(lane="geo", runner=lambda **k: {}, poster=lambda **k: None)


# --- error paths ------------------------------------------------------------


def test_one_fixture_judge_unreachable_others_continue(tmp_repo: Path, monkeypatch):
    fixtures = [{"fixture_id": f"geo-{i}", "client": "c", "context": "x"} for i in range(3)]
    manifest = _manifest(tmp_repo, fixtures)
    monkeypatch.setenv("EVOLUTION_HOLDOUT_MANIFEST", str(manifest))

    runner = _runner_factory(_session_dir(tmp_repo))

    # Fixture 1 fails with 500s through all 4 attempts; fixtures 0 and 2 succeed.
    responses = (
        [_FakeResponse(body={"score": 4.5})]
        + [_FakeResponse(status_code=500, text="boom")] * 4
        + [_FakeResponse(body={"score": 5.0})]
    )
    poster = _poster_factory(responses)
    sleeper_calls = []

    result = score_holdout.score_holdout(
        lane="geo", runner=runner, poster=poster,
        sleeper=lambda s: sleeper_calls.append(s),
    )
    assert result["fixtures_total"] == 3
    assert result["fixtures_scored"] == 2
    statuses = [r["status"] for r in result["per_fixture"]]
    assert "judge_unreachable" in statuses
    assert sleeper_calls  # backoff was exercised


def test_judge_4xx_yields_zero_score_not_unreachable(tmp_repo: Path, monkeypatch):
    fixtures = [{"fixture_id": "geo-1", "client": "c", "context": "x"}]
    manifest = _manifest(tmp_repo, fixtures)
    monkeypatch.setenv("EVOLUTION_HOLDOUT_MANIFEST", str(manifest))

    runner = _runner_factory(_session_dir(tmp_repo))
    poster = _poster_factory([_FakeResponse(status_code=400, text="bad request")])

    result = score_holdout.score_holdout(lane="geo", runner=runner, poster=poster, write_tsv=False)
    assert result["fixtures_scored"] == 0
    assert result["per_fixture"][0]["composite"] == 0.0
    assert "judge_4xx_400" in result["per_fixture"][0]["status"]


def test_missing_token_raises(tmp_repo: Path, monkeypatch):
    fixtures = [{"fixture_id": "geo-1", "client": "c", "context": "x"}]
    manifest = _manifest(tmp_repo, fixtures)
    monkeypatch.setenv("EVOLUTION_HOLDOUT_MANIFEST", str(manifest))
    monkeypatch.setenv("EVOLUTION_INVOKE_TOKEN", "")

    runner = _runner_factory(_session_dir(tmp_repo))

    result = score_holdout.score_holdout(
        lane="geo", runner=runner,
        poster=_poster_factory([_FakeResponse()]),
    )
    # Token check raises JudgeUnreachable inside post_with_retry; surfaces
    # as judge_unreachable status per-fixture (continues across the suite).
    assert result["fixtures_scored"] == 0
    assert "judge_unreachable" in result["per_fixture"][0]["status"]


def test_codex_credits_exhausted_short_circuits(tmp_repo: Path, monkeypatch):
    fixtures = [{"fixture_id": "geo-1", "client": "c", "context": "x"}]
    manifest = _manifest(tmp_repo, fixtures)
    monkeypatch.setenv("EVOLUTION_HOLDOUT_MANIFEST", str(manifest))

    runner = _runner_factory(_session_dir(tmp_repo))
    poster = _poster_factory([
        _FakeResponse(status_code=500, text="error: codex credits exhausted, sorry"),
    ])
    result = score_holdout.score_holdout(
        lane="geo", runner=runner, poster=poster, write_tsv=False,
    )
    assert result["fixtures_scored"] == 0
    assert "judge_unreachable" in result["per_fixture"][0]["status"]
    assert "credits" in result["per_fixture"][0]["error"]


# --- post_with_retry direct -------------------------------------------------


def test_post_with_retry_retries_then_succeeds(tmp_repo: Path):
    sleeper_calls = []
    responses = [
        _FakeResponse(status_code=500, text="boom"),
        _FakeResponse(status_code=500, text="boom"),
        _FakeResponse(body={"score": 4.0}),
    ]
    poster = _poster_factory(responses)
    r = score_holdout.post_with_retry(
        endpoint="http://judge/invoke/score",
        request_body={},
        token="t",
        fixture_id="f",
        domain="geo",
        poster=poster,
        sleeper=lambda s: sleeper_calls.append(s),
    )
    assert r.status_code == 200
    assert sleeper_calls == [2.0, 8.0]


def test_post_with_retry_all_attempts_fail_raises(tmp_repo: Path):
    poster = _poster_factory([_FakeResponse(status_code=500, text="boom")] * 4)
    with pytest.raises(score_holdout.JudgeUnreachable):
        score_holdout.post_with_retry(
            endpoint="http://judge/invoke/score",
            request_body={},
            token="t",
            fixture_id="f",
            domain="geo",
            poster=poster,
            sleeper=lambda s: None,
        )


def test_post_with_retry_network_exception_retries(tmp_repo: Path):
    """Connection errors get retried (transient class)."""
    call_count = {"n": 0}
    responses = [_FakeResponse(body={"score": 4.0})]

    def poster(endpoint, json, headers, timeout):
        call_count["n"] += 1
        if call_count["n"] < 3:
            raise ConnectionError("network down")
        return responses.pop(0)

    r = score_holdout.post_with_retry(
        endpoint="http://judge/invoke/score",
        request_body={},
        token="t",
        fixture_id="f",
        domain="geo",
        poster=poster,
        sleeper=lambda s: None,
    )
    assert r.status_code == 200
    assert call_count["n"] == 3


# --- artifacts gathering ----------------------------------------------------


def test_artifacts_skips_binary_and_logs(tmp_repo: Path):
    sd = tmp_repo / "session"
    sd.mkdir()
    (sd / "session.md").write_text("text content")
    (sd / "image.png").write_bytes(b"PNG\x89\x00")  # binary, should skip
    log_dir = sd / "logs"
    log_dir.mkdir()
    (log_dir / "x.log").write_text("not useful to judge")  # logs/ subtree should skip

    artifacts, meta = score_holdout._gather_artifacts(sd)
    assert "session.md" in artifacts
    assert "image.png" not in artifacts
    assert not any(k.startswith("logs/") for k in artifacts)
    assert meta["skipped_binary"] == 1


def test_artifacts_caps_large_file(tmp_repo: Path):
    sd = tmp_repo / "session"
    sd.mkdir()
    (sd / "huge.md").write_text("x" * 300_000)  # > _MAX_FILE_BYTES (200K)
    (sd / "tiny.md").write_text("ok")

    artifacts, meta = score_holdout._gather_artifacts(sd)
    assert "tiny.md" in artifacts
    assert "huge.md" not in artifacts
    assert meta["skipped_too_large"] == 1


def test_artifacts_truncates_total_payload(tmp_repo: Path):
    sd = tmp_repo / "session"
    sd.mkdir()
    # Create 6 files at 150KB each = 900KB total; payload cap is 800KB.
    for i in range(6):
        (sd / f"a{i}.md").write_text("x" * 150_000)

    artifacts, meta = score_holdout._gather_artifacts(sd)
    assert len(artifacts) < 6
    assert meta["truncated"] is True


# --- rubric hash hook -------------------------------------------------------


def test_rubric_mismatch_raises_when_version_present(tmp_repo: Path, monkeypatch):
    """If RUBRIC_VERSION is published and judge returns a different
    rubric_hash, the check raises."""
    monkeypatch.setattr(score_holdout, "_current_rubric_version", lambda: "abc123")
    with pytest.raises(score_holdout.JudgeRubricMismatch):
        score_holdout._check_rubric_hash({"score": 4.5, "rubric_hash": "different"})


def test_rubric_match_passes(tmp_repo: Path, monkeypatch):
    monkeypatch.setattr(score_holdout, "_current_rubric_version", lambda: "abc123")
    score_holdout._check_rubric_hash({"score": 4.5, "rubric_hash": "abc123"})


def test_rubric_check_skipped_when_version_unavailable(tmp_repo: Path, monkeypatch):
    """Soft-skip when rubrics module is unreadable — keeps tool runnable
    in environments without the evaluation package installed."""
    monkeypatch.setattr(score_holdout, "_current_rubric_version", lambda: None)
    score_holdout._check_rubric_hash({"score": 4.5, "rubric_hash": "anything"})


def test_rubric_check_no_hash_in_response(tmp_repo: Path, monkeypatch):
    """If RUBRIC_VERSION is set but the judge didn't include rubric_hash,
    we don't enforce — older judge versions may not emit the field."""
    monkeypatch.setattr(score_holdout, "_current_rubric_version", lambda: "abc123")
    score_holdout._check_rubric_hash({"score": 4.5})
