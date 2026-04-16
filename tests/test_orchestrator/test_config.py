"""Tests for AgentSettings configuration."""

import pytest
from pydantic import ValidationError

from src.common.gemini_models import GEMINI_FLASH
from src.orchestrator.config import AgentSettings


class TestAgentSettingsDefaults:
    """Test AgentSettings loads with default values (no env vars required)."""

    def test_defaults_no_env_vars(self):
        """All fields have defaults — no AGENT_* env vars required."""
        settings = AgentSettings()

        assert settings.model == GEMINI_FLASH
        assert settings.max_loop_iterations == 10
        assert settings.cost_limit_usd == 1.5
        assert settings.tool_timeout_seconds == 120
        assert settings.gemini_timeout_seconds == 60
        assert settings.overall_timeout_seconds == 240


class TestAgentSettingsEnvOverrides:
    """Test AgentSettings loads from AGENT_* env vars."""

    def test_model_override(self, monkeypatch):
        monkeypatch.setenv("AGENT_MODEL", GEMINI_FLASH)
        settings = AgentSettings()
        assert settings.model == GEMINI_FLASH

    def test_max_loop_iterations_override(self, monkeypatch):
        monkeypatch.setenv("AGENT_MAX_LOOP_ITERATIONS", "5")
        settings = AgentSettings()
        assert settings.max_loop_iterations == 5

    def test_cost_limit_override(self, monkeypatch):
        monkeypatch.setenv("AGENT_COST_LIMIT_USD", "5.0")
        settings = AgentSettings()
        assert settings.cost_limit_usd == 5.0

    def test_overall_timeout_override(self, monkeypatch):
        monkeypatch.setenv("AGENT_OVERALL_TIMEOUT_SECONDS", "200")
        settings = AgentSettings()
        assert settings.overall_timeout_seconds == 200


class TestAgentSettingsValidation:
    """Test validation rejects out-of-range values."""

    def test_rejects_zero_iterations(self):
        with pytest.raises(ValidationError):
            AgentSettings(max_loop_iterations=0)

    def test_rejects_negative_cost(self):
        with pytest.raises(ValidationError):
            AgentSettings(cost_limit_usd=-1.0)

    def test_rejects_timeout_at_300(self):
        """overall_timeout_seconds must be < 300 (Cloud Run limit)."""
        with pytest.raises(ValidationError):
            AgentSettings(overall_timeout_seconds=300)

    def test_accepts_boundary_timeout_299(self):
        settings = AgentSettings(overall_timeout_seconds=299)
        assert settings.overall_timeout_seconds == 299


class TestAgentSettingsRepr:
    """Test __repr__ format."""

    def test_repr_format(self):
        settings = AgentSettings()
        assert repr(settings) == f"AgentSettings(model='{GEMINI_FLASH}', max_iterations=10, use_adk=True)"

    def test_repr_with_custom_model(self):
        settings = AgentSettings(model=GEMINI_FLASH, max_loop_iterations=5)
        assert repr(settings) == f"AgentSettings(model='{GEMINI_FLASH}', max_iterations=5, use_adk=True)"


class TestAgentSettingsDynamicCostRates:
    """Test cost rates are synced from GEMINI_PRICING based on model."""

    def test_flash_rates(self):
        settings = AgentSettings(model=GEMINI_FLASH)
        assert settings.cost_input_rate_per_million == 0.50
        assert settings.cost_output_rate_per_million == 3.00

    def test_pro_rates(self):
        from src.common.gemini_models import GEMINI_PRO
        settings = AgentSettings(model=GEMINI_PRO)
        assert settings.cost_input_rate_per_million == 2.00
        assert settings.cost_output_rate_per_million == 12.00

    def test_flash_lite_rates(self):
        from src.common.gemini_models import GEMINI_FLASH_LITE
        settings = AgentSettings(model=GEMINI_FLASH_LITE)
        assert settings.cost_input_rate_per_million == 0.25
        assert settings.cost_output_rate_per_million == 1.50
