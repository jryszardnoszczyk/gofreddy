"""Tests for PR-059 WS-1: Config validation sweep."""

import os

import pytest
from pydantic import SecretStr, ValidationError


class TestDatabaseUrlSecretStr:
    """database_url must be SecretStr to prevent credential leaking."""

    def test_database_url_is_secret_str(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@host/db")
        from src.analysis.config import DatabaseSettings

        settings = DatabaseSettings()
        assert isinstance(settings.database_url, SecretStr)

    def test_database_url_hidden_in_repr(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:secret@host/db")
        from src.analysis.config import DatabaseSettings

        settings = DatabaseSettings()
        repr_str = repr(settings)
        assert "secret" not in repr_str.lower() or "SecretStr" in repr_str

    def test_database_url_get_secret_value(self, monkeypatch):
        dsn = "postgresql://user:pass@host/db"
        monkeypatch.setenv("DATABASE_URL", dsn)
        from src.analysis.config import DatabaseSettings

        settings = DatabaseSettings()
        assert settings.database_url.get_secret_value() == dsn


class TestFrontendBaseUrlProdEnforcement:
    """frontend_base_url must not be localhost in production."""

    def test_rejects_localhost_in_production(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("CREDIT_FRONTEND_BASE_URL", "http://localhost:5173")
        from src.billing.credits.config import CreditSettings

        with pytest.raises(ValidationError, match="localhost"):
            CreditSettings()

    def test_rejects_loopback_in_production(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("CREDIT_FRONTEND_BASE_URL", "http://127.0.0.1:5173")
        from src.billing.credits.config import CreditSettings

        with pytest.raises(ValidationError, match="localhost"):
            CreditSettings()

    def test_allows_localhost_in_development(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "development")
        from src.billing.credits.config import CreditSettings

        settings = CreditSettings()
        assert "localhost" in settings.frontend_base_url

    def test_allows_real_url_in_production(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("CREDIT_FRONTEND_BASE_URL", "https://app.example.com")
        from src.billing.credits.config import CreditSettings

        settings = CreditSettings()
        assert settings.frontend_base_url == "https://app.example.com"


class TestSupabaseSettingsValidation:
    """SupabaseSettings must reject empty strings."""

    def test_rejects_empty_url(self, monkeypatch):
        monkeypatch.setenv("SUPABASE_URL", "")
        monkeypatch.setenv("SUPABASE_ANON_KEY", "valid-key")
        monkeypatch.setenv("SUPABASE_JWT_SECRET", "valid-secret")
        from src.auth.config import SupabaseSettings

        with pytest.raises(ValidationError):
            SupabaseSettings()

    def test_rejects_empty_anon_key(self, monkeypatch):
        monkeypatch.setenv("SUPABASE_URL", "https://x.supabase.co")
        monkeypatch.setenv("SUPABASE_ANON_KEY", "")
        monkeypatch.setenv("SUPABASE_JWT_SECRET", "valid-secret")
        from src.auth.config import SupabaseSettings

        with pytest.raises(ValidationError):
            SupabaseSettings()

    def test_rejects_empty_jwt_secret(self, monkeypatch):
        monkeypatch.setenv("SUPABASE_URL", "https://x.supabase.co")
        monkeypatch.setenv("SUPABASE_ANON_KEY", "valid-key")
        monkeypatch.setenv("SUPABASE_JWT_SECRET", "")
        from src.auth.config import SupabaseSettings

        with pytest.raises(ValidationError):
            SupabaseSettings()

    def test_accepts_valid_settings(self, monkeypatch):
        monkeypatch.setenv("SUPABASE_URL", "https://x.supabase.co")
        monkeypatch.setenv("SUPABASE_ANON_KEY", "valid-key")
        monkeypatch.setenv("SUPABASE_JWT_SECRET", "valid-secret")
        from src.auth.config import SupabaseSettings

        settings = SupabaseSettings()
        assert settings.supabase_url == "https://x.supabase.co"
