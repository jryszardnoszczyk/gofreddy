"""Tests for monitoring CLI commands — mock api_request, verify endpoints and params."""

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from cli.freddy.main import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def mock_config():
    """Mock load_config to return a fake config for all CLI tests."""
    fake_config = MagicMock()
    fake_config.api_key = "test-key"
    fake_config.base_url = "http://localhost:8080"
    with patch("cli.freddy.commands.monitor.load_config", return_value=fake_config), \
         patch("cli.freddy.commands.search_mentions.load_config", return_value=fake_config), \
         patch("cli.freddy.commands.trends.load_config", return_value=fake_config), \
         patch("cli.freddy.commands.digest.load_config", return_value=fake_config):
        yield fake_config


class TestMonitorMentions:
    @patch("cli.freddy.commands.monitor.make_client")
    @patch("cli.freddy.commands.monitor.api_request")
    def test_mentions_basic(self, mock_api, mock_client, mock_config):
        mock_api.return_value = {"mentions": [{"id": "1", "content": "test"}]}
        result = runner.invoke(app, ["monitor", "mentions", "abc-123"])
        assert result.exit_code == 0
        mock_api.assert_called_once()
        call_args = mock_api.call_args
        assert "/v1/monitors/abc-123/mentions" in call_args.args[2]

    @patch("cli.freddy.commands.monitor.make_client")
    @patch("cli.freddy.commands.monitor.api_request")
    def test_mentions_with_dates(self, mock_api, mock_client, mock_config):
        mock_api.return_value = {"mentions": []}
        result = runner.invoke(app, [
            "monitor", "mentions", "abc-123",
            "--date-from", "2026-03-10",
            "--date-to", "2026-03-17",
        ])
        assert result.exit_code == 0
        call_kwargs = mock_api.call_args.kwargs
        assert call_kwargs["params"]["date_from"] == "2026-03-10"
        assert call_kwargs["params"]["date_to"] == "2026-03-17"

    @patch("cli.freddy.commands.monitor.make_client")
    @patch("cli.freddy.commands.monitor.api_request")
    def test_mentions_auto_pagination(self, mock_api, mock_client, mock_config):
        """Auto-pagination fetches multiple pages."""
        page1 = {"mentions": [{"id": str(i)} for i in range(50)]}
        page2 = {"mentions": [{"id": str(i)} for i in range(50, 80)]}
        mock_api.side_effect = [page1, page2]
        result = runner.invoke(app, ["monitor", "mentions", "abc-123"])
        assert result.exit_code == 0
        assert mock_api.call_count == 2


class TestMonitorSentiment:
    @patch("cli.freddy.commands.monitor.make_client")
    @patch("cli.freddy.commands.monitor.api_request")
    def test_sentiment_basic(self, mock_api, mock_client, mock_config):
        mock_api.return_value = {"buckets": []}
        result = runner.invoke(app, ["monitor", "sentiment", "abc-123"])
        assert result.exit_code == 0
        call_args = mock_api.call_args
        assert "/v1/monitors/abc-123/sentiment" in call_args.args[2]


class TestMonitorSOV:
    @patch("cli.freddy.commands.monitor.make_client")
    @patch("cli.freddy.commands.monitor.api_request")
    def test_sov_basic(self, mock_api, mock_client, mock_config):
        mock_api.return_value = {"entries": []}
        result = runner.invoke(app, ["monitor", "sov", "abc-123"])
        assert result.exit_code == 0
        call_args = mock_api.call_args
        assert "/v1/monitors/abc-123/share-of-voice" in call_args.args[2]


class TestMonitorTopics:
    @patch("cli.freddy.commands.monitor.make_client")
    @patch("cli.freddy.commands.monitor.api_request")
    def test_topics_basic(self, mock_api, mock_client, mock_config):
        mock_api.return_value = {"clusters": []}
        result = runner.invoke(app, ["monitor", "topics", "abc-123"])
        assert result.exit_code == 0
        call_args = mock_api.call_args
        assert "/v1/monitors/abc-123/topics" in call_args.args[2]


class TestSearchMentions:
    @patch("cli.freddy.commands.search_mentions.make_client")
    @patch("cli.freddy.commands.search_mentions.api_request")
    def test_search_basic(self, mock_api, mock_client, mock_config):
        mock_api.return_value = {"mentions": []}
        result = runner.invoke(app, ["search-mentions", "abc-123", "pricing complaints"])
        assert result.exit_code == 0
        call_kwargs = mock_api.call_args.kwargs
        assert call_kwargs["params"]["q"] == "pricing complaints"

    @patch("cli.freddy.commands.search_mentions.make_client")
    @patch("cli.freddy.commands.search_mentions.api_request")
    def test_search_with_filters(self, mock_api, mock_client, mock_config):
        mock_api.return_value = {"mentions": []}
        result = runner.invoke(app, [
            "search-mentions", "abc-123", "pricing",
            "--source", "reddit",
            "--sentiment", "negative",
        ])
        assert result.exit_code == 0
        call_kwargs = mock_api.call_args.kwargs
        assert call_kwargs["params"]["source"] == "reddit"
        assert call_kwargs["params"]["sentiment"] == "negative"


class TestTrends:
    @patch("cli.freddy.commands.trends.make_client")
    @patch("cli.freddy.commands.trends.api_request")
    def test_trends_basic(self, mock_api, mock_client, mock_config):
        mock_api.return_value = {"buckets": [], "correlation_coefficient": None}
        result = runner.invoke(app, ["trends", "abc-123"])
        assert result.exit_code == 0
        call_args = mock_api.call_args
        assert "/v1/monitors/abc-123/trends-correlation" in call_args.args[2]
        assert mock_api.call_args.kwargs["params"]["window_days"] == 30

    @patch("cli.freddy.commands.trends.make_client")
    @patch("cli.freddy.commands.trends.api_request")
    def test_trends_custom_window(self, mock_api, mock_client, mock_config):
        mock_api.return_value = {"buckets": []}
        result = runner.invoke(app, ["trends", "abc-123", "--window", "7d"])
        assert result.exit_code == 0
        assert mock_api.call_args.kwargs["params"]["window_days"] == 7


class TestDigestPersist:
    @patch("cli.freddy.commands.digest.make_client")
    @patch("cli.freddy.commands.digest.api_request")
    def test_persist(self, mock_api, mock_client, mock_config, tmp_path):
        meta_file = tmp_path / "digest-meta.json"
        meta_file.write_text('{"week_ending": "2026-03-17", "stories": []}')
        mock_api.return_value = {"id": "uuid-123", "week_ending": "2026-03-17"}
        result = runner.invoke(app, ["digest", "persist", "abc-123", "--file", str(meta_file)])
        assert result.exit_code == 0
        call_args = mock_api.call_args
        assert "/v1/monitors/abc-123/digests" in call_args.args[2]
        assert call_args.kwargs["json_data"]["week_ending"] == "2026-03-17"
