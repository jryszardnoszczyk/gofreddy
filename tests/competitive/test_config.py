"""Tests for competitive intelligence configuration and domain validation."""

from __future__ import annotations

import pytest

from src.competitive.config import CompetitiveSettings
from src.competitive.utils import normalize_domain


class TestCompetitiveSettings:
    def test_defaults(self) -> None:
        settings = CompetitiveSettings(
            foreplay_api_key="",
            adyntel_api_key="",
        )
        assert settings.foreplay_timeout_seconds == 30
        assert settings.adyntel_timeout_seconds == 30
        assert settings.foreplay_daily_credit_limit == 5000
        assert settings.adyntel_max_pages == 1
        assert settings.enable_vision_enrichment is True

    def test_secret_str_values(self) -> None:
        settings = CompetitiveSettings(
            foreplay_api_key="fp-key-123",
            adyntel_api_key="ad-key-456",
        )
        assert settings.foreplay_api_key.get_secret_value() == "fp-key-123"
        assert settings.adyntel_api_key.get_secret_value() == "ad-key-456"
        # SecretStr repr should not leak the key
        assert "fp-key-123" not in repr(settings.foreplay_api_key)


class TestNormalizeDomain:
    def test_bare_domain(self) -> None:
        assert normalize_domain("nike.com") == "nike.com"

    def test_strips_https(self) -> None:
        assert normalize_domain("https://nike.com") == "nike.com"

    def test_strips_http(self) -> None:
        assert normalize_domain("http://nike.com") == "nike.com"

    def test_strips_www(self) -> None:
        assert normalize_domain("www.nike.com") == "nike.com"

    def test_strips_protocol_and_www(self) -> None:
        assert normalize_domain("https://www.nike.com") == "nike.com"

    def test_strips_path(self) -> None:
        assert normalize_domain("nike.com/shoes") == "nike.com"

    def test_strips_path_with_query(self) -> None:
        assert normalize_domain("nike.com/shoes?q=1") == "nike.com"

    def test_strips_fragment(self) -> None:
        assert normalize_domain("nike.com#section") == "nike.com"

    def test_strips_trailing_slash(self) -> None:
        assert normalize_domain("nike.com/") == "nike.com"

    def test_lowercases(self) -> None:
        assert normalize_domain("Nike.COM") == "nike.com"

    def test_strips_whitespace(self) -> None:
        assert normalize_domain("  nike.com  ") == "nike.com"

    def test_subdomain(self) -> None:
        assert normalize_domain("ads.nike.com") == "ads.nike.com"

    def test_full_url_with_everything(self) -> None:
        assert normalize_domain("https://www.nike.com/shoes?q=1#section") == "nike.com"

    def test_invalid_domain_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid domain format"):
            normalize_domain("not a domain")

    def test_empty_string_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid domain format"):
            normalize_domain("")

    def test_ip_address_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid domain format"):
            normalize_domain("192.168.1.1")
