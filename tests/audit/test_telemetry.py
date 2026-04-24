"""Audit telemetry: JSONL append semantics + Slack notifier contract."""
from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from src.audit import telemetry


class TestAppend:
    def test_writes_single_jsonl_line(self, tmp_path: Path) -> None:
        events = tmp_path / "events.jsonl"
        telemetry.append(events, "stage_complete", stage="stage_1a", duration_s=12.3)

        content = events.read_text()
        assert content.count("\n") == 1
        record = json.loads(content.strip())
        assert record["event"] == "stage_complete"
        assert record["stage"] == "stage_1a"
        assert record["duration_s"] == 12.3
        assert "ts" in record  # auto-stamped

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        events = tmp_path / "clients" / "acme" / "audit" / "events.jsonl"
        telemetry.append(events, "start")
        assert events.exists()

    def test_appends_to_existing_log_preserving_prior_lines(self, tmp_path: Path) -> None:
        events = tmp_path / "events.jsonl"
        telemetry.append(events, "one", n=1)
        telemetry.append(events, "two", n=2)
        telemetry.append(events, "three", n=3)

        lines = events.read_text().strip().split("\n")
        assert len(lines) == 3
        assert [json.loads(line)["n"] for line in lines] == [1, 2, 3]

    def test_timestamp_is_utc_iso(self, tmp_path: Path) -> None:
        events = tmp_path / "events.jsonl"
        telemetry.append(events, "x")
        record = json.loads(events.read_text().strip())
        # +00:00 suffix → UTC. ISO-8601 format.
        assert record["ts"].endswith("+00:00")

    def test_non_json_payload_coerced_via_default_str(self, tmp_path: Path) -> None:
        from datetime import datetime
        events = tmp_path / "events.jsonl"
        telemetry.append(events, "x", when=datetime(2026, 4, 24, 2, 30, 0))
        record = json.loads(events.read_text().strip())
        assert record["when"] == "2026-04-24 02:30:00"


class TestNotifySlack:
    def test_returns_false_when_no_webhook_configured(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("AUDIT_SLACK_WEBHOOK_URL", raising=False)
        assert telemetry.notify_slack("hello") is False

    def test_returns_false_on_network_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def raise_connect_error(*args, **kwargs):  # type: ignore[no-untyped-def]
            raise httpx.ConnectError("no route")

        monkeypatch.setattr("httpx.Client.post", raise_connect_error)
        assert telemetry.notify_slack("hi", webhook_url="https://slack.test/x") is False

    def test_returns_false_on_non_2xx_response(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def fake_post(self, url, **kwargs):  # type: ignore[no-untyped-def]
            return httpx.Response(500, text="server error")

        monkeypatch.setattr("httpx.Client.post", fake_post)
        assert telemetry.notify_slack("hi", webhook_url="https://slack.test/x") is False

    def test_returns_true_on_2xx_response(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        captured: dict = {}

        def fake_post(self, url, **kwargs):  # type: ignore[no-untyped-def]
            captured["url"] = url
            captured["json"] = kwargs.get("json")
            return httpx.Response(200, text="ok")

        monkeypatch.setattr("httpx.Client.post", fake_post)
        assert telemetry.notify_slack("hello world", webhook_url="https://slack.test/x") is True
        assert captured["url"] == "https://slack.test/x"
        assert captured["json"] == {"text": "hello world"}

    def test_explicit_url_beats_env_var(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        captured: dict = {}

        def fake_post(self, url, **kwargs):  # type: ignore[no-untyped-def]
            captured["url"] = url
            return httpx.Response(200)

        monkeypatch.setenv("AUDIT_SLACK_WEBHOOK_URL", "https://env.test/x")
        monkeypatch.setattr("httpx.Client.post", fake_post)

        telemetry.notify_slack("hi", webhook_url="https://explicit.test/y")
        assert captured["url"] == "https://explicit.test/y"


class TestCompositeHelpers:
    def test_record_cost_breaker_writes_event_and_attempts_slack(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("AUDIT_SLACK_WEBHOOK_URL", raising=False)
        events = tmp_path / "events.jsonl"

        telemetry.record_cost_breaker(
            events,
            client_slug="acme",
            spent_usd=152.38,
            ceiling_usd=150.0,
            current_stage="stage_2",
        )
        record = json.loads(events.read_text().strip())
        assert record["event"] == "cost_breaker_tripped"
        assert record["client_slug"] == "acme"
        assert record["spent_usd"] == 152.38
        assert record["current_stage"] == "stage_2"

    def test_record_preflight_gate_captures_threshold_data(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("AUDIT_SLACK_WEBHOOK_URL", raising=False)
        events = tmp_path / "events.jsonl"

        telemetry.record_preflight_gate(
            events,
            client_slug="suspect",
            reason="sitemap_too_large",
            sitemap_urls=1200,
            subdomains=42,
            domain_age_days=14,
        )
        record = json.loads(events.read_text().strip())
        assert record["event"] == "preflight_gate_blocked"
        assert record["reason"] == "sitemap_too_large"
        assert record["sitemap_urls"] == 1200
        assert record["domain_age_days"] == 14

    def test_record_audit_complete_captures_summary(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("AUDIT_SLACK_WEBHOOK_URL", raising=False)
        events = tmp_path / "events.jsonl"

        telemetry.record_audit_complete(
            events,
            client_slug="acme",
            total_cost_usd=87.43,
            duration_s=412.7,
            finding_count=28,
            health_score=72,
            band="green",
        )
        record = json.loads(events.read_text().strip())
        assert record["event"] == "audit_complete"
        assert record["finding_count"] == 28
        assert record["health_score"] == 72
        assert record["band"] == "green"
        assert record["total_cost_usd"] == 87.43
