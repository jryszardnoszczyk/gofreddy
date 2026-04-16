"""Tests for generation config."""

import os

from src.generation.config import GenerationSettings


def _clear_generation_env(monkeypatch):
    for key in list(os.environ):
        if key.startswith("GENERATION_"):
            monkeypatch.delenv(key, raising=False)


def test_default_settings(monkeypatch):
    _clear_generation_env(monkeypatch)
    settings = GenerationSettings(_env_file=None)
    assert settings.generation_enabled is False
    assert settings.default_aspect_ratio == "9:16"
    assert settings.max_cadres_per_video == 20
    assert settings.daily_spend_limit_cents == 5000
    assert settings.cost_per_second_cents_480p == 5
    assert settings.cost_per_second_cents_720p == 7
    assert settings.xai_api_key is None
    assert settings.xai_video_model == "grok-imagine-video"


def test_env_prefix(monkeypatch):
    _clear_generation_env(monkeypatch)
    monkeypatch.setenv("GENERATION_GENERATION_ENABLED", "true")
    monkeypatch.setenv("GENERATION_DAILY_SPEND_LIMIT_CENTS", "10000")
    monkeypatch.setenv("GENERATION_XAI_VIDEO_MODEL", "grok-imagine-video")
    settings = GenerationSettings(_env_file=None)
    assert settings.generation_enabled is True
    assert settings.daily_spend_limit_cents == 10000
    assert settings.xai_video_model == "grok-imagine-video"
