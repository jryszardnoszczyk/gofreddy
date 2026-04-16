"""Tests for PR-059 WS-4: Auth hardening (token blocklist + timing-safe API key)."""

from uuid import uuid4

import pytest

from src.api.dependencies import (
    _blocklist_token_key,
    _token_blocklist,
    is_token_revoked,
    revoke_token,
)


class TestTokenBlocklist:
    """Token blocklist functions."""

    def setup_method(self):
        _token_blocklist.clear()

    def test_revoke_token_with_jti(self):
        claims = {"jti": "abc-123", "sub": "user-1", "iat": 1000}
        assert revoke_token(claims) is True
        assert is_token_revoked(claims) is True

    def test_revoke_token_without_jti_uses_sub_iat(self):
        claims = {"sub": "user-1", "iat": 1000}
        assert revoke_token(claims) is True
        assert is_token_revoked(claims) is True

    def test_revoke_token_without_jti_or_iat_returns_false(self):
        claims = {"sub": "user-1"}
        assert revoke_token(claims) is False
        assert is_token_revoked(claims) is False

    def test_unrevoked_token_not_blocked(self):
        claims = {"jti": "not-revoked", "sub": "user-1", "iat": 1000}
        assert is_token_revoked(claims) is False

    def test_blocklist_key_prefers_jti(self):
        claims = {"jti": "token-id", "sub": "user-1", "iat": 1000}
        assert _blocklist_token_key(claims) == "jti:token-id"

    def test_blocklist_key_composite_fallback(self):
        claims = {"sub": "user-1", "iat": 1000}
        assert _blocklist_token_key(claims) == "sub:user-1:iat:1000"

    def test_blocklist_key_none_without_identifiers(self):
        assert _blocklist_token_key({}) is None
        assert _blocklist_token_key({"sub": "user-1"}) is None


class TestTimingSafeAPIKeyComparison:
    """API key comparison uses hmac.compare_digest."""

    @pytest.mark.db
    async def test_api_key_correct_key_returns_user(self, billing_repo, db_pool):
        """Correct key returns user via timing-safe comparison."""
        uid = uuid4().hex[:8]
        async with db_pool.acquire() as conn:
            user_row = await conn.fetchrow(
                "INSERT INTO users (email, supabase_user_id) VALUES ($1, $2) RETURNING id",
                f"apikey-correct-{uid}@example.com",
                f"sb-api-key-correct-{uid}",
            )
            user_id = user_row["id"]

        api_key = f"vi_sk_test_{uid}_1234567890"
        await billing_repo.create_api_key(user_id, api_key, "test-key")

        user = await billing_repo.get_user_by_api_key(api_key)
        assert user is not None
        assert user.id == user_id

    @pytest.mark.db
    async def test_api_key_wrong_key_returns_none(self, billing_repo, db_pool):
        """Wrong key returns None."""
        uid = uuid4().hex[:8]
        async with db_pool.acquire() as conn:
            user_row = await conn.fetchrow(
                "INSERT INTO users (email, supabase_user_id) VALUES ($1, $2) RETURNING id",
                f"apikey-wrong-{uid}@example.com",
                f"sb-api-key-wrong-{uid}",
            )
            user_id = user_row["id"]

        api_key = f"vi_sk_correct_{uid}_12345"
        await billing_repo.create_api_key(user_id, api_key, "test-key")

        user = await billing_repo.get_user_by_api_key(f"vi_sk_wrong_{uid}_12345")
        assert user is None

    def test_get_user_by_api_key_uses_hmac(self):
        """Verify get_user_by_api_key source contains hmac.compare_digest."""
        import inspect

        from src.billing.repository import BillingRepository

        source = inspect.getsource(BillingRepository.get_user_by_api_key)
        assert "hmac.compare_digest" in source
