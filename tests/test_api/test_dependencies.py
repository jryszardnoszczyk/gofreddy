"""Tests for _resolve_user_from_jwt — identity linking and race conditions."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from src.billing.models import User


@pytest.fixture
def mock_repo() -> MagicMock:
    """Mock BillingRepository with default no-user state."""
    repo = MagicMock()
    repo.get_user_by_supabase_id = AsyncMock(return_value=None)
    repo.get_user_by_email = AsyncMock(return_value=None)
    repo.create_user = AsyncMock()
    repo.link_supabase_user = AsyncMock(return_value=True)
    return repo


@pytest.fixture
def mock_request(mock_repo: MagicMock) -> MagicMock:
    """Mock Request with billing_repository on app.state."""
    request = MagicMock()
    request.app.state.billing_repository = mock_repo
    return request


def _make_user(
    *,
    email: str = "test@example.com",
    supabase_user_id: str | None = None,
) -> User:
    from datetime import datetime, timezone

    return User(
        id=uuid4(),
        email=email,
        stripe_customer_id=None,
        supabase_user_id=supabase_user_id,
        created_at=datetime.now(timezone.utc),
    )


@pytest.mark.mock_required
class TestResolveUserFromJwt:
    """Tests for _resolve_user_from_jwt in src/api/dependencies.py."""

    async def _call(self, request, claims):
        from src.api.dependencies import _resolve_user_from_jwt

        return await _resolve_user_from_jwt(request, claims)

    @pytest.mark.asyncio
    async def test_normalizes_email_to_lowercase(
        self, mock_request: MagicMock, mock_repo: MagicMock
    ) -> None:
        """JWT email is lowercased before lookup."""
        new_user = _make_user(email="user@example.com", supabase_user_id="sub-1")
        mock_repo.create_user = AsyncMock(return_value=new_user)

        await self._call(mock_request, {"sub": "sub-1", "email": "User@Example.COM"})

        # Verify email was lowered before create_user
        mock_repo.get_user_by_email.assert_awaited_once_with("user@example.com")

    @pytest.mark.asyncio
    async def test_identity_conflict_returns_409(
        self, mock_request: MagicMock, mock_repo: MagicMock
    ) -> None:
        """Linking to user with existing different Supabase identity returns 409."""
        existing = _make_user(supabase_user_id="other-sub-id")
        mock_repo.get_user_by_email = AsyncMock(return_value=existing)
        mock_repo.link_supabase_user = AsyncMock(return_value=False)

        with pytest.raises(HTTPException) as exc_info:
            await self._call(mock_request, {"sub": "new-sub-id", "email": "test@example.com"})

        assert exc_info.value.status_code == 409
        assert exc_info.value.detail["code"] == "identity_conflict"

    @pytest.mark.asyncio
    async def test_idempotent_relink_succeeds(
        self, mock_request: MagicMock, mock_repo: MagicMock
    ) -> None:
        """Re-linking same Supabase identity to same user succeeds silently."""
        existing = _make_user(supabase_user_id="same-sub-id")
        mock_repo.get_user_by_email = AsyncMock(return_value=existing)

        result = await self._call(
            mock_request, {"sub": "same-sub-id", "email": "test@example.com"}
        )

        assert result == existing.id
        # link_supabase_user should NOT be called (idempotent early return)
        mock_repo.link_supabase_user.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_unique_violation_retries_lookup(
        self, mock_request: MagicMock, mock_repo: MagicMock
    ) -> None:
        """Concurrent create_user race → UniqueViolationError → retry lookup succeeds."""
        import asyncpg

        existing = _make_user(email="race@example.com", supabase_user_id="sub-x")

        mock_repo.create_user = AsyncMock(
            side_effect=asyncpg.UniqueViolationError("")
        )
        # First call returns None (race window), second call finds the user
        mock_repo.get_user_by_email = AsyncMock(
            side_effect=[None, existing]
        )

        result = await self._call(
            mock_request, {"sub": "sub-new", "email": "race@example.com"}
        )

        assert result == existing.id
        assert mock_repo.get_user_by_email.await_count == 2

    @pytest.mark.asyncio
    async def test_missing_sub_claim_raises_401(
        self, mock_request: MagicMock
    ) -> None:
        """Missing 'sub' claim in JWT returns 401."""
        with pytest.raises(HTTPException) as exc_info:
            await self._call(mock_request, {"email": "test@example.com"})

        assert exc_info.value.status_code == 401
