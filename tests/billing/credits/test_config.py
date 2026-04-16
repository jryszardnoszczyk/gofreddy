"""Tests for credit billing configuration."""

import pytest

from src.billing.credits.config import BillingFlags, CreditSettings


class TestBillingFlags:
    def test_defaults_with_env(self):
        """Credit billing is active (hybrid_write_enabled=true in .env)."""
        flags = BillingFlags()
        assert flags.shadow_metering_enabled is False
        assert flags.hybrid_write_enabled is True  # Activated in PR-099
        assert flags.hybrid_read_enabled is False
        assert flags.analysis_transcript_first_enabled is False

    def test_loads_from_env(self, monkeypatch):
        monkeypatch.setenv("BILLING_FLAG_SHADOW_METERING_ENABLED", "true")
        monkeypatch.setenv("BILLING_FLAG_HYBRID_WRITE_ENABLED", "true")
        flags = BillingFlags()
        assert flags.shadow_metering_enabled is True
        assert flags.hybrid_write_enabled is True
        assert flags.hybrid_read_enabled is False


class TestCreditSettings:
    def test_defaults(self):
        settings = CreditSettings()
        assert settings.l1_cost == 1
        assert settings.l2_cost == 2
        assert settings.forensic_addon_cost == 2
        assert settings.sync_reservation_ttl_minutes == 15
        assert settings.async_reservation_ttl_minutes == 30
        assert settings.promo_expiry_days == 90

    def test_pack_catalog_default(self):
        settings = CreditSettings()
        assert settings.pack_catalog == {
            "starter_100": (100, 999),
            "growth_500": (500, 3999),
            "scale_2000": (2000, 14999),
        }

    def test_pack_catalog_from_json_env(self, monkeypatch):
        monkeypatch.setenv("CREDIT_PACK_CATALOG", '{"test_5": [5, 499]}')
        settings = CreditSettings()
        assert settings.pack_catalog == {"test_5": (5, 499)}

    def test_loads_from_env(self, monkeypatch):
        monkeypatch.setenv("CREDIT_L1_COST", "3")
        monkeypatch.setenv("CREDIT_L2_COST", "5")
        settings = CreditSettings()
        assert settings.l1_cost == 3
        assert settings.l2_cost == 5

    def test_pack_catalog_rejects_zero_credits(self, monkeypatch):
        monkeypatch.setenv("CREDIT_PACK_CATALOG", '{"bad": [0, 999]}')
        with pytest.raises(ValueError, match="invalid credits"):
            CreditSettings()

    def test_pack_catalog_rejects_negative_credits(self, monkeypatch):
        monkeypatch.setenv("CREDIT_PACK_CATALOG", '{"bad": [-5, 999]}')
        with pytest.raises(ValueError, match="invalid credits"):
            CreditSettings()

    def test_pack_catalog_rejects_zero_price(self, monkeypatch):
        monkeypatch.setenv("CREDIT_PACK_CATALOG", '{"bad": [10, 0]}')
        with pytest.raises(ValueError, match="invalid price_cents"):
            CreditSettings()

    def test_frontend_base_url_default(self):
        settings = CreditSettings()
        assert settings.frontend_base_url == "http://localhost:5173"
