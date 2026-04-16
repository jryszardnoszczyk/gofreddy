from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from cli.freddy.main import app


runner = CliRunner()


def test_critique_command_reads_stdin_and_posts_payload() -> None:
    request_payload = {
        "criteria": [
            {
                "criterion_id": "GEO-1",
                "rubric_prompt": "Judge GEO-1",
                "output_text": "Direct answer block",
                "source_text": "Original page",
                "scoring_type": "gradient",
            }
        ]
    }
    response_payload = {
        "results": [
            {
                "criterion_id": "GEO-1",
                "scoring_type": "gradient",
                "raw_score": 4,
                "normalized_score": 0.75,
                "reasoning": "Specific answer block.",
                "evidence": ["Direct answer block"],
                "model": "judge-model",
            }
        ]
    }

    mock_client = MagicMock()
    mock_response = MagicMock(status_code=200)
    mock_response.json.return_value = response_payload
    mock_client.request.return_value = mock_response

    with patch("cli.freddy.config.load_config", return_value=MagicMock()):
        with patch("cli.freddy.api.make_client", return_value=mock_client):
            result = runner.invoke(
                app,
                ["evaluate", "critique", "-"],
                input=json.dumps(request_payload),
            )

    assert result.exit_code == 0
    assert json.loads(result.stdout) == response_payload
    assert mock_client.request.call_args.kwargs["json"] == request_payload
