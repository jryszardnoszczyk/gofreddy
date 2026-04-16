"""Tests for agent model override via user preferences."""

from src.common.gemini_models import GEMINI_FLASH, GEMINI_PRICING, GEMINI_PRO
from src.orchestrator.config import AgentSettings
from src.preferences.models import UserPreferences


class TestAgentSettingsModelOverride:
    def test_default_settings_use_flash(self):
        settings = AgentSettings()
        assert settings.model == GEMINI_FLASH

    def test_model_copy_with_pricing_override(self):
        """Agent router passes cost rates explicitly (model_copy skips validators)."""
        settings = AgentSettings()
        pricing = GEMINI_PRICING[GEMINI_PRO]
        overridden = settings.model_copy(update={
            "model": GEMINI_PRO,
            "cost_input_rate_per_million": pricing["text_input"],
            "cost_output_rate_per_million": pricing["output"],
        })
        assert overridden.model == GEMINI_PRO
        assert overridden.cost_input_rate_per_million == 2.00
        assert overridden.cost_output_rate_per_million == 12.00
        assert overridden.max_loop_iterations == settings.max_loop_iterations
        assert overridden.gemini_timeout_seconds == settings.gemini_timeout_seconds

    def test_preferences_default_matches_settings_default(self):
        prefs = UserPreferences()
        settings = AgentSettings()
        assert prefs.agent_model == settings.model
