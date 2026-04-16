"""Shared fixtures for competitive intelligence tests."""

from __future__ import annotations

import pytest

from src.competitive.config import CompetitiveSettings
from src.competitive.providers.foreplay import ForeplayProvider
from src.competitive.providers.adyntel import AdyntelProvider
from src.competitive.service import CompetitiveAdService


@pytest.fixture
def comp_settings() -> CompetitiveSettings:
    return CompetitiveSettings(
        foreplay_api_key="test-foreplay-key",
        foreplay_timeout_seconds=5,
        adyntel_api_key="test-adyntel-key",
        adyntel_email="test@example.com",
        adyntel_timeout_seconds=5,
        foreplay_daily_credit_limit=5000,
    )


@pytest.fixture
def foreplay_provider() -> ForeplayProvider:
    return ForeplayProvider(
        api_key="test-foreplay-key",
        timeout=5,
        daily_credit_limit=5000,
    )


@pytest.fixture
def adyntel_provider() -> AdyntelProvider:
    return AdyntelProvider(
        api_key="test-adyntel-key",
        email="test@example.com",
        timeout=5,
    )


@pytest.fixture
def ad_service(
    foreplay_provider: ForeplayProvider,
    adyntel_provider: AdyntelProvider,
    comp_settings: CompetitiveSettings,
) -> CompetitiveAdService:
    return CompetitiveAdService(
        foreplay_provider=foreplay_provider,
        adyntel_provider=adyntel_provider,
        settings=comp_settings,
    )
