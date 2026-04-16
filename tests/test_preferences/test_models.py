"""Tests for user preferences models."""

import pytest

from src.common.gemini_models import GEMINI_FLASH, GEMINI_FLASH_LITE, GEMINI_PRO
from src.preferences.models import UserPreferences, ALLOWED_AGENT_MODELS


class TestUserPreferences:
    def test_defaults_to_flash(self):
        prefs = UserPreferences()
        assert prefs.agent_model == GEMINI_FLASH

    def test_accepts_pro_model(self):
        prefs = UserPreferences(agent_model=GEMINI_PRO)
        assert prefs.agent_model == GEMINI_PRO

    def test_accepts_flash_lite_model(self):
        prefs = UserPreferences(agent_model=GEMINI_FLASH_LITE)
        assert prefs.agent_model == GEMINI_FLASH_LITE

    def test_rejects_unknown_model(self):
        with pytest.raises(Exception):
            UserPreferences(agent_model="gemini-unknown")

    def test_from_empty_dict(self):
        prefs = UserPreferences(**{})
        assert prefs.agent_model == GEMINI_FLASH

    def test_allowed_models_contains_all_three(self):
        assert GEMINI_FLASH_LITE in ALLOWED_AGENT_MODELS
        assert GEMINI_FLASH in ALLOWED_AGENT_MODELS
        assert GEMINI_PRO in ALLOWED_AGENT_MODELS
