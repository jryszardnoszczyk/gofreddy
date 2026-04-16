"""Tests for PR-109 CLI commands — publish extensions, write, calendar, articles,
newsletter, media, rank, seo, competitive.

Mock api_request/make_client, verify endpoints, params, and payloads.
"""

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from cli.freddy.main import app

runner = CliRunner()


def _fake_config():
    cfg = MagicMock()
    cfg.api_key = "test-key"
    cfg.base_url = "http://localhost:8080"
    return cfg


# ---------------------------------------------------------------------------
# Publish group — 5 new commands
# ---------------------------------------------------------------------------

class TestPublishList:
    @patch("cli.freddy.commands.publish.make_client")
    @patch("cli.freddy.commands.publish.api_request")
    @patch("cli.freddy.commands.publish.load_config", return_value=_fake_config())
    def test_list_basic(self, _cfg, mock_api, _client):
        mock_api.return_value = {"items": []}
        result = runner.invoke(app, ["publish", "list"])
        assert result.exit_code == 0
        assert mock_api.call_args.args[2] == "/v1/publish/queue"

    @patch("cli.freddy.commands.publish.make_client")
    @patch("cli.freddy.commands.publish.api_request")
    @patch("cli.freddy.commands.publish.load_config", return_value=_fake_config())
    def test_list_with_filters(self, _cfg, mock_api, _client):
        mock_api.return_value = {"items": []}
        result = runner.invoke(app, ["publish", "list", "--status", "draft", "--tag", "seo"])
        assert result.exit_code == 0
        params = mock_api.call_args.kwargs["params"]
        assert params["status"] == "draft"
        assert params["tag"] == "seo"


class TestPublishApprove:
    @patch("cli.freddy.commands.publish.make_client")
    @patch("cli.freddy.commands.publish.api_request")
    @patch("cli.freddy.commands.publish.load_config", return_value=_fake_config())
    def test_approve(self, _cfg, mock_api, _client):
        mock_api.return_value = {"status": "approved"}
        result = runner.invoke(app, ["publish", "approve", "draft-uuid"])
        assert result.exit_code == 0
        assert "/v1/publish/drafts/draft-uuid/approve" in mock_api.call_args.args[2]


class TestPublishSchedule:
    @patch("cli.freddy.commands.publish.make_client")
    @patch("cli.freddy.commands.publish.api_request")
    @patch("cli.freddy.commands.publish.load_config", return_value=_fake_config())
    def test_schedule_valid(self, _cfg, mock_api, _client):
        mock_api.return_value = {"status": "scheduled"}
        result = runner.invoke(app, ["publish", "schedule", "draft-uuid", "--at", "2026-04-15T10:00:00"])
        assert result.exit_code == 0
        assert mock_api.call_args.kwargs["json_data"]["scheduled_at"] == "2026-04-15T10:00:00"

    @patch("cli.freddy.commands.publish.load_config", return_value=_fake_config())
    def test_schedule_invalid_datetime(self, _cfg):
        result = runner.invoke(app, ["publish", "schedule", "draft-uuid", "--at", "not-a-date"])
        assert result.exit_code == 1


class TestPublishDispatch:
    @patch("cli.freddy.commands.publish.make_client")
    @patch("cli.freddy.commands.publish.api_request")
    @patch("cli.freddy.commands.publish.load_config", return_value=_fake_config())
    def test_dispatch(self, _cfg, mock_api, _client):
        mock_api.return_value = {"dispatched": 3}
        result = runner.invoke(app, ["publish", "dispatch"])
        assert result.exit_code == 0
        assert mock_api.call_args.args[2] == "/v1/publish/dispatch"


class TestPublishDelete:
    @patch("cli.freddy.commands.publish.make_client")
    @patch("cli.freddy.commands.publish.api_request")
    @patch("cli.freddy.commands.publish.load_config", return_value=_fake_config())
    def test_delete(self, _cfg, mock_api, _client):
        mock_api.return_value = {}
        result = runner.invoke(app, ["publish", "delete", "draft-uuid"])
        assert result.exit_code == 0
        assert mock_api.call_args.args[1] == "DELETE"


# ---------------------------------------------------------------------------
# Write group
# ---------------------------------------------------------------------------

class TestWriteFromDigest:
    @patch("cli.freddy.commands.write.make_client")
    @patch("cli.freddy.commands.write.api_request")
    @patch("cli.freddy.commands.write.load_config", return_value=_fake_config())
    def test_from_digest(self, _cfg, mock_api, _client):
        mock_api.return_value = {"draft_id": "d1"}
        result = runner.invoke(app, [
            "write", "from-digest",
            "--monitor-id", "mon-uuid",
            "--platforms", "linkedin,x",
        ])
        assert result.exit_code == 0
        body = mock_api.call_args.kwargs["json_data"]
        assert body["source"] == "monitoring"
        assert body["platforms"] == ["linkedin", "x"]
        assert body["monitor_id"] == "mon-uuid"


class TestWriteFromReport:
    @patch("cli.freddy.commands.write.make_client")
    @patch("cli.freddy.commands.write.api_request")
    @patch("cli.freddy.commands.write.load_config", return_value=_fake_config())
    def test_from_report(self, _cfg, mock_api, _client):
        mock_api.return_value = {"draft_id": "d2"}
        result = runner.invoke(app, [
            "write", "from-report",
            "--session-dir", "/tmp/session",
            "--type", "seo_recommendations",
        ])
        assert result.exit_code == 0
        body = mock_api.call_args.kwargs["json_data"]
        assert body["source"] == "report"
        assert body["report_type"] == "seo_recommendations"


# ---------------------------------------------------------------------------
# Calendar group
# ---------------------------------------------------------------------------

class TestCalendarView:
    @patch("cli.freddy.commands.calendar.make_client")
    @patch("cli.freddy.commands.calendar.api_request")
    @patch("cli.freddy.commands.calendar.load_config", return_value=_fake_config())
    def test_view_with_month(self, _cfg, mock_api, _client):
        mock_api.return_value = {"items": []}
        result = runner.invoke(app, ["calendar", "view", "--month", "2026-04"])
        assert result.exit_code == 0
        params = mock_api.call_args.kwargs["params"]
        assert params["scheduled_after"] == "2026-04-01T00:00:00Z"
        assert params["scheduled_before"] == "2026-04-30T23:59:59Z"
        assert params["status"] == "scheduled"

    @patch("cli.freddy.commands.calendar.make_client")
    @patch("cli.freddy.commands.calendar.api_request")
    @patch("cli.freddy.commands.calendar.load_config", return_value=_fake_config())
    def test_view_february(self, _cfg, mock_api, _client):
        mock_api.return_value = {"items": []}
        result = runner.invoke(app, ["calendar", "view", "--month", "2026-02"])
        assert result.exit_code == 0
        params = mock_api.call_args.kwargs["params"]
        assert params["scheduled_before"] == "2026-02-28T23:59:59Z"

    @patch("cli.freddy.commands.calendar.make_client")
    @patch("cli.freddy.commands.calendar.api_request")
    @patch("cli.freddy.commands.calendar.load_config", return_value=_fake_config())
    def test_view_leap_year(self, _cfg, mock_api, _client):
        mock_api.return_value = {"items": []}
        result = runner.invoke(app, ["calendar", "view", "--month", "2028-02"])
        assert result.exit_code == 0
        params = mock_api.call_args.kwargs["params"]
        assert params["scheduled_before"] == "2028-02-29T23:59:59Z"

    @patch("cli.freddy.commands.calendar.load_config", return_value=_fake_config())
    def test_view_invalid_month(self, _cfg):
        result = runner.invoke(app, ["calendar", "view", "--month", "invalid"])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# Articles group
# ---------------------------------------------------------------------------

class TestArticlesGenerate:
    @patch("cli.freddy.commands.articles.make_client")
    @patch("cli.freddy.commands.articles.api_request")
    @patch("cli.freddy.commands.articles.load_config", return_value=_fake_config())
    def test_generate(self, _cfg, mock_api, mock_client):
        mock_client.return_value = MagicMock()
        mock_api.return_value = {"article_id": "a1"}
        result = runner.invoke(app, [
            "articles", "generate",
            "--url", "https://example.com/post",
            "--keywords", "seo,marketing",
        ])
        assert result.exit_code == 0
        body = mock_api.call_args.kwargs["json_data"]
        assert body["source_url"] == "https://example.com/post"
        assert body["keywords"] == ["seo", "marketing"]


class TestArticlesList:
    @patch("cli.freddy.commands.articles.make_client")
    @patch("cli.freddy.commands.articles.api_request")
    @patch("cli.freddy.commands.articles.load_config", return_value=_fake_config())
    def test_list(self, _cfg, mock_api, _client):
        mock_api.return_value = {"articles": []}
        result = runner.invoke(app, ["articles", "list"])
        assert result.exit_code == 0
        assert mock_api.call_args.args[2] == "/v1/articles"


class TestArticlesPerformance:
    @patch("cli.freddy.commands.articles.make_client")
    @patch("cli.freddy.commands.articles.api_request")
    @patch("cli.freddy.commands.articles.load_config", return_value=_fake_config())
    def test_performance(self, _cfg, mock_api, _client):
        mock_api.return_value = {"clicks": 100}
        result = runner.invoke(app, ["articles", "performance", "art-uuid"])
        assert result.exit_code == 0
        assert "/v1/articles/art-uuid/performance" in mock_api.call_args.args[2]


# ---------------------------------------------------------------------------
# Newsletter group
# ---------------------------------------------------------------------------

class TestNewsletterSubscribe:
    @patch("cli.freddy.commands.newsletter.make_client")
    @patch("cli.freddy.commands.newsletter.api_request")
    @patch("cli.freddy.commands.newsletter.load_config", return_value=_fake_config())
    def test_subscribe(self, _cfg, mock_api, _client):
        mock_api.return_value = {"id": "sub1"}
        result = runner.invoke(app, [
            "newsletter", "subscribe",
            "--email", "test@example.com",
            "--name", "Test User",
        ])
        assert result.exit_code == 0
        body = mock_api.call_args.kwargs["json_data"]
        assert body["email"] == "test@example.com"
        assert body["name"] == "Test User"


class TestNewsletterSend:
    @patch("cli.freddy.commands.newsletter.make_client")
    @patch("cli.freddy.commands.newsletter.api_request")
    @patch("cli.freddy.commands.newsletter.load_config", return_value=_fake_config())
    def test_send_from_digest(self, _cfg, mock_api, _client):
        mock_api.return_value = {"sent": True}
        result = runner.invoke(app, [
            "newsletter", "send",
            "--from-digest", "--monitor-id", "mon-uuid",
        ])
        assert result.exit_code == 0
        body = mock_api.call_args.kwargs["json_data"]
        assert body["from_digest"] is True
        assert body["monitor_id"] == "mon-uuid"

    @patch("cli.freddy.commands.newsletter.make_client")
    @patch("cli.freddy.commands.newsletter.api_request")
    @patch("cli.freddy.commands.newsletter.load_config", return_value=_fake_config())
    def test_send_explicit(self, _cfg, mock_api, _client, tmp_path):
        html_file = tmp_path / "email.html"
        html_file.write_text("<h1>Hello</h1>")
        mock_api.return_value = {"sent": True}
        result = runner.invoke(app, [
            "newsletter", "send",
            "--segment", "pro",
            "--subject", "Weekly Update",
            "--html-file", str(html_file),
        ])
        assert result.exit_code == 0
        body = mock_api.call_args.kwargs["json_data"]
        assert body["segment"] == "pro"
        assert body["html_body"] == "<h1>Hello</h1>"

    @patch("cli.freddy.commands.newsletter.load_config", return_value=_fake_config())
    def test_send_no_mode_errors(self, _cfg):
        """Neither explicit nor digest mode specified."""
        result = runner.invoke(app, ["newsletter", "send"])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# Media group
# ---------------------------------------------------------------------------

class TestMediaUpload:
    @patch("cli.freddy.commands.media.load_config", return_value=_fake_config())
    def test_upload_missing_file(self, _cfg):
        result = runner.invoke(app, ["media", "upload", "/nonexistent/file.png"])
        assert result.exit_code == 1

    @patch("cli.freddy.commands.media.load_config", return_value=_fake_config())
    def test_upload_oversized_file(self, _cfg, tmp_path):
        big_file = tmp_path / "big.bin"
        # Create a file just over 100MB by writing the size marker
        big_file.write_bytes(b"\0")
        with patch("pathlib.Path.stat") as mock_stat:
            mock_stat.return_value = MagicMock(st_size=101 * 1024 * 1024)
            with patch("pathlib.Path.is_file", return_value=True):
                result = runner.invoke(app, ["media", "upload", str(big_file)])
                assert result.exit_code == 1


class TestMediaList:
    @patch("cli.freddy.commands.media.make_client")
    @patch("cli.freddy.commands.media.api_request")
    @patch("cli.freddy.commands.media.load_config", return_value=_fake_config())
    def test_list(self, _cfg, mock_api, _client):
        mock_api.return_value = {"assets": []}
        result = runner.invoke(app, ["media", "list"])
        assert result.exit_code == 0
        assert mock_api.call_args.args[2] == "/v1/media"


class TestMediaSearch:
    @patch("cli.freddy.commands.media.make_client")
    @patch("cli.freddy.commands.media.api_request")
    @patch("cli.freddy.commands.media.load_config", return_value=_fake_config())
    def test_search(self, _cfg, mock_api, _client):
        mock_api.return_value = {"assets": []}
        result = runner.invoke(app, ["media", "search", "--tag", "logo"])
        assert result.exit_code == 0
        assert mock_api.call_args.kwargs["params"]["tag"] == "logo"


class TestMediaDelete:
    @patch("cli.freddy.commands.media.make_client")
    @patch("cli.freddy.commands.media.api_request")
    @patch("cli.freddy.commands.media.load_config", return_value=_fake_config())
    def test_delete(self, _cfg, mock_api, _client):
        mock_api.return_value = {}
        result = runner.invoke(app, ["media", "delete", "asset-uuid"])
        assert result.exit_code == 0
        assert mock_api.call_args.args[1] == "DELETE"


class TestMediaUrl:
    @patch("cli.freddy.commands.media.make_client")
    @patch("cli.freddy.commands.media.api_request")
    @patch("cli.freddy.commands.media.load_config", return_value=_fake_config())
    def test_url(self, _cfg, mock_api, _client):
        mock_api.return_value = {"url": "https://cdn.example.com/file.png", "expires_in": 3600}
        result = runner.invoke(app, ["media", "url", "asset-uuid"])
        assert result.exit_code == 0
        assert "/v1/media/asset-uuid/url" in mock_api.call_args.args[2]


# ---------------------------------------------------------------------------
# Rank group
# ---------------------------------------------------------------------------

class TestRankSnapshot:
    @patch("cli.freddy.commands.rank.make_client")
    @patch("cli.freddy.commands.rank.api_request")
    @patch("cli.freddy.commands.rank.load_config", return_value=_fake_config())
    def test_snapshot(self, _cfg, mock_api, _client):
        mock_api.return_value = {"rank": 42}
        result = runner.invoke(app, ["rank", "snapshot", "--domain", "example.com"])
        assert result.exit_code == 0
        body = mock_api.call_args.kwargs["json_data"]
        assert body["domain"] == "example.com"

    @patch("cli.freddy.commands.rank.make_client")
    @patch("cli.freddy.commands.rank.api_request")
    @patch("cli.freddy.commands.rank.load_config", return_value=_fake_config())
    def test_snapshot_no_domain(self, _cfg, mock_api, _client):
        mock_api.return_value = {"rank": 42}
        result = runner.invoke(app, ["rank", "snapshot"])
        assert result.exit_code == 0
        body = mock_api.call_args.kwargs["json_data"]
        assert body == {}


class TestRankHistory:
    @patch("cli.freddy.commands.rank.make_client")
    @patch("cli.freddy.commands.rank.api_request")
    @patch("cli.freddy.commands.rank.load_config", return_value=_fake_config())
    def test_history(self, _cfg, mock_api, _client):
        mock_api.return_value = {"snapshots": []}
        result = runner.invoke(app, ["rank", "history", "--days", "30"])
        assert result.exit_code == 0
        assert mock_api.call_args.kwargs["params"]["days"] == 30


# ---------------------------------------------------------------------------
# SEO group
# ---------------------------------------------------------------------------

class TestSeoKeywords:
    @patch("cli.freddy.commands.seo.make_client")
    @patch("cli.freddy.commands.seo.api_request")
    @patch("cli.freddy.commands.seo.load_config", return_value=_fake_config())
    def test_keywords(self, _cfg, mock_api, _client):
        mock_api.return_value = {"keywords": []}
        result = runner.invoke(app, ["seo", "keywords", "--seed", "marketing"])
        assert result.exit_code == 0
        body = mock_api.call_args.kwargs["json_data"]
        assert body["seed_keyword"] == "marketing"
        assert body["limit"] == 50


class TestSeoOptimize:
    @patch("cli.freddy.commands.seo.make_client")
    @patch("cli.freddy.commands.seo.api_request")
    @patch("cli.freddy.commands.seo.load_config", return_value=_fake_config())
    def test_optimize(self, _cfg, mock_api, mock_client):
        mock_client.return_value = MagicMock()
        mock_api.return_value = {"recommendations": []}
        result = runner.invoke(app, [
            "seo", "optimize",
            "--url", "https://example.com/page",
            "--query", "best marketing tools",
        ])
        assert result.exit_code == 0
        body = mock_api.call_args.kwargs["json_data"]
        assert body["action"] == "optimize"
        assert body["url"] == "https://example.com/page"
        assert body["query"] == "best marketing tools"


# ---------------------------------------------------------------------------
# Competitive group
# ---------------------------------------------------------------------------

class TestCompetitiveBrief:
    @patch("cli.freddy.commands.competitive.make_client")
    @patch("cli.freddy.commands.competitive.api_request")
    @patch("cli.freddy.commands.competitive.load_config", return_value=_fake_config())
    def test_brief(self, _cfg, mock_api, mock_client):
        mock_client.return_value = MagicMock()
        mock_api.return_value = {"brief": "..."}
        result = runner.invoke(app, ["competitive", "brief", "--domain", "competitor.com"])
        assert result.exit_code == 0
        body = mock_api.call_args.kwargs["json_data"]
        assert body["domain"] == "competitor.com"


# ---------------------------------------------------------------------------
# Registration test — all new groups appear in app
# ---------------------------------------------------------------------------

class TestMainRegistration:
    def test_all_new_groups_registered(self):
        """Verify all 8 new command groups are registered in the app."""
        from cli.freddy.commands import (
            articles, calendar, competitive, media, newsletter, rank, seo, write,
        )
        # All modules should import without error and have an app attribute
        for mod in [articles, calendar, competitive, media, newsletter, rank, seo, write]:
            assert hasattr(mod, "app"), f"{mod.__name__} missing app attribute"
