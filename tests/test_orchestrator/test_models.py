"""Tests for AgentResponse model."""

from src.orchestrator.models import AgentResponse


class TestAgentResponse:
    """Test AgentResponse construction and serialization."""

    def test_construct_all_fields(self):
        response = AgentResponse(
            text="Analysis complete",
            actions_taken=["search_videos", "analyze_video"],
            tool_results=[{"tool": "search", "count": 5}],
            cost_usd=0.05,
            gemini_calls=3,
        )
        assert response.text == "Analysis complete"
        assert response.actions_taken == ["search_videos", "analyze_video"]
        assert response.tool_results == [{"tool": "search", "count": 5}]
        assert response.cost_usd == 0.05
        assert response.gemini_calls == 3

    def test_default_values(self):
        response = AgentResponse(text="Hello")
        assert response.actions_taken == []
        assert response.tool_results == []
        assert response.cost_usd == 0.0
        assert response.gemini_calls == 0

    def test_serializes_to_dict(self):
        response = AgentResponse(
            text="Done",
            actions_taken=["analyze_video"],
            cost_usd=0.01,
            gemini_calls=1,
        )
        data = response.model_dump()
        assert data["text"] == "Done"
        assert data["actions_taken"] == ["analyze_video"]
        assert data["tool_results"] == []
        assert data["cost_usd"] == 0.01
        assert data["gemini_calls"] == 1

    def test_serializes_to_json(self):
        response = AgentResponse(text="Test")
        json_str = response.model_dump_json()
        assert '"text":"Test"' in json_str or '"text": "Test"' in json_str
