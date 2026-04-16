"""Tests for freddy evaluate CLI command."""

import json
import os
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from cli.freddy.main import app

runner = CliRunner()


def _mock_genai_module(response_text: str):
    """Build a fake google.genai module with Client and types.

    Returns (mock_genai, mock_client) so tests can inspect calls on mock_client.
    """
    mock_genai = MagicMock()
    mock_client = MagicMock()
    mock_genai.Client.return_value = mock_client
    mock_response = MagicMock()
    mock_response.text = response_text
    mock_client.models.generate_content.return_value = mock_response
    return mock_genai, mock_client


def _make_google_modules(mock_genai):
    """Build the sys.modules dict needed to mock `from google import genai`."""
    mock_types = MagicMock()
    mock_google = MagicMock()
    mock_google.genai = mock_genai
    mock_google.genai.types = mock_types
    return {
        "google": mock_google,
        "google.genai": mock_genai,
        "google.genai.types": mock_types,
    }


VALID_RESPONSE = json.dumps({
    "decision": "KEEP",
    "confidence": 0.8,
    "weaknesses": ["w1", "w2", "w3"],
    "strongest_competitor": "example.com",
    "would_be_cited_over_competitor": True,
    "rationale": "Good content",
})


def _get_prompt(mock_client) -> str:
    """Extract the prompt string sent to generate_content."""
    call_args = mock_client.models.generate_content.call_args
    # The evaluate command uses keyword arg: contents=prompt
    return call_args.kwargs.get("contents", "")


class TestEvaluateCommand:
    def test_missing_api_key(self, tmp_path):
        """Should error when GEMINI_API_KEY is not set."""
        optimized = tmp_path / "test.md"
        optimized.write_text("# Test content")

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("GEMINI_API_KEY", None)
            result = runner.invoke(app, ["evaluate", str(optimized)])

        assert result.exit_code != 0
        output = json.loads(result.stdout.strip())
        assert "error" in output
        assert "GEMINI_API_KEY" in output["error"]

    def test_missing_file(self):
        """Should error when optimized file doesn't exist."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            result = runner.invoke(app, ["evaluate", "/nonexistent/file.md"])

        assert result.exit_code != 0
        output = json.loads(result.stdout.strip())
        assert "error" in output
        assert "not found" in output["error"].lower()

    def test_loads_optimized_file(self, tmp_path):
        """Should read the optimized file and pass its content to the model."""
        optimized = tmp_path / "test.md"
        optimized.write_text("# Optimized Content\nFAQ section here")

        mock_genai, mock_client = _mock_genai_module(VALID_RESPONSE)

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            with patch.dict("sys.modules", _make_google_modules(mock_genai)):
                result = runner.invoke(app, ["evaluate", str(optimized)])

        assert result.exit_code == 0
        output = json.loads(result.stdout.strip())
        assert output["decision"] == "KEEP"

        # Verify the prompt sent to generate_content contains the file content
        prompt_sent = _get_prompt(mock_client)
        assert "Optimized Content" in prompt_sent
        assert "FAQ section here" in prompt_sent

    def test_loads_page_cache(self, tmp_path):
        """Should load original content from page cache JSON into the prompt."""
        optimized = tmp_path / "test.md"
        optimized.write_text("# Optimized")

        cache = tmp_path / "page.json"
        cache.write_text(json.dumps({"text": "Original page content here"}))

        mock_genai, mock_client = _mock_genai_module(VALID_RESPONSE)

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            with patch.dict("sys.modules", _make_google_modules(mock_genai)):
                result = runner.invoke(app, [
                    "evaluate", str(optimized),
                    "--page-cache", str(cache),
                ])

        assert result.exit_code == 0

        # Verify the original content from page cache appears in the prompt
        prompt_sent = _get_prompt(mock_client)
        assert "Original page content here" in prompt_sent

    def test_loads_competitive_data(self, tmp_path):
        """Should load competitive context from file into the prompt."""
        optimized = tmp_path / "test.md"
        optimized.write_text("# Optimized")

        comp = tmp_path / "visibility.json"
        comp.write_text(json.dumps({"query": "test query", "results": {"competitor.com": 0.85}}))

        discard_response = json.dumps({
            "decision": "DISCARD",
            "confidence": 0.7,
            "weaknesses": ["a", "b", "c"],
            "strongest_competitor": "competitor.com",
            "would_be_cited_over_competitor": False,
            "rationale": "Weak competitive positioning",
        })

        mock_genai, mock_client = _mock_genai_module(discard_response)

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            with patch.dict("sys.modules", _make_google_modules(mock_genai)):
                result = runner.invoke(app, [
                    "evaluate", str(optimized),
                    "--competitive", str(comp),
                ])

        assert result.exit_code == 0
        output = json.loads(result.stdout.strip())
        assert output["decision"] == "DISCARD"

        # Verify competitive data appears in the prompt
        prompt_sent = _get_prompt(mock_client)
        assert "test query" in prompt_sent
        assert "competitor.com" in prompt_sent

    def test_no_page_cache_uses_fallback_text(self, tmp_path):
        """Without page cache, prompt should contain fallback original content text."""
        optimized = tmp_path / "test.md"
        optimized.write_text("# Optimized")

        mock_genai, mock_client = _mock_genai_module(VALID_RESPONSE)

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            with patch.dict("sys.modules", _make_google_modules(mock_genai)):
                result = runner.invoke(app, ["evaluate", str(optimized)])

        assert result.exit_code == 0

        prompt_sent = _get_prompt(mock_client)
        assert "Original content not available." in prompt_sent

    def test_no_competitive_data_uses_fallback(self, tmp_path):
        """Without competitive file, prompt should contain fallback competitive text."""
        optimized = tmp_path / "test.md"
        optimized.write_text("# Optimized")

        mock_genai, mock_client = _mock_genai_module(VALID_RESPONSE)

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            with patch.dict("sys.modules", _make_google_modules(mock_genai)):
                result = runner.invoke(app, ["evaluate", str(optimized)])

        assert result.exit_code == 0

        prompt_sent = _get_prompt(mock_client)
        assert "No competitive data available." in prompt_sent

    def test_gemini_import_error(self, tmp_path):
        """Should handle missing google-genai package gracefully."""
        optimized = tmp_path / "test.md"
        optimized.write_text("# Test")

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            with patch.dict(
                "sys.modules",
                {"google": None, "google.genai": None, "google.genai.types": None},
            ):
                result = runner.invoke(app, ["evaluate", str(optimized)])

        assert result.exit_code != 0
        output = json.loads(result.stdout.strip())
        assert "error" in output
        assert "not installed" in output["error"].lower() or "genai" in output["error"].lower()

    def test_gemini_api_error(self, tmp_path):
        """Should handle Gemini API errors and return fallback JSON."""
        optimized = tmp_path / "test.md"
        optimized.write_text("# Test")

        mock_genai = MagicMock()
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        mock_client.models.generate_content.side_effect = RuntimeError("API quota exceeded")

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            with patch.dict("sys.modules", _make_google_modules(mock_genai)):
                result = runner.invoke(app, ["evaluate", str(optimized)])

        assert result.exit_code != 0
        output = json.loads(result.stdout.strip())
        assert "error" in output
        assert output["error"] == "Evaluation failed"
        assert output.get("fallback") == "self-evaluate"
